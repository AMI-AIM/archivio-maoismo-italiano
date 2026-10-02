"""
Esportazione dei dati dell'AMI nei formati archivistici XML standard.

- EAD3 (Encoded Archival Description, versione 3): un solo file con la
  descrizione ISAD(G) della raccolta (foglio 'Raccolta') e di tutte le
  unità (foglio 'Catalogo') -> build/dati/ami-ead.xml
- EAC-CPF 2.0 (Encoded Archival Context - Corporate Bodies, Persons and
  Families): un file per ogni record d'autorità ISAAR(CPF) (fogli 'Persone',
  'Organizzazioni', 'Relazioni') -> build/dati/eac/AMI-P-001.xml, ...

I file vengono validati contro gli schemi ufficiali salvati in
scripts/schemi/ (ead3.xsd, eac.xsd) se la libreria lxml e' installata.
Un file non valido viene comunque scritto, ma l'errore viene segnalato
durante la generazione.

I collegamenti tra i due formati passano per gli identificativi ISAAR:
in EAD3 i nomi hanno l'attributo identifier="AMI-O-004", che e' il
recordId del file EAC-CPF corrispondente.
"""

import os
import re
import xml.etree.ElementTree as ET
from datetime import date

import pandas as pd

from .site_config import site_url
from .utils import formatta_estremo, soggetto_produttore, split_nomi

NS_EAD = 'http://ead3.archivists.org/schema/'
NS_EAC = 'https://archivists.org/ns/eac/v2'
SCHEMI_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'schemi')

AGENZIA = 'Archivio del Maoismo Italiano'
REDATTORE = 'Ivan Masci'
NORMA_ISAD = 'ISAD(G): General International Standard Archival Description, 2nd ed., 2000'
NORMA_ISAAR = ('ISAAR(CPF): International Standard Archival Authority Record for '
               'Corporate Bodies, Persons and Families, 2nd ed., 2004')

# Lingue (colonna 'Lingua') -> ISO 639-2/B, usato da EAD3 e EAC-CPF
CODICI_LINGUA = {
    'italiano': 'ita', 'cinese': 'chi', 'inglese': 'eng', 'francese': 'fre',
    'tedesco': 'ger', 'spagnolo': 'spa', 'russo': 'rus', 'albanese': 'alb',
}

# Codici ISAD del foglio 'Raccolta' -> elemento EAD3 di <archdesc> (testo in <p>)
ISAD_A_EAD = {
    '3.2.2': 'bioghist', '3.2.3': 'custodhist', '3.2.4': 'acqinfo',
    '3.3.1': 'scopecontent', '3.3.2': 'appraisal', '3.3.3': 'accruals',
    '3.3.4': 'arrangement', '3.4.1': 'accessrestrict', '3.4.2': 'userestrict',
    '3.4.4': 'phystech', '3.4.5': 'otherfindaid', '3.5.1': 'originalsloc',
    '3.5.2': 'altformavail', '3.5.3': 'relatedmaterial', '3.5.4': 'bibliography',
    '3.6.1': 'odd', '3.7.1': 'processinfo',
}

VERO = ('sì', 'si', 's', 'yes', 'true', '1')


def _v(valore):
    t = str(valore if valore is not None else '').strip()
    return '' if t in ('nan', 'None', 'NaT') else t


def _sub(parent, ns, tag, text=None, **attrs):
    el = ET.SubElement(parent, f'{{{ns}}}{tag}', {k: v for k, v in attrs.items() if v})
    if text:
        el.text = text
    return el


def _paragrafi(parent, ns, testo):
    righe = [r.strip() for r in str(testo).splitlines() if r.strip()]
    for r in righe:
        _sub(parent, ns, 'p', r)


def _data_iso(valore):
    v = _v(valore)
    return v if re.fullmatch(r'\d{4}(-\d{2}(-\d{2})?)?', v) else ''


