from flask import Flask, jsonify
from DrissionPage import ChromiumPage, ChromiumOptions
import time
import subprocess
import os
import logging
import threading
from datetime import datetime

# Flask logging'i kapat
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.logger.disabled = True

# ============================== CONFIG ==============================
CLOUDFLARE_SITEKEY = '0x4AAAAAAA4cK60wpgOTyti9'
CRAFTRISE_URL = 'https://www.craftrise.com.tr'
TOKEN_TIMEOUT = 20  # saniye
WARP_RESTART_THRESHOLD = 2  # Kaç token hatası sonrası WARP restart
WARP_AUTO_RESTART_INTERVAL = 300 

# ============================== GLOBALS ==============================
page = None
widget_id = None
token_failures = 0
last_warp_restart = time.time()

# ============================== BROWSER SETUP ==============================
def get_edge_path():
    """Microsoft Edge yolunu bulur"""
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    
    for path in edge_paths:
        if os.path.exists(path):
            return path
    return None

def create_browser_options():
    """Tarayıcı seçeneklerini oluşturur"""
    co = ChromiumOptions()
    
    browser_path = get_edge_path()
    if browser_path:
        co.set_browser_path(browser_path)
    
    co.auto_port()  # Port çakışmalarını önle
    return co

def start_browser():
    """Tarayıcıyı başlatır (SADECE İLK AÇILIŞTA ÇAĞRILMALI!)"""
    global page
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] !!! YENİ TARAYICI AÇILIYOR !!!")
        co = create_browser_options()
        page = ChromiumPage(co)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Tarayıcı başlatıldı")
        return True
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Tarayıcı başlatma hatası: {e}")
        return False

# ============================== WARP MANAGEMENT ==============================
def restart_warp():
    """WARP VPN'i yeniden başlatır"""
    global last_warp_restart
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] WARP yeniden başlatılıyor...")
        subprocess.run(["warp-cli", "disconnect"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        subprocess.run(["warp-cli", "connect"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)
        last_warp_restart = time.time()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] WARP yeniden başlatıldı")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] WARP restart hatası: {e}")

def auto_restart_warp_loop():
    """Her 15 dakikada bir WARP'ı otomatik restart eder"""
    global page
    
    while True:
        time.sleep(WARP_AUTO_RESTART_INTERVAL)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Otomatik WARP restart başlıyor...")
        restart_warp()
        
        # Mevcut tarayıcıyı kontrol et
        if not page:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] UYARI: Tarayıcı bulunamadı!")
            continue
        
        try:
            # Sadece sayfayı yenile (YENİ TARAYICI AÇMA!)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Sayfa yenileniyor...")
            page.refresh()
            time.sleep(3)
            
            # Widget'ı yeniden başlat
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Widget yenileniyor...")
            if reinitialize_turnstile():
                print(f"[{datetime.now().strftime('%H:%M:%S')}] WARP restart tamamlandı")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Widget yenileme başarısız")
                
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Sayfa yenileme hatası: {e}")

# ============================== TURNSTILE SETUP ==============================
def inject_turnstile_widget():
    """Turnstile widget'ını sayfaya inject eder"""
    global page
    
    if not page:
        return False
    
    js_code = f"""
    // Turnstile script'i zaten yüklü mü kontrol et
    if (!window.turnstile) {{
        const script = document.createElement('script');
        script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js';
        script.async = true;
        script.defer = true;
        document.head.appendChild(script);
        
        script.onload = () => {{
            renderWidget();
        }};
    }} else {{
        renderWidget();
    }}
    
    function renderWidget() {{
        const div = document.createElement('div');
        div.id = 'captcha-container';
        document.body.appendChild(div);
        
        const id = turnstile.render('#captcha-container', {{
            sitekey: '{CLOUDFLARE_SITEKEY}',
            callback: function(token) {{
                window._cf_token = token;
                console.log('Token received:', token.substring(0, 20) + '...');
            }}
        }});
        window._cf_widget_id = id;
    }}
    """
    
    try:
        page.run_js(js_code)
        return True
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Widget inject hatası: {e}")
        return False

