# Walkthrough: Accessori e Risonanza Elementale

## Panoramica
Sono stati implementati due nuovi sistemi di personalizzazione delle build:

1. **Slot Monile (Accessori)** — Un terzo slot equipaggiamento con effetti passivi unici.
2. **Risonanza Elementale** — Bonus potenti quando Arma e Armatura condividono lo stesso elemento.

---

## 1. Slot Monile (Accessori)

### Come funziona
- Il giocatore ha ora 3 slot: **Arma**, **Armatura**, **Monile**.
- I Monili si trovano dal Mercante, negli Scrigni, e nelle Trappole.
- Si equipaggiano dall'inventario come le armi/armature (sostituendo il vecchio).
- Bonus stat (HP/Dodge/Acc) vengono rimossi correttamente quando si cambia monile.

### 6 Accessori disponibili

| Nome | Effetto | Tipo |
|---|---|---|
| Anello del Berserker | +15% probabilità critico | `crit_chance` |
| Amuleto del Vampiro | +2 HP per colpo a segno | `lifesteal` |
| Cintura di Ferro | +15 HP Massimi | `max_hp` |
| Collana del Vento | +10% Schivata | `dodge` |
| Occhio del Cacciatore | +15% Precisione | `acc` |
| Spallacci a Spilli | Rifletti 3 danni quando colpito | `reflect` |

### Integrazione nel combattimento
- **Critico**: Roll aggiuntivo prima del calcolo hit, raddoppia i danni.
- **Lifesteal**: Cura applicata dopo ogni colpo a segno (si somma a reliquie vampiriche).
- **Riflesso**: Unificato con la reliquia `armatura_spilli` in un unico `reflect_total`.
- **Stat passivi** (`max_hp`, `dodge`, `acc`): Applicati all'equipaggiamento, rimossi allo scambio.

---

## 2. Risonanza Elementale

### Come funziona
Se l'**Arma** e l'**Armatura** equipaggiate hanno lo **stesso elemento** (escluso Normale), si attiva una **Risonanza** con effetti passivi per tutta la durata del combattimento.

### Tabella Risonanze

| Elemento | Effetto | Quando si applica |
|---|---|---|
| 🔥 Fuoco | Ustione: +5 danni per turno (cumulativi) | Fine turno nemico |
| 💧 Acqua | Riduce ATK nemico del 15% | Inizio combattimento |
| 🪨 Terra | +5 Difesa fissa | Calcolo danni subiti |
| 💨 Vento | +15% Schivata | Calcolo hit nemico |
| ✨ Luce | +3 HP per ogni colpo a segno | Dopo danno inflitto |
| 🌑 Tenebra | +5 danni puri (ignora difesa) | Calcolo danno inflitto |

### Dilemma strategico
La Risonanza crea una scelta tattica: un'arma con +5 ATK e un elemento diverso, o un'arma leggermente più debole che mantiene attiva la Risonanza di Fuoco?

### Indicatore visivo
L'inventario mostra `✨ RISONANZA ATTIVA: [elemento]!` quando la sinergia è attiva.

---

## File Modificati

| File | Modifica |
|---|---|
| `data/accessories.json` | **NUOVO** — Database 6 accessori |
| `data_manager.py` | Caricamento `accessories` in `RAW_DATA`/`GAME_DATA` |
| `entities.py` | Classe `Accessory`, `generate_accessory()`, slot player, inventario, `_get_resonance_element()` |
| `rooms.py` | Drop accessori (mercante/tesori/trappole), bonus combat (crit/lifesteal/reflect), risonanza (6 elementi) |
| `fuzzer.py` | **NUOVO** — Stress test con accessori e risonanza forzata |

---

## Test

Fuzzer eseguito con successo:
- **50 run** simulate
- **178 combattimenti** completati
- **50 accessori** equipaggiati automaticamente
- **17 run con risonanza forzata**
- **0 crash** rilevati

# Refactoring di `base_camp` Completato!

Ho completato con successo l'estrazione delle logiche dei sottomenu del campo base.

## Modifiche Effettuate

Nel file `roguelike.py` sono state create quattro nuove funzioni dedicate:
- `base_camp_fire()`: Gestisce gli acquisti dei Perk con l'Essenza Astrale.
- `base_camp_forge()`: Gestisce lo sblocco di nuovi oggetti nel database.
- `base_camp_tavern()`: Gestisce lo sblocco di nuove classi giocabili.
- `base_camp_grimoire()`: Mostra le Imprese completate e l'esperienza delle classi.

La funzione originale `base_camp()` è stata drasticamente semplificata ed ora si occupa unicamente di mostrare il menu principale e reindirizzare la logica alle nuove funzioni in base all'input del giocatore.

## Risultati dei Test
- Ho verificato tramite compilatore Python locale che non ci fossero errori di sintassi.
- Il codice ora è molto più leggibile e aderisce al principio di singola responsabilità (SRP), almeno a livello strutturale del menu. Questo renderà molto più facile in futuro aggiungere nuove funzionalità al campo base (ad esempio, una Stanza dei Trofei o un Mercante Esotico).

# Sistema a Hook/Eventi Implementato

Ho completato la creazione del sistema ad eventi per le reliquie, rimuovendo le dipendenze hardcoded dal resto del motore di gioco.

## Modifiche Effettuate

1. **Creazione di `relic_effects.py`**
   - Ho creato il nuovo file `relic_effects.py` contenente la classe base `RelicEffect` che definisce i metodi vuoti (hook) per vari momenti di gioco come l'inizio del combattimento (`on_combat_start`), prima e dopo un attacco, quando si riceve un colpo e all'uccisione di un nemico.
   - Sono state create circa 20 sottoclassi (es. `LamaSangue`, `CaliceAlchimista`, `PietraLuna`) ognuna delle quali estende solo l'hook di cui ha bisogno.
   - Un dizionario `RELIC_REGISTRY` mappa l'ID testuale della reliquia (dal JSON) alla classe corrispondente.

2. **Aggiornamento di `entities.py` (`Player`)**
   - Quando il giocatore ottiene una reliquia (`add_relic`), viene ora istanziato il `RelicEffect` corretto e aggiunto a una nuova lista `self.relic_effects`.
   - L'effetto viene innescato una sola volta con il metodo `on_equip()`.
   - I calcoli passivi di schivata (`get_dodge`) ed exp (`gain_exp`) scorrono la lista degli effetti per raccogliere i modificatori anziché cercare le stringhe. Lo stesso avviene per le cure e l'uso degli oggetti in `manage_inventory`.

3. **Pulizia in `rooms.py` e `roguelike.py`**
   - Dalla classe `CombatSession` in `rooms.py` sono stati eliminati più di 20 `if "id_reliquia" in player.relic_ids:`. Adesso, quando il nemico muore, la stanza chiama semplicemente `r.on_enemy_death(self)` per tutte le reliquie del giocatore, e l'effetto della Pietra Filosofale, Teschio di Sangue e così via viene gestito internamente in `relic_effects.py`.
   - Anche il check passivo della `Bussola Dimensionale` in `roguelike.py` ora avviene tramite l'hook `modify_room_weights`.

## Risultato Finale
Questo pattern ha trasformato un potenziale "spaghetti code" in un sistema elegante e scalabile. Per creare una nuova reliquia in futuro, non servirà toccare **mai più** `rooms.py` o `entities.py`: basterà definire una classe per il nuovo oggetto in `relic_effects.py` e aggiungerla al file JSON dei dati.
