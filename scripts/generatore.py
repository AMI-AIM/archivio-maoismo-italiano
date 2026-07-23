import os
import pandas as pd
from core.soggetti import carica_soggetti
from core.schede import crea_schede
from core.archivio import genera_indice
from core.json_export import genera_json
from core.home import genera_home

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'docs')

def main():
    print("🚀 Avvio del generatore di schede AMI...")
    print(f"📂 Root: {ROOT_DIR}")
    print(f"📂 Dati: {DATA_DIR}")
    print(f"📂 Output: {OUTPUT_DIR}")
    
    persone, organizzazioni = carica_soggetti(DATA_DIR)
    
    try:
        catalogo_path = os.path.join(DATA_DIR, 'catalogo.xlsx')
        df = pd.read_excel(catalogo_path, dtype=str).fillna('')
    except FileNotFoundError:
        print(f"❌ ERRORE: Non trovo '{catalogo_path}'.")
        return
    except Exception as e:
        print(f"❌ ERRORE durante la lettura di catalogo.xlsx: {e}")
        return
    
    df.columns = df.columns.str.strip().str.lower()
    print(f"📊 Trovate {len(df)} righe e le seguenti colonne: {list(df.columns)}")
    
    crea_schede(df, persone, organizzazioni, OUTPUT_DIR)
    genera_indice(df, OUTPUT_DIR)
    genera_json(df, persone, organizzazioni, OUTPUT_DIR)
    genera_home(df, OUTPUT_DIR)
    
    print("\n🎉 Conversione completata con successo!")

if __name__ == "__main__":
    main()