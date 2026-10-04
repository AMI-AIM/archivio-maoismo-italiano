"""
Validazione di data/dati.xlsx prima della generazione del sito.

Ogni problema è indicato con foglio, riga (numero di riga di Excel) e
colonna, così da poterlo correggere direttamente nel file.

Tre livelli:
- ERRORE: il sito uscirebbe rotto o sbagliato (ID duplicati o mancanti,
  colonne o fogli mancanti, immagini indicate ma inesistenti, due schede con
  lo stesso indirizzo...). Blocca la pubblicazione (salvo --skip-validation).
- AVVISO: dato probabilmente sbagliato o incompleto, ma il sito funziona
  (data non riconosciuta, URL non di Internet Archive, relazione con
  categoria "da definire", nome scritto con una forma variante...).
- NOTA: informazione, nessuna azione richiesta (es. persone citate nei
  documenti che non hanno una scheda: per scelta, restano senza link).

Punto d'ingresso: run_validation(data_dir), usato da Launcher.py e da
.github/workflows/deploy.yml. Si può anche lanciare a mano:
    python -m scripts.core.validator
"""

import os
import re
from collections import defaultdict
from pathlib import Path

from .dati import FOGLI_ATTESI, ErroreDati, fogli
from .utils import formatta_data, slugify, split_nomi

ROOT_DIR = Path(__file__).resolve().parents[2]
CARTELLA_PROFILI = ROOT_DIR / "assets" / "immagini" / "profili"
CARTELLA_ARGOMENTI = ROOT_DIR / "assets" / "immagini" / "argomenti"
ESTENSIONI_ARGOMENTI = (".webp", ".jpg", ".jpeg", ".png")  # come scripts/argomenti.py

ERRORE, AVVISO, NOTA = "errore", "avviso", "nota"

# Colonne che la pipeline legge: se una manca (es. rinominata per sbaglio)
# le pagine perdono dati senza che nessuno se ne accorga -> ERRORE.
COLONNE_ATTESE = {
    "Catalogo": ["ID", "Livello", "Lingua", "Titolo", "Titolo_attribuito", "Organizzazione",
                 "Autore", "Editore", "Data", "Data_normalizzata", "Tipo", "Luogo", "Percorsi",
                 "Persone_collegate", "Organizzazioni_collegate", "Provenienza", "URL",
                 "Nome_file", "Nome_file_originale", "Nome_file_traduzione", "Consistenza",
                 "Descrizione"],
    "Raccolta": ["Codice_ISAD", "Elemento", "Valore"],
    "Persone": ["ID_autorita", "Tipo_entita", "Norme", "Nome", "Cognome", "Forme_varianti",
                "Nascita", "Morte", "Immagine", "Biografia", "Wikidata", "VIAF"],
    "Organizzazioni": ["ID_autorita", "Tipo_entita", "Norme", "Nome", "Forme_varianti",
                       "Categoria", "Fondazione", "Scioglimento", "Immagine", "Storia",
                       "Wikidata", "VIAF"],
    "Relazioni": ["ID_relazione", "ID_entita_A", "Entita_A", "ID_entita_B", "Entita_B",
                  "Relazione", "Categoria_ISAAR", "Date"],
}

TIPI_DOCUMENTO = {"libro", "opuscolo", "articolo", "manifesto", "foto", "fotografia", "testo",
                  "testo_bilingue", "volantino", "audio", "periodico", "giornale", "rivista",
                  "corrispondenza", "documento", "archivio", "altro"}
LIVELLI = {"unità"}
SI_NO = {"sì", "si", "no", ""}
TIPI_ENTITA = {"Persone": {"persona"}, "Organizzazioni": {"ente"}}
CATEGORIE_ISAAR = {"gerarchica", "associativa", "temporale", "familiare"}

