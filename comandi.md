AMI — Comandi

Tutti i comandi si lanciano dalla root del progetto tramite Launcher.py, l'unico punto di ingresso previsto (gli script in ./scripts/ non hanno flag CLI propri e non vanno lanciati direttamente in produzione).

---

python Launcher.py [comando] [argomenti]

---

## Uso quotidiano

### Rigenera e pubblica tutto

python Launcher.py

### Rigenera e pubblica con un messaggio di commit custom

python Launcher.py "Aggiunta serie 1972-73"

## Rigenerazione mirata

### Rigenera solo schede specifiche

python Launcher.py --only AMI-0034
python Launcher.py --only AMI-0034,AMI-0035,AMI-0102

**Quando usarlo:** una scheda specifica mostra dati sbagliati/obsoleti (es. descrizione IA non aggiornata, errore nei metadati) e vuoi correggerla senza toccare il resto.

## Cache Internet Archive

### Invalida la cache IA di identifier specifici

python Launcher.py --refresh-ia identifier1,identifier2

**Nota:** questo NON invalida la cache metadati-documento — se la scheda esiste già e non è cambiato nient'altro, potrebbe comunque essere saltata. Per correggere una singola scheda in modo completo usa `--only` (sopra).

### Invalida TUTTA la cache Internet Archive

python Launcher.py --force-refresh-ia

## Manutenzione cache

### Svuota tutta la cache

python Launcher.py --clear-cache

### Statistiche cache

python Launcher.py --cache-stats

### Aiuto

python Launcher.py --help
