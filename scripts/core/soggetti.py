import pandas as pd
import os
import json
from scripts.config import BUILD_DIR
from scripts.core.utils import slugify, split_nomi

def carica_soggetti(data_dir):
    persone = {}
    organizzazioni = {}

    try:
        persone_path = data_dir / "dati.xlsx"
        df_persone = pd.read_excel(persone_path, sheet_name='Persone', dtype=str).fillna('')
        df_persone.columns = df_persone.columns.str.strip().str.lower()
        for _, row in df_persone.iterrows():
            nome = str(row.get('nome', '')).strip()
            if nome and nome not in ['nan', 'None']:
                persone[nome] = {
                    'slug': slugify(nome),
                    'biografia': str(row.get('biografia', '')).strip(),
                    'nascita': str(row.get('nascita', '')).strip(),
                    'morte': str(row.get('morte', '')).strip(),
                    'cognome': str(row.get('cognome', '')).strip()
                }
        print(f"   ✅ Caricate {len(persone)} persone dal foglio 'Persone' di dati.xlsx")
    except FileNotFoundError:
        print("   ⚠️ File data/dati.xlsx non trovato. Le persone non saranno linkate.")
    except Exception as e:
        print(f"   ⚠️ Errore durante il caricamento del foglio 'Persone' in dati.xlsx: {e}")

    try:
        org_path = data_dir / "dati.xlsx"
        df_org = pd.read_excel(org_path, sheet_name='Organizzazioni', dtype=str).fillna('')
        df_org.columns = df_org.columns.str.strip().str.lower()
        for _, row in df_org.iterrows():
            nome = str(row.get('nome', '')).strip()
            if nome and nome not in ['nan', 'None']:
                organizzazioni[nome] = {
                    'slug': slugify(nome),
                    'storia': str(row.get('storia', '')).strip(),
                    'categoria': str(row.get('categoria', '')).strip(),
                    'fondazione': str(row.get('fondazione', '')).strip()
                }
        print(f"   ✅ Caricate {len(organizzazioni)} organizzazioni dal foglio 'Organizzazioni' di dati.xlsx")
    except FileNotFoundError:
        print("   ⚠️ File data/dati.xlsx non trovato. Le organizzazioni non saranno linkate.")
    except Exception as e:
        print(f"   ⚠️ Errore durante il caricamento del foglio 'Organizzazioni' in dati.xlsx: {e}")

    return persone, organizzazioni

def trova_soggetto(nome, persone, organizzazioni):
    if not nome or nome in ['nan', 'None']:
        return None, None

    if nome in persone:
        return 'persone', persone[nome]['slug']
    elif nome in organizzazioni:
        return 'organizzazioni', organizzazioni[nome]['slug']
    else:
        return None, None

def crea_link(nome, persone, organizzazioni):
    if not nome or nome in ['nan', 'None']:
        return ''
    sezione, slug = trova_soggetto(nome, persone, organizzazioni)
    if sezione:
        return f'<a href="/archivio-maoismo-italiano/{sezione}/{slug}/">{nome}</a>'
    else:
        return nome

def link_lista(nomi_str, persone, organizzazioni):
    nomi = split_nomi(nomi_str)
    if not nomi:
        return 'N/A'
    links = []
    for nome in nomi:
        if nome:
            link = crea_link(nome, persone, organizzazioni)
            links.append(link)
    if links:
        return ', '.join(links)
    return 'N/A'

def genera_json_soggetti(persone, organizzazioni, output_dir=None):
    if output_dir is None:
        output_dir = BUILD_DIR

    print("\n👤 Generazione del JSON di persone e organizzazioni (per la ricerca)...")

    persone_json = []
    for nome, info in persone.items():
        persone_json.append({
            'nome': nome,
            'slug': info.get('slug', ''),
            'biografia': info.get('biografia', ''),
            'nascita': info.get('nascita', ''),
            'morte': info.get('morte', '')
        })

    organizzazioni_json = []
    for nome, info in organizzazioni.items():
        organizzazioni_json.append({
            'nome': nome,
            'slug': info.get('slug', ''),
            'storia': info.get('storia', ''),
            'categoria': info.get('categoria', ''),
            'fondazione': info.get('fondazione', '')
        })

    data = {
        'persone': persone_json,
        'organizzazioni': organizzazioni_json
    }

    json_path = output_dir / "soggetti.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"   ✅ soggetti.json generato con {len(persone_json)} persone e {len(organizzazioni_json)} organizzazioni.")