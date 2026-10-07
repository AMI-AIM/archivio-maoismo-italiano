"""
Interfaccia a terminale del Launcher.

Mostra ogni fase su una riga (spinner mentre lavora, poi esito e durata) e
manda l'output dettagliato degli script in un file di registro, log/, uno
per esecuzione (si conservano gli ultimi REGISTRI_CONSERVATI). Se una fase
fallisce, a schermo compaiono le ultime righe del suo output e il percorso
del registro completo.

Usa la libreria `rich` per colori, spinner e riquadri; se non è installata
ripiega su un output testuale semplice, così il Launcher parte comunque e
può segnalare le dipendenze mancanti.

Modalità dettagliata (python Launcher.py --dettagli): l'output degli script
scorre a schermo come una volta, utile per capire un problema.
"""

import contextlib
import io
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from rich.console import Console
    from rich.markup import escape
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.theme import Theme
    RICH = True
except ImportError:  # pragma: no cover - ripiego senza rich
    RICH = False

    def escape(testo):
        return testo

REGISTRI_CONSERVATI = 30
RIGHE_IN_CASO_DI_ERRORE = 30

TEMA = {
    "marchio": "bold #c62828",
    "ok": "green",
    "errore": "bold red",
    "avviso": "yellow",
    "nota": "grey58",
    "tenue": "grey58",
    "titolo": "bold",
}


def _senza_markup(testo):
    """Ripiego senza rich: toglie i tag di stile ([ok]...[/]) e le protezioni (\\[)."""
    testo = re.sub(r"(?<!\\)\[/?[a-z ]*\]", "", str(testo))
    return testo.replace("\\[", "[")


class ErroreComando(Exception):
    """Una fase non è riuscita: la sequenza si ferma, nulla viene pubblicato."""


class Registro:
    """File di registro dell'esecuzione corrente (creato alla prima scrittura)."""

    def __init__(self, cartella):
        self.cartella = Path(cartella)
        self.percorso = None

    def _apri(self):
        if self.percorso:
            return
        self.cartella.mkdir(exist_ok=True)
        nome = datetime.now().strftime("launcher_%Y-%m-%d_%H-%M-%S.log")
        self.percorso = self.cartella / nome
        self.percorso.write_text(
            f"Launcher AMI — {datetime.now():%d/%m/%Y %H:%M:%S}\n"
            f"Comando: {' '.join(sys.argv)}\n\n", encoding="utf-8")
        vecchi = sorted(self.cartella.glob("launcher_*.log"))[:-REGISTRI_CONSERVATI]
        for file in vecchi:
            with contextlib.suppress(OSError):
                file.unlink()

    def scrivi(self, testo):
        self._apri()
        with open(self.percorso, "a", encoding="utf-8") as f:
            f.write(testo if testo.endswith("\n") else testo + "\n")

    def sezione(self, titolo):
        self.scrivi(f"\n{'=' * 70}\n{titolo}\n{'=' * 70}")

    def relativo(self, radice):
        if not self.percorso:
            return ""
        try:
            return str(self.percorso.relative_to(radice))
        except ValueError:
            return str(self.percorso)


def _durata(secondi):
    if secondi < 60:
        return f"{secondi:.1f} s".replace(".", ",")
    minuti, sec = divmod(int(secondi), 60)
    return f"{minuti} min {sec:02d} s"


