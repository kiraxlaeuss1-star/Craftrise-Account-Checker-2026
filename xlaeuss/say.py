import os, re

base = r'C:\Users\s2132\Desktop\pewacheck\hits'
# bansız klasörünü bul
hedef = None
for d in os.listdir(base):
    if 'bans' in d.lower():
        hedef = os.path.join(base, d)
        break

if not hedef:
    print("Klasör bulunamadı")
    exit()

print(f"Klasör: {hedef}")
toplam = 0
rcli = 0

for dosya in os.listdir(hedef):
    if not dosya.endswith('.txt'):
        continue
    yol = os.path.join(hedef, dosya)
    for satir in open(yol, encoding='utf-8', errors='ignore'):
        toplam += 1
        m = re.search(r'RC:\s*(\d+)\s*RC', satir)
        if m and int(m.group(1)) > 0:
            rcli += 1

print(f"Toplam bansız hit: {toplam}")
print(f"RC > 0 olan: {rcli}")
print(f"RC = 0 olan: {toplam - rcli}")