def _leggi(path, foglio):
    try:
        df = pd.read_excel(path, sheet_name=foglio, dtype=str).fillna('')
    except Exception:
        return pd.DataFrame()
    df.columns = df.columns.str.strip().str.lower()
    return df


def _scrivi(root, path, ns):
    ET.register_namespace('', ns)
    tree = ET.ElementTree(root)
    ET.indent(tree, space='  ')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tree.write(path, encoding='utf-8', xml_declaration=True)


def valida(path, schema_file):
    """Lista degli errori di validazione ([] se il file e' valido), oppure
    None se lxml o lo schema non sono disponibili."""
    try:
        from lxml import etree
    except ImportError:
        return None
    xsd = os.path.join(SCHEMI_DIR, schema_file)
    if not os.path.exists(xsd):
        return None
    schema = etree.XMLSchema(etree.parse(xsd))
    if schema.validate(etree.parse(path)):
        return []
    return [f'riga {e.line}: {e.message}' for e in schema.error_log]


# ---------------------------------------------------------------------------
# Record d'autorità: indice nome -> id, tipo, riga del foglio
# ---------------------------------------------------------------------------
def _indice_autorita(excel_path):
    indice = {}
    for foglio, tipo in (('Persone', 'persona'), ('Organizzazioni', 'ente')):
        for _, r in _leggi(excel_path, foglio).iterrows():
            nome = _v(r.get('nome'))
            if nome:
                indice[nome] = {'id': _v(r.get('id_autorita')), 'tipo': tipo, 'riga': r}
    return indice


def _nome_ead(parent, nome, indice, tag_ignoto='corpname', relator=None):
    info = indice.get(nome) or {}
    if info.get('tipo') == 'persona':
        tag = 'persname'
    elif info.get('tipo') == 'ente':
        tag = 'corpname'
    else:
        tag = tag_ignoto
    el = _sub(parent, NS_EAD, tag, identifier=info.get('id') or None, relator=relator)
    _sub(el, NS_EAD, 'part', nome)
    return el


# ---------------------------------------------------------------------------
# EAD3
# ---------------------------------------------------------------------------
def _control_ead(ead, raccolta, oggi):
    control = _sub(ead, NS_EAD, 'control')
    _sub(control, NS_EAD, 'recordid', 'AMI', instanceurl=site_url('dati/ami-ead.xml'))
    filedesc = _sub(control, NS_EAD, 'filedesc')
    titlestmt = _sub(filedesc, NS_EAD, 'titlestmt')
    _sub(titlestmt, NS_EAD, 'titleproper', raccolta.get('3.1.2') or AGENZIA)
    _sub(titlestmt, NS_EAD, 'author', REDATTORE)
    _sub(control, NS_EAD, 'maintenancestatus', value='revised')
    agency = _sub(control, NS_EAD, 'maintenanceagency')
    _sub(agency, NS_EAD, 'agencyname', AGENZIA)
    langdecl = _sub(control, NS_EAD, 'languagedeclaration')
    _sub(langdecl, NS_EAD, 'language', 'italiano', langcode='ita')
    _sub(langdecl, NS_EAD, 'script', 'latino', scriptcode='Latn')
    for norma in (NORMA_ISAD, NORMA_ISAAR):
        _sub(_sub(control, NS_EAD, 'conventiondeclaration'), NS_EAD, 'citation', norma)
    history = _sub(control, NS_EAD, 'maintenancehistory')
    data_descr = raccolta.get('3.7.3') or oggi
    ev = _sub(history, NS_EAD, 'maintenanceevent')
    _sub(ev, NS_EAD, 'eventtype', value='created')
    _sub(ev, NS_EAD, 'eventdatetime', data_descr, standarddatetime=_data_iso(data_descr) or None)
    _sub(ev, NS_EAD, 'agenttype', value='human')
    _sub(ev, NS_EAD, 'agent', REDATTORE)
    ev = _sub(history, NS_EAD, 'maintenanceevent')
    _sub(ev, NS_EAD, 'eventtype', value='derived')
    _sub(ev, NS_EAD, 'eventdatetime', oggi, standarddatetime=oggi)
    _sub(ev, NS_EAD, 'agenttype', value='machine')
    _sub(ev, NS_EAD, 'agent', 'scripts/core/ead_export.py')
    _sub(ev, NS_EAD, 'eventdescription', 'File generato automaticamente da data/dati.xlsx')


