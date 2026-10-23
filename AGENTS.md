# Istruzioni per gli agenti IA

Questo repository è mantenuto in buona parte con assistenti IA. Queste regole valgono per qualsiasi agente che lo modifichi.

## Come proporre modifiche

- Lavora su un branch e apri una pull request. Non fare push diretti su `main`.
- Su ogni pull request gira [rsp](https://github.com/fedeveloper/rsp) (`.github/workflows/rsp.yml`), che commenta fatti riproducibili sul diff: test saltati o cancellati, import di pacchetti non dichiarati, controlli disattivati.
- Prima di considerare pronta una PR, leggi il commento di rsp. Per ogni fatto segnalato correggi la modifica oppure spiega nella descrizione della PR perché è voluto. Non aggirare il segnale (per esempio spostando il codice o rinominando i test).

## Branch

- `main` è la versione stabile, sempre giocabile, e contiene la v2 (lore, eventi a scene, personaggi ricorrenti, mappa, biomi, finali).
- La v3 (modalità e profondità: Ascensione, Sfida del Giorno e ciò che segue) si sviluppa su `v3`. Apri verso `v3` le PR che la riguardano; `v3` confluirà in `main` quando sarà stabile.
- Le correzioni alla versione stabile vanno verso `main`.

## Documenti

- `README.md` si genera con `python tools/genera_readme.py` (i test falliscono se non è aggiornato). Il Manuale del Giocatore e la Documentazione Tecnica vanno aggiornati nella stessa PR che cambia regole, dati o codice.

## Dipendenze

- Il gioco usa solo la libreria standard di Python, ed è una scelta voluta: funziona senza installare nulla.
- Se un pacchetto esterno è davvero necessario, dichiaralo in `dependencies` dentro `pyproject.toml` nella stessa PR.

## Test

- Esegui i test con `python -m unittest discover -s tests` dalla radice del repository. La CI li esegue su ogni PR.
- Quando cambi la logica di gioco o i file in `data/`, aggiungi o aggiorna i test.
- Non cancellare, saltare o indebolire un test per farlo passare. Se un test è sbagliato, correggilo e spiega perché nella PR.

## File da non committare

- `profile.json` è il salvataggio del giocatore, generato al primo avvio.
