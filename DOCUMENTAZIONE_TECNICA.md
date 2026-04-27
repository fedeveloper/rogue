# ⚙️ Documentazione Tecnica (Sviluppatori)

Il gioco è sviluppato in Python puro (senza librerie esterne non standard) utilizzando un'architettura **Data-Driven**. La logica di gioco è separata dai contenuti (asset).

## 📂 Struttura dell'Architettura
Il codice in `roguelike.py` agisce unicamente come "Motore Fisico" e "Interfaccia UI". 
Tutti i contenuti testuali, le statistiche, i nemici e l'economia risiedono all'interno della directory `/data/` in formato `.json`.

### Il Sistema di Patching del Profilo
Il salvataggio è gestito tramite `profile.json` (generato nella root dir). 
La funzione `load_profile()` contiene un meccanismo di retrocompatibilità ricorsivo: se uno sviluppatore aggiunge nuove chiavi (feats, perks, ecc.) ai JSON di sistema, il codice aggiornerà automaticamente il file dell'utente aggiungendo i dati mancanti, senza causare `KeyError` o resettare i progressi.

## 🗂️ Panoramica dei File Dati (JSON)

* `elements.json`: Definisce le regole di Sasso-Carta-Forbice e le icone emoji.
* `enemies.json`: Base dei mostri. `"base_hp"` e `"base_atk"` scalano linearmente col livello del piano calcolato in Python.
* `events.json`: **[NUOVO]** Contiene i bivi narrativi. Ogni evento ha un testo e scelte multiple mappate a `"action"` specifiche.
* `relics.json`: **[NUOVO]** Array di Reliquie passive con i relativi `"id"`. Gli effetti sono hardcodati nella classe `Player` e nel loop di combattimento, ma i testi risiedono qui.
* `weapons.json` / `armors.json` / `consumables.json`: Dati dell'equipaggiamento. Il campo `"unlock_id"` serve per la Forgia Dimensionale.
* `classes.json`: Definisce statistiche di base e l'albero dinamico della Maestria.
* `meta.json`: Regole di meta-progressione (Requisiti XP, Feats, Traits) e i **Patti del Caos** per l'Endgame.

## 🛠️ Come Estendere il Gioco (Modding)

### 1. Aggiungere una Reliquia Passiva
1. Aggiungi i testi in `data/relics.json`:
   `{"id": "anello_veloce", "name": "Anello del Vento", "desc": "Aggiunge +20% di schivata base."}`
2. Implementa la logica in `roguelike.py`. Ad esempio, nella classe `Player`, aggiungi la condizione: 
   `if "anello_veloce" in self.relic_ids: self.base_dodge += 20`

### 2. Aggiungere una Stanza Evento
Apri `data/events.json`. Crea un nuovo oggetto radice:

"statua_guerriero": {
  "title": "Statua Antica", 
  "text": "Una statua che richiede un tributo di sangue.",
  "choices":[
    {"text": "Dona 20 HP per un potenziamento Arma", "action": "upgrade_weapon"},
    {"text": "Ignora", "action": "none"}
  ]
}

Dovrai poi intercettare l'azione "upgrade_weapon" all'interno della funzione event_room() in Python.

### 3 Aggiungere Patti del Caos (Maledizioni)
In `meta.json`, sotto "pacts", aggiungi:
"niente_cure": {"name": "Morte Certa", "desc": "I nemici tolgono cura", "bonus": 0.50}
Poi nel codice di combattimento, se "niente_cure" in active_pacts, azzera gli HP recuperati.

## 🧠 Funzionamento del "Mazzo" e Mappa a Bivi
La funzione di gioco scorre su un loop di 5 step (tappe) per ogni Piano.
Dallo Step 1 al 4, genera 2 stanze casuali basate su Pesi Statistici (es. 40% Combattimento, 20% Evento, 10% Forziere).
Lo Step 5 forza obbligatoriamente un "type": "boss".