def _lingue(valori):
    lingue = []
    for v in valori:
        for l in _v(v).split(';'):
            l = l.strip().lower()
            if l and l not in lingue:
                lingue.append(l)
    return lingue


def _langmaterial(did, lingue):
    if lingue:
        lm = _sub(did, NS_EAD, 'langmaterial')
        for l in lingue:
            _sub(lm, NS_EAD, 'language', l, langcode=CODICI_LINGUA.get(l))


def _archdesc(ead, df_catalogo, raccolta):
    archdesc = _sub(ead, NS_EAD, 'archdesc', level='collection')
    did = _sub(archdesc, NS_EAD, 'did')
    _sub(did, NS_EAD, 'unitid', raccolta.get('3.1.1') or 'AMI')
    _sub(did, NS_EAD, 'unittitle', raccolta.get('3.1.2') or AGENZIA)

    anni = sorted({int(m.group(1)) for v in df_catalogo.get('data_normalizzata', [])
                   for m in [re.match(r'(\d{4})', _v(v))] if m})
    if raccolta.get('3.1.3'):
        _sub(did, NS_EAD, 'unitdate', raccolta['3.1.3'])
    elif anni:
        _sub(did, NS_EAD, 'unitdate', f'{anni[0]}-{anni[-1]}',
             normal=f'{anni[0]}/{anni[-1]}', unitdatetype='inclusive')

    produttore = raccolta.get('3.2.1')
    if produttore:
        m = re.match(r'^(.*?)\s*\((.+)\)\s*$', produttore)
        nome, ruolo = (m.group(1), m.group(2)) if m else (produttore, None)
        orig = _sub(did, NS_EAD, 'origination')
        _sub(_sub(orig, NS_EAD, 'persname', relator=ruolo), NS_EAD, 'part', nome)

    unita = sum(1 for v in df_catalogo.get('id', []) if _v(v))
    _sub(did, NS_EAD, 'physdesc', raccolta.get('3.1.5') or f'{unita} unità')
    _langmaterial(did, _lingue(df_catalogo.get('lingua', [])))

    for codice, tag in ISAD_A_EAD.items():
        if raccolta.get(codice):
            _paragrafi(_sub(archdesc, NS_EAD, tag), NS_EAD, raccolta[codice])
    return archdesc


