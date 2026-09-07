import pandas as pd
import re
import logging
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURAZIONE VALIDAZIONE
# ============================================================================

COLONNE_OBBLIGATORIE_CATALOGO = ['id', 'titolo', 'tipo']
COLONNE_OPZIONALI_CATALOGO = [
    'autore', 'organizzazione', 'luogo', 'editore', 'provenienza',
    'persone_collegate', 'organizzazioni_collegate', 'data', 'anno',
    'serie', 'url', 'url_ia', 'nome_file', 'nome_file_originale',
    'nome_file_traduzione', 'descrizione', 'note'
]

TIPI_DOCUMENTO_VALIDI = [
    'libro', 'opuscolo', 'articolo', 'manifesto', 'foto', 'fotografia',
    'testo', 'testo_bilingue', 'volantino', 'giornale', 'rivista',
    'corrispondenza', 'documento', 'archivio', 'altro'
]

COLONNE_OBBLIGATORIE_SOGGETTI = ['nome']

# Pattern per validazione URL Internet Archive
URL_IA_PATTERN = re.compile(r'^https?://(www\.)?archive\.org/details/[a-zA-Z0-9_-]+')

# Pattern per validazione ID documento (solo caratteri alfanumerici e trattini)
ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

# Anni validi per documenti storici (range ragionevole)
ANNO_MINIMO = 1900
ANNO_MASSIMO = datetime.now().year + 1


