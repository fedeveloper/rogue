# Istruzioni per gli agenti IA

Questo repository è mantenuto in buona parte con assistenti IA. Queste regole valgono per qualsiasi agente che lo modifichi.

## Come proporre modifiche

- Lavora su un branch e apri una pull request. Non fare push diretti su `main`.
- Su ogni pull request gira [rsp](https://github.com/fedeveloper/rsp) (`.github/workflows/rsp.yml`), che commenta fatti riproducibili sul diff: test saltati o cancellati, import di pacchetti non dichiarati, controlli disattivati.
- Prima di considerare pronta una PR, leggi il commento di rsp. Per ogni fatto segnalato correggi la modifica oppure spiega nella descrizione della PR perché è voluto. Non aggirare il segnale (per esempio spostando il codice o rinominando i test).

## Branch

- `main` è la versione stabile, sempre giocabile, e contiene la v5: lore, eventi a scene, personaggi ricorrenti, mappa e biomi (v2); Ascensione e Sfida del Giorno (v3); identità dei nemici, biomi popolati, il Ciclo del Labirinto e armi con carattere (v4); attributi, magia con l'Etere, talenti, l'Elementalista e il Campo a livelli (v5).
- Lavora su un branch nato da `main` e apri la PR verso `main`. Le correzioni alla versione stabile vanno verso `main`.
- I branch `v3`, `v4` e `v5` sono la storia dello sviluppo e sono già tutti contenuti in `main`: non aprire PR verso di loro.
- Per una versione nuova e corposa, che va provata prima di arrivare in `main`, si apre un branch dedicato (es. `v6`) nato da `main`, e si decide quando portarlo in `main` dopo le prove di gioco.

## Documenti

- `README.md` si genera con `python tools/genera_readme.py` (i test falliscono se non è aggiornato).
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
