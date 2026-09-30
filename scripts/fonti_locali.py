"""Font self-hosted AMI (anti-FOUT).

Il sito NON usa piu' il CSS di Google Fonts a runtime: i woff2 sono
versionati in assets/fonts/ e dichiarati in assets/stylesheets/fonts.css
(con font-display: block). Questo script serve SOLO a rigenerare gli
asset quando cambiano pesi/famiglie richieste.

Uso:
    python scripts/fonti_locali.py            # rigenera solo se necessario
    python scripts/fonti_locali.py --force    # riscrive tutto

Nota: Fraunces e' un font variabile (opsz 9..144): il css2 di Google
restituisce lo stesso file per i pesi richiesti; i blocchi @font-face
mantengono weight espliciti 400/600/900 come l'originale.
"""
import os
import re
import sys
import urllib.request

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS_DIR = os.path.join(ROOT_DIR, 'assets', 'fonts')
CSS_DEST = os.path.join(ROOT_DIR, 'assets', 'stylesheets', 'fonts.css')

# Stessa richiesta dell'URL rimosso da overrides/main.html
API_URL = ('https://fonts.googleapis.com/css2?'
           'family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;'
           '0,9..144,900;1,9..144,400'
           '&family=Archivo:wght@500;600;700'
           '&family=Courier+Prime:ital,wght@0,400;0,700;1,400'
           '&display=swap')
UA = {'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                     '(KHTML, like Gecko) Chrome/126.0 Safari/537.36')}


def _nome_file(blocco):
    fam = re.search(r"font-family: '([^']+)'", blocco).group(1)
    style = re.search(r'font-style: (\w+)', blocco).group(1)
    weight = re.search(r'font-weight: (\d+)', blocco).group(1)
    url = re.search(r'url\((https://fonts\.gstatic\.com/[^)]+)\)', blocco).group(1)
    return f"{fam.lower().replace(' ', '-')}-{weight}-{style}.woff2", url


def rigenera(force=False):
    os.makedirs(FONTS_DIR, exist_ok=True)
    css = urllib.request.urlopen(urllib.request.Request(API_URL, headers=UA),
                                 timeout=30).read().decode('utf-8')
    blocchi = re.findall(r'/\* ([a-z-]+) \*/\n(@font-face \{.*?\})', css, re.S)
    out = ['/* AMI - font self-hosted (Fraunces, Archivo, Courier Prime)',
           '/* Subset latin, generato da scripts/fonti_locali.py */', '']
    n = 0
    for subset, blocco in blocchi:
        if subset != 'latin':
            continue  # il catalogo e' interamente italiano: basta latin
        fname, url = _nome_file(blocco)
        dest = os.path.join(FONTS_DIR, fname)
        if force or not os.path.exists(dest):
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                          timeout=30).read()
            open(dest, 'wb').write(data)
        nuovo = re.sub(r'url\([^)]+\)', f'url(../fonts/{fname})', blocco)
        nuovo = re.sub(r'font-display: (swap|optional);', 'font-display: block;', nuovo)
        nuovo = nuovo.replace('  font-stretch: 100%;\n', '')
        if "'Fraunces'" in nuovo:
            nuovo = nuovo.replace("@font-face {\n",
                                  "@font-face {\n  font-optical-sizing: auto;\n")
        out.append(nuovo.strip())
        n += 1
    open(CSS_DEST, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print(f"Rigenerati {n} blocchi @font-face in fonts.css")


if __name__ == '__main__':
    rigenera(force='--force' in sys.argv)
