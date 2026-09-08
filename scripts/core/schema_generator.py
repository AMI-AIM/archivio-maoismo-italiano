"""
Generazione schema.org JSON-LD per migliorare ricercabilità.
Aiuta Google a comprendere la struttura dei dati.
"""

import json
from core.site_config import SITE_URL


class SchemaGenerator:
    """Genera schema.org JSON-LD per vari tipi di contenuto."""
    
    @staticmethod
    def person_schema(nome, biografia, immagine_url, slug, num_doc, data_range):
        """
        Schema per una persona (CreativeWork author).
        
        Args:
            nome: Nome della persona
            biografia: Biografia (testo)
            immagine_url: URL immagine profilo
            slug: Slug della persona
            num_doc: Numero di documenti associati
            data_range: Intervallo anni (es. "1920 – 1980")
        
        Returns:
            dict: Schema.org Person
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "Person",
            "name": nome,
            "url": f"{SITE_URL}/persone/{slug}/",
            "sameAs": [],
        }
        
        if immagine_url:
            schema["image"] = immagine_url
        
        if biografia and biografia.strip():
            schema["description"] = biografia[:160]
        
        if data_range and data_range.strip():
            schema["jobTitle"] = f"Storico: {data_range}"
        
        if num_doc > 0:
            schema["workExample"] = {
                "@type": "Thing",
                "name": f"{num_doc} documenti nel catalogo AMI"
            }
        
        return schema
    
    @staticmethod
    def organization_schema(nome, storia, categoria, immagine_url, slug, num_doc, data_range):
        """
        Schema per un'organizzazione.
        
        Args:
            nome: Nome organizzazione
            storia: Descrizione (testo)
            categoria: Categoria (es. "Partito")
            immagine_url: URL logo/immagine
            slug: Slug organizzazione
            num_doc: Numero documenti
            data_range: Intervallo anni (es. "1968 – 1995")
        
        Returns:
            dict: Schema.org Organization
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": nome,
            "url": f"{SITE_URL}/organizzazioni/{slug}/",
        }
        
        if immagine_url:
            schema["logo"] = immagine_url
        
        if storia and storia.strip():
            schema["description"] = storia[:160]
        
        if data_range and data_range.strip():
            schema["foundingDate"] = data_range.split(' – ')[0].strip() if ' – ' in data_range else data_range
        
        if categoria:
            schema["additionalType"] = f"Organization/{categoria}"
        
        return schema
    
    @staticmethod
    def document_schema(ami_id, titolo, descrizione, tipo, autori, organizzazioni,
                         data_pubblicazione, keywords, url_ia=None, immagine_url=None):
        """
        Schema per un documento d'archivio.

        Usa "Article" per i tipi seriali (periodico, giornale, rivista,
        articolo), "CreativeWork" per tutti gli altri: e' il tipo generico
        piu' corretto per opuscoli, manifesti, foto e materiali eterogenei
        che non hanno un equivalente schema.org piu' specifico.

        Args:
            ami_id: ID del documento (es. "AMI-0001")
            titolo: Titolo del documento
            descrizione: Descrizione/abstract in testo semplice (senza HTML),
                idealmente gia' troncata (es. la meta description SEO)
            tipo: Tipo di documento normalizzato (es. "libro", "manifesto")
            autori: lista di nomi (stringhe) degli autori
            organizzazioni: lista di nomi (stringhe) delle organizzazioni collegate
            data_pubblicazione: anno come stringa (es. "1968"), o stringa vuota
                se non determinabile
            keywords: lista di argomenti/serie collegati al documento
            url_ia: URL della fonte primaria su Internet Archive, se presente
            immagine_url: URL di un'immagine rappresentativa, se presente

        Returns:
            dict: Schema.org CreativeWork (o Article)
        """
        tipi_seriali = {'periodico', 'giornale', 'rivista', 'articolo'}
        tipo_schema = 'Article' if tipo in tipi_seriali else 'CreativeWork'

        schema = {
            "@context": "https://schema.org",
            "@type": tipo_schema,
            "name": titolo,
            "identifier": ami_id,
            "url": f"{SITE_URL}/documenti/{ami_id}/",
            "isPartOf": {
                "@type": "Collection",
                "name": "Archivio del Maoismo Italiano",
                "url": SITE_URL
            },
            "inLanguage": "it",
        }

        if descrizione and descrizione.strip():
            schema["description"] = descrizione[:300]

        if autori:
            schema["author"] = [{"@type": "Person", "name": nome} for nome in autori]

        if organizzazioni:
            schema["publisher"] = [{"@type": "Organization", "name": nome} for nome in organizzazioni]

        if data_pubblicazione and str(data_pubblicazione).strip():
            schema["datePublished"] = str(data_pubblicazione).strip()

        if keywords:
            schema["keywords"] = ", ".join(keywords)

        if url_ia and url_ia != '#':
            schema["sameAs"] = url_ia

        if immagine_url:
            schema["image"] = immagine_url

        return schema

    @staticmethod
    def breadcrumb_schema(items):
        """
        Schema BreadcrumbList per navigazione.
        
        Args:
            items: List di tuple (label, url)
                   es: [("Home", "/"), ("Persone", "/persone/"), ("Mario Rossi", "/persone/mario-rossi/")]
        
        Returns:
            dict: Schema.org BreadcrumbList
        """
        breadcrumbs = []
        for pos, (label, url) in enumerate(items, 1):
            breadcrumbs.append({
                "@type": "ListItem",
                "position": pos,
                "name": label,
                "item": f"{SITE_URL}{url}" if not url.startswith('http') else url
            })
        
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": breadcrumbs
        }