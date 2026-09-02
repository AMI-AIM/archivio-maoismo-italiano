"""
Indicizzazione del catalogo per lookup O(1) invece di O(n).
Evita loop annidati che causano O(n²) iterazioni.
"""

from core.utils import split_nomi


class CatalogIndexer:
    """Crea indici per documenti associati a persone/organizzazioni."""
    
    def __init__(self, df_catalogo):
        """
        Inizializza gli indici dal DataFrame catalogo.
        
        Args:
            df_catalogo: DataFrame con colonne 'id', 'autore', 'persone_collegate',
                        'organizzazione', 'organizzazioni_collegate'
        """
        self.df = df_catalogo
        
        # Indici per persone
        self.docs_by_author = {}           # nome_persona -> [doc_rows]
        self.docs_by_mentioned = {}        # nome_persona -> [doc_rows]
        
        # Indici per organizzazioni
        self.docs_by_organization = {}     # nome_org -> [doc_rows]
        self.docs_by_org_author = {}       # nome_org -> [doc_rows]
        self.docs_by_org_mentioned = {}    # nome_org -> [doc_rows]
        
        self._build_indexes()
    
    def _build_indexes(self):
        """Costruisce tutti gli indici una sola volta."""
        for idx, row in self.df.iterrows():
            ami_id = str(row.get('id', '')).strip()
            if not ami_id or ami_id in ['nan', 'None']:
                continue
            
            # ============================================================
            # INDICI PERSONE
            # ============================================================
            
            # Autori
            autore_raw = str(row.get('autore', '')).strip()
            if autore_raw and autore_raw not in ['nan', 'None']:
                autori = split_nomi(autore_raw)
                for autore in autori:
                    if autore not in self.docs_by_author:
                        self.docs_by_author[autore] = []
                    self.docs_by_author[autore].append(row)
            
            # Persone menzionate
            persone_raw = str(row.get('persone_collegate', '')).strip()
            if persone_raw and persone_raw not in ['nan', 'None']:
                persone = split_nomi(persone_raw)
                for persona in persone:
                    if persona not in self.docs_by_mentioned:
                        self.docs_by_mentioned[persona] = []
                    self.docs_by_mentioned[persona].append(row)
            
            # ============================================================
            # INDICI ORGANIZZAZIONI
            # ============================================================
            
            # Organizzazione pubblicatrice
            org_raw = str(row.get('organizzazione', '')).strip()
            if org_raw and org_raw not in ['nan', 'None']:
                orgs = split_nomi(org_raw)
                for org in orgs:
                    if org not in self.docs_by_organization:
                        self.docs_by_organization[org] = []
                    self.docs_by_organization[org].append(row)
            
            # Organizzazione autore
            org_autore_raw = str(row.get('autore', '')).strip()
            if org_autore_raw and org_autore_raw not in ['nan', 'None']:
                org_autori = split_nomi(org_autore_raw)
                for org in org_autori:
                    if org not in self.docs_by_org_author:
                        self.docs_by_org_author[org] = []
                    self.docs_by_org_author[org].append(row)
            
            # Organizzazioni menzionate
            org_collegate_raw = str(row.get('organizzazioni_collegate', '')).strip()
            if org_collegate_raw and org_collegate_raw not in ['nan', 'None']:
                org_collegate = split_nomi(org_collegate_raw)
                for org in org_collegate:
                    if org not in self.docs_by_org_mentioned:
                        self.docs_by_org_mentioned[org] = []
                    self.docs_by_org_mentioned[org].append(row)
    
    def get_docs_for_person(self, nome):
        """
        Restituisce tutti i documenti associati a una persona.
        
        Args:
            nome (str): Nome della persona
        
        Returns:
            list: Lista di righe DataFrame
        """
        docs = []
        docs.extend(self.docs_by_author.get(nome, []))
        docs.extend(self.docs_by_mentioned.get(nome, []))
        return docs
    
    def get_docs_for_organization(self, nome):
        """
        Restituisce tutti i documenti associati a un'organizzazione.
        
        Args:
            nome (str): Nome dell'organizzazione
        
        Returns:
            list: Lista di righe DataFrame
        """
        docs = []
        docs.extend(self.docs_by_organization.get(nome, []))
        docs.extend(self.docs_by_org_author.get(nome, []))
        docs.extend(self.docs_by_org_mentioned.get(nome, []))
        return docs
    
    def get_roles_for_person(self, nome, doc_row):
        """
        Restituisce i ruoli di una persona in un documento.
        
        Args:
            nome (str): Nome della persona
            doc_row: Riga del DataFrame
        
        Returns:
            list: Lista di ruoli ['autore', 'menzionato']
        """
        ruoli = []
        
        autore_raw = str(doc_row.get('autore', '')).strip()
        if autore_raw and autore_raw not in ['nan', 'None']:
            autori = split_nomi(autore_raw)
            if nome in autori:
                ruoli.append('autore')
        
        persone_raw = str(doc_row.get('persone_collegate', '')).strip()
        if persone_raw and persone_raw not in ['nan', 'None']:
            persone = split_nomi(persone_raw)
            if nome in persone:
                ruoli.append('menzionato')
        
        return ruoli
    
    def get_roles_for_organization(self, nome, doc_row):
        """
        Restituisce i ruoli di un'organizzazione in un documento.
        
        Args:
            nome (str): Nome dell'organizzazione
            doc_row: Riga del DataFrame
        
        Returns:
            list: Lista di ruoli ['pubblicato da', 'autore', 'menzionato']
        """
        ruoli = []
        
        org_raw = str(doc_row.get('organizzazione', '')).strip()
        if org_raw and org_raw not in ['nan', 'None']:
            orgs = split_nomi(org_raw)
            if nome in orgs:
                ruoli.append('pubblicato da')
        
        autore_raw = str(doc_row.get('autore', '')).strip()
        if autore_raw and autore_raw not in ['nan', 'None']:
            autori = split_nomi(autore_raw)
            if nome in autori:
                ruoli.append('autore')
        
        org_collegate_raw = str(doc_row.get('organizzazioni_collegate', '')).strip()
        if org_collegate_raw and org_collegate_raw not in ['nan', 'None']:
            org_collegate = split_nomi(org_collegate_raw)
            if nome in org_collegate:
                ruoli.append('menzionato')
        
        return ruoli