"""Elenco dei documenti di una persona o di un'organizzazione, diviso per ruolo.

Prima le schede elencavano tutti i documenti in un'unica lista con un badge
per riga ("autore", "menzionato"...): sulle schede piu' ricche (Mao, 37
documenti; PCC) ne usciva una colonna lunghissima in cui il ruolo, cioe'
l'informazione che distingue le righe, andava letto riga per riga.
Ora ogni documento finisce nel gruppo del suo ruolo principale; l'etichetta
per riga resta solo per i ruoli secondari ("anche menzionato").
"""

import html

from .site_config import site_path

# (ruolo, titolo del gruppo, id) in ordine di priorita'
GRUPPI_PERSONA = (
    ('autore', 'Come autore', 'autore'),
    ('menzionato', 'Citato nei documenti', 'menzionato'),
)
GRUPPI_ORGANIZZAZIONE = (
    ('pubblicato da', 'Pubblicazioni', 'pubblicazioni'),
    ('autore', 'Come autore', 'autore'),
    ('menzionato', 'Citata nei documenti', 'menzionata'),
)


def _riga(doc, ruolo_gruppo):
    altri = [r for r in doc['ruoli'] if r != ruolo_gruppo]
    etichetta = ''
    if altri:
        testo = html.escape('anche ' + ', '.join(altri))
        etichetta = f'\n        <div class="doc-ruoli"><span class="ruolo-badge">{testo}</span></div>'
    return f"""
<div class="doc-row">
    <div class="doc-data">{html.escape(doc['data'])}</div>
    <div class="doc-contenuto">
        <div class="doc-titolo"><a href="{site_path(f"documenti/{doc['id']}/")}">{html.escape(doc['titolo'])}</a></div>{etichetta}
    </div>
</div>
"""


def elenco_per_ruolo(documenti, gruppi):
    """HTML dei documenti raggruppati per ruolo (ordine cronologico interno)."""
    assegnati = {chiave: [] for chiave, _, _ in gruppi}
    for doc in documenti:
        for chiave, _, _ in gruppi:
            if chiave in doc['ruoli']:
                assegnati[chiave].append(doc)
                break
    out = []
    for chiave, titolo, ident in gruppi:
        docs = assegnati[chiave]
        if not docs:
            continue
        n = len(docs)
        conteggio = '1 documento' if n == 1 else f'{n} documenti'
        out.append(
            f'<section class="doc-gruppo" aria-labelledby="gruppo-{ident}">\n'
            f'<h3 class="doc-gruppo__titolo" id="gruppo-{ident}">{html.escape(titolo)}'
            f' <span class="doc-gruppo__conteggio">{conteggio}</span></h3>\n'
            '<div class="catalogo-lista">'
            + ''.join(_riga(d, chiave) for d in docs)
            + '</div>\n</section>\n'
        )
    return '\n'.join(out)
