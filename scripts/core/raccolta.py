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
SEGNAPOSTO_CIFRE = '<!-- CIFRE-RACCOLTA -->'
SEGNAPOSTO_INDICE = '<!-- INDICE-PAGINA -->'
SEGNAPOSTO_PESO_EAD = '<!-- PESO-EAD -->'


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
    # Richiudibile: aperta di base; su telefono navigazione.js la chiude e
    # il sommario mostra quanti campi contiene. Su desktop il sommario e'
    # nascosto e la scheda resta aperta.
    return ('<details class="scheda-raccolta" open>\n'
            f'<summary><span class="scheda-raccolta__apri">Mostra i {len(righe)} campi</span>'
            '<span class="scheda-raccolta__chiudi">Nascondi i campi</span></summary>\n'
            '<dl class="doc-scheda__campi">' + ''.join(righe) + '</dl>\n</details>')


def _valori_raccolta(excel_path, df_catalogo):
    """Codice ISAD -> valore pubblicato (foglio Raccolta, o calcolato)."""
    calcolati = _valori_calcolati(df_catalogo)
    try:
        df = pd.read_excel(excel_path, sheet_name='Raccolta', dtype=str).fillna('')
    except Exception:
        return calcolati
    df.columns = df.columns.str.strip().str.lower()
    valori = dict(calcolati)
    for _, r in df.iterrows():
        codice = _pulito(r.get('codice_isad', ''))
        valore = _pulito(r.get('valore', ''))
        if codice and valore:
            valori[codice] = valore
    return valori


def cifre_raccolta_html(excel_path, df_catalogo):
    """Segnatura della raccolta in testa alla pagina, come quella delle
    schede documento: "AMI · Raccolta · 96 unita' · 1964 – 1993 · Italiano,
    cinese". Stessi valori della Scheda (3.1.1, 3.1.4, 3.1.5, 3.1.3, 3.4.3)."""
    v = _valori_raccolta(excel_path, df_catalogo)
    segnatura = v.get('3.1.1', '')
    altri = [v.get(c, '') for c in ('3.1.4', '3.1.5', '3.1.3', '3.4.3')]
    altri = [x for x in altri if x]
    if not segnatura and not altri:
        return ''
    parti = []
    if segnatura:
        parti.append(f'<span class="progetto-cifre__id">{html.escape(segnatura)}</span>')
    parti += [f'<span>{html.escape(x)}</span>' for x in altri]
    # La riga interna sborda a sinistra e il contenitore la ritaglia: il
    # punto separatore che finisce a inizio riga, andando a capo, sparisce.
    return ('<p class="progetto-cifre"><span class="progetto-cifre__riga">'
            + ''.join(parti) + '</span></p>')


def _slug(testo):
    t = re.sub(r'[^\w\s-]', '', testo.lower(), flags=re.UNICODE)
    return re.sub(r'[\s]+', '-', t.strip())


def indice_pagina_html(testo):
    """Indice "In questa pagina" dai titoli ## e ### del Markdown (i titoli
    dentro commenti HTML, come la sezione Diritti sospesa, non contano)."""
    senza_commenti = re.sub(r'<!--.*?-->', '', testo, flags=re.S)
    voci = []
    for m in re.finditer(r'^(#{2,3})\s+(.+?)\s*(?:\{#([\w-]+)\})?\s*$', senza_commenti, flags=re.M):
        livello, titolo, ident = len(m.group(1)), m.group(2).strip(), m.group(3)
        ident = ident or _slug(titolo)
        classe = ' class="progetto-indice__sotto"' if livello == 3 else ''
        voci.append(f'<li{classe}><a href="#{ident}">{html.escape(titolo)}</a></li>')
    if not voci:
        return ''
    return ('<details class="progetto-indice">\n<summary>In questa pagina</summary>\n<ul>\n'
            + '\n'.join(voci) + '\n</ul>\n</details>')


def _peso_file(percorso):
    try:
        byte = os.path.getsize(percorso)
    except OSError:
        return ''
    if byte < 1024:
        return f'{byte} byte'
    if byte < 1024 * 1024:
        return f'{round(byte / 1024)} kB'
    return f'{byte / (1024 * 1024):.1f} MB'.replace('.', ',')


def inserisci_scheda_raccolta(output_dir, excel_path, df_catalogo):
    """Sostituisce i segnaposti in build/progetto.md (scheda della
    raccolta, segnatura d'apertura, indice della pagina, peso dell'EAD:
    va chiamata dopo l'export EAD3). Restituisce
    True se la scheda e' stata inserita."""
    pagina = os.path.join(output_dir, 'progetto.md')
    if not os.path.exists(pagina):
        return False
    with open(pagina, encoding='utf-8') as f:
        testo = f.read()
    if SEGNAPOSTO_CIFRE in testo:
        testo = testo.replace(SEGNAPOSTO_CIFRE, cifre_raccolta_html(excel_path, df_catalogo))
    if SEGNAPOSTO_INDICE in testo:
        testo = testo.replace(SEGNAPOSTO_INDICE, indice_pagina_html(testo))
    if SEGNAPOSTO_PESO_EAD in testo:
        peso = _peso_file(os.path.join(output_dir, 'dati', 'ami-ead.xml'))
        testo = testo.replace(SEGNAPOSTO_PESO_EAD, f', {peso}' if peso else '')
    inserita = SEGNAPOSTO in testo
    if inserita:
        testo = testo.replace(SEGNAPOSTO, scheda_raccolta_html(excel_path, df_catalogo))
    with open(pagina, 'w', encoding='utf-8') as f:
        f.write(testo)
    return inserita
