"""
Citazioni AMI — Archivio del Maoismo Italiano.
Questo modulo prepara i dati per le citazioni bibliografiche.
Le citazioni complete vengono costruite lato JavaScript, così la
"data di consultazione" può essere quella reale del visitatore.
Il modulo NON inserisce più la data di build nelle citazioni.
"""
import json
import re
from .site_config import site_url
from .utils import split_nomi

# VERSIONE AGGIORNATA: invalida cache per applicare modifiche HTML/JS
CITAZIONI_TEMPLATE_VERSION = "2025-01-20-citazioni-div-corsivo-escape-1"

ARCHIVE_NAME = "Archivio del Maoismo Italiano"

TIPI_BIBLIOGRAFICI = {
    "libro",
    "opuscolo",
    "periodico",
    "giornale",
    "rivista",
    "articolo",
}

TIPI_PERIODICI = {
    "periodico",
    "giornale",
    "rivista",
}

def sanitize_citation_id(ami_id: str) -> str:
    """
    Crea un ID HTML/JS sicuro a partire dall'AMI ID.
    Esempio:
        AMI-0001 -> ami_0001
    """
    base = str(ami_id or "").lower().strip()
    base = re.sub(r"[^a-z0-9_]+", "_", base)
    base = re.sub(r"_+", "_", base).strip("_")
    return base or "documento"

def yaml_value(value) -> str:
    """
    Restituisce una stringa YAML sicura per un valore tra virgolette.
    Usa json.dumps perché produce una stringa quoted compatibile
    con la maggior parte dei casi YAML semplici.
    """
    if value is None:
        value = ""
    text = str(value)
    if text in ("nan", "None", "NaN"):
        text = ""
    return json.dumps(text, ensure_ascii=False)

def json_per_script(obj) -> str:
    """
    Serializza JSON in modo sicuro dentro un tag <script>.
    Evita che una stringa contenendo </script> possa chiudere
    prematuramente il blocco HTML.
    """
    payload = json.dumps(obj, ensure_ascii=False)
    return (
        payload
        .replace("<", r"\u003c")
        .replace(">", r"\u003e")
        .replace("&", r"\u0026")
    )

def _clean_periodico_fragment(text: str) -> str:
    """Pulisce virgole, spazi e separatori residui dopo il parsing."""
    text = str(text or "")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[,;:]\s*[,;:]+", ", ", text)
    text = re.sub(r"^\s*[,;:]\s*", "", text)
    text = re.sub(r"\s*[,;:]\s*$", "", text)
    return text.strip(" ,;:")

def parse_periodico_titolo(titolo_raw: str):
    """
    Estrae testata, annata/volume e numero di fascicolo dal titolo.
    Restituisce:
        (journal, volume, issue)
    Esempi gestiti:
        "Lotta di Classe, anno III, no. 1"
        "Lavoro Politico, no. 5/6"
        "Lotta di Classe, supplemento al no. 2"
        "Lotta di Classe anno III n. 2/3"
    """
    title = str(titolo_raw or "").strip()
    if not title or title in ("nan", "None"):
        return "", None, None
    
    working = title
    volume = None
    issue = None
    
    # 1. Annata/volume: "anno III", "anno 3", anche senza virgola.
    m_anno = re.search(
        r"\banno\s+([IVXLCDM]+|\d+)\b",
        working,
        re.IGNORECASE,
    )
    if m_anno:
        volume = m_anno.group(1)
        working = (working[:m_anno.start()] + " " + working[m_anno.end():]).strip()
    
    # 2. Supplemento: deve avere priorità sul numero semplice.
    m_supp = re.search(
        r"\bsupplemento\s+(?:al\s+)?(?:no\.?|n\.?|numero|n°)\s*"
        r"([0-9]+(?:\s*[-/]\s*[0-9]+)?)",
        working,
        re.IGNORECASE,
    )
    if m_supp:
        issue = "suppl. " + re.sub(r"\s+", "", m_supp.group(1))
        working = (working[:m_supp.start()] + " " + working[m_supp.end():]).strip()
    else:
        # 3. Numero fascicolo: no., n., numero, n°; supporta 5/6 e 5-6.
        m_issue = re.search(
            r"\b(?:no\.?|n\.?|numero|n°)\s*"
            r"([0-9]+(?:\s*[-/]\s*[0-9]+)?)",
            working,
            re.IGNORECASE,
        )
        if m_issue:
            issue = re.sub(r"\s+", "", m_issue.group(1))
            working = (working[:m_issue.start()] + " " + working[m_issue.end():]).strip()
    
    journal = _clean_periodico_fragment(working)
    if not journal:
        journal = title
    
    return journal, volume, issue

