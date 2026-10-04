"""Miniature locali delle immagini di Internet Archive.

Le pagine di navigazione (copertine in evidenza in home, griglia della
galleria) mostravano immagini lette in diretta da archive.org: quando
Internet Archive e' lento o irraggiungibile restavano vuote, e la galleria
scaricava gli originali a piena risoluzione per riquadri larghi ~300px.

Questo modulo scarica UNA volta l'immagine, ne ricava una miniatura WebP
alla larghezza richiesta e la salva in:

    assets/immagini/miniature/<chiave>-<larghezza>.webp

La cartella fa parte del repository: il Launcher la committa insieme al
resto, quindi la build su GitHub Actions trova le miniature gia' pronte e
non dipende da Internet Archive. Una miniatura mancante (documento nuovo)
viene creata al volo, anche in CI. La copia in build/ serve alla build in
corso, perche' sync_assets.py copia assets/ prima dei generatori.

Le dimensioni reali (larghezza/altezza) vengono restituite al chiamante: con
width/height nell'<img> il browser riserva lo spazio prima del caricamento
(niente spostamenti di layout) e la galleria impagina subito la griglia.

Se qualcosa va storto (rete, formato, Pillow assente) la funzione restituisce
None e il generatore torna all'URL remoto di sempre: nessuna build si rompe.
Dopo alcuni errori di rete consecutivi smette di riprovare per il resto
dell'esecuzione, cosi' un Internet Archive irraggiungibile non allunga la
build di minuti.
"""

import io
import os
import re
import shutil

from . import esito
from .site_config import site_path

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CARTELLA_ASSETS = os.path.join(_ROOT, 'assets', 'immagini', 'miniature')
CARTELLA_BUILD = os.path.join(_ROOT, 'build', 'immagini', 'miniature')

QUALITA_WEBP = 78
TIMEOUT_SECONDI = 20
MAX_ERRORI_RETE = 3          # dopo N errori di rete di fila: niente piu' tentativi
MAX_BYTE_SORGENTE = 40 * 1024 * 1024  # non scaricare oltre 40 MB per immagine

_stato = {'errori_rete': 0, 'pil': None, 'avvisi': set()}


def _avviso(chiave, testo):
    """Registra un avviso nel riepilogo della pipeline, una sola volta per chiave."""
    if chiave not in _stato['avvisi']:
        _stato['avvisi'].add(chiave)
        esito.avviso(testo)


def _pil():
    if _stato['pil'] is None:
        try:
            from PIL import Image  # noqa: F401
            _stato['pil'] = True
        except ImportError:
            _stato['pil'] = False
            _avviso('pil', 'Miniature: Pillow non installato (pip install -r requirements.txt): '
                           'uso le immagini remote di Internet Archive.')
    return _stato['pil']


def _nome_sicuro(chiave):
    return re.sub(r'[^A-Za-z0-9._-]+', '-', str(chiave)).strip('-') or 'immagine'


def _dimensioni(percorso):
    from PIL import Image
    with Image.open(percorso) as im:
        return im.size


def _copia_in_build(percorso, nome):
    """Allinea build/ (la build in corso usa la copia gia' sincronizzata)."""
    if not os.path.isdir(os.path.dirname(CARTELLA_BUILD)):
        return  # build/ non ancora creata: ci pensera' sync_assets.py
    os.makedirs(CARTELLA_BUILD, exist_ok=True)
    dest = os.path.join(CARTELLA_BUILD, nome)
    if not os.path.exists(dest) or os.path.getsize(dest) != os.path.getsize(percorso):
        shutil.copy2(percorso, dest)


def _scarica(url):
    """Scarica un'immagine; ritorna i byte o None. Conta gli errori di rete."""
    import requests
    try:
        risposta = requests.get(url, timeout=TIMEOUT_SECONDI, stream=True)
    except requests.RequestException as errore:
        _stato['errori_rete'] += 1
        print(f'Miniature: rete non disponibile per {url} ({errore.__class__.__name__})')
        _avviso('rete', 'Miniature: Internet Archive non raggiungibile, alcune copertine '
                        'restano remote (verranno create al prossimo lancio con la rete)')
        return None
    _stato['errori_rete'] = 0
    with risposta:
        tipo = risposta.headers.get('Content-Type', '')
        if risposta.status_code != 200 or not tipo.startswith('image/'):
            print(f'Miniature: {url} non e\' un\'immagine ({risposta.status_code}, {tipo or "tipo ignoto"})')
            return None
        dati = io.BytesIO()
        for blocco in risposta.iter_content(256 * 1024):
            dati.write(blocco)
            if dati.tell() > MAX_BYTE_SORGENTE:
                print(f'Miniature: {url} supera {MAX_BYTE_SORGENTE // (1024 * 1024)} MB, salto')
                return None
        return dati.getvalue()


def _crea(dati, percorso, larghezza):
    from PIL import Image, ImageOps
    with Image.open(io.BytesIO(dati)) as im:
        im = ImageOps.exif_transpose(im)  # foto da smartphone: orientamento corretto
        if im.mode not in ('RGB', 'RGBA'):
            im = im.convert('RGBA' if 'transparency' in im.info else 'RGB')
        if im.width > larghezza:  # mai ingrandire
            altezza = max(1, round(im.height * larghezza / im.width))
            im = im.resize((larghezza, altezza), Image.LANCZOS)
        os.makedirs(os.path.dirname(percorso), exist_ok=True)
        temporaneo = percorso + '.tmp'
        im.save(temporaneo, 'WEBP', quality=QUALITA_WEBP, method=6)
    os.replace(temporaneo, percorso)


def miniatura(chiave, urls, larghezza):
    """Miniatura locale per ``chiave`` (es. l'ID AMI del documento).

    ``urls``: URL da provare in ordine (il primo che risponde con
    un'immagine vince). Ritorna ``{'url', 'width', 'height'}`` oppure None.
    """
    nome = f'{_nome_sicuro(chiave)}-{int(larghezza)}.webp'
    percorso = os.path.join(CARTELLA_ASSETS, nome)

    if not _pil():
        return None

    if not os.path.exists(percorso):
        if _stato['errori_rete'] >= MAX_ERRORI_RETE:
            _avviso('rete', 'Miniature: troppi errori di rete, salto i download '
                            'per questa esecuzione (restano le immagini remote).')
            return None
        for url in [u for u in urls if u]:
            dati = _scarica(url)
            if dati is None:
                if _stato['errori_rete'] >= MAX_ERRORI_RETE:
                    break
                continue
            try:
                _crea(dati, percorso, larghezza)
                print(f'Miniatura creata: {nome}')
                break
            except Exception as errore:  # formato non leggibile, file corrotto...
                print(f'Miniature: impossibile convertire {url} ({errore})')
        if not os.path.exists(percorso):
            return None

    try:
        w, h = _dimensioni(percorso)
    except Exception as errore:
        print(f'Miniature: {nome} illeggibile ({errore}), uso l\'immagine remota')
        return None
    _copia_in_build(percorso, nome)
    return {'url': site_path(f'immagini/miniature/{nome}'), 'width': w, 'height': h}
