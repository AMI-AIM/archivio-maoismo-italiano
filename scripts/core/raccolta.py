"""
Scheda ISAD(G) di livello "raccolta" per l'intero AMI.

Legge il foglio 'Raccolta' di dati.xlsx (colonne Codice_ISAD, Elemento,
Valore) e la inserisce nella pagina "Il progetto" al posto del segnaposto
<!-- SCHEDA-RACCOLTA --> di assets/progetto.md (copiato in build/ da
sync_assets.py prima della generazione).

Date (3.1.3), Consistenza (3.1.5) e Lingua (3.4.3), se lasciate vuote nel
foglio, sono calcolate dal Catalogo a ogni generazione, cosi' non vanno
aggiornate a mano a ogni nuova acquisizione. La colonna Note e' di lavoro
e non viene pubblicata.
"""

import html
import os
import re

import pandas as pd

SEGNAPOSTO = '<!-- SCHEDA-RACCOLTA -->'


def _pulito(v):
    t = str(v if v is not None else '').strip()
    return '' if t in ('nan', 'None') else t


def _valori_calcolati(df):
    """df: Catalogo con colonne minuscole."""
    calcolati = {}
    anni = []
    for _, riga in df.iterrows():
        sorgente = _pulito(riga.get('data_normalizzata', '')) or _pulito(riga.get('data', ''))
        m = re.search(r'(1[89]\d\d|20\d\d)', sorgente)
        if m:
            anni.append(int(m.group(1)))
    if anni:
        calcolati['3.1.3'] = f'{min(anni)} – {max(anni)}' if min(anni) != max(anni) else str(min(anni))

    unita = sum(1 for v in df.get('id', []) if _pulito(v))
    if unita:
        calcolati['3.1.5'] = f'{unita} unità' if unita != 1 else '1 unità'

    lingue = []
    for v in df.get('lingua', []):
        for lingua in _pulito(v).split(';'):
            lingua = lingua.strip().lower()
            if lingua and lingua not in lingue:
                lingue.append(lingua)
    if lingue:
        calcolati['3.4.3'] = ', '.join(sorted(lingue, key=lambda x: (x != 'italiano', x))).capitalize()
    return calcolati


def scheda_raccolta_html(excel_path, df_catalogo):
    try:
        df = pd.read_excel(excel_path, sheet_name='Raccolta', dtype=str).fillna('')
    except Exception:
        return ''
    df.columns = df.columns.str.strip().str.lower()
    calcolati = _valori_calcolati(df_catalogo)

    righe = []
    for _, r in df.iterrows():
        codice = _pulito(r.get('codice_isad', ''))
        elemento = _pulito(r.get('elemento', ''))
        valore = _pulito(r.get('valore', '')) or calcolati.get(codice, '')
        if not elemento or not valore:
            continue
        valore_html = '<br>'.join(html.escape(x) for x in valore.splitlines() if x.strip())
        righe.append(f'<div class="doc-scheda__campo"><dt>{html.escape(elemento)}</dt>'
                     f'<dd>{valore_html}</dd></div>')
    if not righe:
        return ''
    return ('<div class="scheda-raccolta">\n<dl class="doc-scheda__campi">'
            + ''.join(righe) + '</dl>\n</div>')


def inserisci_scheda_raccolta(output_dir, excel_path, df_catalogo):
    """Sostituisce il segnaposto in build/progetto.md. Restituisce True se
    la scheda e' stata inserita."""
    pagina = os.path.join(output_dir, 'progetto.md')
    if not os.path.exists(pagina):
        return False
    with open(pagina, encoding='utf-8') as f:
        testo = f.read()
    if SEGNAPOSTO not in testo:
        return False
    with open(pagina, 'w', encoding='utf-8') as f:
        f.write(testo.replace(SEGNAPOSTO, scheda_raccolta_html(excel_path, df_catalogo)))
    return True
