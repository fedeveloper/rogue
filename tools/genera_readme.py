"""Genera README.md: il testo è scritto a mano, le tabelle e i numeri vengono dai file in data/.

Uso, dalla radice del repository:  python tools/genera_readme.py
tests/test_docs.py fallisce se README.md non è quello che questo script genera dai dati attuali.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = lambda f: json.load(open(f"{ROOT}/data/{f}.json", encoding="utf-8"))
weapons, armors, accs = d("weapons")["weapons"], d("armors")["armors"], d("accessories")["accessories"]
cons, relics, enemies, events = d("consumables")["consumables"], d("relics")["relics"], d("enemies"), d("events")
meta, classes, elements, books = d("meta"), d("classes"), d("elements"), d("books")["books"]
modes, phases, runes_data = d("modes"), d("phases")["bosses"], d("runes")
grades, daily = modes["ascension"]["grades"], modes["daily"]
icon = elements["icons"]

def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)

# --- da dove arriva ogni sblocco ---
source = {}
for f in meta["feats"].values():
    if f["reward_type"] == "unlock": source[f["reward_id"]] = f"Impresa «{f['name']}»"
for c in classes.values():
    for lvl, m in c["mastery"].items():
        if m.get("type") == "unlock": source.setdefault(m["id"], f"Maestria {c['role']} Lv.{lvl}")
source["lama_creatore"] = "Vittoria al piano 30"
def how(x, base="Disponibile da subito"):
    if not x.get("unlock_id"): return base
    if x.get("unlock_cost"): return f"Forgia (✨{x['unlock_cost']})"
    return source.get(x["unlock_id"], "Imprese")

class_unlock = {"1": "Iniziale", "2": "Iniziale", "3": "Iniziale"}
for c in classes.values():
    for lvl, m in c["mastery"].items():
        if m.get("type") == "class" and m.get("id") not in (None, "null"): class_unlock[m["id"]] = f"Maestria {c['role']} Lv.{lvl}"
for f in meta["feats"].values():
    if f["reward_type"] == "class": class_unlock[f["reward_id"]] = f"Impresa «{f['name']}»"
style = {"1": "Tank bilanciato, contrattacca quando si difende", "2": "Agile e ricco, critico garantito dopo la Concentrazione",
         "3": "Arma di Fuoco potente e mira eccellente, ma fragile; si cura difendendosi", "4": "Ultra-tank con Risonanza di Luce; difendendosi si purifica",
         "5": "Glass cannon: l'ascia più forte, nessuna armatura", "6": "Due pozioni iniziali e bombe di Fuoco; difendendosi prepara le reazioni",
         "7": "Critico innato e schivata alta, ma fragile", "8": "Risonanza di Tenebra; difendendosi ruba vita",
         "9": "Maestro delle reazioni: Etere abbondante, incantesimi di Vento e Acqua su una verga di Terra"}
emoji = {"1": "⚔️", "2": "🗡️", "3": "🔮", "4": "🛡️", "5": "🪓", "6": "🧪", "7": "🥷", "8": "💀", "9": "🌈"}
classes_table = table(["Classe", "HP", "Stile", "Maestria Lv.2", "Sblocco"],
    [(f"{emoji[k]} **{c['role']}**", c["max_hp"], style[k], c["mastery"]["2"]["desc"].split(":")[0], class_unlock.get(k, "—")) for k, c in classes.items()])

trait_unlock = {"none": "Iniziale", "deaths_10": "10 morti", "gold_5000": "5.000 Oro raccolti in totale", "benedetto": "Maestria Paladino Lv.5"}
trait_unlock.update({fid: f"Impresa «{f['name']}»" for fid, f in meta["feats"].items()})
traits_table = table(["Tratto", "Effetto", "Sblocco"], [(f"**{t['name']}**", t["desc"], trait_unlock.get(t["unlock_req"], t["unlock_req"])) for t in meta["traits"].values()])
it = lambda x: f"{round(x, 2):g}".replace(".", ",")
grades_table = table(["Grado", "Nome", "Regola che si aggiunge", "Essenza"],
    [(i, f"**{g['name']}**", g["desc"], f"×{it(1 + sum(x['essence_bonus'] for x in grades[:i]))}") for i, g in enumerate(grades, 1)])
boons_table = table(["Dono", "Effetto"], [(f"**{b['name']}**", b["desc"]) for b in daily["boons"]])
start_combos = 2 * len(classes) * len(meta["traits"]) * (len(grades) + 1)

res_names = {"Fuoco": "Ustione", "Acqua": "Flusso", "Terra": "Fortezza", "Vento": "Raffica", "Luce": "Benedizione", "Tenebra": "Ombra"}
res_table = table(["Elemento", "Risonanza", "Effetto"], [(f"{icon[e]} {e}", res_names[e], v["desc"]) for e, v in elements["resonance"].items()])
beats = [f"{icon[a]} **{a}** batte {icon[b]} **{b}**" for a, row in elements["multipliers"].items() for b, m in row.items() if m > 1 and a not in ("Luce", "Tenebra")]

relic_table = table(["Reliquia", "Effetto", "Come ottenerla"], [(f"**{r['name']}**", r["desc"], how(r, "Boss, forzieri, eventi")) for r in relics])
acc_table = table(["Monile", "Effetto", "Come ottenerlo"], [(f"**{a['name']}**", a["desc"].rstrip("."), how(a)) for a in accs])
reward = {"perk": "Potenziamento", "unlock": "Sblocco", "class": "Classe", "trait": "Tratto", "essence": "Essenza"}
names = {x.get("unlock_id"): x["name"] for x in weapons + armors + accs + cons + relics if x.get("unlock_id")}
names.update({k: c["role"] for k, c in classes.items()}); names.update({k: t["name"] for k, t in meta["traits"].items()}); names["scarpisti"] = "Scarpisti (+20% Fuga)"
feats_table = table(["Impresa", "Obiettivo", "Ricompensa"],
    [(f"**{f['name']}**", f["desc"], f"{reward[f['reward_type']]}: {names.get(f['reward_id'], f['reward_id'])}") for f in meta["feats"].values()])
def special(w):
    return w.get("desc") or "—"
attr_names = {k: f"{a['icon']} {a['name']}" for k, a in d('attributes')['attributes'].items()}
weapons_table = table(["Arma", "ATK base", "Elemento", "Scala con", "Caratteristiche", "Come ottenerla"],
    [(f"**{w['name']}**", w["base_atk"], f"{icon[w['element']]} {w['element']}" if w.get("element") else "Casuale", attr_names[w["scaling"]], special(w), how(w)) for w in weapons])
armors_table = table(["Armatura", "DEF base", "Caratteristiche", "Come ottenerla"],
    [(f"**{a['name']}**", a["base_def"], a.get("desc") or "—", how(a)) for a in armors])
cons_table = table(["Consumabile", "Effetto", "Come ottenerlo"],
    [(f"**{c['name']}**", c.get("desc") or f"Cura {c['base_heal']} HP (di più ai piani profondi)", how(c)) for c in cons])

slot_names = {"weapon": "Arma", "armor": "Armatura", "any": "Arma o armatura"}
words_table = table(["Parola", "Rune", "Effetto in più"], [(f"**«{w['name']}»**", " + ".join(runes_data["runes"][r]["name"] for r in w["runes"]), w["desc"]) for w in runes_data["words"].values()])
runes_table = table(["Runa", "Famiglia", "Dove", "Effetto"], [(f"{r['icon']} **{r['name']}**", r["family"], slot_names[r["slot"]], r["desc"]) for r in runes_data["runes"].values()])
count = lambda xs: f"{len(xs)} ({sum(1 for x in xs if not x.get('unlock_id'))} subito, {sum(1 for x in xs if x.get('unlock_id'))} da sbloccare)"
numbers = table(["Contenuto", "Quantità"], [
    ("Classi giocabili", len(classes)), ("Tratti di partenza", len(meta["traits"])), ("Gradi di Ascensione", len(grades)), ("Doni della Sfida del Giorno", len(daily["boons"])),
    ("Armi", count(weapons)), ("Armature", count(armors)), ("Monili", count(accs)), ("Consumabili", count(cons)), ("Reliquie", count(relics)),
    ("Nemici comuni", len(enemies["enemies"])), ("Boss", len(enemies["bosses"])), ("Fasi dei boss", sum(len(p) for p in phases.values())), ("Rune / parole runiche", f"{len(runes_data['runes'])} / {len(runes_data['words'])}"), ("Eventi narrativi", len(events)),
    ("Imprese", len(meta["feats"])), ("Tomi dell'Archivio", len(books)), ("Potenziamenti permanenti", 14),
    ("Elementi / Risonanze", f"{len(elements['list'])} / {len(elements['resonance'])}"),
    ("Combinazioni di partenza (modalità × classe × tratto × grado)", start_combos)])
events_list = ", ".join(f"*{e['title']}*" for e in events.values() if not e.get('scripted'))
scenes = sum(len(e['scenes']) for e in events.values())


# --- la landing page: numeri, schermate vere disegnate con ui.py, biomi ---
import re, sys
sys.path[:0] = [ROOT, os.path.join(ROOT, "tools")]
import conta_testi, ui
plain = lambda text: re.sub(r"\x1b\[[0-9;]*m", "", text)
pyproject = open(f"{ROOT}/pyproject.toml", encoding="utf-8").read()
version = re.search(r'^version = "([^"]+)"', pyproject, re.M).group(1).replace("-", "--")
biomes_data, story, portraits = d("biomes")["biomes"], d("story"), d("ritratti")
floors, biomes = biomes_data[-1]["floors"][1], len(biomes_data)
classes_n, traits_n, grades_n, combos = len(classes), len(meta["traits"]), len(grades), f"{start_combos:,}".replace(",", ".")
lore_words = f"{sum(conta_testi.words(t) for items in conta_testi.blocks().values() for t in items) // 1000 * 1000:,}".replace(",", ".")
topics_n = sum(len(c["topics"]) for c in d("dialogues")["characters"].values())
books_n, events_n, endings_n = len(books), len(events), len(story["endings"])

def trim(lines):
    margin = min((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
    return [l[margin:] for l in lines]

first = biomes_data[0]
boss_name = next(n for n, b in enemies["bosses"].items() if b.get("biome") == first["id"])
boss = enemies["bosses"][boss_name]
boss_screen = "\n".join(plain(l) for l in ui.panel(trim(portraits["bosses"][boss_name]), boss["title"].upper()))
boss_screen += f'\n"{boss["lore"]}"'
goblin = enemies["enemies"]["Goblin"]
hero_hp, enemy_hp = 96, goblin["base_hp"]
names = max(ui.visible_width("Tu"), ui.visible_width("Goblin"))
combat_screen = "\n".join([
    "   " + l for l in trim(portraits["sagome"][portraits["enemies"]["Goblin"]])] + [
    "",
    "--- ⚔️ IN COMBATTIMENTO ⚔️ ---",
    plain(f"{ui.pad('Tu', names)}  {ui.bar(hero_hp, 120)} {hero_hp}/120 HP"),
    plain(f"{ui.pad('Goblin', names)}  {ui.bar(enemy_hp // 2, enemy_hp)} {enemy_hp // 2}/{enemy_hp} HP"),
    "Intento del nemico: 💢 Colpo pesante — difenditi!",
    "",
    "  > Attacca",
    "    Difesa Aggressiva (Dimezza danni e Contrattacca)",
    "    Apri Inventario (Usa oggetto = Costa Turno)",
    "    Statistiche Eroe",
    "    Tenta la Fuga"])
second = biomes_data[1]
biome_screen = "\n".join(plain(l) for l in ui.panel(trim(portraits["biomes"][second["id"]]), f"{second['icon']}  {second['name'].upper()}"))
biome_screen += f"\nPericolo: {second['hazard']['name']}. {second['hazard']['desc']}"
biomes_table = table(["", "Bioma", "Piani", "Il pericolo"],
    [(b["icon"], f"**{b['name']}**", f"{b['floors'][0]}-{b['floors'][1]}", f"*{b['hazard']['name']}*") for b in biomes_data])

README = f"""<a id="top"></a>

