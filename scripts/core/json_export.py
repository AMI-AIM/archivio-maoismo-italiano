import os
import json
import re
import pandas as pd
from .utils import formatta_data, split_nomi, scarica_descrizione_ia

def genera_json(df, persone, organizzazioni, output_dir):
    print("\n📊 Generazione del file JSON per i filtri...")
    
    documenti_json = []
    anni_valori = []
    
    for index, row in df.iterrows():
        ami_id = str(row.get('id', '')).strip()
        if not ami_id or pd.isna(row.get('id')):
            continue
        
        titolo = str(row.get('titolo', 'Senza titolo')).strip()
        if titolo in ['nan', 'None', '']:
            titolo = 'Senza titolo'
        
        autore_raw = str(row.get('autore', '')).strip()
        if autore_raw in ['nan', 'None']:
            autore_raw = ''
        
        org_raw = str(row.get('organizzazione', '')).strip()
        if org_raw in ['nan', 'None']:
            org_raw = ''
        
        persone_collegate = str(row.get('persone_collegate', '')).strip()
        if persone_collegate in ['nan', 'None']:
            persone_collegate = ''
        
        organizzazioni_collegate = str(row.get('organizzazioni_collegate', '')).strip()
        if organizzazioni_collegate in ['nan', 'None']:
            organizzazioni_collegate = ''
        
        data_raw = str(row.get('data', row.get('anno', ''))).strip()
        if data_raw in ['nan', 'None', '']:
            data_raw = ''
        data_formattata, data_ordine = formatta_data(data_raw)
        
        tipo_raw = str(row.get('tipo', '')).strip()
        if tipo_raw in ['nan', 'None']:
            tipo_raw = ''
        tipo = tipo_raw.lower()
        if tipo == 'fotografia':
            tipo = 'foto'
        
        # 🔥 PER I FILTRI: "testo_bilingue" viene mostrato come "testo" (minuscolo per i filtri)
        tipo_display = 'testo' if tipo == 'testo_bilingue' else tipo
        
        serie = str(row.get('serie', '')).strip()
        if serie in ['nan', 'None']:
            serie = ''
        
        # 🔥 KEYWORDS RIMOSSE
        
        url_ia = str(row.get('url', '#')).strip()
        if url_ia in ['nan', 'None', '']:
            url_ia = '#'
        
        anno = None
        if data_ordine and data_ordine[0] != 9999:
            anno = data_ordine[0]
            anni_valori.append(anno)
        elif data_raw and data_raw.isdigit():
            anno = int(data_raw)
            anni_valori.append(anno)
        
        descrizione = None
        if url_ia and url_ia != '#':
            match = re.search(r'/details/([^/?#]+)', url_ia)
            if match:
                identifier = match.group(1)
                descrizione = scarica_descrizione_ia(identifier)
        
        persone_lista = []
        if autore_raw and autore_raw not in ['nan', 'None']:
            autori = split_nomi(autore_raw)
            for autore in autori:
                if autore in persone:
                    persone_lista.append(autore)
        if persone_collegate and persone_collegate not in ['nan', 'None']:
            collegati = split_nomi(persone_collegate)
            for collegato in collegati:
                if collegato in persone:
                    persone_lista.append(collegato)
        persone_lista = list(set(persone_lista))
        
        organizzazioni_lista = []
        if org_raw and org_raw not in ['nan', 'None']:
            orgs = split_nomi(org_raw)
            for org in orgs:
                if org in organizzazioni:
                    organizzazioni_lista.append(org)
        if organizzazioni_collegate and organizzazioni_collegate not in ['nan', 'None']:
            collegati = split_nomi(organizzazioni_collegate)
            for collegato in collegati:
                if collegato in organizzazioni:
                    organizzazioni_lista.append(collegato)
        if autore_raw and autore_raw not in ['nan', 'None']:
            autori = split_nomi(autore_raw)
            for autore in autori:
                if autore in organizzazioni:
                    organizzazioni_lista.append(autore)
        organizzazioni_lista = list(set(organizzazioni_lista))
        
        doc_obj = {
            'id': ami_id,
            'titolo': titolo,
            'autore': autore_raw,
            'organizzazione': org_raw,
            'data': data_formattata,
            'anno': anno,
            'tipo': tipo_display,
            'serie': serie,
            'url_ia': url_ia,
            'persone': persone_lista,
            'organizzazioni': organizzazioni_lista,
            'descrizione': descrizione if descrizione else ''
        }
        documenti_json.append(doc_obj)
    
    documenti_json.sort(key=lambda x: (x['anno'] is None, x['anno'] if x['anno'] else 9999, x['titolo']))
    
    json_data = {
        'documenti': documenti_json,
        'anno_min': min(anni_valori) if anni_valori else 1900,
        'anno_max': max(anni_valori) if anni_valori else 2025
    }
    
    json_path = os.path.join(output_dir, 'documenti.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ JSON generato con {len(documenti_json)} documenti (incluse descrizioni)")
    print(f"   📅 Intervallo anni: {json_data['anno_min']} - {json_data['anno_max']}")