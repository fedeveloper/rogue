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
         "3": "Arma di Fuoco potente e mira eccellente, ma fragile", "4": "Ultra-tank con Risonanza di Luce fin dall'inizio",
         "5": "Glass cannon: l'ascia più forte, nessuna armatura", "6": "Quattro pozioni iniziali e bombe di Fuoco",
         "7": "15% di critico innato e schivata alta, ma fragile", "8": "Risonanza di Tenebra fin dall'inizio"}
emoji = {"1": "⚔️", "2": "🗡️", "3": "🔮", "4": "🛡️", "5": "🪓", "6": "🧪", "7": "🥷", "8": "💀"}
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
reward = {"perk": "Potenziamento", "unlock": "Sblocco", "class": "Classe", "trait": "Tratto"}
names = {x.get("unlock_id"): x["name"] for x in weapons + armors + accs + cons + relics if x.get("unlock_id")}
names.update({k: c["role"] for k, c in classes.items()}); names.update({k: t["name"] for k, t in meta["traits"].items()}); names["scarpisti"] = "Scarpisti (+20% Fuga)"
feats_table = table(["Impresa", "Obiettivo", "Ricompensa"],
    [(f"**{f['name']}**", f["desc"], f"{reward[f['reward_type']]}: {names.get(f['reward_id'], f['reward_id'])}") for f in meta["feats"].values()])
def special(w):
    return w.get("desc") or "—"
weapons_table = table(["Arma", "ATK base", "Elemento", "Caratteristiche", "Come ottenerla"],
    [(f"**{w['name']}**", w["base_atk"], f"{icon[w['element']]} {w['element']}" if w.get("element") else "Casuale", special(w), how(w)) for w in weapons])
armors_table = table(["Armatura", "DEF base", "Caratteristiche", "Come ottenerla"],
    [(f"**{a['name']}**", a["base_def"], a.get("desc") or "—", how(a)) for a in armors])
cons_table = table(["Consumabile", "Effetto", "Come ottenerlo"],
    [(f"**{c['name']}**", c.get("desc") or f"Cura {c['base_heal']} HP (di più ai piani profondi)", how(c)) for c in cons])

slot_names = {"weapon": "Arma", "armor": "Armatura", "any": "Arma o armatura"}
runes_table = table(["Runa", "Famiglia", "Dove", "Effetto"], [(f"{r['icon']} **{r['name']}**", r["family"], slot_names[r["slot"]], r["desc"]) for r in runes_data["runes"].values()])
count = lambda xs: f"{len(xs)} ({sum(1 for x in xs if not x.get('unlock_id'))} subito, {sum(1 for x in xs if x.get('unlock_id'))} da sbloccare)"
numbers = table(["Contenuto", "Quantità"], [
    ("Classi giocabili", len(classes)), ("Tratti di partenza", len(meta["traits"])), ("Gradi di Ascensione", len(grades)), ("Doni della Sfida del Giorno", len(daily["boons"])),
    ("Armi", count(weapons)), ("Armature", count(armors)), ("Monili", count(accs)), ("Consumabili", count(cons)), ("Reliquie", count(relics)),
    ("Nemici comuni", len(enemies["enemies"])), ("Boss", len(enemies["bosses"])), ("Fasi dei boss", sum(len(p) for p in phases.values())), ("Rune", len(runes_data["runes"])), ("Eventi narrativi", len(events)),
    ("Imprese", len(meta["feats"])), ("Tomi dell'Archivio", len(books)), ("Potenziamenti permanenti", 14),
    ("Elementi / Risonanze", f"{len(elements['list'])} / {len(elements['resonance'])}"),
    ("Combinazioni di partenza (modalità × classe × tratto × grado)", start_combos)])
events_list = ", ".join(f"*{e['title']}*" for e in events.values() if not e.get('scripted'))
scenes = sum(len(e['scenes']) for e in events.values())