RE_ID_DOC = re.compile(r"^AMI-\d{4,}$")
RE_ID_AUT = {"Persone": re.compile(r"^AMI-P-\d{3,}$"), "Organizzazioni": re.compile(r"^AMI-O-\d{3,}$")}
RE_ID_REL = re.compile(r"^AMI-R-\d{3,}$")
RE_URL_IA = re.compile(r"^https?://(www\.)?archive\.org/details/[A-Za-z0-9._-]+")
RE_DATA_ISO = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
RE_ESTREMO = re.compile(r"^(\d{4}|\d{1,3}\?{1,3}|\?{4})$")  # 1968, 196?, 19??, ????
# 1968, 1966-1991, 196?, 1921- (aperta), 1968-???? (fine ignota)
RE_DATE_REL = re.compile(r"^(\d{4}|\d{3}\?|\?{4})(-(\d{4}|\d{3}\?|\?{4})?)?$")
RE_WIKIDATA = re.compile(r"^Q\d+$")
RE_VIAF = re.compile(r"^\d+$")
RE_CODICE_ISAD = re.compile(r"^\d+(\.\d+)+$")
SEGNAPOSTI = ("TODO", "DA FARE", "INSERIRE", "XXX")
COLONNE_DATA = {"Data", "Data_normalizzata", "Nascita", "Morte", "Fondazione",
                "Scioglimento", "Date", "Data_redazione"}


class Rapporto:
    def __init__(self):
        self.voci = []

    def aggiungi(self, gravita, foglio, messaggio, riga=None, colonna=None):
        self.voci.append({"gravita": gravita, "foglio": foglio, "riga": riga,
                          "colonna": colonna, "messaggio": messaggio})

    def errore(self, *a, **k):
        self.aggiungi(ERRORE, *a, **k)

    def avviso(self, *a, **k):
        self.aggiungi(AVVISO, *a, **k)

    def nota(self, *a, **k):
        self.aggiungi(NOTA, *a, **k)

    def conta(self, gravita):
        return sum(v["gravita"] == gravita for v in self.voci)

    @property
    def valido(self):
        return self.conta(ERRORE) == 0


def _riga(indice):
    """Numero di riga in Excel (riga 1 = intestazioni)."""
    return int(indice) + 2


def _v(valore):
    return str(valore).strip()


# ---------------------------------------------------------------------------
# Controlli generici
# ---------------------------------------------------------------------------

def _controlla_colonne(r, nome, df):
    mancanti = [c for c in COLONNE_ATTESE.get(nome, []) if c not in df.columns]
    if mancanti:
        r.errore(nome, f"colonne mancanti o rinominate: {', '.join(mancanti)}")
    return not mancanti


def _controlla_id(r, foglio, df, colonna, pattern, esempio):
    visti = {}
    for i, valore in df[colonna].items():
        v = _v(valore)
        if not v:
            r.errore(foglio, "ID mancante", _riga(i), colonna)
            continue
        if v != valore:
            r.avviso(foglio, f"l'ID '{v}' contiene spazi all'inizio o alla fine", _riga(i), colonna)
        if v in visti:
            r.errore(foglio, f"ID '{v}' duplicato (già usato alla riga {visti[v]})", _riga(i), colonna)
        else:
            visti[v] = _riga(i)
        if not pattern.match(v):
            r.avviso(foglio, f"ID '{v}' non segue la convenzione {esempio}", _riga(i), colonna)
    return visti


def _controlla_segnaposti(r, foglio, df):
    for colonna in df.columns:
        if colonna in COLONNE_DATA:
            continue
        for i, valore in df[colonna].items():
            v = _v(valore)
            if not v:
                continue
            for s in SEGNAPOSTI:
                if s.lower() in v.lower():
                    r.avviso(foglio, f"testo provvisorio '{s}' ancora presente", _riga(i), colonna)
                    break
            else:
                if "??" in v:
                    r.avviso(foglio, "contiene '??' (dato da completare?)", _riga(i), colonna)


# ---------------------------------------------------------------------------
# Persone e Organizzazioni (record d'autorità ISAAR)
# ---------------------------------------------------------------------------