def _componente(dsc, r, indice):
    ami_id = _v(r.get('id'))
    c = _sub(dsc, NS_EAD, 'c', level='item', id=ami_id)
    did = _sub(c, NS_EAD, 'did')
    _sub(did, NS_EAD, 'unitid', ami_id)
    attribuito = _v(r.get('titolo_attribuito')).lower() in VERO
    _sub(did, NS_EAD, 'unittitle', _v(r.get('titolo')) or 'Senza titolo',
         localtype='attribuito' if attribuito else None)
    data_iso = _data_iso(r.get('data_normalizzata'))
    _sub(did, NS_EAD, 'unitdate', data_iso or _v(r.get('data')) or 's.d.', normal=data_iso or None)

    prod = soggetto_produttore(_v(r.get('autore')), _v(r.get('organizzazione')))
    if prod:
        orig = _sub(did, NS_EAD, 'origination')
        for nome in split_nomi(prod):
            _nome_ead(orig, nome, indice)

    if _v(r.get('consistenza')):
        _sub(did, NS_EAD, 'physdesc', _v(r.get('consistenza')))
    _langmaterial(did, _lingue([r.get('lingua')]))

    m = re.search(r'archive\.org/details/([^/?#]+)', _v(r.get('url')))
    if m:
        _sub(did, NS_EAD, 'dao', daotype='derived', href=f'https://archive.org/details/{m.group(1)}',
             linktitle='Riproduzione digitale su Internet Archive')

    if _v(r.get('descrizione')):
        _paragrafi(_sub(c, NS_EAD, 'scopecontent'), NS_EAD, _v(r.get('descrizione')))

    luogo, editore = _v(r.get('luogo')), _v(r.get('editore'))
    if editore:
        _paragrafi(_sub(c, NS_EAD, 'odd', localtype='editore'), NS_EAD,
                   f'{luogo}: {editore}' if luogo else editore)
    if _v(r.get('provenienza')):
        _paragrafi(_sub(c, NS_EAD, 'acqinfo'), NS_EAD, _v(r.get('provenienza')))

    p = _sub(_sub(c, NS_EAD, 'otherfindaid'), NS_EAD, 'p')
    _sub(p, NS_EAD, 'ref', f'Scheda {ami_id} nel catalogo AMI', href=site_url(f'documenti/{ami_id}/'))

    ca = ET.Element(f'{{{NS_EAD}}}controlaccess')
    for nome in split_nomi(_v(r.get('organizzazione'))) + split_nomi(_v(r.get('organizzazioni_collegate'))):
        _nome_ead(ca, nome, indice)
    for nome in split_nomi(_v(r.get('persone_collegate'))):
        _nome_ead(ca, nome, indice, tag_ignoto='persname')
    if luogo:
        _sub(_sub(ca, NS_EAD, 'geogname'), NS_EAD, 'part', luogo)
    if _v(r.get('tipo')):
        _sub(_sub(ca, NS_EAD, 'genreform'), NS_EAD, 'part',
             _v(r.get('tipo')).replace('_', ' ').capitalize())
    percorsi = _v(r.get('percorsi')) or _v(r.get('serie'))
    for tema in [t.strip() for t in percorsi.split(';') if t.strip()]:
        _sub(_sub(ca, NS_EAD, 'subject'), NS_EAD, 'part', tema)
    if len(ca):
        c.append(ca)


def genera_ead(df_catalogo, excel_path, output_dir):
    oggi = date.today().isoformat()
    indice = _indice_autorita(excel_path)
    raccolta = {_v(r.get('codice_isad')): _v(r.get('valore'))
                for _, r in _leggi(excel_path, 'Raccolta').iterrows()}

    ead = ET.Element(f'{{{NS_EAD}}}ead')
    _control_ead(ead, raccolta, oggi)
    archdesc = _archdesc(ead, df_catalogo, raccolta)
    dsc = _sub(archdesc, NS_EAD, 'dsc')
    for _, r in df_catalogo.iterrows():
        if _v(r.get('id')):
            _componente(dsc, r, indice)

    path = os.path.join(output_dir, 'dati', 'ami-ead.xml')
    _scrivi(ead, path, NS_EAD)
    return path


# ---------------------------------------------------------------------------
# EAC-CPF 2.0
# ---------------------------------------------------------------------------
def _data_eac(parent, tag, valore):
    """fromDate/toDate: testo leggibile secondo le convenzioni AMI ('ca.',
    's.d.') e, solo se l'anno e' certo, standardDate ISO."""
    grezzo = _v(valore)
    if re.fullmatch(r'\d{4}\.0', grezzo):
        grezzo = grezzo[:4]
    testo = formatta_estremo(grezzo)
    if not testo:
        return None
    return _sub(parent, NS_EAC, tag, testo,
                standardDate=grezzo if re.fullmatch(r'\d{4}', grezzo) else None)


