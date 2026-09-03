"""
Logica condivisa per gli argomenti (campo 'Serie' del Catalogo).

Questo modulo e' la fonte unica di verita' per il calcolo degli slug
degli argomenti. E' usato sia da scripts/argomenti.py (che genera le
pagine argomento) sia da core/schede.py (che genera i backlink dalle
schede documento), cosi' i link puntano sempre alla pagina corretta.

Gli slug sono assegnati in ordine alfabetico per etichetta, in modo
deterministico: a parita' di Catalogo, argomenti.py e schede.py
producono sempre gli stessi slug.
"""
import re
import unicodedata

from .utils import slugify

# Slug che non devono mai essere usati per una pagina argomento.
RESERVED_SLUGS = {
    'index',
    '404',
    'sitemap',
    'robots',
}


def normalize_key(value):
    """
    Normalizza il nome di un argomento per il raggruppamento.
    - minuscole
    - rimozione accenti
    - compressione spazi
    """
    value = str(value).strip().lower()
    value = unicodedata.normalize('NFKD', value)
    value = ''.join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r'\s+', ' ', value)


def split_argomenti(raw):
    """
    Divide il contenuto del campo Serie/Argomenti.
    Separatore principale: ';'. Fallback: ','.
    """
    txt = str(raw).strip()
    if not txt or txt.lower() in {'nan', 'none'}:
        return []
    txt = re.sub(r'\s+', ' ', txt)
    if ';' in txt or '\n' in txt:
        parti = re.split(r';|\n', txt)
    elif ',' in txt:
        parti = txt.split(',')
    else:
        parti = [txt]
    return [p.strip() for p in parti if p.strip()]


def _choose_label(current, new):
    """
    Sceglie quale etichetta mostrare quando lo stesso argomento compare
    con differenze di maiuscole/minuscole.
    """
    if normalize_key(current) != normalize_key(new):
        return current
    current_upper = sum(1 for ch in current if ch.isupper())
    new_upper = sum(1 for ch in new if ch.isupper())
    if new_upper > current_upper:
        return new
    if current_upper == new_upper:
        if len(new) > len(current) and new != new.lower():
            return new
    return current


def _make_slug(label, used_slugs):
    """
    Genera uno slug evitando collisioni e slug riservati.
    """
    base = slugify(label) or 'argomento'
    if base in RESERVED_SLUGS:
        base = 'argomento'
    slug = base
    counter = 2
    while slug in used_slugs or slug in RESERVED_SLUGS:
        slug = f'{base}-{counter}'
        counter += 1
    used_slugs.add(slug)
    return slug


def build_argomenti_index(df_catalogo, topic_column='serie'):
    """
    Costruisce l'indice argomento -> slug a partire dal Catalogo.

    Args:
        df_catalogo: DataFrame del foglio Catalogo (colonne gia' lowercase).
        topic_column: nome della colonna argomenti (default 'serie').

    Returns:
        dict: {normalize_key(label): {'label': str, 'slug': str}}
    """
    if topic_column not in df_catalogo.columns:
        return {}

    # Raccoglie la label preferita per ogni chiave normalizzata,
    # percorrendo il Catalogo nell'ordine dei documenti.
    labels = {}
    for _, row in df_catalogo.iterrows():
        for argomento in split_argomenti(row.get(topic_column, '')):
            key = normalize_key(argomento)
            if not key:
                continue
            if key not in labels:
                labels[key] = argomento
            else:
                labels[key] = _choose_label(labels[key], argomento)

    # Assegnazione slug in ordine alfabetico => deterministico e stabile.
    index = {}
    used_slugs = set()
    for key, label in sorted(labels.items(), key=lambda kv: kv[1].lower()):
        index[key] = {
            'label': label,
            'slug': _make_slug(label, used_slugs),
        }
    return index


def get_argomento_slug(label, index):
    """
    Ritorna lo slug di un argomento, o None se non presente nell'indice.
    """
    entry = index.get(normalize_key(label))
    return entry['slug'] if entry else None