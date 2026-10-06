"""
Record d'autorità ISAAR(CPF) per le pagine di persone e organizzazioni.

Legge dai fogli 'Persone', 'Organizzazioni' e 'Relazioni' di dati.xlsx
gli elementi ISAAR(CPF) (2a ed., 2004) e produce:
- il blocco HTML "Record d'autorità" in fondo alla scheda del soggetto;
- l'arricchimento del JSON-LD schema.org (identificativo, varianti del
  nome, date di esistenza, identificativi esterni).

Corrispondenza colonne → elementi ISAAR(CPF):
  ID_autorita       5.4.1  Identificativo del record d'autorità
  Tipo_entita       5.1.1  Tipo di entità
  Nome              5.1.2  Forma/e autorizzata/e del nome
  Forme_varianti    5.1.5  Altre forme del nome
  Nascita/Morte,
  Fondazione/
  Scioglimento      5.2.1  Date di esistenza
  Biografia/Storia  5.2.2  Storia
  Luoghi            5.2.3  Luoghi
  foglio Relazioni  5.3    Relazioni (5.3.1-5.3.4)
  Norme             5.4.3  Norme e convenzioni
  Stato_record      5.4.4  Stato di elaborazione
  Livello_dettaglio 5.4.5  Livello di completezza
  Data_redazione    5.4.6  Date di redazione e revisione
  Lingua_record     5.4.7  Lingua e scrittura
  Wikidata/VIAF            Identificativi esterni (sameAs)

Note_redazionali, Stato_record e Livello_dettaglio sono campi interni di
lavoro e non vengono pubblicati.
"""

import html
import re

from core.dati import leggi_foglio
from core.site_config import site_path
from core.utils import formatta_data, slugify

ETICHETTE_TIPO = {'persona': 'Persona', 'ente': 'Ente', 'famiglia': 'Famiglia'}


def _pulito(valore):
    testo = str(valore if valore is not None else '').strip()
    return '' if testo in ('nan', 'None', 'NaT') else testo


def _leggi_foglio(path, foglio):
    # Foglio mancante -> errore esplicito (core.dati.ErroreDati), non più
    # un DataFrame vuoto che generava schede senza dati.
    return leggi_foglio(foglio, path)


def carica_autorita(path):
    """Restituisce {nome: record} per persone e organizzazioni, più la
    lista delle relazioni. Se un foglio o una colonna manca, i campi
    corrispondenti restano vuoti e il blocco mostra solo ciò che c'è."""
    record = {}
    for foglio, sezione in (('Persone', 'persone'), ('Organizzazioni', 'organizzazioni')):
        df = _leggi_foglio(path, foglio)
        for _, riga in df.iterrows():
            nome = _pulito(riga.get('nome', ''))
            if not nome:
                continue
            dati = {k: _pulito(v) for k, v in riga.items()}
            dati['_sezione'] = sezione
            record[nome] = dati

    # Le relazioni si risolvono tramite l'identificativo del record
    # (ID_entita_A/B): se la forma autorizzata del nome viene corretta nei
    # fogli Persone/Organizzazioni, il collegamento resta valido. Il nome
    # scritto nel foglio Relazioni serve solo come ripiego se l'ID manca.
    nome_da_id = {d['id_autorita']: n for n, d in record.items() if d.get('id_autorita')}
    relazioni = []
    df_rel = _leggi_foglio(path, 'Relazioni')
    for _, riga in df_rel.iterrows():
        dati = {k: _pulito(v) for k, v in riga.items()}
        for lato in ('a', 'b'):
            nome_id = nome_da_id.get(dati.get(f'id_entita_{lato}', ''))
            if nome_id:
                dati[f'entita_{lato}'] = nome_id
        if dati.get('entita_a') and dati.get('entita_b'):
            relazioni.append(dati)
    return record, relazioni


def _ha_pagina(nome, record, indexer):
    """Una scheda esiste solo per i soggetti con documenti nel catalogo
    (stessa regola di persone.py e org.py): si linkano solo quelle."""
    dati = record.get(nome)
    if not dati or indexer is None:
        return False
    if dati['_sezione'] == 'persone':
        return bool(indexer.get_docs_for_person(nome))
    return bool(indexer.get_docs_for_organization(nome))


def _nome_linkato(nome, record, indexer):
    nome_html = html.escape(nome)
    if _ha_pagina(nome, record, indexer):
        sezione = record[nome]['_sezione']
        url = site_path(f'{sezione}/{slugify(nome)}/')
        return f'<a href="{html.escape(url, quote=True)}">{nome_html}</a>'
    # Soggetto senza pagina: senza documenti collegati oppure citato solo
    # nella relazione, senza record d'autorità (colonna ID vuota nel foglio
    # Relazioni). Il nome resta in grigio, senza link.
    return (f'<span class="autorita-rel__senza-pagina" '
            f'title="Nessun documento nell\'archivio">{nome_html}</span>')


