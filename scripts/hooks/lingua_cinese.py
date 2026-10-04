"""
Hook MkDocs: marca come cinese i caratteri cinesi nelle pagine.

Il sito e' dichiarato in italiano (<html lang="it">). I titoli e le
descrizioni di diversi documenti contengono caratteri cinesi
(es. «毛主席语录»): senza marcatura i lettori di schermo li leggono con
la voce italiana e il browser puo' scegliere glifi giapponesi.
Il hook avvolge ogni sequenza di caratteri CJK del corpo della pagina
in <span lang="zh-Hans">, lasciando intatti tag, attributi, <head>,
<script>, <style> e <textarea> (WCAG 3.1.2, Lingua delle parti).

Registrato in mkdocs.yml alla voce "hooks".
"""
import re

# Ideogrammi CJK (blocco base ed estensione A), compatibilita', e
# punteggiatura cinese a larghezza piena (《》、。：，！？（）).
_CJK = '　-〿㐀-䶿一-鿿豈-﫿！-？（）'
_SEQUENZA = re.compile(f'[{_CJK}](?:[{_CJK}\\s]*[{_CJK}])?')
_SOLO_PUNTEGGIATURA = re.compile('^[　-〿！-？（）\\s]+$')
_TOKEN = re.compile(r'(<!--.*?-->|<[^>]+>)', re.S)
_SALTA = ('head', 'script', 'style', 'textarea', 'title', 'svg')


def _avvolgi(testo):
    def sostituisci(m):
        s = m.group(0)
        if _SOLO_PUNTEGGIATURA.match(s):
            return s
        return f'<span lang="zh-Hans">{s}</span>'
    return _SEQUENZA.sub(sostituisci, testo)


def on_post_page(output, page, config):
    if not re.search(f'[{_CJK}]', output):
        return output
    parti = _TOKEN.split(output)
    salto = []          # pila dei tag in cui non si interviene
    for i, parte in enumerate(parti):
        if i % 2 == 1:  # tag o commento
            m = re.match(r'<(/?)([a-zA-Z][\w-]*)', parte)
            if not m:
                continue
            chiusura, nome = m.group(1) == '/', m.group(2).lower()
            if nome in _SALTA:
                if chiusura:
                    if salto and salto[-1] == nome:
                        salto.pop()
                elif not parte.endswith('/>'):
                    salto.append(nome)
            continue
        if salto or not parte:
            continue
        parti[i] = _avvolgi(parte)
    return ''.join(parti)