def _controlla_autorita(r, foglio, df):
    """Restituisce {nome: id}, {variante: nome autorizzato}, {id: nome}."""
    nomi, varianti, per_id = {}, {}, {}
    ids = _controlla_id(r, foglio, df, "ID_autorita", RE_ID_AUT[foglio],
                        "AMI-P-001" if foglio == "Persone" else "AMI-O-001")
    slug_visti = {}
    for i, row in df.iterrows():
        riga = _riga(i)
        nome = _v(row["Nome"])
        id_aut = _v(row["ID_autorita"])
        if not nome:
            r.errore(foglio, "Nome mancante", riga, "Nome")
            continue
        if nome in nomi:
            r.errore(foglio, f"nome '{nome}' duplicato", riga, "Nome")
        nomi[nome] = id_aut
        if id_aut:
            per_id[id_aut] = nome
        slug = slugify(nome)
        if slug in slug_visti and slug_visti[slug] != nome:
            r.errore(foglio, f"'{nome}' e '{slug_visti[slug]}' producono lo stesso indirizzo "
                             f"di pagina ({slug}): una delle due schede sovrascrive l'altra", riga, "Nome")
        slug_visti[slug] = nome

        tipo = _v(row["Tipo_entita"]).lower()
        if tipo and tipo not in TIPI_ENTITA[foglio]:
            r.avviso(foglio, f"Tipo_entita '{row['Tipo_entita']}' inatteso in questo foglio", riga, "Tipo_entita")

        for variante in split_nomi(row["Forme_varianti"]):
            if variante in varianti and varianti[variante] != nome:
                r.avviso(foglio, f"la forma variante '{variante}' è usata anche per "
                                 f"'{varianti[variante]}'", riga, "Forme_varianti")
            varianti[variante] = nome

        colonne_estremi = ("Nascita", "Morte") if foglio == "Persone" else ("Fondazione", "Scioglimento")
        anni = []
        for col in colonne_estremi:
            v = _v(row[col])
            if v and not RE_ESTREMO.match(v):
                r.avviso(foglio, f"'{v}' non è nel formato atteso (1968, 196? per ca., ???? per s.d.)",
                         riga, col)
            anni.append(int(v) if re.fullmatch(r"\d{4}", v) else None)
        if anni[0] and anni[1] and anni[0] > anni[1]:
            r.avviso(foglio, f"{colonne_estremi[0]} ({anni[0]}) successiva a {colonne_estremi[1]} "
                             f"({anni[1]})", riga, colonne_estremi[1])

        immagine = _v(row["Immagine"])
        if immagine and not immagine.startswith(("http://", "https://")):
            if not (CARTELLA_PROFILI / immagine).is_file():
                r.errore(foglio, f"immagine '{immagine}' non trovata in assets/immagini/profili/ "
                                 "(sul sito apparirebbe un'immagine rotta)", riga, "Immagine")

        wikidata, viaf = _v(row["Wikidata"]), _v(row["VIAF"])
        if wikidata and not RE_WIKIDATA.match(wikidata):
            r.avviso(foglio, f"identificativo Wikidata '{wikidata}' non valido (atteso Q seguito da cifre)",
                     riga, "Wikidata")
        if viaf and not RE_VIAF.match(viaf):
            r.avviso(foglio, f"identificativo VIAF '{viaf}' non valido (attese solo cifre)", riga, "VIAF")
    # Una forma variante identica al nome autorizzato di un altro record
    for variante, nome in varianti.items():
        if variante in nomi and variante != nome:
            r.avviso(foglio, f"'{variante}' è sia il nome di una scheda sia una forma variante di '{nome}'")
    return nomi, varianti, per_id, ids


# ---------------------------------------------------------------------------
# Catalogo
# ---------------------------------------------------------------------------

def _controlla_nomi(r, df, colonna, nomi, varianti, senza_scheda_e_nota):
    """Nomi in `colonna` che non corrispondono a una scheda."""
    assenti = defaultdict(list)
    for i, valore in df[colonna].items():
        for nome in split_nomi(valore):
            if nome in nomi:
                continue
            if nome in varianti:
                r.avviso("Catalogo", f"'{nome}' è una forma variante: per collegare la scheda usa "
                                     f"la forma autorizzata '{varianti[nome]}'", _riga(i), colonna)
            elif senza_scheda_e_nota:
                assenti[nome].append(_v(df.at[i, "ID"]))
            else:
                r.avviso("Catalogo", f"'{nome}' non ha una scheda in Persone/Organizzazioni "
                                     "(sul sito resterà senza link)", _riga(i), colonna)
    if assenti:
        elenco = ", ".join(sorted(assenti))
        r.nota("Catalogo", f"{len(assenti)} nomi senza scheda, mostrati senza link: {elenco}",
               colonna=colonna)