def _data_redazione(valore):
    """Data di redazione leggibile ("2 ottobre 2026"). Excel la consegna
    come timestamp ("2026-10-02 00:00:00"); se non e' una data
    riconoscibile resta com'e'. Nell'export EAC-CPF resta in ISO."""
    if not valore:
        return ''
    leggibile, ordine = formatta_data(str(valore).split(' ')[0])
    return leggibile if ordine[0] != 9999 else str(valore)


def _campo(etichetta, valore_html):
    if not valore_html:
        return ''
    return (f'<div class="doc-scheda__campo"><dt>{html.escape(etichetta)}</dt>'
            f'<dd>{valore_html}</dd></div>')


# Gruppi delle relazioni nella scheda di un soggetto. Per ogni tipo di
# relazione: (ordine, etichetta se il soggetto della scheda è l'entità A,
# etichetta se è l'entità B). Es. "Fosco Dinucci segretario di PCd'I":
# nella scheda di Dinucci compare sotto "Segretario di", in quella del
# PCd'I sotto "Segretari".
GRUPPI_RELAZIONI = {
    'presidente di': (10, 'Presidente di', 'Presidenti'),
    'segretario di': (11, 'Segretario di', 'Segretari'),
    'fondatore di': (12, 'Fondatore di', 'Fondatori'),
    'dirigente di': (13, 'Dirigente di', 'Dirigenti'),
    'rappresentante di': (14, 'Rappresentante di', 'Rappresentanti'),
    'membro di': (15, 'Membro di', 'Membri'),
    'collaboratore di': (16, 'Collaboratore di', 'Collaboratori'),
    'organo di': (20, 'Organo di', 'Organi'),
    'articolazione locale di': (21, 'Articolazione locale di', 'Articolazioni locali'),
    'giovanile di': (21, 'Organizzazione giovanile di', 'Organizzazioni giovanili'),
    'organo di stampa di': (22, 'Organo di stampa di', 'Organi di stampa'),
    'casa editrice di': (23, 'Casa editrice di', 'Case editrici'),
    'curatore di': (24, 'Curatore di', 'Curata da'),
    'derivato da': (30, 'Derivato da', 'Gruppi derivati'),
    'derivata da': (30, 'Derivato da', 'Gruppi derivati'),
    'predecessore di': (31, 'Successori', 'Predecessori'),
    'scissione di': (32, 'Scissione di', 'Scissioni'),
    'confluito in': (33, 'Confluito in', 'Gruppi confluiti'),
    'confluita in': (33, 'Confluito in', 'Gruppi confluiti'),
    'discendenza ideologica': (34, 'Discendenza ideologica', 'Discendenza ideologica da'),
}


def _anno_ordinamento(testo):
    m = re.search(r'(1[89]\d\d|20\d\d)', testo or '')
    return int(m.group(1)) if m else 9999


def _relazioni_html(nome, relazioni, record, indexer):
    """Relazioni del soggetto raggruppate per tipo (Segretari, Membri,
    Scissioni…), in un ordine fisso; dentro ogni gruppo per data e nome."""
    gruppi = {}
    for rel in relazioni:
        a, b = rel['entita_a'], rel['entita_b']
        if nome not in (a, b):
            continue
        tipo = (rel.get('relazione', '') or '').strip().lower()
        attivo = a == nome
        altro = b if attivo else a
        if tipo in GRUPPI_RELAZIONI:
            ordine, et_attiva, et_passiva = GRUPPI_RELAZIONI[tipo]
            etichetta = et_attiva if attivo else et_passiva
        elif tipo and tipo != 'da definire':
            ordine, etichetta = 90, (tipo.capitalize() if attivo else 'Altre relazioni')
        else:
            ordine, etichetta = 99, 'In relazione con'
        dettagli = [x for x in (rel.get('date', ''), rel.get('fonte', '') and f"fonte: {rel['fonte']}") if x]
        dettagli_html = (f' <span class="autorita-rel__nota">({html.escape("; ".join(dettagli))})</span>'
                         if dettagli else '')
        voce = f'<li>{_nome_linkato(altro, record, indexer)}{dettagli_html}</li>'
        chiave = (_anno_ordinamento(rel.get('date', '')), altro.lower())
        gruppi.setdefault((ordine, etichetta), []).append((chiave, voce))
    if not gruppi:
        return ''
    blocchi = []
    for (ordine, etichetta), voci in sorted(gruppi.items()):
        voci_html = ''.join(v for _, v in sorted(voci))
        blocchi.append(f'<div class="autorita-rel__gruppo"><span class="autorita-rel__etichetta">'
                       f'{html.escape(etichetta)}</span><ul class="autorita-rel">{voci_html}</ul></div>')
    return ''.join(blocchi)


