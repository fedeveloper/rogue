# 🌀 Il Labirinto degli Elementi e del Caos

Un gioco di ruolo roguelite testuale in Python, basato su un'architettura Data-Driven (Python + JSON) e dotato di un sistema di meta-progressione profondo.

## 🌟 Caratteristiche Principali
* **Mappa a Bivi Strategica:** Scegli la tua strada stanza dopo stanza. Valuta i rischi tra combattimenti, forzieri, mercanti o misteriosi eventi narrativi.
* **Combattimento Elementale:** Sfrutta le debolezze nemiche in un sistema a 7 elementi (Fuoco, Acqua, Terra, Vento, Luce, Tenebra, Normale).
* **Build e Reliquie:** Trova potenti artefatti passivi che cambiano le regole del gioco durante ogni singola run, creando sinergie uniche.
* **Fusione ed Eventi:** Sacrifica il tuo equipaggiamento all'Altare dell'Evoluzione per potenziarlo, o affronta scelte narrative con esiti imprevedibili.
* **Meta-Progressione (Roguelite):** L'Oro guadagnato (e salvato fuggendo!) viene convertito in *Essenza Astrale* per sbloccare perk, nuove classi e armi all'Hub.
* **I Patti del Caos (Endgame):** Una volta finito il gioco, attiva le Maledizioni per aumentare a dismisura la difficoltà in cambio di moltiplicatori di ricompensa.

## 🚀 Requisiti e Installazione
1. Assicurati di avere **Python 3.7+** installato sul tuo sistema.
2. Scarica la repository/cartella del gioco.
3. La struttura delle cartelle deve essere intatta:
```text
   /
   ├── roguelike.py
   └── data/
       ├── armors.json
       ├── classes.json
       ├── consumables.json
       ├── elements.json
       ├── enemies.json
       ├── events.json
       ├── lore.json
       ├── meta.json
       ├── relics.json
       └── weapons.json

## Avvia il gioco da terminale (o facendo doppio clic su Windows):
python roguelike.py
(Nota: Il file di salvataggio profile.json verrà generato in automatico al primo avvio).