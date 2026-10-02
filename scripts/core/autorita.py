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

import pandas as pd

from core.site_config import site_path
from core.utils import slugify

ETICHETTE_TIPO = {'persona': 'Persona', 'ente': 'Ente', 'famiglia': 'Famiglia'}


def _pulito(valore):
    testo = str(valore if valore is not None else '').strip()
    return '' if testo in ('nan', 'None', 'NaT') else testo


def _leggi_foglio(path, foglio):
    try:
        df = pd.read_excel(path, sheet_name=foglio, dtype=str).fillna('')
    except Exception:
        return pd.DataFrame()
    df.columns = df.columns.str.strip().str.lower()
    return df


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
    return nome_html


def _campo(etichetta, valore_html):
    if not valore_html:
        return ''
    return (f'<div class="doc-scheda__campo"><dt>{html.escape(etichetta)}</dt>'
            f'<dd>{valore_html}</dd></div>')


def _relazioni_html(nome, relazioni, record, indexer):
    voci = []
    for rel in relazioni:
        a, b = rel['entita_a'], rel['entita_b']
        if nome not in (a, b):
            continue
        tipo = rel.get('relazione', '')
        if not tipo or tipo == 'da definire':
            tipo = 'in relazione con'
        lato_a = html.escape(a) if a == nome else _nome_linkato(a, record, indexer)
        lato_b = html.escape(b) if b == nome else _nome_linkato(b, record, indexer)
        dettagli = [x for x in (rel.get('date', ''), rel.get('fonte', '') and f"fonte: {rel['fonte']}") if x]
        dettagli_html = f' <span class="autorita-rel__nota">({html.escape("; ".join(dettagli))})</span>' if dettagli else ''
        voci.append(f'<li>{lato_a} {html.escape(tipo)} {lato_b}{dettagli_html}</li>')
    if not voci:
        return ''
    return '<ul class="autorita-rel">' + ''.join(voci) + '</ul>'


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
        _campo('Redazione', html.escape(dati.get('data_redazione', ''))),
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
