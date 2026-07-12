import os, re

base = r'C:\Users\s2132\Desktop\pewacheck\hits'
hedef = None
for d in os.listdir(base):
    if 'bans' in d.lower():
        hedef = os.path.join(base, d)
        break

hesaplar = {}

for dosya in os.listdir(hedef):
    if not dosya.endswith('.txt'):
        continue
    for satir in open(os.path.join(hedef, dosya), encoding='utf-8', errors='ignore'):
        if 'RC:' not in satir:
            continue
        kullanici = satir.split('|')[0].strip()
        m = re.search(r'RC:\s*(\d+)\s*RC', satir)
        if not m:
            continue
        rc = int(m.group(1))
        if rc == 0:
            continue
        if kullanici not in hesaplar or hesaplar[kullanici] < rc:
            hesaplar[kullanici] = rc

sirali = sorted(hesaplar.items(), key=lambda x: x[1], reverse=True)

print(f"{'Hesap':<45} {'RC':>6}")
print("-" * 55)
for hesap, rc in sirali[:25]:
    print(f"{hesap:<45} {rc:>6} RC")