def blocco_autorita(nome, data_range, record, relazioni, indexer):
    """HTML della sezione "Record d'autorità" (ISAAR(CPF)) di un soggetto."""
    dati = record.get(nome)
    if not dati or not dati.get('id_autorita'):
        return ''

    tipo = ETICHETTE_TIPO.get(dati.get('tipo_entita', '').lower(), dati.get('tipo_entita', ''))
    varianti = '; '.join(v.strip() for v in dati.get('forme_varianti', '').split(';') if v.strip())

    esterni = []
    if dati.get('wikidata'):
        qid = dati['wikidata']
        esterni.append(f'<a href="https://www.wikidata.org/wiki/{html.escape(qid, quote=True)}" '
                       f'rel="noopener">Wikidata {html.escape(qid)}</a>')
    if dati.get('viaf'):
        viaf = dati['viaf']
        esterni.append(f'<a href="https://viaf.org/viaf/{html.escape(viaf, quote=True)}" '
                       f'rel="noopener">VIAF {html.escape(viaf)}</a>')

    campi = ''.join([
        _campo('Identificativo', html.escape(dati['id_autorita'])),
        _campo('Tipo di entità', html.escape(tipo)),
        _campo('Forma autorizzata del nome', html.escape(nome)),
        _campo('Altre forme del nome', html.escape(varianti)),
        _campo('Date di esistenza', html.escape(data_range) if data_range else 'Non determinate'),
        _campo('Luoghi', html.escape(dati.get('luoghi', ''))),
        _campo('Relazioni', _relazioni_html(nome, relazioni, record, indexer)),
        _campo('Identificativi esterni', ', '.join(esterni)),
        _campo('Formato XML', f'<a href="{html.escape(site_path("dati/eac/" + dati["id_autorita"] + ".xml"), quote=True)}">EAC-CPF</a>'),
        _campo('Norme', html.escape(dati.get('norme', ''))),
        _campo('Redazione', html.escape(_data_redazione(dati.get('data_redazione', '')))),
    ])

    url_progetto = site_path('progetto/') + '#norme-di-descrizione'
    return f"""
<section class="soggetto-autorita" aria-labelledby="autorita-{html.escape(slugify(nome), quote=True)}">
<h2 class="soggetto-sezione" id="autorita-{html.escape(slugify(nome), quote=True)}">Record d'autorità</h2>
<dl class="doc-scheda__campi">{campi}</dl>
<p class="autorita-nota">Scheda redatta secondo ISAAR(CPF). <a href="{html.escape(url_progetto, quote=True)}">Norme di descrizione</a></p>
</section>
"""


def arricchisci_schema(schema, nome, record, estremi=None):
    """Aggiunge al JSON-LD i dati del record d'autorità.

    estremi: (inizio, fine) già formattati; per le persone diventano
    birthDate/deathDate, per gli enti foundingDate/dissolutionDate."""
    dati = record.get(nome)
    if not dati:
        return schema
    if dati.get('id_autorita'):
        schema['identifier'] = dati['id_autorita']
    varianti = [v.strip() for v in dati.get('forme_varianti', '').split(';') if v.strip()]
    if varianti:
        schema['alternateName'] = varianti
    same_as = []
    if dati.get('wikidata'):
        same_as.append(f"https://www.wikidata.org/wiki/{dati['wikidata']}")
    if dati.get('viaf'):
        same_as.append(f"https://viaf.org/viaf/{dati['viaf']}")
    if same_as:
        schema['sameAs'] = same_as
    elif schema.get('sameAs') == []:
        del schema['sameAs']

    # Solo date ISO (AAAA, AAAA-MM, AAAA-MM-GG): "ca. 2010" o "s.d." non
    # sono valori validi per schema.org e vengono omessi.
    def _iso(v):
        v = (v or '').strip()
        return v if re.fullmatch(r'\d{4}(-\d{2}(-\d{2})?)?', v) else ''

    inizio, fine = (_iso(x) for x in (estremi or ('', '')))
    for chiave in ('foundingDate', 'dissolutionDate', 'birthDate', 'deathDate'):
        if chiave in schema and not _iso(str(schema[chiave])):
            del schema[chiave]
    if schema.get('@type') == 'Person':
        # jobTitle conteneva l'intervallo di date con l'etichetta "Storico":
        # le date di esistenza vanno nei campi schema.org appropriati.
        schema.pop('jobTitle', None)
        if inizio:
            schema['birthDate'] = inizio
        if fine:
            schema['deathDate'] = fine
    else:
        if inizio:
            schema['foundingDate'] = inizio
        if fine:
            schema['dissolutionDate'] = fine
    return schema