def _controlla_catalogo(r, df, nomi, varianti, incrociati=True):
    _controlla_id(r, "Catalogo", df, "ID", RE_ID_DOC, "AMI-0001")
    url_visti = {}
    percorsi = {}
    for i, row in df.iterrows():
        riga = _riga(i)
        if not _v(row["Titolo"]):
            r.errore("Catalogo", "Titolo mancante", riga, "Titolo")

        tipo = _v(row["Tipo"])
        if not tipo:
            r.avviso("Catalogo", "Tipo mancante", riga, "Tipo")
        elif tipo.lower() not in TIPI_DOCUMENTO:
            r.avviso("Catalogo", f"Tipo '{tipo}' non previsto (ammessi: {', '.join(sorted(TIPI_DOCUMENTO))})",
                     riga, "Tipo")

        livello = _v(row["Livello"]).lower()
        if livello and livello not in LIVELLI:
            r.avviso("Catalogo", f"Livello '{row['Livello']}' inatteso (atteso: unità)", riga, "Livello")
        if _v(row["Titolo_attribuito"]).lower() not in SI_NO:
            r.avviso("Catalogo", f"Titolo_attribuito '{row['Titolo_attribuito']}' inatteso (atteso Sì o No)",
                     riga, "Titolo_attribuito")

        # Date: 'Data' è quella mostrata, 'Data_normalizzata' finisce nell'EAD3.
        data, data_norm = _v(row["Data"]), _v(row["Data_normalizzata"])
        anno_data = None
        if data and data not in ("s.d.", "????"):
            _, ordinamento = formatta_data(data)
            if ordinamento[0] == 9999:
                r.avviso("Catalogo", f"data '{data}' non riconosciuta: sarà mostrata così com'è e messa "
                                     "in fondo agli elenchi (formati: 1968, 196?, 03/1968, 14/05/1968)",
                         riga, "Data")
            else:
                anno_data = ordinamento[0]
        if data_norm:
            if not RE_DATA_ISO.match(data_norm):
                r.avviso("Catalogo", f"Data_normalizzata '{data_norm}' non è AAAA, AAAA-MM o AAAA-MM-GG: "
                                     "non verrà riportata nell'EAD3", riga, "Data_normalizzata")
            elif anno_data and int(data_norm[:4]) != anno_data and "?" not in data:
                r.avviso("Catalogo", f"anno diverso tra Data ({data}) e Data_normalizzata ({data_norm})",
                         riga, "Data_normalizzata")

        url = _v(row["URL"])
        if not url:
            r.avviso("Catalogo", "URL mancante: la scheda non avrà il documento digitalizzato", riga, "URL")
        elif not RE_URL_IA.match(url):
            r.avviso("Catalogo", f"URL non riconosciuto come Internet Archive: {url}", riga, "URL")
        else:
            identificativo = re.search(r"/details/([^/?#]+)", url).group(1)
            if identificativo in url_visti:
                r.avviso("Catalogo", f"stesso item di Internet Archive della riga {url_visti[identificativo]} "
                                     f"({identificativo})", riga, "URL")
            url_visti.setdefault(identificativo, riga)

        for p in split_nomi(row["Percorsi"].replace(",", ";")):
            percorsi.setdefault(p, riga)

    # Ogni percorso tematico ha bisogno della sua immagine (pagina Percorsi).
    for percorso, riga in percorsi.items():
        slug = slugify(percorso)
        if not any((CARTELLA_ARGOMENTI / f"{slug}{est}").is_file() for est in ESTENSIONI_ARGOMENTI):
            r.avviso("Catalogo", f"il percorso '{percorso}' non ha un'immagine: aggiungi "
                                 f"assets/immagini/argomenti/{slug}.webp", riga, "Percorsi")

    if not incrociati:
        return
    # Soggetto produttore: ci si aspetta che abbia sempre una scheda.
    _controlla_nomi(r, df, "Autore", nomi, varianti, senza_scheda_e_nota=False)
    _controlla_nomi(r, df, "Organizzazione", nomi, varianti, senza_scheda_e_nota=False)
    # Persone e organizzazioni citate: senza scheda per scelta -> solo nota.
    _controlla_nomi(r, df, "Persone_collegate", nomi, varianti, senza_scheda_e_nota=True)
    _controlla_nomi(r, df, "Organizzazioni_collegate", nomi, varianti, senza_scheda_e_nota=True)


