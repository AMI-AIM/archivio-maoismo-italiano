"""
Hook MkDocs: dati per la riga finale del footer.

Mette in config.extra.ami_colophon il numero di documenti del catalogo
(da documenti.json, generato da scripts/generatore.py nella cartella
build/) e la data della pubblicazione in italiano ("6 ottobre 2026").
Li usa overrides/partials/footer.html: "96 documenti · aggiornato il …".
Se documenti.json manca, il footer mostra solo la data.

Registrato in mkdocs.yml alla voce "hooks".
"""
import datetime
import json
import os

_MESI = ('gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio',
         'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre')


def on_config(config):
    oggi = datetime.date.today()
    dati = {'aggiornato': f'{oggi.day} {_MESI[oggi.month - 1]} {oggi.year}',
            'anno': oggi.year, 'documenti': None}
    percorso = os.path.join(config['docs_dir'], 'documenti.json')
    try:
        with open(percorso, encoding='utf-8') as f:
            contenuto = json.load(f)
        documenti = contenuto.get('documenti', contenuto) if isinstance(contenuto, dict) else contenuto
        dati['documenti'] = len(documenti)
    except (OSError, ValueError):
        pass
    config['extra']['ami_colophon'] = dati
    return config
