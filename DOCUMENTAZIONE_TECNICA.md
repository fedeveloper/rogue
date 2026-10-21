# 🔧 Documentazione Tecnica

Riferimento per chi modifica il gioco: architettura, formato dei dati, formule di combattimento, salvataggio, test e come aggiungere contenuti. Per le regole viste dal giocatore c'è il [Manuale](MANUALE_GIOCATORE.md); per le regole di contribuzione c'è [AGENTS.md](AGENTS.md).

---

## 1. Principi

- **Solo libreria standard.** Il gioco gira con Python 3.9+ senza installare nulla (`pyproject.toml` dichiara `dependencies = []`).
- **Data-driven.** Contenuti e bilanciamento stanno in `data/*.json`; il codice applica regole generiche. Classi, Maestrie, Risonanze, bonus dell'Archivio, nemici, oggetti ed eventi si cambiano senza toccare Python.
- **Output centralizzato.** I moduli di gioco non chiamano `print` né `input`: passano da `ui.display_msg()` e `ui.wait_enter()`, così l'interfaccia è sostituibile e testabile. Un test lo verifica.

---

## 2. Moduli

| Modulo | Responsabilità |
|---|---|
| `roguelike.py` | Punto d'ingresso (`main`). Menu principale, Impostazioni, Campo Base (Fuoco dell'Anima, Forgia, Taverna, Grimorio, botteghe), scelta di eroe/tratto/patti, ciclo dei piani (`play_game`), generazione delle porte (`_generate_doors`), fine partita (`evaluate_run`), Maestria e imprese. |
| `rooms.py` | `CombatSession` (turni, danni, status, Risonanze, fine scontro) e tutte le stanze: mercante, falò, forziere, trappola, mistero, eventi (`_handle_event_action`). |
| `entities.py` | `Player`, `Enemy`, gli oggetti (`Weapon`, `Armor`, `Accessory`, `Consumable`) e i generatori casuali. Applica tratti, Maestrie, potenziamenti e oggetti iniziali. Sceglie i nemici in base alla profondità (`pick_enemy_name`). |
| `relic_effects.py` | Una classe per reliquia, con gli hook che le servono; `RELIC_REGISTRY` collega l'id del JSON alla classe. |
| `inventory_menu.py` | Zaino, uso dei consumabili (`_use_consumable`), equipaggiamento e schermata delle statistiche. |
| `archive.py` | Tomi dell'Archivio: condizioni di sblocco e bonus (`get_archive_bonus`), letti una volta da `books.json`. |
| `data_manager.py` | Carica i JSON (`RAW_DATA`), filtra ciò che è sbloccato (`GAME_DATA`, ricalcolato da `update_game_data()`), gestisce il profilo (`PROFILE_MANAGER`). |
| `ui.py` | Terminale: colori ANSI, lettura dei tasti (Windows e POSIX), menu a frecce (`interactive_menu`), velocità del testo (`delay_print`, `set_text_speed`). |
| `constants.py` | Costanti di bilanciamento (precisione base, scaling, finestre di profondità, velocità del testo…). |

Dipendenze fra i moduli: `ui` ← `data_manager` ← `archive`/`relic_effects` ← `entities` ← `inventory_menu` ← `rooms` ← `roguelike`. Nessun modulo importa da uno che sta alla sua destra.

---

## 3. I dati (`data/*.json`)

Un campo `"unlock_id"` assente o `null` significa **disponibile da subito**. Un valore indica che l'oggetto va sbloccato:
- alla Forgia, se ha `unlock_cost > 0`;
- altrimenti tramite un'impresa, una Maestria o la vittoria (`VICTORY_UNLOCKS` in `roguelike.py`, oggi la Lama del Creatore).

Un test controlla che ogni oggetto sbloccabile abbia davvero una di queste strade.

**Le descrizioni sono un contratto.** Ogni numero o effetto scritto in `desc`/`text` deve corrispondere a ciò che il gioco fa, e `tests/test_contracts.py` lo verifica. Le proprietà speciali di armi e armature (`hit_modifier`, `crit_chance`, `gold_atk_*`, `dodge_bonus`, `element`) si dichiarano nei dati; la descrizione le racconta con gli stessi numeri.

