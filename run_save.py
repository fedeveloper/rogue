"""Il salvataggio a metà discesa: «Salva ed esci» sulla mappa scrive `run_save.json`, «Riprendi la discesa» lo rilegge.

Il file contiene tutto ciò che serve per ripartire dallo stesso punto della mappa: l'eroe con oggetti, reliquie e
incantesimi, la mappa del piano e la strada fatta, le regole della modalità, il seme del Ciclo e lo stato del
generatore casuale. Ripresa, la discesa continua esattamente come sarebbe continuata senza fermarsi
(`tests/test_run_save.py`). Il file si cancella appena caricato e quando la discesa finisce: non si può ricaricare per
ritentare una stanza.

Il formato è JSON. Gli oggetti del gioco (eroe, nemici, oggetti, reliquie) si scrivono come `{"__object__":
"modulo.Classe", "state": {...}}` e si ricostruiscono solo se la classe è di un modulo in OBJECT_MODULES; tuple, insiemi
e dizionari con chiavi non di testo hanno un'etichetta loro. Un salvataggio con un `version` diverso da SAVE_VERSION non
si carica: si cambia SAVE_VERSION quando cambiano gli attributi degli oggetti salvati (il test lo ricorda).
"""
import importlib
import json
import os
import random
from typing import Optional

import modes
from data_manager import BASE_DIR, CYCLE, set_cycle_seed

SAVE_FILE = os.path.join(BASE_DIR, "run_save.json")
SAVE_VERSION = 1
OBJECT_MODULES = ("entities", "relic_effects")


class SaveError(Exception):
    """Un salvataggio che non si può caricare: illeggibile, di un'altra versione o con oggetti sconosciuti."""


def encode(value):
    if value is None or isinstance(value, (bool, int, float, str)): return value
    if isinstance(value, list): return [encode(v) for v in value]
    if isinstance(value, tuple): return {"__tuple__": [encode(v) for v in value]}
    if isinstance(value, (set, frozenset)): return {"__set__": [encode(v) for v in sorted(value, key=repr)]}
    if isinstance(value, dict):
        if all(isinstance(k, str) and not k.startswith("__") for k in value): return {k: encode(v) for k, v in value.items()}
        return {"__dict__": [[encode(k), encode(v)] for k, v in value.items()]}
    cls = type(value)
    if cls.__module__ in OBJECT_MODULES: return {"__object__": f"{cls.__module__}.{cls.__qualname__}", "state": encode(vars(value))}
    raise TypeError(f"il salvataggio non sa scrivere {cls.__module__}.{cls.__qualname__}")


def decode(value):
    if isinstance(value, list): return [decode(v) for v in value]
    if not isinstance(value, dict): return value
    if "__tuple__" in value: return tuple(decode(v) for v in value["__tuple__"])
    if "__set__" in value: return {decode(v) for v in value["__set__"]}
    if "__dict__" in value: return {decode(k): decode(v) for k, v in value["__dict__"]}
    if "__object__" in value:
        module, _, name = value["__object__"].rpartition(".")
        cls = getattr(importlib.import_module(module), name, None) if module in OBJECT_MODULES else None
        if not isinstance(cls, type): raise SaveError(f"oggetto sconosciuto nel salvataggio: {value['__object__']}")
        obj = cls.__new__(cls)
        vars(obj).update(decode(value["state"]))
        return obj
    return {k: decode(v) for k, v in value.items()}


def snapshot(run: dict) -> dict:
    """Lo stato da scrivere: la discesa (`run`, da `roguelike._descent`) più regole, Ciclo e generatore casuale."""
    return {"version": SAVE_VERSION, "run": run, "rules": dict(modes.RUN), "cycle_seed": CYCLE["seed"], "random": random.getstate()}


def restore(state: dict) -> dict:
    """Rimette regole, Ciclo e generatore casuale come al salvataggio e restituisce la discesa."""
    modes.start_run(state["rules"])
    set_cycle_seed(state["cycle_seed"])
    random.setstate(state["random"])
    return state["run"]


def exists() -> bool:
    return os.path.exists(SAVE_FILE)


def save(run: dict):
    """Scrive il salvataggio in modo atomico, come il profilo."""
    text = json.dumps(encode(snapshot(run)), ensure_ascii=False)
    tmp = SAVE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: f.write(text)
    os.replace(tmp, SAVE_FILE)


def peek() -> Optional[dict]:
    """Ciò che il menu principale mostra della discesa salvata (eroe e piano), senza caricarla; None se non si legge."""
    try:
        with open(SAVE_FILE, encoding="utf-8") as f: state = json.load(f)
        if state.get("version") != SAVE_VERSION: return None
        run = state["run"]
        return {"role": run["player"]["state"]["role"], "floor": run["floor"]}
    except (OSError, ValueError, KeyError, TypeError):
        return None


def load() -> dict:
    """Legge e cancella il salvataggio, poi rimette lo stato della discesa. SaveError se non si può caricare
    (il file viene cancellato comunque: un salvataggio rotto non deve bloccare il menu)."""
    try:
        with open(SAVE_FILE, encoding="utf-8") as f: raw = json.load(f)
    except (OSError, ValueError) as e:
        discard()
        raise SaveError(f"salvataggio illeggibile ({e})")
    discard()
    if not isinstance(raw, dict) or raw.get("version") != SAVE_VERSION:
        raise SaveError("salvataggio di un'altra versione del gioco")
    try:
        return restore(decode(raw))
    except (KeyError, TypeError, ValueError, AttributeError) as e:
        raise SaveError(f"salvataggio incompleto ({e})")


def discard():
    if os.path.exists(SAVE_FILE): os.remove(SAVE_FILE)