README = f"""<div align="center">

# 🌀 Il Labirinto degli Elementi e del Caos

**Un roguelite da terminale in cui ogni discesa è diversa, ogni morte ti rende più forte e ogni elemento conta.**

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![Dipendenze](https://img.shields.io/badge/Dipendenze-nessuna-brightgreen)
[![Test](https://github.com/fedeveloper/rogue/actions/workflows/tests.yml/badge.svg)](https://github.com/fedeveloper/rogue/actions/workflows/tests.yml)
![Piattaforme](https://img.shields.io/badge/Windows%20%7C%20macOS%20%7C%20Linux-grey)
![Licenza](https://img.shields.io/badge/Licenza-Uso_Personale-green)

</div>

---

Sotto le rovine di Aethelgard si apre un labirinto che cambia forma a ogni passo. Scegli un eroe, un tratto e — se hai il coraggio — un grado di Ascensione. Poi scendi: **30 piani** di mostri, trappole, mercanti, falò ed eventi che ti costringono a scegliere. In fondo ti aspetta il **DIO ANTICO**.

Morirai. Spesso. Ma l'**Essenza Astrale** che riporti indietro resta: con essa sblocchi nuovi eroi, armi leggendarie, reliquie e potenziamenti permanenti. Ogni discesa ti avvicina un po' di più al fondo.

```text
!!! Incontri un GOBLIN [⚪ Normale] !!!

--- ⚔️ IN COMBATTIMENTO ⚔️ ---
Tu: 120/120 HP | Goblin: 11 HP
  > Attacca
    Difesa Aggressiva (Dimezza danni e Contrattacca)
    Apri Inventario (Usa oggetto = Costa Turno)
    Statistiche Eroe
    Tenta la Fuga
```

## 🚀 Gioca in 30 secondi

Serve solo **Python 3.9 o superiore**: nessuna libreria da installare.

```bash
git clone https://github.com/fedeveloper/rogue.git
cd rogue
python roguelike.py
```

> **Windows:** se le emoji non si vedono bene, esegui prima `chcp 65001` o usa *Windows Terminal*.

Si gioca **solo con la tastiera**: frecce ⬆️⬇️ per muoversi nei menu, **Invio** per confermare, **Ctrl+C** per uscire. Il salvataggio (`profile.json`) si crea da solo al primo avvio.

## ✨ Perché giocarci

- 🗺️ **Una mappa per ogni piano.** Quattro file di stanze collegate (combattimento, Élite, mercante, falò, forziere, trappola, evento o la *Stanza del Mistero*) e il boss in fondo, tutte visibili fin dall'arrivo: scegli il percorso, non solo la porta. Ogni stanza ha un prezzo e un premio: le trappole custodiscono un bottino, i forzieri profondi possono essere Mimic, e l'**Audacia** fa crescere il bottino del boss per ogni rischio corso nel piano. Nemici e boss crescono con la profondità.
- 🌍 **Sei biomi, sei regole.** Ogni cinque piani il Labirinto cambia volto e legge: la *Nostalgia Letale* dei Chiostri, il *Gas del Silenzio* delle Miniere, la *Caduta Astrale* delle Guglie, la *Dissoluzione dell'Io* del Ventre, l'*Ebollizione Astrale* della Forgia e il *Paradosso Temporale* della Soglia. Ogni bioma ha i suoi nemici nativi e le sue stanze speciali.
- 🔥 **Combattimento tattico.** Il nemico **annuncia la sua mossa**, colpo pesante, guardia, rigenerazione o colpo infetto, e tu decidi se attaccare o difenderti. Sette elementi, vantaggi e svantaggi, **Risonanze** quando arma e armatura condividono l'elemento e **{len(d('elements')['reactions'])} reazioni** (Vapore, Gelo, Eclissi…) quando li combini.
- 🧬 **{len(classes)} classi** con alberi di Maestria a 5 livelli che sbloccano bonus, oggetti, reliquie e altre classi.
- 🎭 **{len(meta['traits'])} tratti** e **{len(grades)} gradi di Ascensione**: {f'{start_combos:,}'.replace(',', '.')} combinazioni di partenza diverse.
- 📅 **Sfida del Giorno.** Una discesa al giorno uguale per tutti: eroe, tratto, malus e dono assegnati, la stessa mappa a ogni piano. Conta il primo tentativo; punteggio, serie di giorni e record restano nel profilo.
- 📖 **Eventi che ricordano.** {len(events)} storie a scene con opzioni che esistono solo per la tua classe, il tuo tratto o le tue reliquie: `[Mago]`, `[Tocco di Mida]`, `[Chiave Arrugginita]`. Il Labirinto ricorda chi hai aiutato e chi hai derubato, e certe scelte tornano a bussare qualche piano dopo.
- 🗝️ **Personaggi che ritornano.** *Sir Alaric*, il Primo Paladino, e *Silas*, il Cercatore, hanno storie in tre capitoli che proseguono di run in run. Le tue scelte decidono come finiscono, e se liberi Alaric il Cavaliere Oscuro non tornerà più.
- 🔷 **Rune e Incastoni.** {len(runes_data['runes'])} rune da incastonare al Falò in armi e armature: allungano i marchi, potenziano le reazioni, fanno sanguinare, rubano vita, riflettono i colpi. Restano sull'oggetto finché non le estrai, quindi ogni cambio d'arma è una scelta.
- 👑 **Boss che cambiano.** A metà della vita ogni boss entra in una nuova fase con un nome, mosse nuove e regole proprie: il Re dei Goblin chiama le guardie, il Drago di Zaffiro si copre di Scaglie che solo una reazione elementale infrange, la Badessa ti sigilla la difesa. Il DIO ANTICO ha tre fasi, e nella seconda diventa l'elemento che ti ferisce di più.
- 🩸 **Corruzione.** Le scelte oscure danno potere e opzioni proibite, ma il Labirinto comincia a nasconderti le cose: gli effetti delle scelte, le mosse dei nemici.
- 🏁 **{len(d('story')['endings'])} finali.** Uccidere il Dio, prenderne il posto, risvegliare Aethelgard… e un finale segreto per chi legge davvero il Labirinto.
- 🔥 **Un campo che ricorda.** Chi salvi nel Labirinto viene a scaldarsi al tuo fuoco, ti parla di ciò che hai fatto e ti aiuta a costruire.
- 🌟 **{len(relics)} reliquie** che piegano le regole: danni raddoppiati, scudi, vampirismo, oro moltiplicato.
- 🏕️ **Meta-progressione profonda**: potenziamenti permanenti, una Forgia per sbloccare equipaggiamento, artigiani da liberare, un Archivio di lore con bonus, imprese da completare.
- ♾️ **Modalità Infinita** dopo la prima vittoria, per chi vuole spingersi oltre il piano 30.

## 🧬 Gli eroi

{classes_table}

Ogni classe ha un **albero di Maestria** a 5 livelli. Si sale giocando con quella classe. Il **Lv.4** dà un bonus permanente a *tutti* gli eroi; il **Lv.5** sblocca una classe, un tratto o una reliquia. Assassino e Negromante, per esempio, si conquistano portando al massimo Ladro e Mago.

## 🎭 Tratti

All'inizio di ogni discesa scegli un **tratto**, che cambia le regole per tutta la partita:

{traits_table}

## 🎮 Modalità

### Ascensione

Dopo la prima vittoria, a ogni partenza scegli un **grado di Ascensione**: ogni grado aggiunge una regola a quelle dei gradi precedenti e moltiplica l'Essenza. Vincendo al grado più alto sblocchi il successivo, fino al {len(grades)}. I vecchi **Patti del Caos** sono diventati gradi.

{grades_table}

### 📅 Sfida del Giorno

Sempre disponibile dal menu principale. Ogni giorno la stessa discesa per chiunque: eroe e tratto assegnati (anche non ancora sbloccati), {daily['maluses']} malus presi dai gradi di Ascensione e un dono. Ogni piano nasce dallo stesso seme, quindi la sua mappa non dipende dalla strada fatta prima. Conta il primo tentativo, che vale Essenza ×{it(daily['first_attempt_essence_mult'])}: {daily['score']['per_floor']} punti per piano, {daily['score']['per_boss']} per boss, {daily['score']['victory']} per la vittoria e uno ogni {daily['score']['gold_div']} Oro.

{boons_table}

## ⚔️ Il combattimento

A ogni turno puoi **attaccare**, **difenderti** (ogni classe ha la sua difesa: contrattacco, concentrazione o riparo magico), usare un oggetto dallo zaino, consultare le statistiche o **tentare la fuga** (impossibile contro i boss). Le statistiche mostrano la tua **probabilità reale di colpire** contro il nemico che hai davanti.

**Elementi.** Un colpo *Super Efficace* fa il **50% di danni in più** e ha +15% di precisione; uno *Poco efficace* fa metà danni e −20% di precisione.

- {" · ".join(beats)}
- ✨ **Luce** e 🌑 **Tenebra** sono forti l'una contro l'altra e deboli contro sé stesse; ⚪ **Normale** è neutro.

**Risonanze.** Se arma e armatura hanno lo stesso elemento (non Normale), ottieni un bonus per tutto lo scontro. Si ricalcola subito se cambi equipaggiamento a metà combattimento.

{res_table}

**Status.** Alcuni nemici infliggono *Veleno* o *Sanguinamento*, che svaniscono a fine scontro (l'*Antidoto* li toglie subito). Alcune armi speciali li infliggono ai nemici.

**Maledizioni.** Gli oggetti `[MALEDETTO]` hanno statistiche altissime ma drenano HP od Oro, o rallentano. Si purificano al Falò (100 Oro) o con l'*Acqua Santa*.

## 🏕️ Il Campo Base

Fra una discesa e l'altra spendi l'**Essenza Astrale**:

- 🔥 **Il Fuoco dell'Anima** — 14 potenziamenti permanenti: HP, Oro, schivata, precisione, EXP, sconti, la *Speranza di Luce* (fino al 15% degli HP recuperati a ogni piano) e altro.
- ⚒️ **La Forgia Dimensionale** — sblocca armi, armature, monili, consumabili e reliquie.
- 🍺 **La Taverna** — le classi da conquistare e come ottenerle.
- 📜 **Grimorio e Imprese** — le sfide completate e i progressi di Maestria.
- 📚 **L'Archivio di Aethelgard** — {len(books)} tomi di storia da sbloccare, ognuno con un bonus permanente.
- 📖 **Il Codice del Labirinto** — bestiario, fasi dei boss, personaggi, eventi, lettere insanguinate e reliquie scoperti fra una run e l'altra, con la percentuale di completamento. Ciò che manca è un `???` da riempire.
- 🧑‍🔧 **Gli artigiani** — salva lo *Speziale*, *Borek*, *Elara* e *Valerius* dagli eventi del labirinto: apriranno una bottega dove comprare consumabili, armi, armature e monili con cui iniziare la discesa successiva.

E in **Impostazioni** scegli la velocità del testo: lenta, normale, veloce o istantanea.

## 💰 L'Essenza

| Come finisce la discesa | Essenza ottenuta |
|---|---|
| ☠️ Morte | 20% dell'Oro posseduto |
| 🏃 Fuga dal labirinto | 100% dell'Oro posseduto |
| 🏆 Vittoria al piano 30 | 100% dell'Oro + 1.000 |

A questo si aggiungono **50 Essenza per ogni boss** sconfitto, il moltiplicatore del grado di **Ascensione** (o del primo tentativo della **Sfida del Giorno**) e, oltre il piano 30 in Modalità Infinita, un ulteriore **×1,5**.

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
├── rooms.py           # Combattimento (CombatSession) e stanze: mercante, falò, forziere, trappola, mistero
├── events.py          # Motore degli eventi: scene, condizioni, effetti, memoria fra le run
├── entities.py        # Eroe, nemici e oggetti; generazione dell'equipaggiamento
├── relic_effects.py   # Effetti delle reliquie come hook (on_attack, on_take_damage, ...)
├── inventory_menu.py  # Zaino, consumabili e schermata delle statistiche
├── archive.py         # Archivio di Aethelgard e relativi bonus
├── camp.py            # Il Fuoco del Campo: personaggi e strutture
├── endings.py         # I finali multipli
├── codex.py           # Il Codice del Labirinto: ciò che hai scoperto fra le run
├── runes.py           # Rune e Incastoni: effetti, drop, etichette
├── modes.py           # Ascensione e Sfida del Giorno: le regole della discesa
├── data_manager.py    # Caricamento dei dati e salvataggio del profilo
├── ui.py              # Terminale: colori, menu a frecce, output centralizzato
├── constants.py       # Costanti di bilanciamento
├── data/              # Tutti i contenuti del gioco in JSON
├── tools/             # Bilanciamento (simulatore di run) e generatore di questo README
└── tests/             # Test automatici (unittest)
```

```bash
python -m unittest discover -s tests   # esegue i test, gli stessi della CI
```

I **test di contratto** (`tests/test_contracts.py`, `tests/test_modes.py`) verificano che ogni reliquia, monile, arma, armatura, consumabile, evento, tratto, patto, grado di Ascensione, dono della Sfida del Giorno, potenziamento, Maestria e impresa faccia esattamente ciò che dice la sua descrizione: un contenuto nuovo senza il suo contratto fa fallire i test.

- 📖 [**Manuale del Giocatore**](MANUALE_GIOCATORE.md) — strategie e regole in dettaglio.
- 🔧 [**Documentazione Tecnica**](DOCUMENTAZIONE_TECNICA.md) — architettura, formato dei dati, formule e come aggiungere contenuti.
- 📜 [**La Storia**](STORY.md) — il mondo di Aethelgard.
- 🤖 [**AGENTS.md**](AGENTS.md) — regole per contribuire (anche con assistenti IA): branch e pull request, test, niente dipendenze esterne.

## 📝 Roadmap

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

---

<div align="center"><i>Sviluppato con ❤️ e Python. Buona discesa.</i></div>
"""
if __name__ == "__main__":
    with open(f"{ROOT}/README.md", "w", encoding="utf-8") as f: f.write(README)
    print("README scritto:", len(README.splitlines()), "righe")
