# Istruzioni per gli agenti IA

Questo repository è mantenuto in buona parte con assistenti IA. Queste regole valgono per qualsiasi agente che lo modifichi.

## Come proporre modifiche

- Lavora su un branch e apri una pull request. Non fare push diretti su `main`.
- Su ogni pull request gira [rsp](https://github.com/fedeveloper/rsp) (`.github/workflows/rsp.yml`), che commenta fatti riproducibili sul diff: test saltati o cancellati, import di pacchetti non dichiarati, controlli disattivati.
- Prima di considerare pronta una PR, leggi il commento di rsp. Per ogni fatto segnalato correggi la modifica oppure spiega nella descrizione della PR perché è voluto. Non aggirare il segnale (per esempio spostando il codice o rinominando i test).

## Branch

- `main` è la versione stabile, sempre giocabile, e contiene la v6: lore, eventi a scene, personaggi ricorrenti, mappa e biomi (v2); Ascensione e Sfida del Giorno (v3); identità dei nemici, biomi popolati, il Ciclo del Labirinto e armi con carattere (v4); attributi, magia con l'Etere, talenti, l'Elementalista e il Campo a livelli (v5); la lore dieci volte più ampia, con dialoghi del Campo, Archivio, Atlante, vite prestate, Armeria ed epiloghi dei finali (v6).
- Lavora su un branch nato da `main` e apri la PR verso `main`. Le correzioni alla versione stabile vanno verso `main`.
- I branch `v3`, `v4`, `v5` e `v6` sono la storia dello sviluppo e sono già tutti contenuti in `main`: non aprire PR verso di loro.
- Per una versione nuova e corposa, che va provata prima di arrivare in `main`, si apre un branch dedicato nato da `main`, e si decide quando portarlo in `main` dopo le prove di gioco.
- Il branch `v7` è in sviluppo: la v7 dà al gioco una grafica semplice (prima nel terminale: ritratti, barre, riquadri) **senza toccare valori, regole o bilanciamento**. Le PR della v7 vanno verso `v7`.
- Chi aggiunge lore segue la guida e la *Scala delle rivelazioni* di `STORY.md`; una PR di soli testi non cambia valori, regole o bilanciamento e non ha bisogno di simulazioni.

## Documenti

- `README.md` si genera con `python tools/genera_readme.py` (i test falliscono se non è aggiornato).
- La lore segue il canone in `STORY.md`: la Parte I dice come si scrive (lunghezze, voce dei personaggi), la *Scala delle rivelazioni* dice cosa il giocatore può sapere e quando. Un fatto nuovo (un nome, un legame, una data) si scrive in `STORY.md` nella stessa PR che lo mette nel gioco. `python tools/conta_testi.py` misura la lore per blocco e segnala testi ripetuti e parole troppo usate.
- Dopo aver modificato un file in `data/`, riformattalo con `python tools/formatta_dati.py`: i test falliscono se un file di dati non è nel formato unico. Il Manuale del Giocatore e la Documentazione Tecnica vanno aggiornati nella stessa PR che cambia regole, dati o codice.

## Dipendenze

- Il gioco usa solo la libreria standard di Python, ed è una scelta voluta: funziona senza installare nulla.
- Se un pacchetto esterno è davvero necessario, dichiaralo in `dependencies` dentro `pyproject.toml` nella stessa PR.

## Test

- Esegui i test con `python -m unittest discover -s tests` dalla radice del repository. La CI li esegue su ogni PR.
- Quando cambi la logica di gioco o i file in `data/`, aggiungi o aggiorna i test.
- Non cancellare, saltare o indebolire un test per farlo passare. Se un test è sbagliato, correggilo e spiega perché nella PR.

## File da non committare

- `profile.json` è il salvataggio del giocatore, generato al primo avvio.
- `run_save.json` è la discesa salvata a metà («Salva ed esci»), generata dal gioco.
