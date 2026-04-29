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
