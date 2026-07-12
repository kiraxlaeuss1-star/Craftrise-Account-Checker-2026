import glob

klasor = r'C:\Users\s2132\Desktop\pewacheck\hits\bansız'

for dosya in glob.glob(klasor + '\\*.txt'):
    with open(dosya, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if 'Üyelik:' in line and 'Üyelik: OYUNCU' not in line:
                parcalar = line.split('|')
                kullanici = parcalar[0].strip()
                rc = next((x.strip() for x in parcalar if 'RC:' in x and 'E-Mail' not in x), '')
                uyelik = next((x.strip() for x in parcalar if 'Üyelik:' in x), '')
                rank = next((x.strip() for x in parcalar if 'Rank:' in x), '')
                print(f"{kullanici} | {rc} | {uyelik} | {rank}")
