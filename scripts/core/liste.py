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


def valore_pulito(valore):
    """Testo di una cella del catalogo, senza 'nan'/'None'."""
    v = str(valore if valore is not None else '').strip()
    return '' if v in ('nan', 'None', 'NaT') else v


def iniziali(nome, max_lettere=2):
    """Iniziali per il segnaposto "a timbro" (parole con iniziale maiuscola)."""
    import re
    parole = re.findall(r"[^\W\d_][\w'’]*", str(nome))
    maiuscole = [w for w in parole if w[:1].isupper()] or parole
    return ''.join(w[0].upper() for w in maiuscole[:max_lettere]) or '?'


def meta_riga(tipo='', org='', etichette=()):
    """Riga dei metadati sotto il titolo: tipologia (etichetta grigia),
    organizzazione, eventuali etichette extra. Stessa forma in home,
    percorsi tematici, persone e organizzazioni."""
    parti = []
    tipo = valore_pulito(tipo)
    if tipo:
        tipo = 'Testo' if tipo.lower() == 'testo_bilingue' else tipo
        parti.append(f'<span class="doc-type-chip">{html.escape(tipo[:1].upper() + tipo[1:])}</span>')
    org = valore_pulito(org)
    if org:
        parti.append(f'<span class="doc-org">{html.escape(org)}</span>')
    for e in etichette:
        parti.append(f'<span class="ruolo-badge">{html.escape(e)}</span>')
    return f'<div class="doc-meta">{"".join(parti)}</div>' if parti else ''


# Ruolo secondario nella riga ("anche come autore"): il nome del ruolo da
# solo ("anche autore", "anche menzionato") non diceva di chi fosse.
ETICHETTE_RUOLO = {
    'autore': 'come autore',
    'menzionato': 'tra i citati',
    'pubblicato da': 'come editore',
}


def _riga(doc, ruolo_gruppo, escludi_org=''):
    altri = [ETICHETTE_RUOLO.get(r, r) for r in doc['ruoli'] if r != ruolo_gruppo]
    etichette = ('anche ' + ', '.join(altri),) if altri else ()
    org = doc.get('org', '')
    if escludi_org and org.strip().lower() == escludi_org.strip().lower():
        org = ''
    meta = meta_riga(doc.get('tipo', ''), org, etichette)
    return f"""
<div class="doc-row">
    <div class="doc-data">{html.escape(doc['data'])}</div>
    <div class="doc-contenuto">
        <div class="doc-titolo"><a href="{site_path(f"documenti/{doc['id']}/")}">{html.escape(doc['titolo'])}</a></div>
        {meta}
    </div>
</div>
"""


def elenco_per_ruolo(documenti, gruppi, escludi_org=''):
    """HTML dei documenti raggruppati per ruolo (ordine cronologico interno)."""
    assegnati = {chiave: [] for chiave, _, _ in gruppi}
    for doc in documenti:
        for chiave, _, _ in gruppi:
            if chiave in doc['ruoli']:
                assegnati[chiave].append(doc)
                break
    out = []
    # Con un solo gruppo un sottotitolo h3 sotto l'h2 "Documenti" e'
    # ridondante: il ruolo resta come etichetta (p), non come titolo.
    unico = sum(1 for chiave, _, _ in gruppi if assegnati[chiave]) == 1
    for chiave, titolo, ident in gruppi:
        docs = assegnati[chiave]
        if not docs:
            continue
        n = len(docs)
        conteggio = '1 documento' if n == 1 else f'{n} documenti'
        tag = 'p' if unico else 'h3'
        classe = 'doc-gruppo__titolo doc-gruppo__titolo--unico' if unico else 'doc-gruppo__titolo'
        out.append(
            f'<section class="doc-gruppo" aria-labelledby="gruppo-{ident}">\n'
            f'<{tag} class="{classe}" id="gruppo-{ident}">{html.escape(titolo)}'
            f' <span class="doc-gruppo__conteggio">{conteggio}</span></{tag}>\n'
            '<div class="catalogo-lista">'
            + ''.join(_riga(d, chiave, escludi_org) for d in docs)
            + '</div>\n</section>\n'
        )
    return '\n'.join(out)
