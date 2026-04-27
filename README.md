# 🌀 Il Labirinto degli Elementi e del Caos

Un gioco di ruolo roguelite testuale in Python, basato su un'architettura Data-Driven (Python + JSON) e dotato di un sistema di meta-progressione profondo.

## 🌟 Caratteristiche Principali
* **Combattimento Elementale Strategico:** Sfrutta le debolezze nemiche in un sistema a 7 elementi (Fuoco, Acqua, Terra, Vento, Luce, Tenebra, Normale).
* **Generazione Procedurale (Deck-building):** Ogni piano è un mazzo di stanze mescolate (Combattimenti, Boss, Falò, Trappole, Negozi).
* **Meta-Progressione (Roguelite):** L'Oro guadagnato (e salvato fuggendo!) viene convertito in *Essenza Astrale* per sbloccare perk permanenti, nuove classi e oggetti all'Hub centrale.
* **Sistema di Maestria e Imprese:** Completa obiettivi specifici durante le run per sbloccare Tratti mutabili e Sottoclassi.

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
       ├── lore.json
       ├── meta.json
       └── weapons.json