# ---------------------------------------------------------------------------
# Relazioni e Raccolta
# ---------------------------------------------------------------------------

def _controlla_relazioni(r, df, per_id, nomi, varianti):
    _controlla_id(r, "Relazioni", df, "ID_relazione", RE_ID_REL, "AMI-R-001")
    viste = {}
    for i, row in df.iterrows():
        riga = _riga(i)
        for lato in ("A", "B"):
            id_ent, nome = _v(row[f"ID_entita_{lato}"]), _v(row[f"Entita_{lato}"])
            if id_ent:
                if id_ent not in per_id:
                    r.errore("Relazioni", f"l'ID '{id_ent}' non esiste in Persone né in Organizzazioni",
                             riga, f"ID_entita_{lato}")
                elif nome and nome != per_id[id_ent]:
                    r.avviso("Relazioni", f"'{nome}' non coincide con il nome della scheda {id_ent} "
                                          f"('{per_id[id_ent]}'): sul sito vale la scheda",
                             riga, f"Entita_{lato}")
            elif not nome:
                r.errore("Relazioni", f"entità {lato} vuota (né ID né nome)", riga, f"Entita_{lato}")
            elif nome in nomi or nome in varianti:
                autorizzato = nome if nome in nomi else varianti[nome]
                r.avviso("Relazioni", f"'{nome}' ha una scheda ({nomi[autorizzato] or autorizzato}) "
                                      "ma manca l'ID: la relazione non sarà collegata",
                         riga, f"ID_entita_{lato}")
        a = _v(row["ID_entita_A"]) or _v(row["Entita_A"])
        b = _v(row["ID_entita_B"]) or _v(row["Entita_B"])
        if a and a == b:
            r.avviso("Relazioni", "un'entità è in relazione con se stessa", riga)
        chiave = (a, _v(row["Relazione"]).lower(), b)
        if chiave in viste:
            r.avviso("Relazioni", f"relazione ripetuta (uguale alla riga {viste[chiave]})", riga)
        viste.setdefault(chiave, riga)

        if not _v(row["Relazione"]):
            r.avviso("Relazioni", "tipo di relazione mancante", riga, "Relazione")
        categoria = _v(row["Categoria_ISAAR"]).lower()
        if categoria not in CATEGORIE_ISAAR:
            r.avviso("Relazioni", f"Categoria_ISAAR '{row['Categoria_ISAAR']}' non valida "
                                  f"(ammesse: {', '.join(sorted(CATEGORIE_ISAAR))})", riga, "Categoria_ISAAR")
        date = _v(row["Date"])
        if date and not RE_DATE_REL.match(date):
            r.avviso("Relazioni", f"date '{date}' non nel formato 1968, 1966-1991, 196?, 1921- o 1968-????", riga, "Date")


def _controlla_raccolta(r, df):
    visti = {}
    for i, row in df.iterrows():
        riga = _riga(i)
        codice = _v(row["Codice_ISAD"])
        if not codice:
            r.avviso("Raccolta", "Codice_ISAD mancante", riga, "Codice_ISAD")
        elif not RE_CODICE_ISAD.match(codice):
            r.avviso("Raccolta", f"Codice_ISAD '{codice}' non nel formato 3.1.1", riga, "Codice_ISAD")
        elif codice in visti:
            r.avviso("Raccolta", f"Codice_ISAD '{codice}' ripetuto (riga {visti[codice]})", riga, "Codice_ISAD")
        visti.setdefault(codice, riga)
        if not _v(row["Elemento"]):
            r.avviso("Raccolta", "Elemento mancante", riga, "Elemento")


# ---------------------------------------------------------------------------
# Esecuzione e report
# ---------------------------------------------------------------------------

