import os
import json
import gzip
from pathlib import Path


class JSONOptimizer:
    """Ottimizza JSON per caricamento frontend più veloce."""
    
    @staticmethod
    def compress_json(input_path, output_path):
        """
        Comprime JSON con gzip.
        
        Args:
            input_path: Path file JSON sorgente
            output_path: Path file .json.gz compresso
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        with gzip.open(output_path, 'wt', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        size_orig = os.path.getsize(input_path)
        size_comp = os.path.getsize(output_path)
        ratio = round((1 - size_comp/size_orig) * 100, 1)
        
        print(f"   [COMPRESS] {Path(input_path).name}: {size_orig}B → {size_comp}B ({ratio}% riduzione)")
        return output_path
    
    @staticmethod
    def minify_json(input_path, output_path):
        """
        Minifica JSON (rimuove spazi inutili).
        
        Args:
            input_path: Path file JSON sorgente
            output_path: Path file JSON minificato
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Minify: separators=(',', ':') rimuove spazi
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
        
        size_orig = os.path.getsize(input_path)
        size_min = os.path.getsize(output_path)
        ratio = round((1 - size_min/size_orig) * 100, 1)
        
        print(f"   [MINIFY] {Path(input_path).name}: {size_orig}B → {size_min}B ({ratio}% riduzione)")
        return output_path