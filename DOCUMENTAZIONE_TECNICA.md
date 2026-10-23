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
| `roguelike.py` | Punto d'ingresso (`main`). Menu principale, Impostazioni, Campo Base (Fuoco dell'Anima, Forgia, Taverna, Grimorio, botteghe), scelta di eroe/tratto e del grado di Ascensione (`_choose_ascension`), Sfida del Giorno (`daily_menu`, `daily_page`), ciclo dei piani (`play_game` → `_descent`) con la mappa e l'atmosfera del bioma, fine partita (`evaluate_run`), Maestria e imprese. |
| `floor_map.py` | Mappa del piano: file di stanze (`generate_row`), collegamenti e stanze speciali (`generate_floor_map`), percorsi (`reachable`), disegno (`render_map`) ed etichette (`room_label`). |
| `rooms.py` | `CombatSession` (turni, danni, status, Risonanze, fine scontro) e le stanze: mercante, falò, forziere, trappola, mistero. |
| `modes.py` | Modalità: regole della discesa in corso (`RUN`, `rule`, `combine`, `start_run`/`end_run`), gradi di Ascensione (`max_grade`, `ascension_rules`, `ascension_essence_mult`, `record_ascension_win`) e Sfida del Giorno (`daily_setup`, `daily_rules`, `daily_score`, `record_daily`, `daily_streak`). |
| `runes.py` | Rune e Incastoni: chiavi degli effetti (`RUNE_EFFECT_KEYS`), dati delle rune (`rune`, `fits`, `random_rune_id`), probabilità di drop (`roll_drop`), costo di estrazione, etichetta degli incastoni sul nome (`socket_tag`). |
| `camp.py` | Il Fuoco del Campo: personaggi presenti, frasi e doni (`talk`), strutture (`build`, `built`), dono dello Scrittoio a inizio run (`start_of_run_boon`). |
| `endings.py` | Finali: disponibili (`available_endings`), scelta e premio (`choose_ending`), registro in `profile.story.endings`. |
| `codex.py` | Il Codice del Labirinto: registra nemici visti e sconfitti, fasi dei boss, lettere e reliquie (`record_*`), calcola il completamento e mostra le pagine (`show_codex`). |
| `events.py` | Motore degli eventi narrativi: condizioni (`CONDITIONS`), effetti (`EFFECTS`), riepiloghi generati dagli effetti, scene a più passi (`event_room`), scelta dell'evento per le porte (`pick_event`), memoria fra le run e conseguenze differite (`pop_due_event`). |
| `entities.py` | `Player`, `Enemy`, gli oggetti (`Weapon`, `Armor`, `Accessory`, `Consumable`) e i generatori casuali. Applica tratti, Maestrie, potenziamenti e oggetti iniziali. Sceglie i nemici in base alla profondità (`pick_enemy_name`). |
| `relic_effects.py` | Una classe per reliquia, con gli hook che le servono; `RELIC_REGISTRY` collega l'id del JSON alla classe. |
| `inventory_menu.py` | Zaino, uso dei consumabili (`_use_consumable`), equipaggiamento e schermata delle statistiche. |
| `archive.py` | Tomi dell'Archivio: condizioni di sblocco e bonus (`get_archive_bonus`), letti una volta da `books.json`. |
| `data_manager.py` | Carica i JSON (`RAW_DATA`), filtra ciò che è sbloccato (`GAME_DATA`, ricalcolato da `update_game_data()`), gestisce il profilo (`PROFILE_MANAGER`). |
| `ui.py` | Terminale: colori ANSI, lettura dei tasti (Windows e POSIX), menu a frecce (`interactive_menu`), velocità del testo (`delay_print`, `set_text_speed`). |
| `constants.py` | Costanti di bilanciamento (precisione base, scaling, finestre di profondità, velocità del testo…). |

