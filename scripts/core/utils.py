import html
import html as html_lib
import re
from datetime import datetime

from .cache_manager import CacheManager

# Inizializza cache globale
_cache_manager = None


def get_cache_manager():
    """Singleton per CacheManager."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def slugify(name):
    if not name or name in ['nan', 'None']:
        return ''
    name = name.lower()
    name = re.sub(r'[àáâãäå]', 'a', name)
    name = re.sub(r'[èéêë]', 'e', name)
    name = re.sub(r'[ìíîï]', 'i', name)
    name = re.sub(r'[òóôõö]', 'o', name)
    name = re.sub(r'[ùúûü]', 'u', name)
    name = re.sub(r'[().]', ' ', name)
    name = re.sub(r'[^a-z0-9\s-]', '', name)
    name = re.sub(r'\s+', '-', name)
    name = re.sub(r'-+', '-', name)
    return name.strip('-')


# Convenzione per le date incerte del catalogo:
#   "????"  (anno del tutto ignoto)        -> "s.d."      (in fondo agli ordinamenti)
#   "201?"  (cifre finali ignote)          -> "ca. 2010"  (ordinato come 2010)
DATA_SENZA = 's.d.'
_DATE_ASSENTI = {'', 'nan', 'None', 'NaT', 'n.d.', 's.d.'}


def formatta_estremo(valore):
    """Estremo cronologico di una persona o organizzazione (nascita, morte,
    fondazione, scioglimento), con la stessa convenzione delle date incerte:
    "????" -> "s.d.", "201?" -> "ca. 2010"; ogni altro valore resta com'e'."""
    v = str(valore or '').strip()
    if v in ('nan', 'None', 'NaT'):
        return ''
    if re.fullmatch(r'\?{4}', v):
        return DATA_SENZA
    if len(v) == 4 and re.fullmatch(r'(\d{1,3})(\?{1,3})', v):
        return f"ca. {v.replace('?', '0')}"
    return v



def formatta_intervallo(inizio, fine):
    """Estremi cronologici di una persona o organizzazione come intervallo
    ("1921 – 1993"), formattati con formatta_estremo(). Se entrambi gli
    estremi sono ignoti ("????") basta un solo "s.d." invece di
    "s.d. – s.d."."""
    a = formatta_estremo(inizio)
    b = formatta_estremo(fine)
    if a == DATA_SENZA and b == DATA_SENZA:
        return DATA_SENZA
    if a and b:
        return f"{a} – {b}"
    if a:
        return f"{a} – "
    if b:
        return f"? – {b}"
    return ''

def formatta_data(data_str):
    if data_str is None or str(data_str).strip() in _DATE_ASSENTI:
        return DATA_SENZA, (9999, 1, 1)

    data_str = str(data_str).strip()

    if re.fullmatch(r'\?{4}', data_str):
        return DATA_SENZA, (9999, 1, 1)

    match_incerta = re.fullmatch(r'(\d{1,3})(\?{1,3})', data_str)
    if match_incerta and len(data_str) == 4:
        anno = int(data_str.replace('?', '0'))
        return f"ca. {anno}", (anno, 1, 1)

    if re.match(r'^\d{4}$', data_str):
        return data_str, (int(data_str), 1, 1)

    mesi = {1: 'gennaio', 2: 'febbraio', 3: 'marzo', 4: 'aprile',
            5: 'maggio', 6: 'giugno', 7: 'luglio', 8: 'agosto',
            9: 'settembre', 10: 'ottobre', 11: 'novembre', 12: 'dicembre'}

    # SOLO MESE/ANNO scritto come testo puro (es. "10/1967" o "1967-10"):
    # va riconosciuto ESPLICITAMENTE prima del parsing con strptime, perche'
    # altrimenti nessun formato della lista sottostante corrisponde e il
    # valore verrebbe mostrato grezzo senza essere formattato ne' ordinato
    # correttamente. Corrisponde solo se non c'e' alcuna informazione sul
    # giorno nella stringa originale, quindi non inventa mai un giorno.
    match_mese_anno = re.match(r'^(\d{1,2})/(\d{4})$', data_str)
    if match_mese_anno:
        mese, anno = int(match_mese_anno.group(1)), int(match_mese_anno.group(2))
        if 1 <= mese <= 12:
            return f"{mesi[mese]} {anno}", (anno, mese, 1)

    try:
        # NOTA sull'ordine dei formati: %m/%d/%Y e' volutamente per ULTIMO.
        # Il data entry del catalogo segue la convenzione italiana gg/mm/aaaa,
        # quindi %d/%m/%Y deve avere priorita'. %m/%d/%Y resta solo come
        # fallback estremo (es. date esportate da fonti anglofone) per i casi
        # non parsabili in nessun altro modo; su date ambigue (entrambi i
        # numeri <= 12) la lettura resta comunque quella italiana.
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y', '%m/%d/%Y']:
            try:
                dt = datetime.strptime(data_str, fmt)
                if fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y', '%m/%d/%Y']:
                    return f"{dt.day} {mesi[dt.month]} {dt.year}", (dt.year, dt.month, dt.day)
                else:
                    return f"{mesi[dt.month]} {dt.year}", (dt.year, dt.month, 1)
            except ValueError:
                continue
    except Exception:
        pass

    try:
        if isinstance(data_str, (int, float)):
            dt = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(data_str) - 2)
            return f"{dt.day} {mesi[dt.month]} {dt.year}", (dt.year, dt.month, dt.day)
    except Exception:
        pass

    return data_str, (9999, 1, 1)


def split_nomi(nomi_str):
    if not nomi_str or nomi_str in ['nan', 'None']:
        return []
    return [n.strip() for n in re.split(r'[;,]+', nomi_str) if n.strip()]


def scarica_descrizione_ia(identifier):
    """
    Scarica descrizione da Internet Archive, con cache.
    NUOVO: Usa CacheManager per evitare download ripetuti
    """
    if not identifier:
        return None

    cache_mgr = get_cache_manager()

    # 1. Controlla cache
    cached_metadata = cache_mgr.get_ia_metadata(identifier)
    if cached_metadata:
        desc = cached_metadata.get('metadata', {}).get('description', '')
        if desc:
            return desc.strip()
        else:
            return None

    # 2. Download da IA
    try:
        import requests
        url = f"https://archive.org/metadata/{identifier}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            # 3. Salva in cache
            cache_mgr.set_ia_metadata(identifier, data)

            # 4. Estrai descrizione
            desc = data.get('metadata', {}).get('description', '')
            if desc:
                return desc.strip()

    except Exception as e:
        print(f"Errore scaricando descrizione per {identifier}: {e}")

    return None


def scarica_testo_ia(identifier, nome_file=None):
    """
    Scarica testo da Internet Archive, con cache.
    NUOVO: Cache dei download testuali
    """
    if not identifier:
        return None

    if not nome_file:
        nome_file = f"{identifier}.txt"

    cache_mgr = get_cache_manager()
    cache_key = f"{identifier}_{nome_file}"

    # 1. Controlla cache
    cached_text = cache_mgr.ia_cache.get(f"ia_text_{cache_key}")
    if cached_text:
        print(f"Cache: testo {identifier}/{nome_file}")
        return cached_text.get('data')

    # 2. Download
    try:
        import requests
        url = f"https://archive.org/download/{identifier}/{nome_file}"
        response = requests.get(url, timeout=15)

        if response.status_code == 200:
            testo = response.text

            # 3. Salva in cache
            cache_mgr.ia_cache[f"ia_text_{cache_key}"] = {
                'data': testo,
                'timestamp': datetime.now().isoformat()
            }
            cache_mgr._save_json(cache_mgr.ia_cache_file, cache_mgr.ia_cache)

            return testo
        else:
            print(f"Testo non trovato per {identifier} ({response.status_code})")

    except Exception as e:
        print(f"Errore scaricando testo per {identifier}: {e}")

    return None


def pulisci_per_meta_description(testo_html, max_len=155):
    """Converte una descrizione HTML in testo semplice troncato,
    adatto al tag <meta description> per la SEO."""
    if not testo_html:
        return ''

    testo = re.sub(r'<[^>]+>', ' ', testo_html)
    testo = html_lib.unescape(testo)
    testo = re.sub(r'\s+', ' ', testo).strip()

    if len(testo) <= max_len:
        return testo

    troncato = testo[:max_len].rsplit(' ', 1)[0]
    return troncato.rstrip(',.;:') + '…'


def escape_yaml_string(testo):
    """Escape minimo per inserire una stringa in un valore YAML
    tra doppi apici (frontmatter)."""
    if not testo:
        return ''
    return testo.replace('\\', '\\\\').replace('"', '\\"')


def descrizione_da_catalogo(row):
    """Descrizione del documento (ISAD(G) 3.3.1, Ambito e contenuto) dalla
    colonna 'Descrizione' del foglio Catalogo, come HTML: ogni riga del
    testo diventa un paragrafo, con escape. Restituisce None se la cella
    e' vuota: in quel caso i chiamanti ricadono sulla descrizione di
    Internet Archive."""
    testo = str(row.get('descrizione', '') or '').strip()
    if testo in ('', 'nan', 'None'):
        return None
    righe = [r.strip() for r in testo.splitlines() if r.strip()]
    return ''.join(f'<p>{html.escape(r)}</p>' for r in righe)


def soggetto_produttore(autore_raw, org_raw):
    """Soggetto produttore (ISAD(G) 3.2.1) secondo la regola dell'AMI:
    l'autore; se assente o anonimo, l'organizzazione di riferimento.
    Restituisce la stringa dei nomi (separati da ';') o ''."""
    autore = (autore_raw or '').strip()
    if autore and autore.lower() not in ('anonimo', 'anonima', 'n/a', 'nan', 'none'):
        return autore
    org = (org_raw or '').strip()
    return '' if org.lower() in ('nan', 'none', 'n/a') else org


def forme_varianti(valore):
    """Elenco delle "Altre forme del nome" (colonna Forme_varianti dei
    fogli Persone e Organizzazioni, valori separati da punto e virgola)."""
    testo = str(valore or '').strip()
    if testo in ('', 'nan', 'None'):
        return []
    return [v.strip() for v in testo.split(';') if v.strip()]


def testo_ricerca(*parti):
    """Testo normalizzato per le ricerche per nome negli indici di Persone
    e Organizzazioni: minuscole, senza accenti, spazi singoli. Lo stesso
    trattamento lo applica il JavaScript alla query (normalize NFD)."""
    import unicodedata
    testo = ' '.join(str(p) for p in parti if p)
    testo = unicodedata.normalize('NFD', testo.lower())
    testo = ''.join(c for c in testo if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', testo).strip()