def _control_eac(eac, rid, data_red, oggi):
    control = _sub(eac, NS_EAC, 'control', maintenanceStatus='new',
                   languageEncoding='iso639-2b', scriptEncoding='iso15924')
    _sub(control, NS_EAC, 'recordId', rid)
    _sub(_sub(control, NS_EAC, 'maintenanceAgency'), NS_EAC, 'agencyName', AGENZIA)
    history = _sub(control, NS_EAC, 'maintenanceHistory')
    ev = _sub(history, NS_EAC, 'maintenanceEvent', maintenanceEventType='created')
    _sub(ev, NS_EAC, 'agent', REDATTORE, agentType='human')
    _sub(ev, NS_EAC, 'eventDateTime', data_red, standardDateTime=data_red)
    ev = _sub(history, NS_EAC, 'maintenanceEvent', maintenanceEventType='derived')
    _sub(ev, NS_EAC, 'agent', 'scripts/core/ead_export.py', agentType='machine')
    _sub(ev, NS_EAC, 'eventDateTime', oggi, standardDateTime=oggi)
    _sub(_sub(control, NS_EAC, 'conventionDeclaration'), NS_EAC, 'reference', NORMA_ISAAR)
    _sub(control, NS_EAC, 'languageDeclaration', languageCode='ita', scriptCode='Latn')


def _description_eac(r, persona):
    # L'ordine degli elementi segue lo schema EAC-CPF 2.0
    desc = ET.Element(f'{{{NS_EAC}}}description')
    if not persona and _v(r.get('categoria')):
        lst = _sub(desc, NS_EAC, 'legalStatuses')
        _sub(_sub(lst, NS_EAC, 'legalStatus'), NS_EAC, 'term', _v(r.get('categoria')))
    if _v(r.get('luoghi')):
        places = _sub(desc, NS_EAC, 'places')
        for luogo in [x.strip() for x in _v(r.get('luoghi')).split(';') if x.strip()]:
            _sub(_sub(places, NS_EAC, 'place'), NS_EAC, 'placeName', luogo)
    inizio = r.get('nascita') if persona else r.get('fondazione')
    fine = r.get('morte') if persona else r.get('scioglimento')
    if _v(inizio) or _v(fine):
        ed = _sub(desc, NS_EAC, 'existDates')
        if formatta_estremo(_v(inizio)) == 's.d.' and formatta_estremo(_v(fine)) == 's.d.':
            # entrambi ignoti: un solo "s.d.", come sul sito
            _sub(ed, NS_EAC, 'date', 's.d.')
        else:
            dr = _sub(ed, NS_EAC, 'dateRange')
            _data_eac(dr, 'fromDate', inizio)
            _data_eac(dr, 'toDate', fine)
    testo = _v(r.get('biografia') if persona else r.get('storia'))
    if testo:
        _paragrafi(_sub(desc, NS_EAC, 'biogHist'), NS_EAC, testo)
    return desc


