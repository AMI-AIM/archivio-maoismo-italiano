import pandas as pd
import os
from .utils import slugify, split_nomi

def carica_soggetti(data_dir):
    persone = {}
    organizzazioni = {}
    
    try:
        persone_path = os.path.join(data_dir, 'persone.xlsx')
        df_persone = pd.read_excel(persone_path, dtype=str).fillna('')
        df_persone.columns = df_persone.columns.str.strip().str.lower()
        for _, row in df_persone.iterrows():
            nome = str(row.get('nome', '')).strip()
            if nome and nome not in ['nan', 'None']:
                persone[nome] = {
                    'slug': slugify(nome),
                    'biografia': str(row.get('biografia', '')).strip(),
                    'nascita': str(row.get('nascita', '')).strip(),
                    'morte': str(row.get('morte', '')).strip()
                }
        print(f"   ✅ Caricate {len(persone)} persone da data/persone.xlsx")
    except FileNotFoundError:
        print("   ⚠️ File data/persone.xlsx non trovato. Le persone non saranno linkate.")
    except Exception as e:
        print(f"   ⚠️ Errore durante il caricamento di data/persone.xlsx: {e}")
    
    try:
        org_path = os.path.join(data_dir, 'organizzazioni.xlsx')
        df_org = pd.read_excel(org_path, dtype=str).fillna('')
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
        print(f"   ✅ Caricate {len(organizzazioni)} organizzazioni da data/organizzazioni.xlsx")
    except FileNotFoundError:
        print("   ⚠️ File data/organizzazioni.xlsx non trovato. Le organizzazioni non saranno linkate.")
    except Exception as e:
        print(f"   ⚠️ Errore durante il caricamento di data/organizzazioni.xlsx: {e}")
    
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