| File | Contenuto | Campi principali |
|---|---|---|
| `classes.json` | Le classi, per id (`"1"`…`"8"`) | `role`, `max_hp`, `gold`, `acc`, `dodge`, `crit` (opz.), `weapon`/`armor` iniziali (`name`, `value`, `atk`/`def`, `element`), `potions`, `unlocked_by_default`, `mastery` |
| `enemies.json` | `enemies` e `bosses`, per nome | `element`, `base_hp`, `base_atk`, `base_dodge`, `base_acc`, `title`/`lore` (boss), `status_inflict` (opz.), `final_boss` (solo DIO ANTICO) |
| `weapons.json` | Armi | `name`, `base_atk`, `val_base` (opz.), `element` (opz., altrimenti casuale), `status_inflict` (opz.), `hit_modifier`, `crit_chance`, `gold_atk_per`/`gold_atk_max` (opz.), `unlock_id`, `unlock_cost`, `desc`, `flavor` |
| `armors.json` | Armature | `name`, `base_def`, `element` (opz.), `dodge_bonus` (opz.), `unlock_id`, `unlock_cost`, `desc`, `flavor` |
| `accessories.json` | Monili | `name`, `bonus_type` (`crit_chance`, `lifesteal`, `max_hp`, `dodge`, `acc`, `reflect`), `bonus_value`, `base_val`, `desc`, `lore`, `unlock_id`, `unlock_cost` |
| `consumables.json` | Consumabili | `name`, `category` (`heal`, `antidote`, `smoke_bomb`, `chaos_tome`, `chaos_vial`, `holy_water`, `whetstone`, `accuracy_potion`), `base_heal`, `val_base`, `desc`, `unlock_id` |
| `relics.json` | Reliquie | `id`, `name`, `desc`, `lore`, `unlock_id`, `unlock_cost` |
| `elements.json` | Sistema elementale | `list`, `icons`, `multipliers[attaccante][difensore]`, `resonance[elemento] = {value, desc, announce}` |
| `books.json` | Tomi dell'Archivio | `title`, `unlock_condition` (testo), `unlock = {type: max_floor\|total_bosses\|won_normal, value}`, `bonus = {gold_pct, escape, boss_dmg_pct, def}`, `bonus_desc`, `chapters` |
| `meta.json` | Regole di contorno | `traits`, `pacts` (`bonus` di Essenza), `feats` (`target`, `reward_type`, `reward_id`), `mastery_xp_requirements`, `rooms.weights`/`rooms.cooldowns` |
| `events.json` | Eventi narrativi | `title`, `text`, `choices[]` con `text`, `action`, `msg`, `msg_alt`, `requires_item`, `item_id`, `reward_*`, `gold` (oro di `blood_gold`, predefinito 100) |
| `lore.json` | Frasi d'atmosfera | `combat`, `boss`, `vendor`, `treasure`, `trap`, `campfire`, `letters`, `mystery` |

### Maestrie

`classes.json → mastery` ha i livelli `"2"`…`"5"`. Ogni livello ha un `type`:

| `type` | Livello | Campi | Effetto |
|---|---|---|---|
| `personal` | 2 | `effect` | Effetto della sola classe, controllato con `Player.has_mastery_effect(effect)` |
| `unlock` | 3, 5 | `id` | Aggiunge `id` a `unlocked_ids` (oggetto, reliquia, tratto) |
| `global` | 4 | `bonus = {stat, value}` | Bonus a **tutti** gli eroi. Valori di `stat`: `def`, `dodge`, `exp`, `max_hp`, `weapon_atk`, `acc`, `crit`, `lifesteal` |
| `class` | 5 | `id` | Sblocca la classe con quell'id |

Gli sblocchi dei livelli già raggiunti vengono riconcessi all'avvio (`_grant_retroactive_mastery_unlocks`). Così contenuti aggiunti più tardi arrivano anche a chi aveva già il livello.

---

## 4. Il ciclo di gioco

```text
main() ─▶ menu principale ─▶ play_game(infinite_mode)
                                │
          _hero_selection() ────┤  classe, tratto, patti
          Player(...)           │
                                ▼
          per ogni piano: rigenerazione (Speranza di Luce)
            per step 1..5: _generate_doors() ─▶ scelta ─▶ stanza
            (step 5 = boss; al piano 30 il boss è final_boss)
          piano superato: +20+5·piano HP, max_floor aggiornato
                                ▼
          evaluate_run(): Essenza, Maestria, imprese, salvataggio
```

**Porte.** Ogni tipo di stanza ha un peso (`rooms.weights`) e un tempo di ricarica in passi (`rooms.cooldowns`). I pesi vengono ricalcolati a ogni bivio: ci passano le reliquie con `modify_room_weights`. Due porte dello stesso tipo, o una trappola accanto a un forziere o a un mercante, non escono mai insieme.

**Nemici per profondità.** `pick_enemy_name()` ordina i candidati per `base_hp × base_atk` e sceglie a caso in una finestra che sale con `(piano − 1) / 29`. La finestra è di `ENEMY_DEPTH_WINDOW` = 6 nemici e di `BOSS_DEPTH_WINDOW` = 5 boss. I boss con `final_boss` sono esclusi da questa scelta.