def valida(percorso_excel=None):
    """Esegue tutti i controlli e restituisce un Rapporto."""
    r = Rapporto()
    tutti = fogli(percorso_excel)
    presenti = {}
    for nome in FOGLI_ATTESI:
        if nome not in tutti:
            r.errore(nome, "foglio mancante in dati.xlsx")
        elif _controlla_colonne(r, nome, tutti[nome]):
            presenti[nome] = tutti[nome]

    nomi, varianti, per_id = {}, {}, {}
    for foglio in ("Persone", "Organizzazioni"):
        if foglio in presenti:
            n, v, p, _ = _controlla_autorita(r, foglio, presenti[foglio])
            doppi = set(n) & set(nomi)
            for nome in sorted(doppi):
                r.avviso(foglio, f"'{nome}' è sia una persona sia un'organizzazione: i link "
                                 "porteranno alla scheda della persona")
            nomi.update(n)
            varianti.update(v)
            per_id.update(p)

    # Se Persone o Organizzazioni hanno problemi strutturali, i controlli
    # incrociati (nomi nel Catalogo, ID nelle Relazioni) darebbero centinaia
    # di falsi allarmi: si saltano finché il foglio non è corretto.
    incrociati = "Persone" in presenti and "Organizzazioni" in presenti
    if not incrociati:
        r.nota("Catalogo", "controlli su nomi e relazioni saltati: prima correggi "
                           "i fogli Persone/Organizzazioni")
    if "Catalogo" in presenti:
        _controlla_catalogo(r, presenti["Catalogo"], nomi, varianti, incrociati)
    if "Relazioni" in presenti and incrociati:
        _controlla_relazioni(r, presenti["Relazioni"], per_id, nomi, varianti)
    if "Raccolta" in presenti:
        _controlla_raccolta(r, presenti["Raccolta"])
    for nome, df in presenti.items():
        _controlla_segnaposti(r, nome, df)
    return r


def _posizione(v):
    parti = []
    if v["riga"]:
        parti.append(f"riga {v['riga']}")
    if v["colonna"]:
        parti.append(v["colonna"])
    return f"{', '.join(parti)}: " if parti else ""


def formatta_rapporto(r):
    righe = [f"{r.conta(ERRORE)} errori, {r.conta(AVVISO)} avvisi, {r.conta(NOTA)} note"]
    for gravita, titolo in ((ERRORE, "ERRORI (bloccano la pubblicazione)"),
                            (AVVISO, "AVVISI (da controllare, non bloccano)"),
                            (NOTA, "NOTE (nessuna azione richiesta)")):
        voci = [v for v in r.voci if v["gravita"] == gravita]
        if not voci:
            continue
        righe += ["", titolo]
        for foglio in FOGLI_ATTESI:
            del_foglio = [v for v in voci if v["foglio"] == foglio]
            if del_foglio:
                righe.append(f"  Foglio {foglio}")
                for v in sorted(del_foglio, key=lambda x: (x["riga"] or 0)):
                    righe.append(f"    - {_posizione(v)}{v['messaggio']}")
    return "\n".join(righe)


def _scrivi_sommario_github(r):
    sommario = os.environ.get("GITHUB_STEP_SUMMARY")
    if not sommario or not r.voci:
        return
    righe = ["### Validazione dati.xlsx",
             f"{r.conta(ERRORE)} errori, {r.conta(AVVISO)} avvisi, {r.conta(NOTA)} note", ""]
    for v in r.voci:
        if v["gravita"] != NOTA:
            righe.append(f"- **{v['gravita'].upper()}** — {v['foglio']}, {_posizione(v)}{v['messaggio']}")
    with open(sommario, "a", encoding="utf-8") as f:
        f.write("\n".join(righe) + "\n\n")


def run_validation(data_dir):
    """Valida data_dir/dati.xlsx, stampa il rapporto e restituisce un dizionario.

    Chiavi: success (bool), error (str, solo se il file non si legge),
    errori/avvisi/note (conteggi), voci (lista dei problemi).
    """
    percorso = Path(data_dir) / "dati.xlsx"
    print(f"\nVALIDAZIONE DATI - {percorso}")
    try:
        r = valida(percorso)
    except ErroreDati as e:
        return {"success": False, "error": str(e), "voci": []}
    print(formatta_rapporto(r))
    _scrivi_sommario_github(r)
    return {"success": r.valido, "errori": r.conta(ERRORE), "avvisi": r.conta(AVVISO),
            "note": r.conta(NOTA), "voci": r.voci}


if __name__ == "__main__":
    import sys
    esito = run_validation(str(ROOT_DIR / "data"))
    if esito.get("error"):
        print(f"ERRORE: {esito['error']}")
    sys.exit(0 if esito.get("success") else 1)
