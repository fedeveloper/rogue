"""Il combattimento a turni. `CombatSession` (in `session.py`) unisce le parti dello scontro, una per modulo:

- `session.py`: stato, inizio, ciclo dei turni, status e maledizioni, Risonanza, fine e vittoria;
- `actions.py`: il turno dell'eroe (menu, attacco, difesa, fuga);
- `spells.py`: gli incantesimi;
- `reactions.py`: marchi e reazioni elementali;
- `phases.py`: le fasi dei boss;
- `enemy.py`: il turno del nemico (intento, danni, mosse);
- `rules.py`: mosse per tipo e `reaction_key`;
- `rewards.py`: Audacia, rune e pergamene che cadono.

Ogni parte è una classe di soli metodi (mixin) che lavora sullo stato della sessione: i nomi dei metodi sono quelli
di sempre, quindi `CombatSession(...).execute_player_attack()` funziona come prima.
"""
from combat.rules import reaction_key
from combat.session import CombatSession
