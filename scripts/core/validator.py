import pandas as pd
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

COLONNE_OBBLIGATORIE_CATALOGO = ['id', 'titolo', 'tipo']
COLONNE_OBBLIGATORIE_SOGGETTI = ['nome'] # Comune a persone e org

def valida_catalogo(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Valida il DataFrame del Catalogo.
    Restituisce (Successo, Lista Errori)
    """
    errori = []
    warnings = []
    
    # 1. Controllo colonne essenziali
    df.columns = df.columns.str.strip().str.lower()
    mancanti = [col for col in COLONNE_OBBLIGATORIE_CATALOGO if col not in df.columns]
    if mancanti:
        errori.append(f"Colonne mancanti nel Catalogo: {mancanti}")
        return False, errori

    # 2. Controllo ID duplicati o vuoti
    if df['id'].isnull().any():
        errori.append("Trovati ID vuoti nel Catalogo.")
    
    duplicati = df[df.duplicated(subset=['id'], keep=False)]
    if not duplicati.empty:
        ids_dup = duplicati['id'].unique().tolist()
        errori.append(f"ID duplicati trovati: {ids_dup}")

    # 3. Controllo formati data (Warning, non blocca)
    if 'data' in df.columns:
        # Logica semplificata per rilevare date palesemente errate
        # La formattazione vera avviene in utils.py
        pass 

    # 4. Controllo URL IA malformate (Warning)
    if 'url_ia' in df.columns:
        mask_url = df['url_ia'].notna() & (df['url_ia'] != '#')
        url_sospette = df.loc[mask_url, 'url_ia'][~df.loc[mask_url, 'url_ia'].str.contains('archive.org', na=False)]
        if not url_sospette.empty:
            warnings.append(f"URL Internet Archive sospetti (non contengono 'archive.org'): {url_sospette.tolist()}")

    if errori:
        logger.error("Validazione Catalogo FALLITA:")
        for e in errori: logger.error(f" - {e}")
        return False, errori
    
    if warnings:
        logger.warning("Avvisi Validazione Catalogo:")
        for w in warnings: logger.warning(f" - {w}")

    logger.info("Validazione Catalogo superata con successo.")
    return True, []

def valida_soggetti(df: pd.DataFrame, tipo: str = "Soggetto") -> Tuple[bool, List[str]]:
    """
    Valida DataFrame Persone o Organizzazioni.
    """
    errori = []
    df.columns = df.columns.str.strip().str.lower()
    
    if 'nome' not in df.columns:
        errori.append(f"Colonna 'nome' mancante nel foglio {tipo}.")
        return False, errori

    if df['nome'].isnull().any():
        errori.append(f"Trovati nomi vuoti nel foglio {tipo}.")

    if errori:
        logger.error(f"Validazione {tipo} FALLITA:")
        for e in errori: logger.error(f" - {e}")
        return False, errori

    logger.info(f"Validazione {tipo} superata.")
    return True, []