**Statistiche dei nemici.** Partendo dai valori base, con `l = piano − 1`:

| | HP | ATK | Oro | EXP |
|---|---|---|---|---|
| Nemico | base + 5·l ± 5 | base + l + (0..1) | max(5, 5 + 3,5·piano) | 30 + 10·piano |
| Boss | base + 8·l + (0..10) | base + 2,5·l + (0..2) | 50 + 15·piano | 150 + 20·piano |

Poi si applicano, in ordine: ×1,2 dal piano 10; ×1,25 dal piano 20; ×1,4 (potenziato) o ×0,6 (debilitato) nella Stanza del Mistero; ×1,3 agli HP con *Durezza* e ×1,3 all'ATK con *Furia*.

---

## 5. Formule di combattimento

**Precisione dell'eroe** (`Player.get_hit_chance`):

```text
85 + precisione + bonus temporanei − schivata nemico
   + 15 se Super Efficace / − 20 se Poco efficace
   + modificatore dell'arma + bonus delle reliquie        → limitata fra 10 e 100
```

**Danni dell'eroe**, in quest'ordine:
1. `(ATK arma + ATK reliquie ± caso) × moltiplicatore elementale`;
2. effetto dell'arma (es. il critico dell'Ascia del Boia);
3. +bonus dell'Archivio contro i boss;
4. critico (classe + monile, ×2);
5. *Imboscata* (×2);
6. se il colpo va a segno: moltiplicatore di classe, hook `on_attack` delle reliquie, +Tenebra.

**Precisione del nemico**: `85 + precisione nemico − schivata eroe ± elemento`, limitata fra 10 e 100. Il primo attacco di ogni scontro manca sempre con il *Cacciatore Etereo*.

**Danni subiti**:
1. `max(0, (ATK nemico ridotto dall'Acqua ± caso) × elemento − difesa)`, con la difesa che somma armatura, Terra, Eredità e Archivio;
2. dimezzati se ti stai difendendo;
3. modificati dagli hook `on_take_damage` delle reliquie (scudi, riflessi…).

**Fuga**: `20 + schivata − schivata nemico + 20 (Scarpisti) + bonus dell'Archivio`, limitata fra 10 e 90; con la *Bussola Perfetta* è 100. Impossibile dai boss.

**Elementi**: `elements.json → multipliers`; 1,5 Super Efficace, 0,5 Poco efficace, 1 altrimenti. Le reliquie possono modificarli con `modify_multiplier`.

**Livello dell'eroe**: soglia iniziale 100 EXP, ×1,5 a ogni livello; a ogni livello +15 HP massimi, cura completa, +2 precisione e +2 schivata.

---

## 6. Reliquie

Ogni reliquia è una sottoclasse di `RelicEffect` che ridefinisce solo gli hook che le servono:

