import os
import json
import hashlib
import pickle
from pathlib import Path
from datetime import datetime, timedelta


class CacheManager:
    """Gestisce cache per velocizzare rigenerazione."""
    # scripts/core/cache_manager.py → parents[1] = scripts/
    _SCRIPTS_DIR = Path(__file__).resolve().parents[1]
    def __init__(self, cache_dir=None):
        """
        Inizializza il manager cache.
        Args:
            cache_dir: Directory cache. Default: scripts/.cache (relativo al repo, non al cwd)
        """
        if cache_dir is None:
            cache_dir = self._SCRIPTS_DIR / ".cache"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_cache_file = self.cache_dir / "metadata_cache.json"
        self.hashes_file = self.cache_dir / "file_hashes.json"
        self.ia_cache_file = self.cache_dir / "ia_downloads.json"
        
        # Carica cache esistenti
        self.metadata_cache = self._load_json(self.metadata_cache_file)
        self.file_hashes = self._load_json(self.hashes_file)
        self.ia_cache = self._load_json(self.ia_cache_file)
    
    # ============================================================
    # UTILITA
    # ============================================================
    
    @staticmethod
    def _load_json(file_path):
        """Carica JSON, ritorna {} se non esiste."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_json(self, file_path, data):
        """Salva JSON in modo sicuro."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"   [WARNING] Errore salvataggio cache: {e}")
    
    @staticmethod
    def _hash_file(file_path):
        """Calcola hash SHA256 di un file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    @staticmethod
    def hash_data(data):
        """Calcola un hash stabile per i dati che determinano un artefatto."""
        serialized = json.dumps(data, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()
    
    # ============================================================
    # INTERNET ARCHIVE CACHE
    # ============================================================
    
    def get_ia_metadata(self, identifier, max_age_days=365):
        """
        Restituisce metadati Internet Archive, da cache se disponibili.
        
        Args:
            identifier (str): ID IA (es. "my_document")
            max_age_days (int): Invalida cache dopo N giorni. Default: 365
        
        Returns:
            dict: Metadati (con 'description', 'metadata', etc.) o None
        """
        cache_key = f"ia_meta_{identifier}"
        
        if cache_key in self.ia_cache:
            cached = self.ia_cache[cache_key]
            cached_time = datetime.fromisoformat(cached.get('timestamp', '2000-01-01'))
            age_days = (datetime.now() - cached_time).days
            
            if age_days < max_age_days:
                print(f"   [CACHE] Metadati {identifier} (eta: {age_days}d)")
                return cached.get('data')
            else:
                print(f"   [EXPIRED] Metadati {identifier} (eta: {age_days}d)")
                del self.ia_cache[cache_key]
        
        return None
    
    def set_ia_metadata(self, identifier, data):
        """Salva metadati Internet Archive in cache."""
        cache_key = f"ia_meta_{identifier}"
        self.ia_cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        self._save_json(self.ia_cache_file, self.ia_cache)
    
    # ============================================================
    # HASH FILE (rilevare cambiamenti Excel)
    # ============================================================
    
    def get_file_hash(self, file_path):
        """Legge hash salvato di un file."""
        return self.file_hashes.get(str(file_path))
    
    def set_file_hash(self, file_path, hash_value):
        """Salva hash di un file."""
        self.file_hashes[str(file_path)] = hash_value
        self._save_json(self.hashes_file, self.file_hashes)
    
    def is_file_changed(self, file_path):
        """
        Controlla se un file e cambiato.
        
        Returns:
            bool: True se cambiato (o prima generazione), False altrimenti
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return True  # File non esiste = considerato "cambiato"
        
        new_hash = self._hash_file(file_path)
        old_hash = self.get_file_hash(file_path)
        
        if old_hash is None:
            print(f"   [NEW] Prima volta: {file_path.name}")
            return True
        
        if new_hash != old_hash:
            print(f"   [CHANGED] Modificato: {file_path.name}")
            self.set_file_hash(file_path, new_hash)
            return True
        
        print(f"   [OK] Invariato: {file_path.name}")
        return False
    
    # ============================================================
    # CACHE ROWWISE (metadati per riga del catalogo)
    # ============================================================
    
    def get_doc_metadata(self, doc_id):
        """
        Legge cache metadati per un documento specifico.
        
        Args:
            doc_id (str): ID documento (es. "AMI-0001")
        
        Returns:
            dict: Cache data or None
        """
        return self.metadata_cache.get(f"doc_{doc_id}")
    
    def set_doc_metadata(self, doc_id, metadata):
        """
        Salva metadati per un documento.
        
        Args:
            doc_id (str): ID documento
            metadata (dict): Metadati da cachare
        """
        self.metadata_cache[f"doc_{doc_id}"] = {
            'data': metadata,
            'timestamp': datetime.now().isoformat()
        }
        self._save_json(self.metadata_cache_file, self.metadata_cache)

    def clear_doc_metadata(self, doc_ids=None):
        """
        Invalida la cache metadati-documento, forzando la rigenerazione
        della scheda .md alla prossima esecuzione (bypassa lo skip-cache
        in crea_schede, che altrimenti salta qualsiasi documento gia'
        presente in cache indipendentemente da modifiche successive).

        Args:
            doc_ids: None per svuotare tutta la cache metadati documento,
                oppure lista di ID (es. ["AMI-0034"]) da invalidare
                singolarmente.
        """
        if doc_ids is None:
            self.metadata_cache = {}
            self._save_json(self.metadata_cache_file, self.metadata_cache)
            print("   [CLEAN] Cache metadati documenti svuotata")
            return

        rimossi = 0
        for doc_id in doc_ids:
            key = f"doc_{doc_id}"
            if key in self.metadata_cache:
                del self.metadata_cache[key]
                rimossi += 1

        self._save_json(self.metadata_cache_file, self.metadata_cache)
        print(f"   [CLEAN] Invalidati metadati per {rimossi}/{len(doc_ids)} documenti")
    
    # ============================================================
    # CACHE PULIZIA
    # ============================================================
    
    def clear_ia_cache(self):
        """Svuota cache Internet Archive."""
        self.ia_cache = {}
        self._save_json(self.ia_cache_file, self.ia_cache)
        print("   [CLEAN] Cache IA svuotato")

    def clear_ia_metadata(self, identifiers=None):
        """
        Invalida la cache dei metadati/testi Internet Archive.

        Args:
            identifiers: None per svuotare TUTTA la cache IA (equivalente a
                clear_ia_cache). Altrimenti una lista di identifier IA
                (es. ["ami_0001", "ami_0002"]) da invalidare singolarmente,
                cosi' alla prossima generazione solo quei documenti vengono
                ri-scaricati da archive.org.
        """
        if identifiers is None:
            self.clear_ia_cache()
            return

        rimossi = 0
        for identifier in identifiers:
            meta_key = f"ia_meta_{identifier}"
            if meta_key in self.ia_cache:
                del self.ia_cache[meta_key]
                rimossi += 1

            # Rimuove anche eventuali testi cachati per lo stesso identifier
            testo_keys = [
                k for k in self.ia_cache
                if k.startswith(f"ia_text_{identifier}_")
            ]
            for k in testo_keys:
                del self.ia_cache[k]
                rimossi += 1

        self._save_json(self.ia_cache_file, self.ia_cache)
        print(f"   [CLEAN] Invalidate {rimossi} voci di cache per {len(identifiers)} identifier IA")
    
    def clear_all(self):
        """Svuota tutto il cache."""
        self.ia_cache = {}
        self.metadata_cache = {}
        self.file_hashes = {}
        self._save_json(self.metadata_cache_file, self.metadata_cache)
        self._save_json(self.ia_cache_file, self.ia_cache)
        self._save_json(self.hashes_file, self.file_hashes)
        print("   [CLEAN] Cache completamente svuotato")
    
    def print_stats(self):
        """Stampa statistiche cache."""
        print(f"\n[STATS] Statistiche cache:")
        print(f"   - Metadati IA: {len(self.ia_cache)} entries")
        print(f"   - File tracciati: {len(self.file_hashes)} entries")
        print(f"   - Documenti: {len(self.metadata_cache)} entries")