def formatta_autore_bibliografico(nome_completo: str, persone: dict) -> str:
    """
    Trasforma un nome persona in forma bibliografica, se possibile.
    Esempio:
        "Mao Zedong", cognome="Mao" -> "Mao, Zedong"
    """
    nome = str(nome_completo or "").strip()
    if not nome:
        return ""
    
    info = persone.get(nome)
    if info and info.get("cognome"):
        cognome = str(info.get("cognome", "")).strip()
        if cognome:
            resto = nome.replace(cognome, "", 1).strip(" ,")
            return f"{cognome}, {resto}" if resto else cognome
    
    return nome

def costruisci_autori_citazione(
    autore_raw: str,
    org_raw: str,
    persone: dict,
    organizzazioni: dict,
):
    """
    Costruisce la lista degli autori per la citazione.
    Regole:
     - se c'è autore, usa quello;
     - se l'autore è una persona nota, prova a invertire cognome/nome;
     - se l'autore è una organizzazione nota, lo marca come corporate;
     - se non c'è autore ma c'è organizzazione, usa l'organizzazione
       come autore corporativo;
     - non usa mai l'archivio come autore;
     - non usa automaticamente l'editore come autore.
    """
    authors = []
    
    if autore_raw:
        for nome in split_nomi(autore_raw):
            if not nome:
                continue
            if nome in organizzazioni:
                authors.append({
                    "name": nome,
                    "corporate": True,
                })
            elif nome in persone:
                authors.append({
                    "name": formatta_autore_bibliografico(nome, persone),
                    "corporate": False,
                })
            else:
                # Nome non noto: lo lasciamo come letterale.
                # Non lo marchiamo come corporate per prudenza.
                authors.append({
                    "name": nome,
                    "corporate": False,
                })
    elif org_raw:
        for nome in split_nomi(org_raw):
            if not nome:
                continue
            authors.append({
                "name": nome,
                "corporate": True,
            })
    
    return authors

def costruisci_payload_citazione(
    *,
    ami_id: str,
    titolo: str,
    tipo: str,
    autore_raw: str,
    org_raw: str,
    editore_raw: str,
    luogo_raw: str,
    data_formattata: str,
    anno_pubblicazione: str,
    identifier: str,
    persone: dict,
    organizzazioni: dict,
):
    """
    Costruisce il payload JSON usato da documenti.js per generare
    le citazioni lato client.
    """
    ami_id = str(ami_id or "").strip()
    titolo = str(titolo or "").strip()
    tipo = str(tipo or "").strip().lower()
    
    if titolo in ("", "nan", "None"):
        titolo = "Senza titolo"
    
    permalink = site_url(f"documenti/{ami_id}/")
    citation_key = sanitize_citation_id(ami_id)
    
    data_display = str(data_formattata or "").strip()
    if data_display in ("", "nan", "None", "n.d."):
        data_display = "s.d."
    
    year = str(anno_pubblicazione or "").strip()
    if year in ("nan", "None", "9999"):
        year = ""
    
    authors = costruisci_autori_citazione(
        autore_raw=autore_raw,
        org_raw=org_raw,
        persone=persone,
        organizzazioni=organizzazioni,
    )
    
    author_display = "; ".join(
        a.get("name", "")
        for a in authors
        if a.get("name")
    )
    
    is_periodical = tipo in TIPI_PERIODICI
    container_title = ""
    volume = ""
    issue = ""
    
    if is_periodical:
        container_title, volume, issue = parse_periodico_titolo(titolo)
    
    # Per ora manteniamo una logica semplice:
    # l'editore esplicito ha priorità; in mancanza usiamo l'organizzazione.
    publisher = str(editore_raw or "").strip()
    if not publisher:
        publisher = str(org_raw or "").strip()
    
    place = str(luogo_raw or "").strip()
    
    mode = "bibliografica" if tipo in TIPI_BIBLIOGRAFICI else "minima"
    formats = ["chicago", "mla", "bibtex", "semplice"]
    
    if mode == "minima":
        formats = ["semplice"]
    
    return {
        "schema": "ami-citazioni/2",
        "mode": mode,
        "formats": formats,
        "doc": {
            "ami_id": ami_id,
            "citation_key": citation_key,
            "type": tipo,
            "title": titolo,
            "date_display": data_display,
            "year": year,
            "url": permalink,
            "archive": ARCHIVE_NAME,
            "archive_id": ami_id,
            "ia_identifier": str(identifier or "").strip(),
            "authors": authors,
            "author_display": author_display,
            "publisher": publisher,
            "place": place,
            "is_periodical": is_periodical,
            "container_title": container_title,
            "volume": volume or "",
            "issue": issue or "",
        },
    }