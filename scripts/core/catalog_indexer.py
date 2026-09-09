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
            # INDICI PERSONE + ORGANIZZAZIONI (campo 'autore')
            # FIX BUG E: il campo 'autore' viene letto UNA sola volta e
            # usato sia per l'indice persone (docs_by_author) sia per
            # l'indice organizzazioni (docs_by_org_author). Prima veniva
            # letto due volte con variabili diverse (autore_raw e
            # org_autore_raw) contenenti gli stessi identici dati.
            # ============================================================
            autore_raw = str(row.get('autore', '')).strip()
            if autore_raw and autore_raw not in ['nan', 'None']:
                autori = split_nomi(autore_raw)
                for autore in autori:
                    self.docs_by_author.setdefault(autore, []).append(row)
                    self.docs_by_org_author.setdefault(autore, []).append(row)

            # ============================================================
            # INDICI PERSONE (campo 'persone_collegate')
            # ============================================================
            persone_raw = str(row.get('persone_collegate', '')).strip()
            if persone_raw and persone_raw not in ['nan', 'None']:
                persone = split_nomi(persone_raw)
                for persona in persone:
                    self.docs_by_mentioned.setdefault(persona, []).append(row)

            # ============================================================
            # INDICI ORGANIZZAZIONI (campo 'organizzazione')
            # ============================================================
            org_raw = str(row.get('organizzazione', '')).strip()
            if org_raw and org_raw not in ['nan', 'None']:
                orgs = split_nomi(org_raw)
                for org in orgs:
                    self.docs_by_organization.setdefault(org, []).append(row)

            # ============================================================
            # INDICI ORGANIZZAZIONI (campo 'organizzazioni_collegate')
            # ============================================================
            org_collegate_raw = str(row.get('organizzazioni_collegate', '')).strip()
            if org_collegate_raw and org_collegate_raw not in ['nan', 'None']:
                org_collegate = split_nomi(org_collegate_raw)
                for org in org_collegate:
                    self.docs_by_org_mentioned.setdefault(org, []).append(row)

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