<div align="center">

# ⚡ CraftRise Account Checker v3.0

**Java + Python | Ban Detection | Tier Detect | Detaylı Bilgi**

by [xlaeuss](https://t.me/xlaeussx) • [Telegram](https://t.me/xlaeussx)

</div>

---

## 📌 Hakkında

CraftRise.com.tr hesaplarını hızlı ve otomatik olarak kontrol eden gelişmiş bir checker aracıdır.  
Java tabanlı multi-thread checker, Python API ile birlikte çalışır. Cloudflare bypass için Cloudflare WARP entegrasyonu mevcuttur.

---

## ✨ Özellikler

- ⚡ **Multi-thread Java Checker** — Yüksek hızlı hesap kontrolü
- 🎨 **Python Rich UI** — Canlı istatistik paneli (Hit, Bad, Queue, Tier dağılımı)
- 🔍 **Ban Tespiti** — Banlı / Bansız / Belirsiz kategorileri
- 🏆 **Tier Tespiti** — Kömür, Demir, Kızıltaş, Altın, Elmas, Zümrüt, Obsidyen, Ametist
- 📋 **Detaylı Bilgi Çekme** — Ad-soyad, doğum tarihi, telefon, şehir, adres, VIP süresi, toplam ödeme, market işlemleri
- 🌐 **Cloudflare WARP Entegrasyonu** — Token hatalarında otomatik WARP yeniden bağlantısı
- 📦 **Akıllı Kuyruk Sistemi** — Başarılı loginler kuyruğa alınıp sırayla işlenir
- 💾 **Otomatik Hit Kayıt** — `hits/` ve `detaylı_hits/` klasörlerine otomatik kayıt
- 🚀 **Tek Tıkla Başlatma** — `start.bat` ile tüm bileşenler otomatik başlar

---

## 📁 Dosya Yapısı

```
📦 xlaeuss-craftrise-checker/
 ┣ 📄 start.bat                                        ← Buradan başlat
 ┣ 🐍 checker.py                                       ← Python API + Rich UI
 ┣ 🐍 warp_token.py                                    ← Cloudflare WARP Token servisi
 ┣ ☕ account-checker-1.0.0-jar-with-dependencies.jar  ← Java multi-thread checker
 ┣ 📄 hesaplar.txt                                     ← Hesapları buraya yaz
 ┣ 🐍 rc_sirala.py                                     ← Hit sıralama aracı
 ┣ 🐍 say.py                                           ← Sayım aracı
 ┣ 🐍 uyelik_bul.py                                    ← Üyelik bulucu
 ┣ 📋 requirements.txt                                 ← Python kütüphaneleri
 ┗ 📂 jar checker source/                              ← Java kaynak kodu
```

---

## ⚙ Gereksinimler

| Gereksinim | Link |
|---|---|
| Python 3.13+ | https://www.python.org/ |
| Java 17+ | https://adoptium.net/ |
| Cloudflare WARP | https://one.one.one.one/ |
| Microsoft Edge | (WARP token çekimi için) |

---

## 🚀 Kurulum & Kullanım

1. `hesaplar.txt` dosyasını aç, `kullanici:sifre` formatında hesapları ekle
2. `start.bat`'a çift tıkla
3. Script otomatik olarak:
   - Python kütüphanelerini kurar
   - WARP Token API'yi başlatır
   - Python Checker API'yi başlatır
   - Java Checker'ı başlatır
4. Hitler `hits/` ve `detaylı_hits/` klasörlerine kaydedilir

> ⚠️ **NOT:** Cloudflare WARP yüklü ve bağlı olmalıdır. WARP olmadan token alınamaz.

---

## 👤 Krediler

- **Geliştirici:** xlaeuss  
- **Telegram:** [t.me/xlaeussx](https://t.me/xlaeussx)  
- **Versiyon:** v3.0

---

<div align="center">

*Bu araç sadece eğitim amaçlıdır.*

</div>