def _relations_eac(nome, relazioni, indice, nome_da_id):
    rel_el = ET.Element(f'{{{NS_EAC}}}relations')
    for _, rel in relazioni.iterrows():
        a = nome_da_id.get(_v(rel.get('id_entita_a'))) or _v(rel.get('entita_a'))
        b = nome_da_id.get(_v(rel.get('id_entita_b'))) or _v(rel.get('entita_b'))
        if nome not in (a, b) or not a or not b:
            continue
        altro = b if a == nome else a
        info = indice.get(altro, {})
        relation = _sub(rel_el, NS_EAC, 'relation')
        te = _sub(relation, NS_EAC, 'targetEntity',
                  targetType='person' if info.get('tipo') == 'persona' else 'corporateBody',
                  valueURI=site_url(f"dati/eac/{info['id']}.xml") if info.get('id') else None)
        _sub(te, NS_EAC, 'part', altro)
        # Date della relazione: "1966-1968", "1968-????" -> dateRange;
        # altre forme ("attestato al 1969-10-03") restano nella nota.
        date_rel = _v(rel.get('date'))
        m = re.fullmatch(r'([\d?]{4})\s*[-–]\s*([\d?]{4})', date_rel)
        if m:
            dr = _sub(relation, NS_EAC, 'dateRange')
            _data_eac(dr, 'fromDate', m.group(1))
            _data_eac(dr, 'toDate', m.group(2))
            date_rel = ''
        elif re.fullmatch(r'[\d?]{4}', date_rel):
            _data_eac(relation, 'date', date_rel)
            date_rel = ''
        categoria = _v(rel.get('categoria_isaar'))
        if categoria and categoria != 'da definire':
            _sub(relation, NS_EAC, 'relationType', categoria)
        tipo_rel = _v(rel.get('relazione'))
        frase = (f'{a} {tipo_rel} {b}' if tipo_rel and tipo_rel != 'da definire'
                 else f'{a} in relazione con {b}')
        nota = [frase] + [x for x in (date_rel,
                                      _v(rel.get('fonte')) and f"Fonte: {_v(rel.get('fonte'))}") if x]
        dn = _sub(relation, NS_EAC, 'descriptiveNote')
        for riga in nota:
            _sub(dn, NS_EAC, 'p', riga)
    return rel_el


def genera_eac(excel_path, output_dir):
    oggi = date.today().isoformat()
    indice = _indice_autorita(excel_path)
    relazioni = _leggi(excel_path, 'Relazioni')
    nome_da_id = {info['id']: n for n, info in indice.items() if info['id']}
    percorsi = []

    for nome, info in indice.items():
        rid, r = info['id'], info['riga']
        if not rid:
            continue
        persona = info['tipo'] == 'persona'
        eac = ET.Element(f'{{{NS_EAC}}}eac')
        m = re.match(r'\d{4}-\d{2}-\d{2}', _v(r.get('data_redazione')))
        _control_eac(eac, rid, m.group(0) if m else oggi, oggi)

        cpf = _sub(eac, NS_EAC, 'cpfDescription')
        identity = _sub(cpf, NS_EAC, 'identity')
        _sub(identity, NS_EAC, 'entityType', value='person' if persona else 'corporateBody')
        _sub(_sub(identity, NS_EAC, 'nameEntry', status='authorized'), NS_EAC, 'part', nome)
        for variante in [x.strip() for x in _v(r.get('forme_varianti')).split(';') if x.strip()]:
            _sub(_sub(identity, NS_EAC, 'nameEntry', status='alternative'), NS_EAC, 'part', variante)
        for campo, fonte in (('wikidata', 'Wikidata'), ('viaf', 'VIAF')):
            if _v(r.get(campo)):
                _sub(identity, NS_EAC, 'identityId', _v(r.get(campo)), localType=fonte)

        desc = _description_eac(r, persona)
        if len(desc):
            cpf.append(desc)
        rel_el = _relations_eac(nome, relazioni, indice, nome_da_id)
        if len(rel_el):
            cpf.append(rel_el)

        path = os.path.join(output_dir, 'dati', 'eac', f'{rid}.xml')
        _scrivi(eac, path, NS_EAC)
        percorsi.append(path)
    return percorsi


def esporta_tutto(df_catalogo, excel_path, output_dir):
    """Genera e valida EAD3 ed EAC-CPF.

    Restituisce (numero_file, errori): errori e' un dict {file: [messaggi]}
    (vuoto se tutto e' valido) oppure None se la validazione non e'
    disponibile (lxml non installato o schemi mancanti)."""
    ead = genera_ead(df_catalogo, excel_path, output_dir)
    eac = genera_eac(excel_path, output_dir)
    errori = {}
    for path, schema in [(ead, 'ead3.xsd')] + [(p, 'eac.xsd') for p in eac]:
        esito = valida(path, schema)
        if esito is None:
            return 1 + len(eac), None
        if esito:
            errori[os.path.relpath(path, output_dir)] = esito
    return 1 + len(eac), errori
