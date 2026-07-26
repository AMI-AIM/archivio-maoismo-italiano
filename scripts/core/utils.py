import re
from datetime import datetime

def slugify(name):
    if not name or name in ['nan', 'None']:
        return ''
    name = name.lower()
    name = re.sub(r'[àáâãäå]', 'a', name)
    name = re.sub(r'[èéêë]', 'e', name)
    name = re.sub(r'[ìíîï]', 'i', name)
    name = re.sub(r'[òóôõö]', 'o', name)
    name = re.sub(r'[ùúûü]', 'u', name)
    name = re.sub(r'[()\.]', ' ', name)
    name = re.sub(r'[^a-z0-9\s-]', '', name)
    name = re.sub(r'\s+', '-', name)
    name = re.sub(r'-+', '-', name)
    return name.strip('-')

def formatta_data(data_str):
    if not data_str or data_str in ['nan', 'None', 'n.d.']:
        return 'n.d.', (9999, 1, 1)
    
    data_str = str(data_str).strip()
    
    if re.match(r'^\d{4}$', data_str):
        return data_str, (int(data_str), 1, 1)
    
    try:
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y', '%m/%d/%Y']:
            try:
                dt = datetime.strptime(data_str, fmt)
                mesi = {1: 'gennaio', 2: 'febbraio', 3: 'marzo', 4: 'aprile',
                        5: 'maggio', 6: 'giugno', 7: 'luglio', 8: 'agosto',
                        9: 'settembre', 10: 'ottobre', 11: 'novembre', 12: 'dicembre'}
                if fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y', '%m/%d/%Y']:
                    return f"{dt.day} {mesi[dt.month]} {dt.year}", (dt.year, dt.month, dt.day)
                else:
                    return f"{mesi[dt.month]} {dt.year}", (dt.year, dt.month, 1)
            except ValueError:
                continue
    except:
        pass
    
    try:
        if isinstance(data_str, (int, float)):
            dt = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(data_str) - 2)
            mesi = {1: 'gennaio', 2: 'febbraio', 3: 'marzo', 4: 'aprile',
                    5: 'maggio', 6: 'giugno', 7: 'luglio', 8: 'agosto',
                    9: 'settembre', 10: 'ottobre', 11: 'novembre', 12: 'dicembre'}
            return f"{dt.day} {mesi[dt.month]} {dt.year}", (dt.year, dt.month, dt.day)
    except:
        pass
    
    return data_str, (9999, 1, 1)

def split_nomi(nomi_str):
    if not nomi_str or nomi_str in ['nan', 'None']:
        return []
    return [n.strip() for n in re.split(r'[;,]+', nomi_str) if n.strip()]

def scarica_descrizione_ia(identifier):
    if not identifier:
        return None
    
    try:
        import requests
        url = f"https://archive.org/metadata/{identifier}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            desc = data.get('metadata', {}).get('description', '')
            if desc:
                desc = re.sub(r'<[^>]+>', '', desc)
                desc = desc.strip()
                return desc
    except Exception as e:
        print(f"   ⚠️ Errore scaricando descrizione per {identifier}: {e}")
    
    return None

def scarica_testo_ia(identifier, nome_file=None):
    if not identifier:
        return None
    
    if not nome_file:
        nome_file = f"{identifier}.txt"
    
    try:
        import requests
        url = f"https://archive.org/download/{identifier}/{nome_file}"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.text
        else:
            print(f"   ⚠️ Testo non trovato per {identifier} ({response.status_code})")
    except Exception as e:
        print(f"   ⚠️ Errore scaricando testo per {identifier}: {e}")
    
    return None