class Interfaccia:
    def __init__(self, radice, verboso=False):
        self.radice = Path(radice)
        self.verboso = verboso
        self.registro = Registro(self.radice / "log")
        self.console = Console(theme=Theme(TEMA), highlight=False) if RICH else None

    # ---------------------------------------------------------------- testo
    def scrivi(self, testo="", stile=None):
        if self.console:
            self.console.print(testo, style=stile)
        else:
            print(_senza_markup(testo))

    def ok(self, testo, dettaglio="", durata=None):
        self._riga("✓", "ok", testo, dettaglio, durata)

    def fallito(self, testo, dettaglio="", durata=None):
        self._riga("✗", "errore", testo, dettaglio, durata)

    @staticmethod
    def esc(testo):
        """Protegge testo con parentesi quadre (es. "[m-l]") dal markup di rich."""
        return escape(str(testo))

    def avviso(self, testo):
        self.scrivi(f"  [avviso]![/avviso] {self.esc(testo)}" if self.console else f"  ! {testo}")
        self.registro.scrivi(f"AVVISO: {testo}")

    def _riga(self, simbolo, stile, testo, dettaglio, durata):
        tempo = _durata(durata) if durata is not None else ""
        if not self.console:
            print(f"  {'OK' if simbolo == '✓' else 'X '} {testo}  {dettaglio}  {tempo}".rstrip())
            return
        # Colonne a larghezza fissa: le righe delle fasi restano allineate.
        riga = Table.grid(expand=False, padding=(0, 1))
        riga.add_column(width=3, no_wrap=True)
        riga.add_column(width=40, no_wrap=True, overflow="ellipsis")
        riga.add_column(width=32, no_wrap=True, overflow="ellipsis")
        riga.add_column(justify="right", width=9, no_wrap=True)
        riga.add_row(Text(f" {simbolo}", style=stile), Text(testo),
                     Text(dettaglio, style="tenue"), Text(tempo, style="tenue"))
        self.console.print(riga)

    def intestazione(self, sottotitolo=""):
        if self.console:
            self.console.print()
            self.console.print("  AMI · Archivio del Maoismo Italiano", style="marchio")
            if sottotitolo:
                self.console.print(f"  {sottotitolo}", style="tenue")
            self.console.rule(style="grey35")
        else:
            print(f"\nAMI · Archivio del Maoismo Italiano  {sottotitolo}\n" + "-" * 60)

    def pannello(self, titolo, righe, stile="grey50"):
        """righe: lista di stringhe con markup rich (o testo semplice)."""
        if self.console:
            corpo = "\n".join(righe) if righe else ""
            self.console.print(Panel(corpo, title=titolo, title_align="left",
                                     border_style=stile, padding=(0, 1), expand=False))
        else:
            print(f"\n[{titolo}]")
            for r in righe:
                print(f"  {_senza_markup(r)}")

    def chiedi(self, domanda):
        try:
            if self.console:
                return self.console.input(domanda).strip()
            return input(_senza_markup(domanda)).strip()
        except EOFError:
            return ""

    # ---------------------------------------------------------------- fasi
    @contextlib.contextmanager
    def fase(self, nome):
        """Una fase: spinner mentre lavora, poi ✓/✗ con durata.

        Il blocco può impostare stato['dettaglio'] per il testo a destra.
        """
        stato = {"dettaglio": ""}
        self.registro.sezione(nome)
        inizio = time.monotonic()
        if self.verboso or not self.console:
            self.scrivi(f"\n▸ {nome}", "titolo")
            gestore = contextlib.nullcontext()
        else:
            # Il vecchio prompt dei comandi di Windows non ha i caratteri braille
            # dello spinner "dots": lì si usa la classica barretta che ruota.
            spinner = "line" if getattr(self.console, "legacy_windows", False) else "dots"
            gestore = self.console.status(f"[tenue]{nome}…[/tenue]", spinner=spinner)
        try:
            with gestore:
                yield stato
        except BaseException:
            self.fallito(nome, stato["dettaglio"], time.monotonic() - inizio)
            raise
        self.ok(nome, stato["dettaglio"], time.monotonic() - inizio)

    def esegui(self, comando, cwd=None, env=None):
        """Esegue un comando: output nel registro (o a schermo con --dettagli).

        Restituisce l'output catturato; se il comando fallisce mostra le ultime
        righe e solleva ErroreComando.
        """
        ambiente = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", **(env or {})}
        self.registro.scrivi("$ " + " ".join(f'"{c}"' if " " in str(c) else str(c) for c in comando))
        if self.verboso:
            risultato = subprocess.run(comando, cwd=cwd or self.radice, env=ambiente)
            uscita = ""
        else:
            risultato = subprocess.run(comando, cwd=cwd or self.radice, env=ambiente,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            uscita = risultato.stdout.decode("utf-8", errors="replace")
            self.registro.scrivi(uscita)
        self.registro.scrivi(f"[codice di uscita: {risultato.returncode}]")
        if risultato.returncode != 0:
            if uscita:
                self.mostra_coda(uscita)
            raise ErroreComando(f"il comando '{' '.join(map(str, comando))}' è fallito "
                                f"(codice {risultato.returncode}).")
        return uscita

    def cattura(self, funzione, *args, **kwargs):
        """Esegue una funzione Python mandando le sue stampe nel registro."""
        if self.verboso:
            return funzione(*args, **kwargs)
        buffer = io.StringIO()
        try:
            with contextlib.redirect_stdout(buffer):
                return funzione(*args, **kwargs)
        finally:
            self.registro.scrivi(buffer.getvalue())

    def mostra_coda(self, uscita):
        righe = [r for r in uscita.rstrip().splitlines() if r.strip()]
        coda = righe[-RIGHE_IN_CASO_DI_ERRORE:]
        if not coda:
            return
        if self.console:
            self.console.print(Panel(Text("\n".join(coda)), title="Ultime righe dell'output",
                                     title_align="left", border_style="red", padding=(0, 1)))
        else:
            print("\n".join(coda))

    def percorso_registro(self):
        return self.registro.relativo(self.radice)
