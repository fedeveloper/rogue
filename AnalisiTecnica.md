# ⚙️ Documentazione Tecnica (Sviluppatori)

Il gioco è sviluppato in Python puro (senza librerie esterne non standard) utilizzando un'architettura **Data-Driven**. La logica di gioco è separata dai contenuti (asset).

## 📂 Struttura dell'Architettura
Il codice in `roguelike.py` agisce unicamente come "Motore Fisico" e "Interfaccia UI". 
Tutti i contenuti testuali, le statistiche, i nemici e l'economia risiedono all'interno della directory `/data/` in formato `.json`.

### Il Sistema di Patching del Profilo
Il salvataggio è gestito tramite `profile.json` (generato nella root dir). 
La funzione `load_profile()` contiene un meccanismo di retrocompatibilità (fallback): se uno sviluppatore aggiunge una nuova *Impresa* (Feat) nel codice, il gioco aggiorna automaticamente il `profile.json` dell'utente aggiungendo la chiave mancante senza corrompere i dati o i progressi salvati (Essence).

## 🗂️ Panoramica dei File Dati (JSON)

* `elements.json`: Definisce le regole di Sasso-Carta-Forbice e le icone emoji. Se si aggiunge un elemento, va dichiarato nei moltiplicatori di questo file.
* `enemies.json`: Diviso in `"enemies"` (mostri standard) e `"bosses"`. 
  * I parametri `"base_hp"` e `"base_atk"` vengono scalati in Python dal livello del Piano attuale.
* `weapons.json` & `armors.json`: Contengono equipaggiamenti. 
  * Se un oggetto ha il campo `"unlock_id"`, non verrà spawnato nel Labirinto a meno che quell'ID non sia presente nell'array `"unlocked_ids"` del `profile.json` del giocatore.
* `classes.json`: Definisce ruolo, stat base, equipaggiamento iniziale e l'albero della **Maestria**.
* `meta.json`: Il cuore del Roguelite. Contiene la logica e i requisiti per:
  * Tratti d'inizio run (`traits`).
  * Imprese sbloccabili (`feats`).
  * Requisiti di Punti Esperienza per le Maestrie.
* `lore.json`: Array di stringhe testuali estrapolate casualmente durante l'ingresso in una stanza.

## 🛠️ Come Estendere il Gioco (Modding)

### 1. Aggiungere un nuovo Nemico
Apri `data/enemies.json`. Aggiungi un nuovo oggetto JSON sotto `"enemies"`:

"Re Scheletro": {
    "element": "Tenebra", 
    "base_hp": 30, 
    "base_atk": 8, 
    "base_dodge": 0, 
    "base_acc": 10
}

### 2. Aggiungere un Oggetto Sbloccabile
Apri `data/weapons.json`.

{
    "name": "Spada Laser", 
    "base_atk": 20, 
    "unlock_id": "spada_laser_01", 
    "unlock_cost": 500, 
    "desc": "Arma sci-fi."
}

Il motore di gioco intercetterà la chiave "unlock_cost" e popolerà in automatico il menu della Forgia Dimensionale all'interno dell'Hub del Campo Base.

### 3. Aggiungere una Nuova Impresa (Feat)
In data/meta.json sotto "feats", definisci l'impresa. Assicurati che reward_type sia mappato ("perk", "unlock" o "class").
Attenzione: La validazione dell'impresa (il trigger che la segna come completata) andrà codificata in roguelike.py all'interno della funzione evaluate_run().

## 🧠 Funzionamento del "Deck" (Generazione Piani)
La funzione generate_floor_deck(floor) genera un array (es. ["combat", "combat", "vendor", "trap", "boss"]) e usa random.shuffle() per mescolare l'ordine, garantendo che il boss sia sempre l'ultimo elemento (append("boss")).
Questo approccio previene la frustrazione di RNG puramente matematici (es. 5 stanze trappola di fila), assicurando almeno un riposo e un mercante per piano.