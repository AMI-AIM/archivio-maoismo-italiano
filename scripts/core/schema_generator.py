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