Dipendenze fra i moduli: `ui` ← `data_manager` ← `archive`/`relic_effects`/`codex`/`modes` ← `entities` ← `inventory_menu` ← `rooms` ← `events` ← `floor_map`/`camp`/`endings` ← `roguelike`. Nessun modulo importa da uno che sta alla sua destra.

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
| `enemies.json` | `enemies` e `bosses`, per nome | `element`, `base_hp`, `base_atk`, `base_dodge`, `base_acc`, `title`/`lore` (boss), `status_inflict` (opz.), `final_boss` (solo DIO ANTICO), `retired_by_flag` (opz.: il boss non compare più quando il flag del profilo è vero), `moves` (opz.: pesi delle mosse al posto di quelli predefiniti) |
| `weapons.json` | Armi | `name`, `base_atk`, `val_base` (opz.), `element` (opz., altrimenti casuale), `status_inflict` (opz.), `hit_modifier`, `crit_chance`, `gold_atk_per`/`gold_atk_max` (opz.), `unlock_id`, `unlock_cost`, `desc`, `flavor` |
| `armors.json` | Armature | `name`, `base_def`, `element` (opz.), `dodge_bonus` (opz.), `unlock_id`, `unlock_cost`, `desc`, `flavor` |
| `accessories.json` | Monili | `name`, `bonus_type` (`crit_chance`, `lifesteal`, `max_hp`, `dodge`, `acc`, `reflect`), `bonus_value`, `base_val`, `desc`, `lore`, `unlock_id`, `unlock_cost` |
| `consumables.json` | Consumabili | `name`, `category` (`heal`, `antidote`, `smoke_bomb`, `chaos_tome`, `chaos_vial`, `holy_water`, `whetstone`, `accuracy_potion`), `base_heal`, `val_base`, `desc`, `unlock_id` |
| `relics.json` | Reliquie | `id`, `name`, `desc`, `lore`, `unlock_id`, `unlock_cost` |
| `elements.json` | Sistema elementale | `list`, `icons`, `multipliers[attaccante][difensore]`, `resonance[elemento] = {value, desc, announce}`, `marks.duration`, `conditions` (`blind`, `slow`, `scorch_pct`), `reactions["A+B"] = {name, icon, desc, bonus_pct, status: {type, duration}}` |
| `books.json` | Tomi dell'Archivio | `title`, `unlock_condition` (testo), `unlock = {type: max_floor\|total_bosses\|won_normal, value}`, `bonus = {gold_pct, escape, boss_dmg_pct, def}`, `bonus_desc`, `chapters` |
| `meta.json` | Regole di contorno | `traits`, `pacts` (`name`, `desc`: gli effetti dei gradi di Ascensione con `pact`), `feats` (`target`, `reward_type`, `reward_id`), `mastery_xp_requirements`, `rooms.weights`/`rooms.cooldowns`, `corruption` (`max`, `atk_per_10`, `veil`, `voice`, `desc`) |
| `biomes.json` | Biomi | `id`, `name`, `icon`, `floors`, `intro`, `hazard`, `room_weights`, `enemy_elements`, `signature_events` (opzionali gli ultimi quattro) |
| `events.json` | Eventi narrativi | `title`, `start`, `scenes`, `requires` (opz.), `scripted` (opz.), `weight` (opz.): vedi [Eventi narrativi](#eventi-narrativi) |
| `moves.json` | Mosse dei nemici (intenti) | `moves` (`name`, `icon`, `desc`, `damage_mult`, `damage_taken_mult`, `heal_pct`), `defaults` (pesi di `enemy`, `boss`, `with_status`), `rules` (`heal_below_pct`, `max_heals`, `no_repeat`) |
| `story.json` | Elementi della storia | `quest_items` (oggetti chiave: `name`, `desc`), `npcs` (nomi degli artigiani), `characters` (personaggi ricorrenti: vedi sotto), `camp` (Fuoco del Campo), `endings` (finali) |
| `modes.json` | Modalità | `ascension` (`max`, `grades`: `name`, `desc`, `essence_bonus`, `effects`), `daily` (`maluses`, `first_attempt_essence_mult`, `history`, `score`, `boons`: `name`, `desc`, `effects`): vedi [Modalità](#modalità) |
| `phases.json` | Fasi dei boss | `bosses[nome] = [{at_pct, name, text, element, atk_mult, heal_pct, shield_pct, ward, status_inflict, moves}]`: vedi [Intenti e reazioni](#intenti-e-reazioni) |
| `runes.json` | Rune e parole runiche | `rules` (`sockets` per `normal`/`epic`/`boss`, `extract_cost` e `value` come [base, per piano], `drops` per fonte in %, `vendor_stock`); `runes[id] = {name, icon, family, slot (weapon/armor/any), weight, effects, desc}`; `words[id] = {name, runes, effects, desc}` |
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

### Eventi narrativi

Un evento è una piccola storia a **scene**. `start` indica la prima; ogni scena ha un `text`, delle `choices` e, se serve, degli `extra`: frasi aggiunte al testo solo quando le loro condizioni sono vere, per esempio "ci siamo già incontrati" se un contatore del profilo è almeno 1.

```json
"pozzo_desideri": {
  "title": "Il Pozzo dei Desideri", "start": "inizio",
  "scenes": {
    "inizio": {"text": "...", "choices": [
      {"text": "Getta una moneta", "effects": [{"gold": -30}], "next": "desiderio"},
      {"text": "Immergi la mano", "requires": {"trait": "midas"}, "effects": [{"gold": 60}, {"max_hp": -10}], "msg": "..."},
      {"text": "Pesca le monete", "requires": {"class": "2"}, "chance": 70, "success": [{"gold": 90}],
       "fail_effects": [{"damage": 25}], "msg": "...", "fail_msg": "..."},
      {"text": "Allontanati", "msg": "..."}
    ]},
    "desiderio": {"text": "...", "choices": ["..."]}
  }
}
```

**Campi di una scelta.**

| Campo | Significato |
|---|---|
| `text` | Il testo dell'opzione. **Senza numeri**: il riepilogo fra parentesi lo genera il gioco dagli effetti |
| `requires` | Condizioni per vederla. Se mancano la scelta è nascosta, oppure grigia e non selezionabile con `show_locked` (motivo in `locked_hint`). Classe, tratto, reliquia, oggetto chiave e patto compaiono come etichetta, ad esempio `[Mago]` |
| `effects` | Effetti applicati in ordine (con `chance` sono il costo, pagato prima del tiro) |
| `chance`, `success`, `fail_effects` | Probabilità di successo in % (1–99), effetti dei due esiti |
| `msg`, `fail_msg` | Racconto dell'esito. Senza `chance`, `msg` viene mostrato prima degli effetti |
| `next`, `fail_next` | Scena successiva; se manca, l'evento finisce |
| `hidden` | Non mostra il riepilogo degli effetti (sorpresa voluta) |

Una scelta che costa oro è grigia, con "(Oro insufficiente)", se non puoi pagarla.

**Condizioni** (`requires`, tutte in AND): `class`/`not_class` (id o lista), `trait`, `relic`, `quest_item`, `pact`, `gold`, `level`, `atk`, `dodge` (soglie minime), `hp_pct_below`, `min_floor`/`max_floor`, `flag`/`not_flag` (profilo), `run_flag`/`not_run_flag` (run), `counter` (`{"nome": soglia}`, almeno) e `counter_below` (`{"nome": soglia}`, meno di), `npc`/`not_npc`, `biome` (id del bioma del piano), `flags`/`any_flags` (liste di flag: tutti / almeno uno), `letters_complete`, `corruption` (almeno; etichetta `[Corruzione N+]`) e `corruption_below`. A livello di evento decidono se l'evento può uscire in una porta; vengono valutate anche senza l'eroe, contando solo piano e profilo.

**Effetti** (una chiave per voce, più eventuali parametri `level`, `floors`, `value`, `add`, `death_msg`, `gold_pct`):

| Effetto | Riepilogo | Note |
|---|---|---|
| `gold` | `+N Oro` / `-N Oro` | Guadagni triplicati da *Tocco di Mida* |
| `damage` | `-N HP` | Può uccidere; `death_msg` personalizza il messaggio |
| `heal`, `heal_pct` | `Cura N HP`, `Cura N% HP` | Bloccate da *Patto del Sangue* |
| `max_hp` | `±N HP Max` | |
| `atk`, `def` | `±N ATK`, `±N DIF` | Per il resto della discesa |
| `relic` | `Reliquia` | `random` o un id; se le possiedi tutte, +50 Oro |
| `weapon`, `armor` | `Arma Epica`, `Armatura` | `epic`/`normal`; `level` aggiunge piani al livello |
| `accessory`, `potion` | `Monile`, `N Pozioni` | |
| `fight` | `Combatti…` | `normal`, `hard`, `elite`. Gli effetti successivi arrivano solo se vinci; se fuggi l'evento finisce |
| `quest_item`, `take_quest_item` | `Oggetto chiave: …`, `Consuma: …` | Gli id stanno in `story.json` |
| `unlock_npc` | `Libera …` | Artigiano al Campo Base |
| `exp`, `essence` | `+N EXP`, `+N Essenza` | L'EXP passa dai moltiplicatori dell'eroe |
| `flag`, `counter` | nessuno | Memoria nel profilo, resta fra le run |
| `run_flag` | nessuno | Memoria della sola run |
| `later` | nessuno | `{"later": "evento", "floors": N}`: l'evento torna N piani dopo |
| `corruption` | `±N Corruzione` | Corruzione della run, fra 0 e `meta.corruption.max`; gli aumenti sono ridotti dall'Altare della Purificazione |
| `fall` | `Precipiti al piano successivo, -N% Oro` | `{"fall": true, "gold_pct": N}`: Caduta Astrale, chiude l'evento (vedi *Biomi*) |

**Scelta e memoria.** `pick_event` esclude gli eventi `scripted` e quelli con `requires` non soddisfatti, preferisce quelli non ancora visti nella run e usa `weight` (predefinito 1). Un evento `scripted` compare solo quando una scelta lo richiama con `later`: al piano giusto prende il posto della prima porta (mai del boss), con la scritta "✦ qualcosa ti stava aspettando". Flag, contatori e numero di incontri per evento (`story.seen_events`) vengono salvati alla fine di ogni evento.

### Personaggi ricorrenti e Codice

Un personaggio ricorrente (`story.json → characters`) è una catena di eventi legati da un contatore del profilo:

```json
"alaric": {"name": "Sir Alaric", "epithet": "il Primo Paladino", "counter": "alaric", "hint": "...",
           "chapters": [{"event": "alaric_porta", "text": "..."}, "..."],
           "notes": [{"flag": "alaric_lavanda", "text": "..."}]}
```

- Il capitolo *k* (da 0) è un evento con `requires: {"counter": {"alaric": k}, "counter_below": {"alaric": k + 1}}`. Le scelte che chiudono il capitolo hanno `{"counter": "alaric"}`; quelle che lo rimandano no.
- Dal secondo capitolo l'evento ha anche `not_run_flag: "alaric_visto"`, e le scelte che avanzano impostano quel `run_flag`: un solo capitolo per run.
- Nel Codice, `text` di ogni capitolo vissuto racconta la storia fin lì, e le `notes` compaiono quando il loro flag è vero. `hint` si vede finché il personaggio è sconosciuto.
- `retired_by_flag` su un boss chiude la storia anche in combattimento: liberando Alaric (`alaric_liberato`) il Cavaliere Oscuro esce dalla scelta dei boss.

Il **Codice** (`codex.py`) legge e scrive `profile.codex`:
- `enemies[nome] = {seen, killed}`, aggiornato da `CombatSession.start` e `on_enemy_death` con `Enemy.base_name` (il nome senza "(Potenziato)");
- `letters`, gli indici in `lore.json → letters`;
- `relics`, aggiornato da `Player.add_relic`.

Gli eventi visti e i personaggi vengono da `profile.story`. Il completamento conta i nemici sconfitti, i capitoli vissuti, gli eventi visti, le lettere e le reliquie trovate.

### Corruzione, finali e Fuoco del Campo

**Corruzione** (`Player.corruption`, solo per la run).
- *Come varia.* `add_corruption()` la tiene fra 0 e `max`. Con l'Altare costruito gli aumenti valgono `corruption_gain_pct`%.
- *Il potere.* `corruption_atk()` aggiunge `atk_per_10` ATK ogni 10 punti a `get_total_atk()`.
- *Sguardo Velato.* Con `veil.threshold` o più, `events.veiled()` nasconde il riepilogo di una scelta con probabilità `veil.chance`.
- *Voce del Labirinto.* Con `voice.threshold` o più, `choose_intent()` nasconde l'intento con probabilità `voice.chance`.
- Un test verifica che i numeri di `corruption.desc` siano questi.

**Finali** (`story.json → endings`).
- *Campi.* `id`, `title`, `hint` (per il Codice), `choice` (l'opzione nel menu), `requires`, `text` (paragrafi) e `reward.essence`.
- *Condizioni.* Sono le stesse degli eventi, valutate con l'eroe al piano 30: la Corruzione è quella della run, flag e lettere quelli del profilo.
- *Scelta.* Alla vittoria `play_game` chiama `choose_ending()`. Il finale scelto va in `profile.story.endings` (`{id: volte}`) e nel Codice.

**Fuoco del Campo** (`story.json → camp`).
- `characters`: `id`, `name`, `requires`, `lines` (la prima con condizioni vere; l'ultima, senza condizioni, è quella di riserva) e `gift` (`essence`, `text`), ricevuto una volta sola (flag `camp_dono_<id>`).
- `structures`: `id`, `name`, `cost`, `desc`, `requires`, `locked_hint`. Una volta costruite diventano il flag `camp_<id>`.
  - Il *Tavolo della Cartografa* fa mostrare a `floor_map.room_label` il titolo delle stanze speciali e degli eventi richiamati.
  - Lo *Scrittoio di Silas* ha i suoi `boons`, effetti degli eventi con riepilogo generato.
  - L'*Altare* ha `corruption_gain_pct`.
- Le condizioni del campo sono solo quelle del profilo (`PROFILE_CONDITIONS`).

## 4. Il ciclo di gioco

```text
main() ─▶ menu principale ─▶ play_game(infinite_mode, daily)
                                │
          _hero_selection() ────┤  classe e tratto (o quelli della Sfida del Giorno)
          _choose_ascension() ──┤  grado (dopo la prima vittoria)
          modes.start_run() ────┤  regole della discesa; modes.end_run() alla fine
          _descent(): Player(...), _apply_mode_start()
                                │
                                ▼
          per ogni piano: rigenerazione (Speranza di Luce)
            generate_floor_map(): 4 file di stanze + boss, bioma, stanze speciali
            per step 1..5: render_map() ─▶ scelta fra le stanze collegate ─▶ stanza
            (step 5 = boss; al piano 30 il boss è final_boss)
          piano superato: rest_heal() = (20+5·piano) × rest_heal_mult HP, max_floor aggiornato
                                ▼
          evaluate_run(): Essenza, Maestria, imprese, salvataggio
```

**Mappa del piano.** All'arrivo su un piano `generate_floor_map()` crea 4 file di stanze e il boss.
- Le file hanno 2 e 3 stanze alternate (2-3-2-3 o 3-2-3-2), in tre colonne (sinistra, centro, destra).
- Da una stanza si passa a quelle della fila successiva nella stessa colonna o in una accanto: i percorsi non si incrociano, nessuna stanza resta isolata e nessuna è un vicolo cieco.
- Il giocatore vede tutta la mappa (`render_map`): in verde il percorso fatto, in giallo le stanze raggiungibili ora, in grigio ciò che è ormai fuori strada.
- Le etichette sono centrate sulla loro colonna e i collegamenti uniscono i centri. Se il terminale è alto almeno `TALL_MAP_ROWS` righe (30), ogni collegamento occupa due righe e le diagonali si leggono come linee; altrimenti una sola, così mappa e menu stanno in 80×24.

**Tipi di stanza.**
- Ogni tipo ha un peso (`rooms.weights`) e un tempo di ricarica in file (`rooms.cooldowns`), applicati fila dopo fila. I pesi si calcolano all'arrivo sul piano: le reliquie con `modify_room_weights` contano dal piano successivo a quello in cui le trovi.
- In una fila i tipi sono diversi; solo lo scontro può ripetersi, quando i tempi di ricarica lasciano pochi tipi disponibili.
- Una trappola non esce mai nella stessa fila di un forziere o di un mercante.
- L'Élite esce solo dal piano `rooms.elite.from_floor` (2).

**Rischio e ricompensa** (`meta.json`, `rooms`). Nessuna stanza è gratuita e nessuna è solo una punizione; i numeri sono tutti nei dati:

| Chiave | Stanza | Regola |
|---|---|---|
| `elite` | 👺 Élite | `Enemy(modifier="elite")`: HP × `hp_mult`, ATK × `atk_mult`, Oro ed EXP × `reward_mult`. Alla morte: reliquia con `relic_chance`%, altrimenti un pezzo d'equipaggiamento (epico con `epic_chance`%) |
| `trap` | 💀 Trappola | `trap_chances()`: disinnescare = `disarm.base` + Precisione × `per_point`, correre = `dash.base` + Schivata × `per_point`, fra `min_chance` e `max_chance`. Chi la affronta prende sempre il bottino (equipaggiamento con `gear_chance`%, altrimenti un monile); se la prova fallisce subisce `trap_damage()`; disinnescando recupera `salvage_gold`. `trap_room` restituisce se la trappola è stata affrontata |
| `treasure` | 💎 Forziere | `chest_risks(piano)`: probabilità di `mimic` e `locked`, da `from_floor`, + `pct_per_floor` a piano, fino a `max`. Chiuso: costa `hp_cost_pct`% degli HP massimi. Mimic: indizio con `tell`% (falso allarme con `false_tell`% sui forzieri veri; il *Sesto Senso* non sbaglia). La mappa mostra il rischio totale (`d["risk"]`) |
| `mystery` | ❓ Mistero | `outcomes`: pesi degli esiti; `hoard_gold_mult` per il tesoro nascosto. `mystery_odds()` è ciò che mostra il *Sesto Senso* |
| `audacity` | — | `points` per tipo di stanza (la trappola solo se affrontata), azzerati all'inizio del piano in `Player.audacity`. `audacity_reward()` al boss: + `gold_pct_per_point`% del suo Oro per punto, equipaggiamento da `item_at`, epico da `epic_at` |

Il **Mimic** (`enemies.json`) ha `"lair": "treasure"`: non entra mai nelle scelte casuali né nel nemico tipico, e le sue statistiche sono quelle del nemico tipico del piano × `hp_mult`/`atk_mult`. `Enemy(..., name=...)` crea un nemico preciso.
- Un evento richiamato da `later` prende il posto di una stanza della prima fila. La stanza speciale del bioma va in una delle file centrali, al posto dell'evento della fila se ce n'è uno.

**Biomi** (`biomes.json`). Ogni bioma copre un intervallo di piani (`floors`) e ha `name`, `icon` e `intro` (una frase a caso, mostrata sopra la mappa). I campi opzionali ne fanno un luogo con regole proprie:
- `hazard` (`name`, `desc`): annunciato all'ingresso nel bioma;
- `room_weights`: moltiplicatori dei pesi delle stanze;
- `enemy_elements`: moltiplicatori della probabilità dei nemici di un elemento, dentro la finestra di profondità;
- `signature_events`: eventi `scripted`, uno per piano, segnati con l'icona del bioma. Se possibile non si ripete quello già visto nella run;
- `rules`: le regole del pericolo, ognuna con i suoi parametri (un test verifica che i numeri della `hazard.desc` siano questi):

| Regola | Parametri | Dove agisce |
|---|---|---|
| `silence` (Miniere) | `chance` | All'inizio di uno scontro (`CombatSession.silenced`): la Difesa diventa `def_type = "silenced"`, dimezza i danni senza la tecnica della classe |
| `dissolve` (Ventre) | `max_hp_pct` | All'arrivo su ogni piano (`floor_map.apply_biome_on_floor`): toglie HP massimi e li accumula in `Player.dissolved`, che si restituisce quando cambia il bioma |
| `boil` (Forgia) | `chance`, `gold_pct` | Dopo ogni colpo subito con danni (`_enemy_attack`) |
| `paradox` (Soglia) | `player_repeat`, `enemy_double` | In `_combat_loop`: un turno in più al giocatore, o una seconda mossa (non annunciata) al nemico |

La *Caduta Astrale* delle Guglie è invece un effetto degli eventi, `{"fall": true, "gold_pct": 40}`. Toglie l'Oro, imposta `Player.fallen` e chiude l'evento. `play_game` interrompe allora il piano e passa al successivo, senza boss e senza riposo; un test controlla che `fall` sia sempre l'ultimo effetto della sua lista.

I nemici e i boss con `"biome": "id"` (in `enemies.json`) sono **nativi**: compaiono solo in quel bioma, e lì si aggiungono sempre ai candidati della profondità. La condizione `biome` degli eventi vale nei piani del bioma. Tutti e sei i biomi hanno pericolo, stanze speciali, nativi, pesi delle stanze e affinità elementale.

**Nemici per profondità.** `pick_enemy_name()` ordina i candidati non nativi per `base_hp × base_atk` e sceglie in una finestra che sale con `(piano − 1) / 29`. La finestra è di `ENEMY_DEPTH_WINDOW` = 6 nemici e di `BOSS_DEPTH_WINDOW` = 5 boss. Vi si aggiungono i nativi del bioma; la scelta è pesata da `enemy_elements`. I boss con `final_boss` sono esclusi da questa scelta, e quelli con `retired_by_flag` spariscono quando il flag è vero.

**Statistiche dei nemici.** Partendo dai valori base, con `l = piano − 1`:

| | HP | ATK | Oro | EXP |
|---|---|---|---|---|
| Nemico | base + `ENEMY_HP_PER_FLOOR`·l ± 5 | base + `ENEMY_ATK_PER_FLOOR`·l + (0..1) | max(5, 5 + 3,5·piano) | 30 + 10·piano |
| Boss | HP tipico × `BOSS_HP_MULT` × qualità + (0..10) | ATK tipico × `BOSS_ATK_MULT` × qualità + (0..2) | 50 + 15·piano | 150 + 20·piano |

Il **nemico tipico** di un piano (`entities.typical_enemy`) è la media della finestra di profondità con la stessa crescita, salti di piano compresi. I boss ne sono un multiplo (2× gli HP, 1,8× l'ATK; le fasi aggiungono il resto della loro resistenza). I loro valori base diventano una **qualità**, `0,75 + 0,25 · base / media dei boss`, così si distinguono di circa ±25% a ogni piano: niente più boss di inizio partita fuori scala.

Poi si applicano, in ordine: ×1,2 dal piano 10; ×1,25 dal piano 20; ×1,4 (potenziato) o ×0,6 (debilitato) nella Stanza del Mistero, oppure i moltiplicatori dell'Élite; ×1,3 agli HP con *Durezza* e ×1,3 all'ATK con *Furia*.

---

**Equipaggiamento generato** (`generate_weapon`, `generate_armor`). Gli oggetti crescono con il nemico tipico del loro livello:

```text
ATK arma     = HP tipico / WEAPON_TARGET_HITS (3)        × qualità × caso(0,9–1,1)
DIF armatura = ATK tipico × ARMOR_TARGET_ABSORB (0,4)    × qualità × caso(0,9–1,1)
qualità arma     = 0,75 + base_atk / 60     (Spada Corta 0,80 … Lama del Creatore 1,25)
qualità armatura = 0,6  + base_def / 25     (Veste Eterea 0,60 … Egida del Titano 1,40)
poi: ×1,3 se maledetto, ×1,1 se di elemento Normale, ×1,35 se epico
```

Un'arma tipica abbatte un nemico tipico in circa 3 colpi e un'armatura tipica ne assorbe il 40% del colpo, a qualunque piano. La statistica base dei dati decide la qualità, non un bonus fisso: prima pesava tutta all'inizio (armature che annullavano ogni colpo per dieci piani, armi che abbattevano i nemici al primo colpo) e scompariva verso il fondo. `tests/test_balance.py` vieta di tornare indietro: nessuna arma sotto 1,5 colpi, nessuna armatura sopra il 75%, boss proporzionati al piano.

**Strumenti di bilanciamento** (`tools/bilanciamento.py`):
- `curve`: oggetti generabili contro nemici, piano per piano;
- `oggetti`: ogni arma e armatura a ogni piano;
- `run N nuovo|completo`: N run per classe con il codice vero e un giocatore automatico, con vittorie, piano raggiunto, Essenza, colpi annullati, morti per bioma e letalità dei boss;
- `ascensione N gradi`: profilo completo, N run per classe a ogni grado (es. `0,5,10,15,20`), con vittorie e piano mediano;
- `strategie N nuovo|completo`: le stesse run con diversi modi di scegliere le stanze (adattiva in base agli HP, prudente, aggressiva, trappole per prime). Serve a verificare che nessun ordine fisso domini: è la prova che la scelta della stanza è una decisione.

Il profilo del giocatore non viene mai toccato (il caricamento lo riscrive solo se va migrato da una versione precedente).

**README.** `README.md` si genera con `python tools/genera_readme.py`: il testo è nello script, tabelle e numeri vengono da `data/`. `tests/test_docs.py` fallisce se il README non è aggiornato, quindi va rigenerato in ogni PR che cambia i dati.

### Rune e Incastoni

`Weapon` e `Armor` hanno `sockets` (incastoni) e `runes` (id incastonati); il nome mostra `⟨icone◇⟩` (`runes.socket_tag`). I generatori danno `normal` incastoni, gli epici `epic` (`set_sockets`), il drop leggendario dei boss `boss`. Le rune nello zaino sono oggetti `Rune` (`type = "rune"`), create da `generate_rune`. `Player.rune_value(chiave)` somma un effetto sulle rune dell'arma e dell'armatura **equipaggiate**:

| Effetto | Dove agisce |
|---|---|
| `atk_pct`, `def_pct` | `get_total_atk` (% dell'ATK dell'arma), `get_total_def` (% della DIF dell'armatura) |
| `crit_chance_add`, `dodge_add` | `get_crit_chance`, `get_dodge` |
| `gold_pct`, `exp_pct` | `calculate_gold_gain`, `gain_exp` |
| `mark_duration_add`, `reaction_dmg_pct` | `apply_element`, `_trigger_reaction` |
| `super_effective_pct`, `first_strike_pct`, `lifesteal_pct`, `bleed_on_hit`, `poison_on_hit` | `execute_player_attack` (primo attacco dello scontro, colpi a segno; gli status durano 3 turni) |
| `thorns_pct` | `_enemy_attack`, insieme al riflesso dei monili |
| `defend_heal_pct` | `execute_player_defense` |
| `trap_chance_add` | `rooms.trap_chances` |
| `audacity_start` | Audacia all'inizio di ogni piano (`roguelike`) |

Il Falò ha `rune_workshop` (`RUNE_WORKSHOP`): incastonare (gratis, nell'arma o nell'armatura con un incastone libero adatto allo `slot`) ed estrarre (`extract_cost`); non spegne il falò. `rune_drop(player, piano, fonte)` lascia una runa con la probabilità di `drops[fonte]` (Élite, boss, trappola, tesoro del Mistero, Mimic) e la registra nel Codice (`record_rune`, pagina *Rune*). La fusione dell'Altare tiene le rune della base e rimette nello zaino quelle del sacrificio.

**Parole runiche** (`runes.json`, `words[id] = {name, runes, effects, desc}`). `runes.active_words(oggetto)` trova le parole composte dalle rune di un oggetto: prima le più lunghe, poi nell'ordine dei dati, e ogni runa vale per una sola parola. `runes.item_effects` restituisce gli effetti delle rune più quelli delle parole, e `Player.rune_value` li somma, quindi una parola usa le stesse chiavi delle rune. Due chiavi esistono solo nelle parole: `scorch_on_hit` e `stun_on_hit` (con `bleed_on_hit` e `poison_on_hit` in `ON_HIT_STATUSES`: status, chiave, turni). Il nome dell'oggetto mostra le parole fra «». Il laboratorio del Falò annuncia una parola appena composta e la registra nel Codice (`record_runeword`, pagina *Parole runiche*).

### Modalità

`modes.py` e `data/modes.json`. Ascensione e Sfida del Giorno cambiano una discesa con gli stessi **effetti**: `combine()` li somma in un dizionario di regole, `start_run()` lo rende attivo in `modes.RUN` e `modes.rule(chiave)` lo legge dove serve. Fuori da una discesa (e nei test) le regole sono neutre; `play_game` chiama sempre `end_run()` alla fine, anche se la discesa si interrompe con un errore.

| Effetto | Tipo | Dove agisce |
|---|---|---|
| `room_weights` | moltiplicatori per tipo di stanza | `roguelike.floor_room_weights`, dopo le reliquie |
| `rest_heal_mult` | × | `roguelike.rest_heal`, riposo prima delle scale |
| `campfire_heal_mult` | × | Falò: riposo = `CAMPFIRE_REST_PCT` (50) × valore, % degli HP massimi |
| `boss_hp_mult`, `boss_atk_mult`, `final_boss_hp_mult` | × | `Enemy` (boss; l'ultimo solo per il `final_boss`) |
| `enemy_hp_mult`, `elite_hp_mult` | × | `Enemy` (non boss; il secondo solo con `modifier="elite"`) |
| `enemy_atk_mult` | × | `Enemy`, tutti |
| `enemy_acc_add` | + | `Enemy.base_acc` |
| `enemy_gold_mult` | × | `Enemy.gold_drop` |
| `chest_risk_mult` | × | `rooms.chest_risks`, con un tetto del 50% per tipo |
| `curse_chance_mult` | × | `CURSE_CHANCE` dei generatori di armi, armature e monili |
| `start_gold_mult`, `start_gold_add`, `start_corruption`, `start_relic`, `start_potions_add` | ×, + | `roguelike._apply_mode_start`, a inizio discesa |
| `pact` | id di un patto | aggiunto a `active_pacts` (effetti già esistenti: `carestia`, `inflazione`, `trappole`) |

**Ascensione.** I gradi sono cumulativi: `ascension_rules(n)` combina gli effetti dei primi `n`. L'Essenza finale è moltiplicata per `1 + Σ essence_bonus`. `max_grade()` è 0 senza vittorie, poi `profile.ascension.best_win + 1`; una vittoria della discesa standard (non della Sfida) chiama `record_ascension_win(grado)`. I vecchi patti `durezza` e `furia` non esistono più: sono diventati gli effetti `enemy_hp_mult`/`boss_hp_mult` ed `enemy_atk_mult` dei gradi omonimi, con valori più leggeri perché si sommano agli altri gradi. La curva dei gradi si misura con `tools/bilanciamento.py ascensione`.

**Sfida del Giorno.** `daily_setup(data)` usa un `random.Random` con il seme `AAAAMMGG`: classe e tratto (fra tutti, anche non sbloccati), `maluses` gradi distinti e un dono. `play_game(daily=setup)` salta la scelta dell'eroe e del grado, imposta `random.seed(seme)` all'inizio e `random.seed(seme·100 + piano)` prima di generare ogni piano: la mappa di un piano non dipende dalla strada fatta. `evaluate_run` registra solo il primo tentativo (`record_daily`) e gli dà `first_attempt_essence_mult`; `daily_streak` conta i giorni consecutivi. La Sfida non sblocca gradi di Ascensione.

`tests/test_modes.py` ha un contratto per ogni chiave di effetto e controlla che ogni descrizione contenga i numeri dei suoi effetti; `tests/test_docs.py` controlla che il Manuale elenchi gradi e doni come sono nei dati.

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
1. `max(grezzo − difesa, ⌈grezzo × MIN_DAMAGE_PCT⌉)`, con `grezzo = (ATK nemico ridotto dall'Acqua ± caso) × elemento × mossa`. La difesa somma armatura, Terra, Eredità e Archivio. **La difesa non annulla mai un colpo**: ne resta sempre almeno il 20%; solo le reliquie (es. lo Scudo di Cristallo) possono azzerarlo;
2. dimezzati se ti stai difendendo;
3. modificati dagli hook `on_take_damage` delle reliquie (scudi, riflessi…).

**Stati e maledizioni**: veleno `max(3, 4% degli HP massimi)` a turno, per l'eroe e per i nemici; sanguinamento 5% degli HP; la maledizione che drena vita toglie `max(2, 2% degli HP massimi)` a turno. Il *Riparo Magico* cura il 10% degli HP, il *Baluardo della Fede* il 5% in più.

**Fuga**: `20 + schivata − schivata nemico + 20 (Scarpisti) + bonus dell'Archivio`, limitata fra 10 e 90; con la *Bussola Perfetta* è 100. Impossibile dai boss.

**Elementi**: `elements.json → multipliers`; 1,5 Super Efficace, 0,5 Poco efficace, 1 altrimenti. Le reliquie possono modificarli con `modify_multiplier`.

**Livello dell'eroe**: soglia iniziale 100 EXP, ×1,5 a ogni livello; a ogni livello +15 HP massimi, cura completa, +2 precisione e +2 schivata.

---

### Intenti e reazioni

**Intenti.**
- *Quando si sceglie.* All'inizio del turno del giocatore `CombatSession.choose_intent()` chiede la mossa a `Enemy.choose_move()`; un nemico con lo status `stun` annuncia "Congelato". La mossa si sceglie a peso:
  - `Enemy.moves` sono i pesi dei dati, oppure `defaults` più `with_status` se il nemico infligge uno status;
  - niente `heal` sopra `heal_below_pct` degli HP o dopo `max_heals`;
  - niente `venom` senza status;
  - nessuna mossa di `no_repeat` due volte di fila.
- *Cosa vede il giocatore.* Il prompt mostra `intent_text()`. Per gli attacchi riporta i danni previsti da `estimate_enemy_damage()`: la stessa formula dell'attacco, senza il tiro casuale, la difesa attiva e le reliquie.
- *Come si risolve.* `enemy_turn()` esegue la mossa e la consuma:
  - `attack`, `heavy` (`damage_mult` sulla forza, prima della difesa) e `venom` (status garantito) passano da `_enemy_attack`;
  - `guard` non attacca, e durante il turno del giocatore `damage_taken_mult` riduce i suoi colpi;
  - `heal` cura `heal_pct` degli HP massimi;
  - `drain` è un attacco che poi cura il nemico di `heal_ratio` × i danni inflitti;
  - `seal` imposta `CombatSession.sealed`: al turno seguente la Difesa è sigillata (sceglierla non consuma il turno), poi `_combat_loop` lo azzera;
  - `charge` imposta `Enemy.charged`: la prossima `choose_move()` restituisce sempre `unleash` (`damage_mult` 3), che non compare mai nei pesi;
  - `shield` aggiunge a `Enemy.shield` `shield_pct` degli HP massimi; lo scudo assorbe i danni degli attacchi dell'eroe (`_absorb`), non quelli di status, reazioni o riflessi.
- Senza intento (es. nei test) il nemico attacca.

**Fasi dei boss** (`data/phases.json`, `bosses[nome] = [fase, ...]`). `Enemy.phases` sono le fasi del boss in ordine di `at_pct` decrescente; `Enemy.phase` conta quelle attraversate. `CombatSession.check_phase()` gira all'inizio di ogni giro e dopo il turno del giocatore: finché gli HP sono ≤ `at_pct`% e il boss è vivo, entra nella fase successiva, la annuncia, la registra nel Codice (`record_phase`) e ne applica gli effetti con `_apply_phase`. Se la fase scatta dopo il turno del giocatore, l'intento diventa `transform` e il boss usa il suo turno per trasformarsi. Effetti di una fase (tutti opzionali, almeno uno):

| Chiave | Effetto |
|---|---|
| `element` | Nuovo elemento (il marchio si azzera); `"counter"` sceglie l'elemento con il moltiplicatore più alto contro l'armatura dell'eroe |
| `atk_mult` | ATK × valore |
| `heal_pct` | Cura del valore % degli HP massimi |
| `shield_pct` | Scudo del valore % degli HP massimi |
| `ward` | Scaglie: gli attacchi dell'eroe fanno × valore, finché una reazione (`_trigger_reaction`) non le infrange |
| `status_inflict` | Nuovo status dei suoi colpi (`type`, `chance`, `duration`) |
| `moves` | Nuovi pesi delle mosse (deve esserci `attack`; mai `unleash`) |

Un colpo che porta il boss a 0 HP non fa scattare la fase. Il Codice ha la sezione *Fasi dei boss* (`codex.phases_page`), contata nel completamento.

**Marchi e reazioni.**
- *Il marchio.* `apply_element(elemento)` marchia il nemico (`Enemy.mark = [elemento, marks.duration]`). Lo chiamano il colpo a segno del giocatore, con l'elemento dell'arma, e l'attacco a segno del nemico mentre il giocatore è in guardia, con l'elemento dell'armatura. `Normale` non marchia.
- *La reazione.* Se il nemico ha già un marchio di un altro elemento e la coppia è in `reactions` (in qualsiasi ordine), scatta `_trigger_reaction`: danni pari a `bonus_pct` del `get_total_atk()`, poi lo `status`. Il marchio si consuma e la scoperta finisce nel Codice. Senza reazione il marchio viene sostituito; con lo stesso elemento si rinnova.
- *Gli effetti di controllo.* `stun` fa saltare il turno del nemico. `blind` toglie `conditions.blind` alla precisione nemica, `slow` toglie `conditions.slow` alla schivata nemica. Scadono, come il marchio, alla fine del turno del nemico (`_tick_enemy_conditions`). `scorch` è un danno nel tempo (`scorch_pct` degli HP massimi) che segue le regole di veleno e sanguinamento.

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
| `essence`, `max_floor`, `won_normal` | Essenza, piano più profondo raggiunto, vittoria standard ottenuta (sblocca Ascensione e Modalità Infinita) |
| `ascension` | `best_win`: il grado più alto vinto; è disponibile fino a `best_win + 1` (massimo 20) |
| `daily` | Sfide del Giorno registrate, per data ISO: `score`, `floor`, `won`, `class` (solo il primo tentativo; ultime `history` date) |
| `unlocked_ids` | Tutti gli sblocchi: oggetti, reliquie, classi (per id), tratti |
| `class_xp`, `class_lvl` | Esperienza e livello di Maestria per classe |
| `stats` | `total_deaths`, `total_gold`, `total_bosses` |
| `completed_feats` | Imprese completate |
| `perks` | Livelli dei potenziamenti del Fuoco dell'Anima |
| `story` | Memoria del Labirinto: `flags` (anche strutture `camp_<id>` e doni `camp_dono_<id>`), `counters`, `seen_events` (incontri per evento), `endings` (finali visti) |
| `codex` | Codice: `enemies` (`seen`/`killed` per nome, `phases` per i boss: fasi viste), `letters` (indici), `relics` (id), `reactions` (chiavi `"A+B"`), `runes` (id), `runewords` (id) |
| `npc_unlocked` | Artigiani liberati |
| `starting_consumables` / `_weapons` / `_armors` / `_accessories` | Oggetti comprati nelle botteghe per la prossima discesa. Vengono svuotati all'inizio della partita, anche se un oggetto non si può costruire, così un dato difettoso non blocca le partite successive |
| `settings.text_speed` | `lenta`, `normale`, `veloce`, `istantanea` |

---

## 8. Aggiungere contenuti

- **Un'arma, un'armatura, un monile o un consumabile.** Aggiungi l'oggetto al JSON. Per renderlo sbloccabile alla Forgia dagli un `unlock_id` e un `unlock_cost`; con `unlock_cost: 0` lo si ottiene solo da un'impresa o da una Maestria che ne citi l'`unlock_id`. Una volta sbloccato compare anche nella bottega dell'artigiano.
- **Una reliquia.** Aggiungila a `relics.json`, scrivi la sua classe in `relic_effects.py`, registrala in `RELIC_REGISTRY` e aggiungi il suo contratto in `RelicContractTest`: un test fallisce se ne manca uno.
- **Un nemico o un boss.** Basta `enemies.json`: la sua forza (`base_hp × base_atk`) decide a che profondità compare.
- **Una classe.** Aggiungila a `classes.json` con le sue Maestrie e rendila sbloccabile da un'impresa o da una Maestria di tipo `class`. Gli effetti personali nuovi vanno controllati nel codice con `has_mastery_effect`.
- **Un evento.** Aggiungilo a `events.json` con condizioni ed effetti esistenti: di solito non serve toccare il codice. Un effetto o una condizione nuovi vanno aggiunti a `EFFECTS`/`CONDITIONS` in `events.py` e al contratto in `EventContractTest`. I test controllano che ogni scena sia raggiungibile, che abbia sempre un'uscita senza requisiti, che ogni oggetto chiave serva a qualcosa e che ogni evento `scripted` venga richiamato.
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
| `test_runes.py` | Rune e parole runiche (dati, stesso oggetto, precedenza delle parole lunghe, annuncio e Codice, effetti solo delle parole): dati, un contratto per ogni effetto, incastoni per rarità ed equipaggiamento iniziale, nome, drop dei boss, solo l'equipaggiamento conta; laboratorio del Falò (incastonare gratis e nello slot giusto, oggetto pieno, estrarre a pagamento, falò acceso); fusione; drop per fonte; Mercante; Codice |
| `test_boss_phases.py` | Fasi dei boss: dati di tutti i boss, contratto di ogni effetto (soglia e unicità, elemento e contro-elemento, cura, scudo, Scaglie e reazione, status, mosse, annuncio), turno di trasformazione, Codice, soglie multiple, colpo letale, nemici senza fasi |
| `test_modes.py` | Modalità: contratto e testo di ogni effetto, gradi cumulativi e sblocco, menu del grado, Essenza, regole nella vera discesa e pulizia; Sfida del Giorno (stessa sfida nello stesso giorno, regole, primo tentativo, storico e serie, Essenza, mappe uguali qualunque strada, schermata, statistiche) |
| `test_docs.py` | Il Manuale elenca gradi di Ascensione e doni della Sfida come nei dati |
| `test_mechanics.py` | Tratti, patti, Maestrie, ricompense di fine partita, profilo corrotto |
| `test_combat_design.py` | Risonanza dinamica, status a fine scontro, armi con status |
| `test_polish.py` | Messaggi di combattimento, Falò, Fuoco dell'Anima, limite di fuga |
| `test_features.py` | Velocità del testo, Speranza di Luce, Assassino e Negromante, probabilità di colpire |
| `test_depth.py` | Nemici e boss per profondità, boss finale, tratto e antidoto mostrati |
| `test_refactor.py` | Ciclo del turno, ridisegno dei menu, bonus nei dati, output tramite `ui`, etichette dei consumabili |
| `test_shops.py` | Botteghe degli artigiani, elenco della Forgia, Cuore di Drago |
| `test_balance.py` | Invarianti di bilanciamento: armi fra 1,5 e 5 colpi per il nemico tipico, armature sotto il 75% del colpo, qualità che mantiene il rango a ogni piano, nemico tipico fedele ai nemici veri, boss proporzionati al piano, difesa che non annulla mai un colpo, maledizione e veleno in % degli HP |
| `test_endgame.py` | Corruzione (limiti, ATK, contratto della descrizione, Sguardo Velato, Voce del Labirinto, opzioni proibite, statistiche), finali (dati, condizioni, scelta e premio, vittoria nel vero ciclo), Fuoco del Campo (dati, personaggi e doni, strutture, Tavolo, Scrittoio, Altare, menu) |
| `test_biomes.py` | Equipaggiamento iniziale (reazione o Risonanza), completezza dei biomi, contratti dei pericoli, Gas del Silenzio, Ebollizione, Paradosso, Dissoluzione, Caduta Astrale nel vero ciclo dei piani |
| `test_tactics.py` | Intenti (pesi predefiniti e dei dati, regole delle mosse, prompt, Congelato) e reazioni (arma poi armatura, armatura poi arma, solo in guardia, stesso elemento, nessuna reazione, scadenza dei marchi, Codice) |
| `test_map.py` | Mappa (file alternate, collegamenti senza incroci né vicoli ciechi, tipi e tempi di ricarica, evento richiamato, disegno, ciclo dei piani reale) e biomi (copertura dei piani, dati, nativi, elementi, pesi delle stanze, stanza speciale per piano, Prima Pietra, annuncio del pericolo) |
| `test_risk_rooms.py` | Stanze a rischio: trappola (ritirata, bottino garantito, prove e probabilità mostrate), forziere (rischio per piano, serratura, Mimic, Sesto Senso), Élite (piano minimo, statistiche, ricompensa, etichette), Audacia (punti, premio del boss, ciclo dei piani), Mistero (probabilità dai dati, reliquia esaurita) |
| `test_codex.py` | Codice (registrazione, pagine, completamento, menu) e personaggi ricorrenti (catena dei capitoli, un capitolo per run, boss ritirato, indizio della lavanda) |
| `test_events.py` | Motore degli eventi: integrità dei dati, opzioni con etichetta e bloccate, scene a più passi, fuga e morte, memoria fra le run, conseguenze differite, scelta degli eventi |
| `test_contracts.py` | **Contratti descrizione ↔ effetto** per mosse dei nemici e stima dei danni, reazioni elementali ed effetti di controllo, reliquie, armi, armature, monili (anche maledetti), consumabili, scelte degli eventi, tratti, patti, potenziamenti, Maestrie e imprese; ogni sbloccabile è ottenibile |

Oltre ai test automatici il gioco è stato provato al terminale vero, avviandolo in un pty e inviandogli tasti, con un profilo che sblocca tutto:
- tutte le combinazioni del menu pre-partita, provate nel banco di prova automatico;
- 112 partite al terminale, che coprono ogni classe e ogni tratto in entrambe le modalità e tutte le 32 combinazioni di Patti.