<div align="center">

<img src="docs/banner.png" alt="Il Ritornante inginocchiato accanto al Fuoco del Campo, davanti al Labirinto che sprofonda; in cielo il Dio Antico dorme e sogna" width="100%">

# 🌀 Il Labirinto degli Elementi e del Caos

### Scendi. Muori. Ricorda. Scendi ancora.

**Un gioco di ruolo roguelite da terminale, in italiano, gratuito e open source.**<br>
Ogni discesa è diversa, ogni morte ti rende più forte e un mondo intero aspetta di essere ricordato.

<br>

[![Test](https://github.com/fedeveloper/rogue/actions/workflows/tests.yml/badge.svg)](https://github.com/fedeveloper/rogue/actions/workflows/tests.yml)
[![Licenza MIT](https://img.shields.io/badge/Licenza-MIT-yellow.svg)](LICENSE)
![Versione](https://img.shields.io/badge/versione-{version}-blueviolet)
![Lingua](https://img.shields.io/badge/lingua-italiano-009246)
![Gratis](https://img.shields.io/badge/prezzo-gratis-brightgreen)

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Libreria standard](https://img.shields.io/badge/solo-libreria_standard-3776AB?logo=python&logoColor=white)
![Dipendenze](https://img.shields.io/badge/dipendenze-0-brightgreen)
![Terminale](https://img.shields.io/badge/interfaccia-terminale-333333?logo=windowsterminal&logoColor=white)
![Dati JSON](https://img.shields.io/badge/contenuti-JSON-000000?logo=json&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?logo=githubactions&logoColor=white)

![Windows](https://img.shields.io/badge/Windows-0078D6?logo=windows&logoColor=white)
![macOS](https://img.shields.io/badge/macOS-000000?logo=apple&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?logo=linux&logoColor=black)

<br>

**[⬇️ Installazione](#installazione)** · **[🎮 Come si gioca](#come-si-gioca)** · **[🌍 Il mondo](#il-mondo)** · **[✨ Caratteristiche](#caratteristiche)** · **[❓ Domande](#domande)** · **[📜 Licenza](#licenza)**

</div>

---

## 🌀 Che cos'è

*Il Labirinto degli Elementi e del Caos* è un **gioco di ruolo a turni** che si gioca nella finestra del terminale, con la tastiera. Non serve una scheda grafica, non serve un account, non si compra niente: scarichi una cartella, scrivi un comando e sei dentro.

Interpreti **il Ritornante**, qualcuno che si sveglia accanto a un fuoco che non brucia senza ricordare il proprio nome. Sotto di te si apre un Labirinto che ha inghiottito un intero mondo, Aethelgard: **{floors} piani**, **{biomes} biomi**, mostri, trappole, mercanti ed eventi che ti chiedono di scegliere. In fondo dorme il **DIO ANTICO**.

È un **roguelite**: ogni discesa è generata da capo e, quando muori, ricominci dall'inizio. Ma non a mani vuote. L'**Essenza** che riporti al Campo sblocca nuovi eroi, armi, reliquie e potenziamenti, e chi hai incontrato laggiù viene a sedersi al tuo fuoco per raccontarti chi era. Ogni discesa ti porta un po' più a fondo, nel Labirinto e nella sua storia.

<table>
<tr>
<td width="33%" valign="top">

### 🎲 Mai uguale
Mappa, nemici, bottino ed eventi cambiano a ogni discesa. {classes_n} eroi, {traits_n} tratti e {grades_n} gradi di Ascensione fanno **{combos} partenze diverse**.

</td>
<td width="33%" valign="top">

### 💀 La morte insegna
Morire fa parte del gioco. L'Essenza che riporti al Campo diventa **potenziamenti permanenti**, e chi ti ha ucciso torna a cercarti come **Nemesi**.

</td>
<td width="33%" valign="top">

### 📖 Un mondo da leggere
**Oltre {lore_words} parole** di storia: {topics_n} conversazioni al Campo, {books_n} libri da sbloccare, {events_n} eventi a scene e {endings_n} finali.

</td>
</tr>
</table>

## 👀 Uno sguardo

Il gioco è fatto di testo, colori e disegni in caratteri. Questo è l'arrivo davanti al primo boss, così come appare nel terminale:

```text
{boss_screen}
```

E questo è un turno di combattimento: il nemico **annuncia la sua prossima mossa**, e tu scegli se attaccare, difenderti, lanciare un incantesimo o fuggire.

```text
{combat_screen}
```

Ogni bioma ha il suo paesaggio, le sue regole e i suoi abitanti:

```text
{biome_screen}
```

<a id="installazione"></a>

## ⬇️ Installazione

Il gioco funziona su **Windows, macOS e Linux** e ha bisogno di una cosa sola: **Python 3.9 o più recente**. Non c'è niente altro da installare.

### 1. Installa Python

<details>
<summary><b>🪟 Windows</b></summary>

1. Vai su [python.org/downloads](https://www.python.org/downloads/) e scarica l'ultima versione (oppure installa *Python* dal **Microsoft Store**).
2. Avvia l'installer e **spunta la casella «Add python.exe to PATH»** prima di premere *Install Now*.
3. Per controllare: apri il menu Start, cerca **Terminale** (o *Prompt dei comandi*) e scrivi `py --version`. Deve comparire `Python 3.` seguito da un numero.

</details>

<details>
<summary><b>🍎 macOS</b></summary>

1. Vai su [python.org/downloads](https://www.python.org/downloads/) e scarica l'installer per macOS (oppure, se usi Homebrew, `brew install python`).
2. Apri l'app **Terminale** (la trovi con Spotlight, ⌘ + Spazio) e scrivi `python3 --version` per controllare.

</details>

<details>
<summary><b>🐧 Linux</b></summary>

Quasi tutte le distribuzioni hanno già Python 3. Controlla con `python3 --version`; se manca, installalo dal gestore di pacchetti (per esempio `sudo apt install python3` su Debian e Ubuntu).

</details>

### 2. Scarica il gioco

**Senza Git (più semplice):** premi il pulsante verde **Code** in alto in questa pagina e scegli **Download ZIP**, oppure [scarica lo ZIP direttamente](https://github.com/fedeveloper/rogue/archive/refs/heads/main.zip). Poi estrai la cartella dove preferisci.

**Con Git:**

```bash
git clone https://github.com/fedeveloper/rogue.git
```

### 3. Avvia

Apri il terminale **nella cartella del gioco** e lancia `roguelike.py`:

| Sistema | Comando |
|---|---|
| 🪟 Windows | `py roguelike.py` |
| 🍎 macOS | `python3 roguelike.py` |
| 🐧 Linux | `python3 roguelike.py` |

> 💡 **Come si apre il terminale nella cartella giusta.** Su Windows: apri la cartella in Esplora file, clicca col tasto destro su uno spazio vuoto e scegli *Apri nel Terminale*. Su macOS: trascina la cartella sull'icona di Terminale, oppure scrivi `cd ` e trascina la cartella nella finestra. Su Linux: tasto destro → *Apri in un terminale*.

### Per giocare al meglio

- **Una finestra ampia.** Allarga il terminale ad almeno **100 colonne e 30 righe**: la mappa del piano usa lo spazio in più per disegnare i collegamenti fra le stanze.
- **Un terminale moderno.** Su Windows usa **Windows Terminal** (è già installato su Windows 11): colori ed emoji si vedono bene. Se nel vecchio *Prompt dei comandi* le emoji appaiono come quadratini, scrivi prima `chcp 65001`.
- **Aggiornare.** Con Git: `git pull` nella cartella del gioco. Con lo ZIP: scarica la versione nuova e copiaci dentro il tuo `profile.json`, così i progressi restano.
- **Disinstallare.** Basta cancellare la cartella: il gioco non scrive niente altrove.

<a id="come-si-gioca"></a>

## 🎮 Come si gioca

### I comandi

Si gioca **solo con la tastiera**:

| Tasto | Cosa fa |
|---|---|
| ⬆️ ⬇️ | Scorri le voci dei menu |
| **Invio** | Conferma la scelta, prosegui nel racconto |
| **«Indietro»** | Non è un tasto ma l'ultima voce di molti menu: riporta alla schermata precedente |
| **Ctrl + C** | Esci dal gioco in qualunque momento |

### La prima discesa

1. **Scegli un eroe.** All'inizio puoi essere **Guerriero**, **Ladro** o **Mago**; gli altri si sbloccano giocando. Per cominciare, il Guerriero è robusto e semplice da usare.
2. **Scegli il percorso.** Ogni piano è una mappa di stanze collegate: combattimenti, mercanti, falò, forzieri, trappole ed eventi. Vedi tutto fin dall'arrivo: decidi tu quanto rischiare.
3. **Combatti leggendo il nemico.** Prima di ogni tuo turno il nemico dice cosa sta per fare. Se prepara un colpo pesante, difenditi; se si chiude in guardia, è il momento di caricare.
4. **Cresci.** A ogni livello metti un punto in un attributo; ogni cinque livelli scegli un talento. Equipaggia le armi che trovi e incastona le rune al falò.
5. **Affronta il boss** in fondo al piano e scendi. Ogni cinque piani cambia il bioma, con nuove regole e nuovi nemici.
6. **Quando cadi**, torni al **Campo Base** con l'Essenza raccolta: spendila nei potenziamenti, parla con chi siede al fuoco, leggi ciò che hai scoperto nel **Codice** e nell'**Archivio**. Poi riparti.

> 💾 **Il salvataggio è automatico.** I progressi stanno in `profile.json`, che si crea da solo al primo avvio. A metà discesa puoi scegliere **Salva ed esci** e riprendere più tardi dallo stesso punto.

Le regole complete, con strategie e consigli, sono nel [**📖 Manuale del Giocatore**](MANUALE_GIOCATORE.md).

<a id="il-mondo"></a>

## 🌍 Il mondo di Aethelgard

Mille anni fa, in una notte sola, il cielo si strappò. Gli elementi che gli Architetti avevano tenuto insieme si separarono, le città sprofondarono e il mondo intero scese in un Labirinto che da allora non smette di cambiare forma. Tu sei l'unico che, morendo laggiù, torna indietro. Nessuno sa perché. Forse nemmeno il Fuoco che ti riporta.

Il Labirinto è fatto di quello che c'era prima: l'Accademia di Aurelia è diventata un chiostro di silenzio, le miniere dei nani scavano ancora verso il basso, il Mare Interno è un ventre che digerisce i ricordi.

{biomes_table}

Chi incontri nel Labirinto ha una storia, e se lo salvi viene a raccontartela al Campo: un astronomo che cerca la sorella, una cartografa che finisce la mappa del nonno, un vecchio speziale che non si perdona, un paladino che custodisce da mille anni una porta che non porta più da nessuna parte. **Più scendi, più ricordi.** Il resto lo scopri giocando.

<a id="caratteristiche"></a>

## ✨ Caratteristiche


- 🗺️ **Una mappa per ogni piano.** Quattro file di stanze collegate (combattimento, Élite, mercante, falò, forziere, trappola, evento o la *Stanza del Mistero*) e il boss in fondo, tutte visibili fin dall'arrivo: scegli il percorso, non solo la porta. Ogni stanza ha un prezzo e un premio: le trappole custodiscono un bottino, i forzieri profondi possono essere Mimic, e l'**Audacia** fa crescere il bottino del boss per ogni rischio corso nel piano. Nemici e boss crescono con la profondità, e quasi ogni nemico ha uno **stile** (Bruto, Predatore, Difensore, Succhiavita, Infetto, Mistico, Furia) che decide le mosse che preferisce.
- 🌍 **Sei biomi, sei regole.** Ogni cinque piani il Labirinto cambia volto e legge: la *Nostalgia Letale* dei Chiostri, il *Gas del Silenzio* delle Miniere, la *Caduta Astrale* delle Guglie, la *Dissoluzione dell'Io* del Ventre, l'*Ebollizione Astrale* della Forgia e il *Paradosso Temporale* della Soglia. Ogni bioma ha sei nemici nativi, un boss tutto suo e le sue stanze speciali.
- 🔥 **Combattimento tattico.** Il nemico **annuncia la sua mossa**, colpo pesante, guardia, rigenerazione o colpo infetto, e tu decidi se attaccare o difenderti. Sette elementi, vantaggi e svantaggi, **Risonanze** quando arma e armatura condividono l'elemento e **{len(d('elements')['reactions'])} reazioni** (Vapore, Gelo, Eclissi…) quando li combini.
- 🧬 **{len(classes)} classi** con alberi di Maestria a 5 livelli che sbloccano bonus, oggetti, reliquie e altre classi.
- 🔮 **La magia.** {len(d('spells')['spells'])} incantesimi che costano **Etere**, una risorsa che resta fra uno scontro e l'altro e si guadagna colpendo, difendendosi e scatenando reazioni. Lasciano il marchio del loro elemento: con l'arma di Fuoco e *Lama d'Acqua* componi il *Vapore* senza cambiare equipaggiamento.
- 📈 **Sei attributi da costruire.** A ogni livello un punto fra {', '.join(a['name'] for a in d('attributes')['attributes'].values())}: ogni discesa è una build diversa, e il raro *Tomo dell'Oblio* permette di ripensarla al Falò.
- 🌟 **Talenti.** Ogni {d('talents')['rules']['every']} livelli scegli uno dei {len(d('talents')['talents'])} talenti fra {d('talents')['rules']['offered']} proposti a caso: danni, difesa, Etere, cure, fortuna.
- 🎭 **{len(meta['traits'])} tratti** e **{len(grades)} gradi di Ascensione**: {f'{start_combos:,}'.replace(',', '.')} combinazioni di partenza diverse.
- 📅 **Sfida del Giorno.** Una discesa al giorno uguale per tutti: eroe, tratto, malus e dono assegnati, la stessa mappa a ogni piano. Conta il primo tentativo; punteggio, serie di giorni e record restano nel profilo.
- 📖 **Eventi che ricordano.** {len(events)} storie a scene con opzioni che esistono solo per la tua classe, il tuo tratto o le tue reliquie: `[Mago]`, `[Tocco di Mida]`, `[Chiave Arrugginita]`. Il Labirinto ricorda chi hai aiutato e chi hai derubato, e certe scelte tornano a bussare qualche piano dopo.
- 🗝️ **Personaggi che ritornano.** *Sir Alaric*, il Primo Paladino, *Silas*, il Cercatore, la Fata della Fontana, il fabbro muto e il Mercante Senza Volto hanno storie in più capitoli che proseguono di run in run. Le tue scelte decidono come finiscono, e se liberi Alaric il Cavaliere Oscuro non tornerà più.
- 🔷 **Rune e Incastoni.** {len(runes_data['runes'])} rune da incastonare al Falò in armi e armature: allungano i marchi, potenziano le reazioni, fanno sanguinare, rubano vita, riflettono i colpi. Restano sull'oggetto finché non le estrai, quindi ogni cambio d'arma è una scelta. Le combinazioni giuste formano {len(runes_data['words'])} **parole runiche** da scoprire.
- 👑 **Boss che cambiano.** A metà della vita ogni boss entra in una nuova fase con un nome, mosse nuove e regole proprie: il Re dei Goblin chiama le guardie, il Drago di Zaffiro si copre di Scaglie che solo una reazione elementale infrange, la Badessa ti sigilla la difesa. Il DIO ANTICO ha tre fasi, e nella seconda diventa l'elemento che ti ferisce di più. Ogni bioma ha il suo boss nativo, dalla Badessa dei Chiostri al Custode della Soglia.
- 😈 **La Nemesi.** Il nemico che ti uccide se ne ricorda: prende un nome, un rango e il tuo Oro, impara qualcosa da te e torna a cercarti vicino al piano della tua morte. Sconfiggilo e ti riprendi tutto, con un trofeo.
- 🪦 **Un epitaffio per ogni discesa.** A fine partita poche frasi raccontano chi eri, cosa hai attraversato e chi ti ha ucciso; il Cimitero del Codice conserva le ultime cinquanta.
- 🩸 **Corruzione.** Le scelte oscure danno potere e opzioni proibite, ma il Labirinto comincia a nasconderti le cose: gli effetti delle scelte, le mosse dei nemici.
- 🏁 **{len(d('story')['endings'])} finali.** Uccidere il Dio, prenderne il posto, risvegliare Aethelgard… e un finale segreto per chi legge davvero il Labirinto.
- 🔥 **Un campo che ricorda.** Chi salvi nel Labirinto viene a scaldarsi al tuo fuoco, ti parla di ciò che hai fatto e ti aiuta a costruire.
- 📚 **Una storia da leggere con calma.** In discesa il testo è breve; la storia vera si legge fuori: {topics_n} conversazioni al Campo, {books_n} libri nell'Archivio, l'*Atlante* dei biomi, le *Vite prestate* degli eroi, l'*Armeria* con la storia di ogni oggetto, le lettere delle discese dimenticate. Si sblocca un pezzo alla volta, man mano che scendi.
- 🎨 **Grafica nel terminale.** Ogni boss ha il suo ritratto, ogni nemico la sagoma della sua famiglia, ogni bioma il suo paesaggio; HP ed Etere hanno le loro barre.
- 🌟 **{len(relics)} reliquie** che piegano le regole: danni raddoppiati, scudi, vampirismo, oro moltiplicato.
- 🏕️ **Meta-progressione profonda**: potenziamenti permanenti, una Forgia per sbloccare equipaggiamento, artigiani da liberare, un Archivio di lore con bonus, imprese da completare.
- ♾️ **Modalità Infinita** dopo la prima vittoria: oltre il piano 30 inizia il **Ciclo del Labirinto**. I sei biomi tornano in un ordine nuovo a ogni ciclo, ogni ciclo è un'Eco più dura (Eco II, Eco III…) e alla fine di ognuno ti attende di nuovo il DIO ANTICO.

## 🧭 Dentro il gioco

Tutto quello che serve sapere prima di scendere: gli eroi, le modalità, le regole del combattimento e cosa succede al Campo fra una discesa e l'altra.

### 🧬 Gli eroi

{classes_table}

Ogni classe ha un **albero di Maestria** a 5 livelli. Si sale giocando con quella classe. Il **Lv.4** dà un bonus permanente a *tutti* gli eroi; il **Lv.5** sblocca una classe, un tratto o una reliquia. Assassino e Negromante, per esempio, si conquistano portando al massimo Ladro e Mago.

### 🎭 Tratti

All'inizio di ogni discesa scegli un **tratto**, che cambia le regole per tutta la partita:

{traits_table}

### 🎮 Modalità

#### Ascensione

Dopo la prima vittoria, a ogni partenza scegli un **grado di Ascensione**: ogni grado aggiunge una regola a quelle dei gradi precedenti e moltiplica l'Essenza. Vincendo al grado più alto sblocchi il successivo, fino al {len(grades)}. I vecchi **Patti del Caos** sono diventati gradi.

{grades_table}

#### 📅 Sfida del Giorno

Sempre disponibile dal menu principale. Ogni giorno la stessa discesa per chiunque: eroe e tratto assegnati (anche non ancora sbloccati), {daily['maluses']} malus presi dai gradi di Ascensione e un dono. Ogni piano nasce dallo stesso seme, quindi la sua mappa non dipende dalla strada fatta prima. Conta il primo tentativo, che vale Essenza ×{it(daily['first_attempt_essence_mult'])}: {daily['score']['per_floor']} punti per piano, {daily['score']['per_boss']} per boss, {daily['score']['victory']} per la vittoria e uno ogni {daily['score']['gold_div']} Oro.

{boons_table}

### ⚔️ Il combattimento

A ogni turno puoi **attaccare**, **difenderti** (ogni classe ha la sua tecnica: contrattacco, concentrazione, riparo magico, purificazione, fiala reattiva o furto di vita), usare un oggetto dallo zaino, consultare le statistiche o **tentare la fuga** (impossibile contro i boss). Le statistiche mostrano la tua **probabilità reale di colpire** contro il nemico che hai davanti.

**Elementi.** Un colpo *Super Efficace* fa il **50% di danni in più** e ha +15% di precisione; uno *Poco efficace* fa metà danni e −20% di precisione.

- {" · ".join(beats)}
- ✨ **Luce** e 🌑 **Tenebra** sono forti l'una contro l'altra e deboli contro sé stesse; ⚪ **Normale** è neutro.

**Risonanze.** Se arma e armatura hanno lo stesso elemento (non Normale), ottieni un bonus per tutto lo scontro. Si ricalcola subito se cambi equipaggiamento a metà combattimento.

{res_table}

**Status.** Alcuni nemici infliggono *Veleno* o *Sanguinamento*, che svaniscono a fine scontro (l'*Antidoto* li toglie subito). Alcune armi speciali li infliggono ai nemici.

**Maledizioni.** Gli oggetti `[MALEDETTO]` hanno statistiche altissime ma drenano HP od Oro, o rallentano. Si purificano al Falò (100 Oro) o con l'*Acqua Santa*.

### 🏕️ Il Campo Base

Fra una discesa e l'altra spendi l'**Essenza Astrale**:

- 🔥 **Il Fuoco dell'Anima** — 14 potenziamenti permanenti: HP, Oro, schivata, precisione, EXP, sconti, la *Speranza di Luce* (fino al 15% degli HP recuperati a ogni piano) e altro.
- ⚒️ **La Forgia Dimensionale** — sblocca armi, armature, monili, consumabili e reliquie.
- 🍺 **La Taverna** — le classi da conquistare e come ottenerle.
- 📜 **Grimorio e Imprese** — le sfide completate e i progressi di Maestria.
- 📚 **L'Archivio di Aethelgard** — {len(books)} tomi di storia da sbloccare: {sum(1 for b in books.values() if "bonus" in b)} danno un bonus permanente, gli altri si leggono e basta.
- 📖 **Il Codice del Labirinto** — bestiario, fasi dei boss, personaggi, eventi, lettere insanguinate e reliquie scoperti fra una run e l'altra, con la percentuale di completamento. Ciò che manca è un `???` da riempire.
- 🧑‍🔧 **Gli artigiani** — salva lo *Speziale*, *Borek*, *Elara* e *Valerius* dagli eventi del labirinto: apriranno una bottega dove comprare consumabili, armi, armature e monili con cui iniziare la discesa successiva.

E in **Impostazioni** scegli la velocità del testo: lenta, normale, veloce o istantanea.

### 💰 L'Essenza

| Come finisce la discesa | Essenza ottenuta |
|---|---|
| ☠️ Morte | 20% dell'Oro posseduto |
| 🏃 Fuga dal labirinto | 100% dell'Oro posseduto |
| 🏆 Vittoria al piano 30 | 100% dell'Oro + 1.000 |

A questo si aggiungono **50 Essenza per ogni boss** sconfitto, il moltiplicatore del grado di **Ascensione** (o del primo tentativo della **Sfida del Giorno**) e, oltre il piano 30 in Modalità Infinita, un ulteriore **×1,5**, che cresce del 25% per ogni Eco oltre la seconda.

## 📚 Enciclopedia

<details>
<summary>🌟 Le {len(relics)} reliquie</summary>

Si tengono al massimo 4 reliquie alla volta: trovandone un'altra scegli quale sacrificare.

{relic_table}

</details>

<details>
<summary>⚔️ Le {len(weapons)} armi</summary>

L'ATK reale cresce con il piano in cui l'arma viene trovata; le armi di elemento *Normale* ricevono un bonus di ATK.

{weapons_table}

</details>

<details>
<summary>🛡️ Le {len(armors)} armature</summary>

{armors_table}

</details>

<details>
<summary>💍 I {len(accs)} monili</summary>

{acc_table}

</details>

<details>
<summary>🧪 I {len(cons)} consumabili</summary>

{cons_table}

</details>

<details>
<summary>🔷 Le {len(runes_data['runes'])} rune</summary>

Si incastonano al Falò in armi e armature: {runes_data['rules']['sockets']['normal']} incastone per gli oggetti comuni, {runes_data['rules']['sockets']['epic']} per gli epici, {runes_data['rules']['sockets']['boss']} per i premi dei boss.

{runes_table}

Certe combinazioni sullo stesso oggetto formano una **parola runica**, con un effetto in più:

{words_table}

</details>

<details>
<summary>🏆 Le {len(meta['feats'])} imprese</summary>

{feats_table}

</details>

<details>
<summary>🎭 Gli eventi narrativi</summary>

{len(events)} storie e {scenes} scene: {events_list}… e qualcuno che torna a cercarti più in basso.

Ogni scelta mostra i suoi effetti reali, molte opzioni esistono solo per certe classi, tratti o reliquie, gli *oggetti chiave* di un evento aprono strade segrete in un altro e il Labirinto ricorda le tue decisioni da una run all'altra. Quattro eventi nascondono gli artigiani prigionieri.

</details>

## 📊 In numeri

{numbers}

## 🛠️ Per chi sviluppa

Il gioco è **data-driven**: classi, nemici, oggetti, reliquie, eventi, Maestrie, Risonanze e bonus dell'Archivio stanno in `data/*.json` e si bilanciano senza toccare il codice. Usa solo la libreria standard di Python.

```text
rogue/
├── roguelike.py       # Menu principale, Campo Base, scelta dell'eroe, ciclo dei piani, fine partita
├── floor_map.py       # Mappa del piano: file di stanze, percorsi, biomi, disegno
├── rooms.py           # Le stanze: combattimento, mercante, falò, forziere, trappola, mistero
├── combat/            # Il combattimento (CombatSession): turno dell'eroe e del nemico, incantesimi, reazioni, fasi, premi
├── events.py          # Motore degli eventi: scene, condizioni, effetti, memoria fra le run
├── entities.py        # Eroe, nemici e oggetti; generazione dell'equipaggiamento
├── relic_effects.py   # Effetti delle reliquie come hook (on_attack, on_take_damage, ...)
├── inventory_menu.py  # Zaino, consumabili e schermata delle statistiche
├── archive.py         # Archivio di Aethelgard e relativi bonus
├── camp.py            # Il Fuoco del Campo: personaggi e strutture
├── camp_rules.py      # Livelli ed effetti delle strutture del Campo
├── endings.py         # I finali multipli
├── codex.py           # Il Codice del Labirinto: ciò che hai scoperto fra le run
├── epitaph.py         # L'Epitaffio e il Cimitero
├── nemesis.py         # La Nemesi: chi ti uccide torna a cercarti
├── attributes.py      # Attributi dell'eroe e punti abilità
├── talents.py         # Talenti ogni 5 livelli
├── magic.py           # Incantesimi ed Etere
├── runes.py           # Rune e Incastoni: effetti, drop, etichette
├── modes.py           # Ascensione e Sfida del Giorno: le regole della discesa
├── data_manager.py    # Caricamento dei dati e salvataggio del profilo
├── run_save.py        # Salvataggio a metà discesa: «Salva ed esci» e «Riprendi la discesa»
├── ui.py              # Terminale: colori, menu a frecce, output centralizzato
├── constants.py       # Costanti di bilanciamento
├── data/              # Tutti i contenuti del gioco in JSON
├── texts.py           # I testi d'atmosfera scelti a caso, con un caso tutto loro
├── tools/             # Bilanciamento (simulatore di run), conteggio della lore e generatore di questo README
└── tests/             # Test automatici (unittest)
```

```bash
python -m unittest discover -s tests   # esegue i test, gli stessi della CI
```

I **test di contratto** (`tests/test_contracts.py`, `tests/test_modes.py`) verificano che ogni reliquia, monile, arma, armatura, consumabile, evento, tratto, patto, grado di Ascensione, dono della Sfida del Giorno, potenziamento, Maestria e impresa faccia esattamente ciò che dice la sua descrizione: un contenuto nuovo senza il suo contratto fa fallire i test.

- 📖 [**Manuale del Giocatore**](MANUALE_GIOCATORE.md) — strategie e regole in dettaglio.
- 🔧 [**Documentazione Tecnica**](DOCUMENTAZIONE_TECNICA.md) — architettura, formato dei dati, formule e come aggiungere contenuti.
- 📜 [**La Storia**](STORY.md) — il canone del mondo di Aethelgard e la guida di scrittura della lore.
- 🤖 [**AGENTS.md**](AGENTS.md) — regole per contribuire (anche con assistenti IA): branch e pull request, test, niente dipendenze esterne.

## 📝 Roadmap

Il gioco è cresciuto per versioni, ognuna provata su un branch dedicato prima di arrivare qui. Le ultime: la **v6** ha moltiplicato per dieci la storia, la **v7** ha portato la grafica nel terminale.

<details>
<summary>Tutto ciò che è già nel gioco</summary>

- [x] Classi **Assassino** e **Negromante**
- [x] Nemici e boss legati alla profondità
- [x] Impostazioni (velocità del testo)
- [x] Rune e Incastoni per armi e armature
- [x] Nemici che annunciano la mossa e reazioni elementali
- [x] Boss con fasi: soglie di HP, mosse nuove (Sigillo, Carica, Prosciugamento, Barriera), scudi e Scaglie
- [x] Eventi a scene, opzioni per classe e tratto, memoria fra le run
- [x] Personaggi ricorrenti (Sir Alaric, Silas) e il Codice del Labirinto
- [x] Mappa dei piani e primo bioma (I Chiostri del Rimpianto)
- [x] Regole per tutti e sei i biomi
- [x] Hub fra le run, finali multipli e Corruzione
- [x] Stanze a rischio e ricompensa (trappole con bottino, Mimic, Élite, Audacia)
- [x] Gradi di Ascensione e Sfida del Giorno
- [x] Stili dei nemici, un boss per ogni bioma, una difesa per ogni classe
- [x] Sei nemici nativi per ogni bioma
- [x] Il Ciclo del Labirinto: biomi che tornano in Eco sempre più dure oltre il piano 30
- [x] Armi con carattere: precisione, critico, schivata, Guardia e scudi
- [x] Livelli e attributi: un punto a ogni livello fra Vitalità, Forza, Destrezza, Agilità, Arcano e Fortuna
- [x] La magia: l'Etere e i primi incantesimi, che compongono le reazioni elementali
- [x] Grimori: pergamene, tre posti per gli incantesimi, cure fuori dal combattimento, Medita al Falò
- [x] Armi e attributi: ogni arma scala con Forza, Destrezza o Arcano; bastoni e focus potenziano gli incantesimi
- [x] Talenti: ogni 5 livelli un talento fra tre proposti
- [x] La magia nel mondo: Silenzio, Risucchio d'Etere e boss che lanciano incantesimi; rune, reliquie, eventi, Maestrie, Ascensione e Nemesi
- [x] Grande ribilanciamento: classi più vicine fra loro, nemici un po' più duri
- [x] Contenuti: esiti del Mistero, tomi dell'Archivio, imprese e tratti legati alla magia
- [x] L'Elementalista, la nona classe
- [x] Il Campo cresce: strutture a più livelli, Biblioteca dell'Arcano e Sala d'Armi
- [x] La storia a dieci volte: dialoghi del Campo, Archivio, Atlante, vite prestate, Armeria, epiloghi dei finali
- [x] Grafica nel terminale: ritratti dei boss, sagome dei nemici, paesaggi dei biomi, insegne delle stanze, barre

</details>

<a id="domande"></a>

## ❓ Domande frequenti

<details>
<summary><b>È gratis? Ci sono acquisti o pubblicità?</b></summary>

È completamente gratuito e open source, sotto licenza MIT. Niente acquisti, niente pubblicità, niente account, niente connessione a internet: tutto gira sul tuo computer.

</details>

<details>
<summary><b>Perché nel terminale e non in una finestra?</b></summary>

Perché così funziona ovunque, senza installare niente oltre a Python, e lascia tutto lo spazio all'immaginazione e alla storia. La grafica c'è, ma è fatta di caratteri: ritratti, paesaggi, barre e colori.

</details>

<details>
<summary><b>È difficile?</b></summary>

All'inizio sì, ed è voluto: in un roguelite si muore spesso. Ma ogni morte lascia qualcosa, e dopo poche discese l'Essenza accumulata fa la differenza. Chi cerca una sfida vera ha venti gradi di Ascensione e il Ciclo del Labirinto oltre il piano 30.

</details>

<details>
<summary><b>Dove sono i miei salvataggi? Posso spostarli?</b></summary>

Tutti i progressi stanno in `profile.json`, nella cartella del gioco; una discesa interrotta con *Salva ed esci* sta in `run_save.json`. Per portare i progressi su un altro computer, o in una versione nuova, basta copiare questi file. Se `profile.json` si rovina, il gioco ne mette da parte una copia e riparte da un profilo nuovo.

</details>

<details>
<summary><b>Le emoji appaiono come quadratini, o i colori sono strani.</b></summary>

È il terminale, non il gioco. Su Windows usa **Windows Terminal**, oppure scrivi `chcp 65001` prima di avviare; su macOS e Linux il terminale predefinito va bene. Se il testo scorre troppo lento o troppo veloce, cambia la velocità nelle impostazioni del menu principale.

</details>

<details>
<summary><b>Posso giocarci senza leggere tutta la storia?</b></summary>

Sì. In discesa i testi sono brevi e le scelte chiare; la storia lunga sta al Campo, nel Codice e nell'Archivio, e la leggi solo se ti va.

</details>

<details>
<summary><b>Posso modificare il gioco o aggiungere contenuti?</b></summary>

Sì: la licenza MIT lo permette, e quasi tutto il gioco sta in file JSON leggibili nella cartella `data/`. La [Documentazione Tecnica](DOCUMENTAZIONE_TECNICA.md) spiega come aggiungere nemici, oggetti, eventi e testi.

</details>

## 🧩 Componenti

Il gioco è costruito volutamente con pochissimo: **Python e la sua libreria standard, niente altro**.

| Componente | Cosa fa nel gioco |
|---|---|
| ![Python](https://img.shields.io/badge/Python_3.9+-3776AB?logo=python&logoColor=white) | Il linguaggio di tutto il gioco |
| ![Libreria standard](https://img.shields.io/badge/libreria_standard-3776AB?logo=python&logoColor=white) | Solo moduli inclusi in Python (`json`, `random`, `os`, `re`, `unicodedata`…): nessun pacchetto da installare |
| ![ANSI](https://img.shields.io/badge/terminale-ANSI_e_Unicode-333333?logo=windowsterminal&logoColor=white) | Colori, menu a frecce, riquadri e disegni in caratteri |
| ![JSON](https://img.shields.io/badge/dati-JSON-000000?logo=json&logoColor=white) | Tutti i contenuti, dalle armi alla storia, nella cartella `data/` |
| ![unittest](https://img.shields.io/badge/test-unittest-3776AB?logo=python&logoColor=white) | Centinaia di test automatici sulle regole, i dati e i testi |
| ![GitHub Actions](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?logo=githubactions&logoColor=white) | I test girano su ogni modifica, con Python 3.9 e con l'ultima versione |
| ![rsp](https://img.shields.io/badge/review-rsp-6f42c1) | Controlla ogni pull request: test saltati, dipendenze non dichiarate, controlli disattivati |

<a id="licenza"></a>

## 📜 Licenza

[![Licenza MIT](https://img.shields.io/badge/Licenza-MIT-yellow.svg)](LICENSE)

*Il Labirinto degli Elementi e del Caos* è distribuito sotto **licenza MIT**: puoi giocarci, studiarlo, modificarlo e ridistribuirlo, anche per scopi commerciali, a patto di mantenere l'avviso di copyright e il testo della licenza. Il testo completo è nel file [LICENSE](LICENSE).

Il gioco usa solo la libreria standard di Python: non include librerie di terze parti, quindi non ci sono altre licenze da rispettare per giocarci o ridistribuirlo.

---

<div align="center">

**[⬆️ Torna su](#top)** · **[⬇️ Scarica il gioco](https://github.com/fedeveloper/rogue/archive/refs/heads/main.zip)** · **[📖 Manuale](MANUALE_GIOCATORE.md)**

<sub>Fatto con Python e nient'altro. Buona discesa, Ritornante.</sub>

</div>
"""
if __name__ == "__main__":
    with open(f"{ROOT}/README.md", "w", encoding="utf-8") as f: f.write(README)
    print("README scritto:", len(README.splitlines()), "righe")