class ValidationResult:
    """Classe per incapsulare il risultato della validazione."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.stats: Dict[str, Any] = {}

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, message: str):
        self.errors.append(message)
        logger.error(f"❌ {message}")

    def add_warning(self, message: str):
        self.warnings.append(message)
        logger.warning(f"⚠️ {message}")

    def add_info(self, message: str):
        self.info.append(message)
        logger.info(f"ℹ️ {message}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info,
            'stats': self.stats
        }

    def print_report(self):
        """Stampa un report formattato della validazione."""
        print("\n" + "=" * 70)
        print("REPORT VALIDAZIONE DATI")
        print("=" * 70)

        if self.is_valid:
            print("✅ VALIDAZIONE SUPERATA CON SUCCESSO")
        else:
            print("❌ VALIDAZIONE FALLITA")

        print(f"\n📊 STATISTICHE:")
        for key, value in self.stats.items():
            print(f"   • {key}: {value}")

        if self.errors:
            print(f"\n❌ ERRORI ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")

        if self.warnings:
            print(f"\n⚠️ WARNING ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")

        if self.info:
            print(f"\nℹ️ INFO ({len(self.info)}):")
            for i, info in enumerate(self.info, 1):
                print(f"   {i}. {info}")

        print("=" * 70 + "\n")


class AdvancedValidator:
    """
    Sistema avanzato di validazione dati per AMI.

    Funzionalità:
    - Validazione struttura colonne
    - Controllo duplicati e valori nulli
    - Validazione formati (URL, date, ID)
    - Controllo coerenza referenziale
    - Report dettagliato con statistiche
    """

    def __init__(self, strict_mode: bool = False):
        """
        Inizializza il validatore.

        Args:
            strict_mode: Se True, i warning diventano errori bloccanti
        """
        self.strict_mode = strict_mode
        self.result = ValidationResult()

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalizza i nomi delle colonne (minuscole, strip)."""
        df.columns = df.columns.str.strip().str.lower()
        return df

    def validate_catalogo(self, df: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
        """
        Valida il DataFrame del Catalogo completo.

        Args:
            df: DataFrame del catalogo

        Returns:
            Tuple[bool, Dict]: (Successo, Report completo)
        """
        self.result = ValidationResult()

        # Normalizza colonne
        df = self._normalize_columns(df.copy())

        # 1. Controllo colonne essenziali
        self._check_required_columns(df, COLONNE_OBBLIGATORIE_CATALOGO, "Catalogo")

        if not self.result.is_valid:
            self.result.stats['righe_totali'] = len(df)
            return self.result.is_valid, self.result.to_dict()

        # 2. Statistiche base
        self.result.stats['righe_totali'] = len(df)
        self.result.stats['colonne_totali'] = len(df.columns)
        self.result.stats['colonne_rilevate'] = list(df.columns)

        # 3. Controllo ID
        self._validate_id_column(df)

        # 4. Controllo titoli
        self._validate_titoli(df)

        # 5. Controllo tipi documento
        self._validate_tipi_documento(df)

        # 6. Controllo date/anni
        self._validate_date(df)

        # 7. Controllo URL Internet Archive
        self._validate_url_ia(df)

        # 8. Controllo coerenza riferimenti
        self._validate_riferimenti(df)

        # 9. Controllo valori vuoti sospetti
        self._validate_valori_sospetti(df)

        # In strict mode, converte warning in errori
        if self.strict_mode and self.result.warnings:
            self.result.errors.extend(self.result.warnings)
            self.result.warnings = []

        return self.result.is_valid, self.result.to_dict()

    def validate_soggetti(self, df: pd.DataFrame, tipo: str = "Soggetto") -> Tuple[bool, Dict[str, Any]]:
        """
        Valida DataFrame Persone o Organizzazioni.

        Args:
            df: DataFrame soggetti
            tipo: Tipo di soggetto ("Persone" o "Organizzazioni")

        Returns:
            Tuple[bool, Dict]: (Successo, Report completo)
        """
        self.result = ValidationResult()

        df = self._normalize_columns(df.copy())

        # 1. Controllo colonna nome
        self._check_required_columns(df, COLONNE_OBBLIGATORIE_SOGGETTI, tipo)

        if not self.result.is_valid:
            return self.result.is_valid, self.result.to_dict()

        # 2. Statistiche
        self.result.stats['soggetti_totali'] = len(df)
        self.result.stats['tipo'] = tipo

        # 3. Controllo nomi vuoti o duplicati
        if 'nome' in df.columns:
            nomi_nulli = df['nome'].isnull().sum()
            if nomi_nulli > 0:
                self.result.add_error(f"Trovati {nomi_nulli} nomi vuoti nel foglio {tipo}")

            duplicati = df[df.duplicated(subset=['nome'], keep=False)]
            if not duplicati.empty:
                nomi_dup = duplicati['nome'].unique().tolist()[:10]  # Max 10
                self.result.add_warning(f"Nomi duplicati in {tipo}: {nomi_dup}")
                self.result.stats['nomi_duplicati'] = len(duplicati)

        # 4. Controllo campi opzionali comuni
        campi_comuni = ['bio', 'note', 'immagine', 'slug']
        for campo in campi_comuni:
            if campo in df.columns:
                self.result.stats[f'campo_{campo}_presente'] = True

        return self.result.is_valid, self.result.to_dict()

    def validate_persone(self, df: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
        """Validazione specifica per persone."""
        df = self._normalize_columns(df.copy())
        valido, report = self.validate_soggetti(df, "Persone")

        if valido:
            # Controlli specifici persone
            if 'cognome' in df.columns:
                cognomi_nulli = df['cognome'].isnull().sum()
                if cognomi_nulli > 0:
                    self.result.add_warning(f"{cognomi_nulli} persone senza cognome")

            if 'nascita' in df.columns and 'morte' in df.columns:
                # Controllo coerenza date nascita/morte
                mask = df['nascita'].notna() & df['morte'].notna()
                if mask.any():
                    # Logica semplificata - validazione completa in utils.py
                    pass

        return self.result.is_valid, self.result.to_dict()

    def validate_organizzazioni(self, df: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
        """Validazione specifica per organizzazioni."""
        df = self._normalize_columns(df.copy())
        valido, report = self.validate_soggetti(df, "Organizzazioni")

        if valido:
            # Controlli specifici organizzazioni
            if 'sigla' in df.columns:
                sigle_nulle = df['sigla'].isnull().sum()
                sigle_vuote = (df['sigla'] == '').sum()
                if sigle_nulle + sigle_vuote > 0:
                    self.result.add_info(f"{sigle_nulle + sigle_vuote} organizzazioni senza sigla")

        return self.result.is_valid, self.result.to_dict()

    # =========================================================================
    # METODI DI VALIDAZIONE INTERNI
    # =========================================================================

    def _check_required_columns(self, df: pd.DataFrame, required: List[str], sheet_name: str):
        """Verifica presenza colonne obbligatorie."""
        mancanti = [col for col in required if col not in df.columns]
        if mancanti:
            self.result.add_error(f"Colonne mancanti nel foglio {sheet_name}: {mancanti}")

    def _validate_id_column(self, df: pd.DataFrame):
        """Valida la colonna ID."""
        if 'id' not in df.columns:
            return

        # ID vuoti
        id_nulli = df['id'].isnull().sum()
        id_vuoti = (df['id'] == '').sum()
        if id_nulli + id_vuoti > 0:
            self.result.add_error(f"Trovati {id_nulli + id_vuoti} ID vuoti nel Catalogo")

        # ID duplicati
        duplicati = df[df.duplicated(subset=['id'], keep=False)]
        if not duplicati.empty:
            ids_dup = duplicati['id'].unique().tolist()
            self.result.add_error(f"ID duplicati trovati: {ids_dup[:10]}{'...' if len(ids_dup) > 10 else ''}")
            self.result.stats['id_duplicati'] = len(duplicati)

        # ID formato invalido
        mask_valido = df['id'].astype(str).str.match(ID_PATTERN)
        invalidi = df[~mask_valido & df['id'].notna() & (df['id'] != '')]
        if not invalidi.empty:
            self.result.add_warning(f"ID con formato sospetto: {invalidi['id'].tolist()[:10]}")

    def _validate_titoli(self, df: pd.DataFrame):
        """Valida i titoli dei documenti."""
        if 'titolo' not in df.columns:
            return

        titoli_mancanti = df[df['titolo'].isin(['', 'nan', 'None', 'Senza titolo'])]
        if len(titoli_mancanti) > 0:
            self.result.add_warning(f"{len(titoli_mancanti)} documenti senza titolo significativo")

    def _validate_tipi_documento(self, df: pd.DataFrame):
        """Valida i tipi di documento."""
        if 'tipo' not in df.columns:
            return

        tipi_unici = df['tipo'].unique()
        tipi_invalidi = [t for t in tipi_unici if str(t).lower() not in TIPI_DOCUMENTO_VALIDI and str(t) not in ['', 'nan', 'None']]

        if tipi_invalidi:
            self.result.add_warning(f"Tipi documento non standard: {tipi_invalidi}")
            self.result.add_info(f"Tipi validi: {', '.join(TIPI_DOCUMENTO_VALIDI)}")

    def _validate_date(self, df: pd.DataFrame):
        """Valida date e anni."""
        # Controllo colonna 'data'
        if 'data' in df.columns:
            # Validazione semplificata - controllo anni estremi
            mask_data = df['data'].notna() & (df['data'] != '')
            if mask_data.any():
                # Estrai anni per controllo range
                anni_sospetti = []
                for val in df.loc[mask_data, 'data']:
                    match = re.search(r'(19|20)\d{2}', str(val))
                    if match:
                        anno = int(match.group())
                        if anno < ANNO_MINIMO or anno > ANNO_MASSIMO:
                            anni_sospetti.append(str(val))

                if anni_sospetti:
                    self.result.add_warning(f"Date con anni sospetti: {anni_sospetti[:10]}")

        # Controllo colonna 'anno'
        if 'anno' in df.columns:
            mask_anno = df['anno'].notna() & (df['anno'] != '') & (df['anno'] != 'nan')
            if mask_anno.any():
                try:
                    df_anni = pd.to_numeric(df.loc[mask_anno, 'anno'], errors='coerce')
                    anni_fuori_range = df_anni[(df_anni < ANNO_MINIMO) | (df_anni > ANNO_MASSIMO)]
                    if not anni_fuori_range.empty:
                        self.result.add_warning(f"Anni fuori range ({ANNO_MINIMO}-{ANNO_MASSIMO}): {anni_fuori_range.tolist()[:10]}")
                except Exception:
                    pass

    def _validate_url_ia(self, df: pd.DataFrame):
        """Valida URL di Internet Archive."""
        url_cols = ['url', 'url_ia']

        for col in url_cols:
            if col not in df.columns:
                continue

            mask_url = df[col].notna() & (df[col] != '') & (df[col] != '#')
            if not mask_url.any():
                continue

            # Controllo formato URL IA
            url_non_ia = df.loc[mask_url, col][~df.loc[mask_url, col].str.contains('archive.org', na=False)]
            if not url_non_ia.empty:
                self.result.add_warning(f"URL in '{col}' non puntano a archive.org: {url_non_ia.tolist()[:5]}")

            # Controllo URL malformati
            url_malformati = []
            for url in df.loc[mask_url, col]:
                if not URL_IA_PATTERN.match(str(url)):
                    url_malformati.append(url)

            if url_malformati:
                self.result.add_warning(f"URL potenzialmente malformati: {url_malformati[:5]}")

    def _validate_riferimenti(self, df: pd.DataFrame):
        """Valida riferimenti incrociati (persone, organizzazioni collegate)."""
        # Controllo sintassi liste separate da punto e virgola
        col_lista = ['persone_collegate', 'organizzazioni_collegate', 'serie']

        for col in col_lista:
            if col not in df.columns:
                continue

            mask = df[col].notna() & (df[col] != '')
            if mask.any():
                # Controllo che non ci siano separatori inconsistenti
                valori = df.loc[mask, col]
                # Rileva uso misto di separatori
                misto = valori[vali.str.contains(',') & vali.str.contains(';')]
                if not misto.empty:
                    self.result.add_info(f"Colonna '{col}': rilevato uso misto di separatori in {len(misto)} righe")

    def _validate_valori_sospetti(self, df: pd.DataFrame):
        """Rileva valori potenzialmente errati o inconsistenti."""
        # Controllo celle con solo spazi
        for col in df.columns:
            if df[col].dtype == object:
                mask_spazi = df[col].str.match(r'^\s*$', na=False)
                if mask_spazi.any():
                    self.result.add_info(f"Colonna '{col}': {mask_spazi.sum()} valori sono solo spazi bianchi")

        # Controllo placeholder text
        placeholder_patterns = ['TODO', 'DA FARE', 'INSERIRE', '??', 'N/D']
        for col in df.columns:
            if df[col].dtype == object:
                for pattern in placeholder_patterns:
                    mask = df[col].str.contains(pattern, case=False, na=False)
                    if mask.any():
                        self.result.add_warning(f"Colonna '{col}': trovati {mask.sum()} placeholder '{pattern}'")


def run_validation(data_dir: str) -> Dict[str, Any]:
    """
    Esegue validazione completa su tutti i fogli Excel.

    Args:
        data_dir: Directory contenente dati.xlsx

    Returns:
        Dict: Report completo di validazione
    """
    validator = AdvancedValidator()
    reports = {}

    excel_path = Path(data_dir) / 'dati.xlsx'

    if not excel_path.exists():
        return {
            'success': False,
            'error': f"File non trovato: {excel_path}",
            'reports': {}
        }

    try:
        # Carica tutti i fogli
        xls = pd.ExcelFile(excel_path)
        sheet_names = xls.sheet_names

        print(f"\n🔍 VALIDAZIONE DATI - {excel_path}")
        print(f"📋 Fogli rilevati: {', '.join(sheet_names)}\n")

        # Valida Catalogo
        if 'Catalogo' in sheet_names:
            df_cat = pd.read_excel(excel_path, sheet_name='Catalogo', dtype=str).fillna('')
            valido, report = validator.validate_catalogo(df_cat)
            reports['catalogo'] = report
            print(f"Catalogo: {'✅ VALIDO' if valido else '❌ INVALIDO'}")

        # Valida Persone
        if 'Persone' in sheet_names:
            df_pers = pd.read_excel(excel_path, sheet_name='Persone', dtype=str).fillna('')
            valido, report = validator.validate_persone(df_pers)
            reports['persone'] = report
            print(f"Persone: {'✅ VALIDO' if valido else '❌ INVALIDO'}")

        # Valida Organizzazioni
        if 'Organizzazioni' in sheet_names:
            df_org = pd.read_excel(excel_path, sheet_name='Organizzazioni', dtype=str).fillna('')
            valido, report = validator.validate_organizzazioni(df_org)
            reports['organizzazioni'] = report
            print(f"Organizzazioni: {'✅ VALIDO' if valido else '❌ INVALIDO'}")

        # Report finale
        tutti_validi = all(r.get('is_valid', False) for r in reports.values())

        print("\n" + "=" * 70)
        if tutti_validi:
            print("✅ TUTTE LE VALIDAZIONI SONO STATE SUPERATE")
        else:
            print("❌ ALMENO UNA VALIDAZIONE È FALLITA - RIVEDERE I DATI")
        print("=" * 70)

        return {
            'success': tutti_validi,
            'reports': reports,
            'summary': {
                'fogli_validati': len(reports),
                'fogli_validi': sum(1 for r in reports.values() if r.get('is_valid', False))
            }
        }

    except Exception as e:
        logger.error(f"Errore durante validazione: {e}")
        return {
            'success': False,
            'error': str(e),
            'reports': {}
        }


# ============================================================================
# MAIN PER TESTING
# ============================================================================

if __name__ == "__main__":
    import sys

    # Configura logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    # Directory dati di default
    data_dir = sys.argv[1] if len(sys.argv) > 1 else '../data'

    result = run_validation(data_dir)

    if not result['success']:
        sys.exit(1)
