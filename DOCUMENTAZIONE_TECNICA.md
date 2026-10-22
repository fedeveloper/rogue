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
| `roguelike.py` | Punto d'ingresso (`main`). Menu principale, Impostazioni, Campo Base (Fuoco dell'Anima, Forgia, Taverna, Grimorio, botteghe), scelta di eroe/tratto/patti, ciclo dei piani (`play_game`) con la mappa e l'atmosfera del bioma, fine partita (`evaluate_run`), Maestria e imprese. |
| `floor_map.py` | Mappa del piano: file di stanze (`generate_row`), collegamenti e stanze speciali (`generate_floor_map`), percorsi (`reachable`), disegno (`render_map`) ed etichette (`room_label`). |
| `rooms.py` | `CombatSession` (turni, danni, status, Risonanze, fine scontro) e le stanze: mercante, falò, forziere, trappola, mistero. |
| `codex.py` | Il Codice del Labirinto: registra nemici visti e sconfitti, lettere e reliquie (`record_*`), calcola il completamento e mostra le pagine (`show_codex`). |
| `events.py` | Motore degli eventi narrativi: condizioni (`CONDITIONS`), effetti (`EFFECTS`), riepiloghi generati dagli effetti, scene a più passi (`event_room`), scelta dell'evento per le porte (`pick_event`), memoria fra le run e conseguenze differite (`pop_due_event`). |
| `entities.py` | `Player`, `Enemy`, gli oggetti (`Weapon`, `Armor`, `Accessory`, `Consumable`) e i generatori casuali. Applica tratti, Maestrie, potenziamenti e oggetti iniziali. Sceglie i nemici in base alla profondità (`pick_enemy_name`). |
| `relic_effects.py` | Una classe per reliquia, con gli hook che le servono; `RELIC_REGISTRY` collega l'id del JSON alla classe. |
| `inventory_menu.py` | Zaino, uso dei consumabili (`_use_consumable`), equipaggiamento e schermata delle statistiche. |
| `archive.py` | Tomi dell'Archivio: condizioni di sblocco e bonus (`get_archive_bonus`), letti una volta da `books.json`. |
| `data_manager.py` | Carica i JSON (`RAW_DATA`), filtra ciò che è sbloccato (`GAME_DATA`, ricalcolato da `update_game_data()`), gestisce il profilo (`PROFILE_MANAGER`). |
| `ui.py` | Terminale: colori ANSI, lettura dei tasti (Windows e POSIX), menu a frecce (`interactive_menu`), velocità del testo (`delay_print`, `set_text_speed`). |
| `constants.py` | Costanti di bilanciamento (precisione base, scaling, finestre di profondità, velocità del testo…). |

