"""Il formato unico dei file in data/: un valore sta su una riga se ci entra, altrimenti si apre su più righe.

Uso, dalla radice del repository:
    python tools/formatta_dati.py           # riformatta tutti i file di data/
    python tools/formatta_dati.py --check   # elenca i file fuori formato, senza toccarli (esce con 1 se ce ne sono)

La regola è una sola, così ogni modifica ai dati, fatta a mano o da un agente, torna allo stesso testo:
- indentazione di 4 spazi, caratteri non ASCII scritti così come sono (é, emoji);
- un oggetto o una lista sta su una riga sola se, con la sua chiave e l'indentazione, non supera WIDTH caratteri;
- altrimenti si apre e ogni voce va su una riga sua, con la stessa regola un livello più in dentro;
- il file finisce con un a capo.
Il contenuto non cambia: chiavi, ordine e valori restano quelli di prima.
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
WIDTH = 120
INDENT = "    "


def _inline(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(", ", ": "))


def _format(value, depth: int, prefix: str) -> str:
    """Il testo di `value`, che inizia dopo `prefix` (la chiave, se c'è) a profondità `depth`."""
    one_line = _inline(value)
    if not isinstance(value, (dict, list)) or not value or len(INDENT * depth + prefix + one_line) + 1 <= WIDTH:
        return one_line
    inner = INDENT * (depth + 1)
    if isinstance(value, dict):
        items = [f"{inner}{json.dumps(k, ensure_ascii=False)}: " + _format(v, depth + 1, f"{json.dumps(k, ensure_ascii=False)}: ")
                 for k, v in value.items()]
        return "{\n" + ",\n".join(items) + "\n" + INDENT * depth + "}"
    items = [inner + _format(v, depth + 1, "") for v in value]
    return "[\n" + ",\n".join(items) + "\n" + INDENT * depth + "]"


def format_json(data) -> str:
    """Il testo canonico di un file di dati."""
    return _format(data, 0, "") + "\n"


def files() -> list:
    return sorted(glob.glob(os.path.join(DATA, "*.json")))


def out_of_format() -> list:
    """I file di data/ il cui testo non è quello canonico."""
    bad = []
    for path in files():
        with open(path, encoding="utf-8") as f: text = f.read()
        if text != format_json(json.loads(text)): bad.append(os.path.basename(path))
    return bad


def main(argv) -> int:
    if "--check" in argv:
        bad = out_of_format()
        for name in bad: print(f"fuori formato: data/{name}")
        return 1 if bad else 0
    for path in files():
        with open(path, encoding="utf-8") as f: data = json.load(f)
        with open(path, "w", encoding="utf-8") as f: f.write(format_json(data))
    print(f"{len(files())} file riformattati")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
