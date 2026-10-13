"""
Hook MkDocs: comprime i fogli di stile dell'archivio nel sito generato.

I sorgenti in assets/stylesheets/ restano commentati e leggibili; a fine
build (on_post_build) i file .css in site/stylesheets/ perdono commenti e
spazi superflui. I CSS di Material (site/assets/) sono gia' minificati e
non vengono toccati.

La compressione e' volutamente prudente:
- le stringhe ("..." e '...') restano intatte, commenti compresi;
- lo spazio prima dei due punti NON si toglie, perche' nei selettori
  separa un discendente (".a :first-child" non e' ".a:first-child");
- gli spazi interni si riducono a uno solo, mai a zero, cosi' calc() e
  i valori composti ("0 0 1px", "a - b") restano validi.

Registrato in mkdocs.yml alla voce "hooks".
"""
import os

# Caratteri accanto ai quali lo spazio non serve mai
_SENZA_SPAZIO_PRIMA = set('{};,>')
_SENZA_SPAZIO_DOPO = set('{};,>:')


def minifica(css):
    """Restituisce il CSS senza commenti e senza spazi superflui."""
    pezzi = []
    i = 0
    n = len(css)
    while i < n:
        c = css[i]
        # Stringhe: copiate cosi' come sono
        if c in '"\'':
            j = i + 1
            while j < n and css[j] != c:
                j += 2 if css[j] == '\\' else 1
            pezzi.append(css[i:j + 1])
            i = j + 1
            continue
        # Commenti: eliminati
        if css.startswith('/*', i):
            fine = css.find('*/', i + 2)
            i = n if fine < 0 else fine + 2
            # un commento tra due parole vale come spazio
            pezzi.append(' ')
            continue
        # Spazi: ridotti a uno
        if c.isspace():
            while i < n and css[i].isspace():
                i += 1
            pezzi.append(' ')
            continue
        pezzi.append(c)
        i += 1

    # Seconda passata: togli gli spazi accanto alla punteggiatura
    testo = ''.join(pezzi)
    out = []
    i = 0
    n = len(testo)
    in_stringa = None
    while i < n:
        c = testo[i]
        if in_stringa:
            out.append(c)
            if c == '\\' and i + 1 < n:
                out.append(testo[i + 1])
                i += 2
                continue
            if c == in_stringa:
                in_stringa = None
            i += 1
            continue
        if c in '"\'':
            in_stringa = c
            out.append(c)
            i += 1
            continue
        if c == ' ':
            prima = out[-1] if out else ''
            dopo = testo[i + 1] if i + 1 < n else ''
            if not prima or not dopo or prima in _SENZA_SPAZIO_DOPO or dopo in _SENZA_SPAZIO_PRIMA:
                i += 1
                continue
        out.append(c)
        i += 1

    risultato = ''.join(out).replace(';}', '}')
    return risultato.strip() + '\n'


def on_post_build(config):
    cartella = os.path.join(config['site_dir'], 'stylesheets')
    if not os.path.isdir(cartella):
        return
    for nome in sorted(os.listdir(cartella)):
        if not nome.endswith('.css'):
            continue
        percorso = os.path.join(cartella, nome)
        with open(percorso, encoding='utf-8') as f:
            originale = f.read()
        with open(percorso, 'w', encoding='utf-8', newline='\n') as f:
            f.write(minifica(originale))