Dipendenze fra i moduli: `ui` ← `data_manager` ← `archive`/`relic_effects`/`codex` ← `entities` ← `inventory_menu` ← `rooms` ← `events` ← `floor_map` ← `roguelike`. Nessun modulo importa da uno che sta alla sua destra.

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
| `meta.json` | Regole di contorno | `traits`, `pacts` (`bonus` di Essenza), `feats` (`target`, `reward_type`, `reward_id`), `mastery_xp_requirements`, `rooms.weights`/`rooms.cooldowns` |
| `biomes.json` | Biomi | `id`, `name`, `icon`, `floors`, `intro`, `hazard`, `room_weights`, `enemy_elements`, `signature_events` (opzionali gli ultimi quattro) |
| `events.json` | Eventi narrativi | `title`, `start`, `scenes`, `requires` (opz.), `scripted` (opz.), `weight` (opz.): vedi [Eventi narrativi](#eventi-narrativi) |
| `moves.json` | Mosse dei nemici (intenti) | `moves` (`name`, `icon`, `desc`, `damage_mult`, `damage_taken_mult`, `heal_pct`), `defaults` (pesi di `enemy`, `boss`, `with_status`), `rules` (`heal_below_pct`, `max_heals`, `no_repeat`) |
| `story.json` | Elementi della storia | `quest_items` (oggetti chiave: `name`, `desc`), `npcs` (nomi degli artigiani), `characters` (personaggi ricorrenti: vedi sotto) |
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

**Condizioni** (`requires`, tutte in AND): `class`/`not_class` (id o lista), `trait`, `relic`, `quest_item`, `pact`, `gold`, `level`, `atk`, `dodge` (soglie minime), `hp_pct_below`, `min_floor`/`max_floor`, `flag`/`not_flag` (profilo), `run_flag`/`not_run_flag` (run), `counter` (`{"nome": soglia}`, almeno) e `counter_below` (`{"nome": soglia}`, meno di), `npc`/`not_npc`, `biome` (id del bioma del piano). A livello di evento decidono se l'evento può uscire in una porta; vengono valutate anche senza l'eroe, contando solo piano e profilo.

**Effetti** (una chiave per voce, più eventuali parametri `level`, `floors`, `value`, `add`, `death_msg`):

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

## 4. Il ciclo di gioco

```text
main() ─▶ menu principale ─▶ play_game(infinite_mode)
                                │
          _hero_selection() ────┤  classe, tratto, patti
          Player(...)           │
                                ▼
          per ogni piano: rigenerazione (Speranza di Luce)
            generate_floor_map(): 4 file di stanze + boss, bioma, stanze speciali
            per step 1..5: render_map() ─▶ scelta fra le stanze collegate ─▶ stanza
            (step 5 = boss; al piano 30 il boss è final_boss)
          piano superato: +20+5·piano HP, max_floor aggiornato
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
- Un evento richiamato da `later` prende il posto di una stanza della prima fila. La stanza speciale del bioma va in una delle file centrali, al posto dell'evento della fila se ce n'è uno.

**Biomi** (`biomes.json`). Ogni bioma copre un intervallo di piani (`floors`) e ha `name`, `icon` e `intro` (una frase a caso, mostrata sopra la mappa). I campi opzionali ne fanno un luogo con regole proprie:
- `hazard` (`name`, `desc`): annunciato all'ingresso nel bioma;
- `room_weights`: moltiplicatori dei pesi delle stanze;
- `enemy_elements`: moltiplicatori della probabilità dei nemici di un elemento, dentro la finestra di profondità;
- `signature_events`: eventi `scripted`, uno per piano, segnati con l'icona del bioma. Se possibile non si ripete quello già visto nella run.

I nemici e i boss con `"biome": "id"` (in `enemies.json`) sono **nativi**: compaiono solo in quel bioma, e lì si aggiungono sempre ai candidati della profondità. La condizione `biome` degli eventi vale nei piani del bioma. Oggi ha tutte le regole *I Chiostri del Rimpianto* (piani 1–5); gli altri cinque biomi hanno nome, icona e atmosfera.

**Nemici per profondità.** `pick_enemy_name()` ordina i candidati non nativi per `base_hp × base_atk` e sceglie in una finestra che sale con `(piano − 1) / 29`. La finestra è di `ENEMY_DEPTH_WINDOW` = 6 nemici e di `BOSS_DEPTH_WINDOW` = 5 boss. Vi si aggiungono i nativi del bioma; la scelta è pesata da `enemy_elements`. I boss con `final_boss` sono esclusi da questa scelta, e quelli con `retired_by_flag` spariscono quando il flag è vero.

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
  - `heal` cura `heal_pct` degli HP massimi.
- Senza intento (es. nei test) il nemico attacca.

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
| `essence`, `max_floor`, `won_normal` | Essenza, piano più profondo raggiunto, vittoria standard ottenuta (sblocca Patti e Modalità Infinita) |
| `unlocked_ids` | Tutti gli sblocchi: oggetti, reliquie, classi (per id), tratti |
| `class_xp`, `class_lvl` | Esperienza e livello di Maestria per classe |
| `stats` | `total_deaths`, `total_gold`, `total_bosses` |
| `completed_feats` | Imprese completate |
| `perks` | Livelli dei potenziamenti del Fuoco dell'Anima |
| `story` | Memoria del Labirinto: `flags`, `counters`, `seen_events` (incontri per evento) |
| `codex` | Codice: `enemies` (`seen`/`killed` per nome), `letters` (indici), `relics` (id), `reactions` (chiavi `"A+B"`) |
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
| `test_mechanics.py` | Tratti, patti, Maestrie, ricompense di fine partita, profilo corrotto |
| `test_combat_design.py` | Risonanza dinamica, status a fine scontro, armi con status |
| `test_polish.py` | Messaggi di combattimento, Falò, Fuoco dell'Anima, limite di fuga |
| `test_features.py` | Velocità del testo, Speranza di Luce, Assassino e Negromante, probabilità di colpire |
| `test_depth.py` | Nemici e boss per profondità, boss finale, tratto e antidoto mostrati |
| `test_refactor.py` | Ciclo del turno, ridisegno dei menu, bonus nei dati, output tramite `ui`, etichette dei consumabili |
| `test_shops.py` | Botteghe degli artigiani, elenco della Forgia, Cuore di Drago |
| `test_tactics.py` | Intenti (pesi predefiniti e dei dati, regole delle mosse, prompt, Congelato) e reazioni (arma poi armatura, armatura poi arma, solo in guardia, stesso elemento, nessuna reazione, scadenza dei marchi, Codice) |
| `test_map.py` | Mappa (file alternate, collegamenti senza incroci né vicoli ciechi, tipi e tempi di ricarica, evento richiamato, disegno, ciclo dei piani reale) e biomi (copertura dei piani, dati, nativi, elementi, pesi delle stanze, stanza speciale per piano, Prima Pietra, annuncio del pericolo) |
| `test_codex.py` | Codice (registrazione, pagine, completamento, menu) e personaggi ricorrenti (catena dei capitoli, un capitolo per run, boss ritirato, indizio della lavanda) |
| `test_events.py` | Motore degli eventi: integrità dei dati, opzioni con etichetta e bloccate, scene a più passi, fuga e morte, memoria fra le run, conseguenze differite, scelta degli eventi |
| `test_contracts.py` | **Contratti descrizione ↔ effetto** per mosse dei nemici e stima dei danni, reazioni elementali ed effetti di controllo, reliquie, armi, armature, monili (anche maledetti), consumabili, scelte degli eventi, tratti, patti, potenziamenti, Maestrie e imprese; ogni sbloccabile è ottenibile |

Oltre ai test automatici il gioco è stato provato al terminale vero, avviandolo in un pty e inviandogli tasti, con un profilo che sblocca tutto:
- tutte le combinazioni del menu pre-partita, provate nel banco di prova automatico;
- 112 partite al terminale, che coprono ogni classe e ogni tratto in entrambe le modalità e tutte le 32 combinazioni di Patti.