| Hook | Quando |
|---|---|
| `on_equip` / `on_unequip` | Quando la reliquia entra o esce (anche sacrificandola per farne posto a un'altra) |
| `on_combat_start` | All'inizio di ogni scontro |
| `on_before_attack` | Prima di attaccare; restituire `False` annulla l'attacco |
| `on_attack(session, dmg, mult, testo)` | Su un colpo a segno, restituisce `(danni, testo)` |
| `on_attack_landed` | Dopo un colpo a segno |
| `on_take_damage(session, dmg, mult)` | Prima di subire danni, restituisce i danni |
| `on_enemy_death` | Alla morte del nemico, prima dell'EXP |
| `on_gold_gain` / `on_heal` | Modificano oro e qualsiasi cura |
| `on_item_heal` | Modifica solo le cure di pozioni e consumabili |
| `get_atk_modifier(player)` / `get_def_modifier(session)` | ATK e Difesa aggiuntivi, calcolati sul momento (es. Spirito della Spada, Pietra di Luna) |
| `on_item_use(player, item)` | Restituire `False` evita di consumare l'oggetto |
| `get_dodge_modifier` / `get_acc_modifier` / `get_exp_modifier` / `get_escape_modifier` | Modificatori passivi |
| `modify_multiplier(mult, is_defense)` / `modify_trap_damage` / `modify_room_weights` | Elementi, trappole e generazione delle stanze |

---

## 7. Il profilo (`profile.json`)

Il salvataggio si crea al primo avvio e **non va committato** (è in `.gitignore`). La scrittura è atomica: file temporaneo e poi `os.replace`. Se il file è illeggibile viene messo da parte come `profile.json.corrotto` e si riparte da un profilo nuovo. Al caricamento le chiavi mancanti vengono aggiunte con i valori predefiniti.

| Chiave | Contenuto |
|---|---|
| `essence`, `max_floor`, `won_normal` | Essenza, piano più profondo raggiunto, vittoria standard ottenuta (sblocca Patti e Modalità Infinita) |
| `unlocked_ids` | Tutti gli sblocchi: oggetti, reliquie, classi (per id), tratti |
| `class_xp`, `class_lvl` | Esperienza e livello di Maestria per classe |
| `stats` | `total_deaths`, `total_gold`, `total_bosses` |
| `completed_feats` | Imprese completate |
| `perks` | Livelli dei potenziamenti del Fuoco dell'Anima |
| `npc_unlocked` | Artigiani liberati |
| `starting_consumables` / `_weapons` / `_armors` / `_accessories` | Oggetti comprati nelle botteghe per la prossima discesa. Vengono svuotati all'inizio della partita, anche se un oggetto non si può costruire, così un dato difettoso non blocca le partite successive |
| `settings.text_speed` | `lenta`, `normale`, `veloce`, `istantanea` |

---

## 8. Aggiungere contenuti

- **Un'arma, un'armatura, un monile o un consumabile.** Aggiungi l'oggetto al JSON. Per renderlo sbloccabile alla Forgia dagli un `unlock_id` e un `unlock_cost`; con `unlock_cost: 0` lo si ottiene solo da un'impresa o da una Maestria che ne citi l'`unlock_id`. Una volta sbloccato compare anche nella bottega dell'artigiano.
- **Una reliquia.** Aggiungila a `relics.json`, scrivi la sua classe in `relic_effects.py`, registrala in `RELIC_REGISTRY` e aggiungi il suo contratto in `RelicContractTest`: un test fallisce se ne manca uno.
- **Un nemico o un boss.** Basta `enemies.json`: la sua forza (`base_hp × base_atk`) decide a che profondità compare.
- **Una classe.** Aggiungila a `classes.json` con le sue Maestrie e rendila sbloccabile da un'impresa o da una Maestria di tipo `class`. Gli effetti personali nuovi vanno controllati nel codice con `has_mastery_effect`.
- **Un evento.** Aggiungilo a `events.json`. Le azioni esistenti sono in `_handle_event_action` (`rooms.py`); un'azione nuova va aggiunta lì.
- **Una Risonanza o un tomo dell'Archivio.** Modifica `elements.json → resonance` o `books.json`.

Dopo ogni modifica alla logica o ai dati aggiungi o aggiorna i test (vedi `AGENTS.md`). Per i contenuti nuovi vuol dire anche: descrizione con i numeri reali e, se servono, i contratti in `tests/test_contracts.py`.

---

## 9. Test

```bash
python -m unittest discover -s tests
```

La CI (`.github/workflows/tests.yml`) li esegue su Python 3.9 e sull'ultima 3.x; su ogni pull request gira anche [rsp](https://github.com/fedeveloper/rsp). I test non salvano mai il profilo: lo modificano in memoria e lo ripristinano.

| File | Cosa copre |
|---|---|
| `test_data.py` | Coerenza dei JSON |
| `test_entities.py` | Generazione di oggetti, eroi, nemici; reliquie registrate |
| `test_mechanics.py` | Tratti, patti, Maestrie, ricompense di fine partita, profilo corrotto |
| `test_combat_design.py` | Risonanza dinamica, status a fine scontro, armi con status |
| `test_polish.py` | Messaggi di combattimento, Falò, Fuoco dell'Anima, limite di fuga |
| `test_features.py` | Velocità del testo, Speranza di Luce, Assassino e Negromante, probabilità di colpire |
| `test_depth.py` | Nemici e boss per profondità, boss finale, tratto e antidoto mostrati |
| `test_refactor.py` | Ciclo del turno, ridisegno dei menu, bonus nei dati, output tramite `ui`, etichette dei consumabili |
| `test_shops.py` | Botteghe degli artigiani, elenco della Forgia, Cuore di Drago |
| `test_contracts.py` | **Contratti descrizione ↔ effetto** per reliquie, armi, armature, monili (anche maledetti), consumabili, scelte degli eventi, tratti, patti, potenziamenti, Maestrie e imprese; ogni sbloccabile è ottenibile |

Oltre ai test automatici il gioco è stato provato al terminale vero, avviandolo in un pty e inviandogli tasti, con un profilo che sblocca tutto:
- tutte le combinazioni del menu pre-partita, provate nel banco di prova automatico;
- 112 partite al terminale, che coprono ogni classe e ogni tratto in entrambe le modalità e tutte le 32 combinazioni di Patti.
