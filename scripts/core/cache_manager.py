import os
import json
import hashlib
import pickle
from pathlib import Path
from datetime import datetime, timedelta

from scripts.config import CACHE_DIR

class CacheManager:
    def __init__(self):
        self.cache_dir = CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_cache_file = self.cache_dir / "metadata_cache.json"
        self.hashes_file = self.cache_dir / "file_hashes.json"
        self.ia_cache_file = self.cache_dir / "ia_downloads.json"

        self.metadata_cache = self._load_json(self.metadata_cache_file)
        self.file_hashes = self._load_json(self.hashes_file)
        self.ia_cache = self._load_json(self.ia_cache_file)

    @staticmethod
    def _load_json(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_json(self, file_path, data):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"   [WARNING] Errore salvataggio cache: {e}")

    @staticmethod
    def _hash_file(file_path):
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def get_ia_metadata(self, identifier, max_age_days=365):
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
        cache_key = f"ia_meta_{identifier}"
        self.ia_cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        self._save_json(self.ia_cache_file, self.ia_cache)

    def get_file_hash(self, file_path):
        return self.file_hashes.get(str(file_path))

    def set_file_hash(self, file_path, hash_value):
        self.file_hashes[str(file_path)] = hash_value
        self._save_json(self.hashes_file, self.file_hashes)

    def is_file_changed(self, file_path):
        file_path = Path(file_path)
        if not file_path.exists():
            return True
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

    def get_doc_metadata(self, doc_id):
        return self.metadata_cache.get(f"doc_{doc_id}")

    def set_doc_metadata(self, doc_id, metadata):
        self.metadata_cache[f"doc_{doc_id}"] = {
            'data': metadata,
            'timestamp': datetime.now().isoformat()
        }
        self._save_json(self.metadata_cache_file, self.metadata_cache)

    def clear_ia_cache(self):
        self.ia_cache = {}
        self._save_json(self.ia_cache_file, self.ia_cache)
        print("   [CLEAN] Cache IA svuotato")

    def clear_all(self):
        self.ia_cache = {}
        self.metadata_cache = {}
        self.file_hashes = {}
        self._save_json(self.metadata_cache_file, self.metadata_cache)
        self._save_json(self.ia_cache_file, self.ia_cache)
        self._save_json(self.hashes_file, self.file_hashes)
        print("   [CLEAN] Cache completamente svuotato")

    def print_stats(self):
        print(f"\n[STATS] Statistiche cache:")
        print(f"   - Metadati IA: {len(self.ia_cache)} entries")
        print(f"   - File tracciati: {len(self.file_hashes)} entries")
        print(f"   - Documenti: {len(self.metadata_cache)} entries")