def reinitialize_turnstile():
    """Mevcut sayfada widget'ı yeniden başlatır (yeni tarayıcı açmaz)"""
    global page
    
    if not page:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Tarayıcı bulunamadı, widget yenilenemedi")
        return False
    
    try:
        # Önce mevcut widget'ı temizle
        page.run_js("""
            if (window._cf_widget_id !== undefined) {
                try {
                    turnstile.remove(window._cf_widget_id);
                } catch(e) {}
            }
            const oldDiv = document.getElementById('captcha-container');
            if (oldDiv) oldDiv.remove();
            window._cf_token = undefined;
            window._cf_widget_id = undefined;
        """)
        
        time.sleep(1)
        
        # Yeni widget inject et
        inject_turnstile_widget()
        
        # Widget'ın yüklenmesini bekle
        for i in range(TOKEN_TIMEOUT):
            has_token = page.run_js('return window._cf_token !== undefined')
            has_widget = page.run_js('return window._cf_widget_id !== undefined')
            if has_token and has_widget:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Widget yenilendi ({i+1}s)")
                return True
            time.sleep(1)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Widget yenileme timeout")
        return False
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Widget yenileme hatası: {e}")
        return False

def initialize_turnstile():
    """Cloudflare Turnstile widget'ını başlatır (ilk açılış)"""
    if not start_browser():
        return False

    try:
        page.get(CRAFTRISE_URL)
        time.sleep(3)

        inject_turnstile_widget()

        # Widget'ın yüklenmesini bekle
        for _ in range(TOKEN_TIMEOUT):
            has_token = page.run_js('return window._cf_token !== undefined')
            has_widget = page.run_js('return window._cf_widget_id !== undefined')
            if has_token and has_widget:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Turnstile widget başarıyla yüklendi")
                return True
            time.sleep(1)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Turnstile widget yüklenemedi")
        return False

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Turnstile başlatma hatası: {e}")
        return False

# ============================== TOKEN MANAGEMENT ==============================
def get_fresh_token():
    """Yeni bir Turnstile token'ı alır"""
    global token_failures
    
    try:
        if not page:
            return None

        # Mevcut token'ı temizle ve widget'ı resetle
        page.run_js("window._cf_token = undefined;")
        page.run_js("if (window._cf_widget_id !== undefined) { turnstile.reset(window._cf_widget_id); }")

        # Yeni token'ı bekle
        for _ in range(TOKEN_TIMEOUT):
            token = page.run_js('return window._cf_token || null;')
            if token:
                token_failures = 0
                return token
            time.sleep(1)

        # Token alınamadı
        token_failures += 1
        
        # Eşik aşıldıysa WARP'ı restart et
        if token_failures >= WARP_RESTART_THRESHOLD:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {WARP_RESTART_THRESHOLD} token hatası! WARP restart...")
            restart_warp()
            token_failures = 0
            time.sleep(2)
            page.refresh()
            time.sleep(3)
            reinitialize_turnstile()

        return None

    except Exception as e:
        token_failures += 1
        return None

# ============================== FLASK ENDPOINTS ==============================
@app.route('/get-token', methods=['GET'])
def get_new_token():
    """Yeni Turnstile token döner"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Token istendi...")
    token = get_fresh_token()
    
    if token:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Token basariyla uretildi")
        return jsonify({"token": token}), 200
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Token uretilemedi!")
        return jsonify({"error": "Yeni token alınamadı"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Servis sağlık kontrolü"""
    return jsonify({
        "status": "ok",
        "browser_active": page is not None,
        "token_failures": token_failures,
        "last_warp_restart": datetime.fromtimestamp(last_warp_restart).strftime('%H:%M:%S')
    }), 200

@app.route('/')
def index():
    """Ana sayfa"""
    return jsonify({
        "service": "Cloudflare Turnstile Token API",
        "status": "running",
        "endpoints": {
            "get_token": "/get-token",
            "health": "/health"
        }
    })

# ============================== MAIN ==============================
if __name__ == '__main__':
    try:
        print("=" * 60)
        print("   CLOUDFLARE TURNSTILE TOKEN API")
        print("=" * 60)
        
        if initialize_turnstile():
            # Otomatik WARP restart thread'ini başlat
            warp_thread = threading.Thread(target=auto_restart_warp_loop, daemon=True)
            warp_thread.start()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Otomatik WARP restart aktif (Her 15 dakika)")
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Token API başlatılıyor (Port: 5001)")
            print("=" * 60)
            app.run(host='0.0.0.0', port=5001, debug=False)
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Turnstile başlatılamadı, servis kapatılıyor")
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Servis kapatılıyor...")
    finally:
        if page:
            page.quit()
