import os
import re
import requests

FONT_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Fraunces:opsz,wght@9..144,400..900"
    "&family=Archivo:wght@500..700"
    "&family=Courier+Prime:ital,wght@0,400;1,400"
    "&display=swap"
)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

FALLBACK_METRICS = """
/* ============================================================
   FALLBACK METRICS (Anti-CLS)
   Questi blocchi creano font di fallback locali che occupano
   esattamente lo stesso spazio dei font web, azzerando il layout shift.
   ============================================================ */
@font-face {
  font-family: 'Fraunces fallback';
  src: local('Georgia');
  size-adjust: 94.5%;
  ascent-override: 102.5%;
  descent-override: 29.5%;
  line-gap-override: 0%;
}
@font-face {
  font-family: 'Archivo fallback';
  src: local('Arial');
  size-adjust: 99.5%;
  ascent-override: 108.5%;
  descent-override: 23.5%;
  line-gap-override: 0%;
}
@font-face {
  font-family: 'Courier Prime fallback';
  src: local('Courier New');
  size-adjust: 100%;
  ascent-override: 100%;
  descent-override: 25%;
  line-gap-override: 0%;
}
"""

def main():
    print("1. Richiedo CSS a Google Fonts...")
    css_response = requests.get(FONT_URL, headers=HEADERS)
    css_response.raise_for_status()
    css_content = css_response.text

    print("2. Estraggo URL dei font...")
    urls = re.findall(r'url\((https://fonts\.gstatic\.com/[^)]+\.woff2)\)', css_content)

    dest_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'fonts')
    os.makedirs(dest_dir, exist_ok=True)

    print(f"3. Download di {len(urls)} file in {dest_dir}...")
    for url in urls:
        filename = url.split('/')[-1].split('?')[0]
        filepath = os.path.join(dest_dir, filename)
        if not os.path.exists(filepath):
            print(f"   - {filename}")
            font_resp = requests.get(url, headers=HEADERS)
            with open(filepath, 'wb') as f:
                f.write(font_resp.content)

    print("\n4. Generazione blocco CSS locale...")
    # Sostituisce gli URL remoti con il path locale relativo
    local_css = re.sub(
        r'url\(https://fonts\.gstatic\.com/([^)]+\.woff2)(?:\?[^)]*)?\)',
        r'url("../fonts/\1")',
        css_content
    )

    # Inietta i fallback nelle dichiarazioni font-family
    replacements = [
        ("font-family: 'Fraunces';", "font-family: 'Fraunces', 'Fraunces fallback', Georgia, serif;"),
        ("font-family: 'Archivo';", "font-family: 'Archivo', 'Archivo fallback', Arial, sans-serif;"),
        ("font-family: 'Courier Prime';", "font-family: 'Courier Prime', 'Courier Prime fallback', 'Courier New', monospace;"),
    ]
    for old, new in replacements:
        local_css = local_css.replace(old, new)

    output_css_path = os.path.join(dest_dir, 'fonts-locali.css')
    with open(output_css_path, 'w', encoding='utf-8') as f:
        f.write(local_css)
        f.write(FALLBACK_METRICS)

    print(f"\n[OK] Font salvati in '{dest_dir}'.")
    print(f"[OK] CSS pronto in '{output_css_path}'.")
    print("\nProssimi passi:")
    print("1. Copia il contenuto di 'assets/fonts/fonts-locali.css'")
    print("2. Incollalo all'inizio di 'assets/stylesheets/extra.css'")
    print("3. Rimuovi i <link> a Google Fonts da 'overrides/main.html'")

if __name__ == "__main__":
    main()