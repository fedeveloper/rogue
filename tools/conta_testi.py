"""Quanta lore c'è nel gioco, blocco per blocco, e quanto manca all'obiettivo della v6 (almeno 10 volte la v5).

Uso, dalla radice del repository:
    python tools/conta_testi.py            # parole per blocco, confronto con la v5, doppioni e parole più usate
    python tools/conta_testi.py --check    # esce con 1 se due testi narrativi sono identici

Conta solo la narrativa che il giocatore legge (eventi, frasi delle stanze, lettere, personaggi, Bestiario, libri…),
non le descrizioni delle regole. Un blocco nuovo (per esempio i dialoghi del Campo) si aggiunge a BLOCKS insieme ai
dati che lo contengono. Le parole più usate servono a tenere vario il tono: se una parola compare troppo spesso
rispetto al resto, è il segnale per cercarne un'altra (vedi la guida di scrittura in STORY.md).
"""
import collections
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
TARGET_MULT = 10
# Le parole della v5, prima dell'espansione della lore (calcolate con questo stesso strumento)
BASELINE = {"eventi": 5166, "stanze": 1900, "lettere": 544, "personaggi": 583, "finali": 340, "bestiario": 1147,
            "fasi dei boss": 436, "biomi": 283, "libri": 346, "reliquie e oggetti": 999, "epitaffi e nemesi": 229,
            "dialoghi del Campo": 0, "atlante": 0,
            "discese dimenticate": 0, "vite prestate": 0, "voci dei boss": 0}
STOPWORDS = set("""il lo la i gli le un uno una di a da in con su per tra fra e o ma se che chi non ne ci si mi ti vi
è sono era ha ho hai del della dei degli delle al alla ai agli alle dal dalla nel nella nei negli nelle sul sulla
come più quando dove anche solo poi già ancora tutto tutti tua tuo tue tuoi sua suo sue suoi mia mio è ed d l un'
cosa questo questa quello quella c'è te me lui lei loro noi voi""".split())


def load(name: str):
    with open(os.path.join(DATA, name), encoding="utf-8") as f: return json.load(f)


def strings(value, keys=None):
    """Tutte le stringhe dentro `value`; con `keys`, solo quelle sotto una di quelle chiavi (a qualunque profondità)."""
    out = []
    def walk(v, key=None, inside=False):
        if isinstance(v, dict):
            for k, x in v.items(): walk(x, k, inside or keys is None or k in keys)
        elif isinstance(v, list):
            for x in v: walk(x, key, inside)
        elif isinstance(v, str) and (inside or keys is None) and len(v.split()) >= 3:
            out.append(v)
    walk(value)
    return out


def event_texts(events: dict) -> list:
    """Il racconto degli eventi: il testo di ogni scena e ciò che succede dopo una scelta (non le etichette delle
    scelte, che possono ripetersi da un evento all'altro come «Cerca le chiavi»)."""
    out = []
    for e in events.values():
        for scene in e["scenes"].values():
            out.append(scene["text"])
            out += [c[k] for c in scene["choices"] for k in ("msg", "fail_msg") if len(c.get(k, "").split()) >= 3]
    return out


def dialogue_texts(dialogues: dict) -> list:
    """Le conversazioni del Campo: saluti, battute degli argomenti e risposte alle scelte."""
    out = []
    for c in dialogues["characters"].values():
        out += [l["text"] for l in c.get("lines", [])]
        for t in c["topics"]:
            out += t["lines"] + [ch["reply"] for ch in t.get("choices", [])]
    return out


def blocks() -> dict:
    """I testi narrativi, per blocco."""
    story, enemies = load("story.json"), load("enemies.json")
    return {
        "eventi": event_texts(load("events.json")),
        "stanze": [t for k, v in load("lore.json").items() if k != "letters" for t in v]
                  + [t for rooms in load("atmosfere.json")["biomes"].values() for v in rooms.values() for t in v],
        "lettere": list(load("lore.json")["letters"]),
        "personaggi": strings(story["characters"], {"hint", "text"}) + strings(story["camp"]["characters"], {"text"}),
        "finali": strings(story["endings"], {"text", "choice"}) + [t for e in load("epiloghi.json")["endings"].values() for t in e.values()],
        "bestiario": strings(enemies, {"lore", "title"}) + [v for e in load("bestiario.json")["creatures"].values() for v in e.values()],
        "fasi dei boss": strings(load("phases.json"), {"text"}),
        "biomi": strings(load("biomes.json"), {"intro"}),
        "libri": strings(load("books.json"), {"text"}),
        "reliquie e oggetti": strings(load("relics.json"), {"lore"}) + strings(load("weapons.json"), {"flavor"})
                              + strings(load("armors.json"), {"flavor"}) + strings(load("accessories.json"), {"lore"})
                              + [t for group in load("armeria.json").values() for t in group.values()],
        "epitaffi e nemesi": strings(load("epitaph.json")) + strings(load("nemesis.json"), {"born", "returns", "defeated", "boss_grudge"}),
        "dialoghi del Campo": dialogue_texts(load("dialogues.json")),
        "atlante": [p["text"] for pages in load("atlante.json")["biomes"].values() for p in pages],
        "discese dimenticate": [x for t in load("lettere.json")["threads"] for x in t["letters"] + [t["epilogue"]]],
        "vite prestate": [m["text"] for c in load("vite.json")["classes"].values() for m in c["memories"]],
        "voci dei boss": [t for b in load("voci_boss.json")["bosses"].values() for lines in b.values() for t in lines],
    }


def words(text: str) -> int:
    return len(text.split())


def duplicates(by_block: dict) -> list:
    seen, out = {}, []
    for block, items in by_block.items():
        for t in items:
            if t in seen: out.append((seen[t], block, t))
            else: seen[t] = block
    return out


def frequent(by_block: dict, n: int = 25) -> list:
    """Le parole più usate (senza le parole vuote), con quante volte compaiono ogni 10.000 parole."""
    counts, total = collections.Counter(), 0
    for items in by_block.values():
        for t in items:
            tokens = [w.lower() for w in re.findall(r"[A-Za-zÀ-ÿ']+", t)]
            total += len(tokens)
            counts.update(w.strip("'") for w in tokens if w.strip("'") not in STOPWORDS and len(w) > 2)
    return [(w, c, round(c * 10000 / max(1, total))) for w, c in counts.most_common(n)]


def report() -> str:
    by_block = blocks()
    lines, total, base = ["Blocco                 parole    v5   ×"], 0, 0
    for name, items in by_block.items():
        n, b = sum(map(words, items)), BASELINE.get(name, 0)
        total, base = total + n, base + b
        lines.append(f"{name:20} {n:8} {b:5} " + (f"{n / b:4.1f}" if b else "nuovo"))
    lines.append(f"{'TOTALE':20} {total:8} {base:5} {total / base:4.1f}   obiettivo {base * TARGET_MULT} (×{TARGET_MULT})")
    dups = duplicates(by_block)
    lines.append(f"\nTesti identici: {len(dups)}")
    lines += [f"  [{a} / {b}] {t[:90]}" for a, b, t in dups[:20]]
    lines.append("\nParole più usate (volte, ogni 10.000 parole):")
    lines.append("  " + ", ".join(f"{w} {c} ({r})" for w, c, r in frequent(by_block)))
    return "\n".join(lines)


def main(argv) -> int:
    if "--check" in argv:
        dups = duplicates(blocks())
        for a, b, t in dups: print(f"testo ripetuto [{a} / {b}]: {t}")
        return 1 if dups else 0
    print(report())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
