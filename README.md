# 🌀 Il Labirinto degli Elementi e del Caos

> Un roguelite testuale in Python con combattimento elementale, meta-progressione profonda e centinaia di build possibili.

![Python](https://img.shields.io/badge/Python-3.7%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/Licenza-Uso_Personale-green)
![Status](https://img.shields.io/badge/Stato-In_Sviluppo_Attivo-orange)

---

## 📖 Panoramica

**Il Labirinto degli Elementi e del Caos** è un gioco di ruolo roguelite da terminale. Ogni partita (detta *run*) ti mette nei panni di un avventuriero che scende sempre più in profondità in un labirinto pieno di mostri, trappole, tesori ed enigmi.

Muori? Perdi quasi tutto. Ma l'**Essenza Astrale** che raccogli persiste tra una partita e l'altra, permettendoti di sbloccare nuove classi, potenziamenti permanenti, reliquie leggendarie e molto altro.

L'obiettivo? **Raggiungere il Piano 30 e sconfiggere il boss finale** — o sfidare la sorte nella **Modalità Infinita**, dove i nemici non hanno fine e le ricompense crescono esponenzialmente.

---

## ✨ Caratteristiche Principali

### ⚔️ Combattimento Tattico Elementale
Un sistema a **7 elementi** (Fuoco, Acqua, Terra, Vento, Luce, Tenebra, Normale) governa ogni scontro. I vantaggi e gli svantaggi elementali influenzano danni, precisione e schivata.

### 🗺️ Mappa a Bivi Strategica
Ogni piano è composto da 5 stanze. Prima di ogni stanza scegli tra **2 porte** diverse: combattimento, mercante, falò, forziere, trappola, evento narrativo o la temibile *Stanza del Mistero*. La quinta stanza è sempre un **Boss**.

### 🧬 6 Classi Giocabili

| Classe | HP | Stile | Sblocco |
|---|---|---|---|
| ⚔️ **Guerriero** | 120 | Tank bilanciato, Contrattacco | Iniziale |
| 🗡️ **Ladro** | 85 | Schivata alta, Colpo Critico garantito | Iniziale |
| 🔮 **Mago** | 65 | Danno elementale puro, Rubavita su colpi SE | Iniziale |
| 🛡️ **Paladino** | 180 | Ultra-tank, Cura in difesa | Maestria Guerriero Lv.5 |
| 🪓 **Berserker** | 100 | Glass cannon, +50% ATK sotto il 30% HP | Impresa "Danza con la Morte" |
| 🧪 **Alchimista** | 95 | Pozioni potenziate, danni caotici | Impresa "Genio Elementale" |

Ogni classe ha un **albero di Maestria** a 5 livelli che sblocca bonus personali, consumabili unici, bonus globali (per tutti gli eroi) e perfino nuove classi o reliquie.

### 💍 Triplo Slot Equipaggiamento
- **Arma** — Determina i tuoi danni e il tuo elemento offensivo.
- **Armatura** — Assorbe i danni e determina il tuo elemento difensivo.
- **Monile** *(Accessorio)* — Anelli, amuleti e cinture con effetti passivi unici:

| Monile | Effetto |
|---|---|
| Anello del Berserker | +15% probabilità di colpo critico |
| Amuleto del Vampiro | +2 HP rubati per ogni colpo a segno |
| Cintura di Ferro | +15 HP Massimi |
| Collana del Vento | +10% Schivata |
| Occhio del Cacciatore | +15% Precisione |
| Spallacci a Spilli | Rifletti 3 danni quando vieni colpito |

### ✨ Risonanza Elementale
Se equipaggi un'**Arma** e un'**Armatura** dello **stesso elemento** (escluso Normale), si attiva una **Risonanza** con bonus potenti per tutta la durata del combattimento:

| Elemento | Risonanza | Effetto |
|---|---|---|
| 🔥 Fuoco | Ustione | +5 danni cumulativi per turno per ogni colpo a segno |
| 💧 Acqua | Flusso | Riduce l'attacco nemico del 15% |
| 🪨 Terra | Fortezza | +5 Difesa fissa aggiuntiva |
| 💨 Vento | Raffica | +15% Schivata |
| ✨ Luce | Benedizione | +3 HP curati per ogni colpo a segno |
| 🌑 Tenebra | Perforazione | +5 danni puri (ignora la difesa nemica) |

La Risonanza viene ricalcolata subito se cambi Arma o Armatura dall'inventario durante uno scontro: puoi attivarla (o perderla) a metà combattimento.

Questo crea dilemmi strategici profondi: *tieni l'arma più forte, o quella più debole che mantiene attiva la Risonanza?*

### ☣️ Meccaniche Avanzate: Status, Maledizioni e Quest
Il Labirinto offre sfide dinamiche per metterti alla prova:
- **Status Alterati**: Alcuni nemici infliggono *Veleno* o *Sanguinamento*, che ti danneggeranno ogni turno fino alla fine dello scontro. Usa l'*Antidoto Universale* per liberartene subito! Alcune armi speciali (Frusta di Spine, Pugnali del Vento, Falce del Mietitore, Balestra Gnomica, Tridente Oceanico) possono infliggere gli stessi status ai nemici.
- **Oggetti Maledetti**: Troverai equipaggiamenti con la dicitura `[MALEDETTO]`. Hanno statistiche altissime ma applicano malus pesanti (drenano HP, rubano Oro, riducono la schivata). Puoi purificarli spendendo 100 Oro al Falò.
- **Eventi a Catena e Oggetti Chiave**: Alcuni Eventi Narrativi ti daranno *Oggetti Chiave* (es. Chiave Arrugginita) che sbloccheranno scelte segrete in eventi successivi.

### 🌟 30 Reliquie
Artefatti passivi che stravolgono le regole del gioco. Alcune sono trovabili sconfiggendo boss, altre vanno sbloccate tramite Essenza o completando Imprese.

<details>
<summary>📜 Lista completa delle Reliquie (clicca per espandere)</summary>

**Reliquie Base (drop da Boss)**
| Reliquia | Effetto |
|---|---|
| Artiglio Vampirico | +5 HP per ogni attacco a segno |
| Lente Prismatica | Vantaggi e svantaggi elementali RADDOPPIATI |
| Scudo di Cristallo | Il primo danno in ogni combattimento è ridotto a 0 |
| Tasca Dorata | +25% Oro trovato |
| Idolo della Guerra | +5 ATK permanente |
| Calice dell'Alchimista | Pozioni curano il 50% in più |
| Mantello Nebbioso | +15% Schivata |
| Bussola Perfetta | Fuga riuscita al 100% (non su Boss) |
| Occhio del Cacciatore | +20% Precisione |
| Spallacci di Rovo | Rifletti 5 danni quando colpito |
| Cuore di Troll | +2 HP Max per ogni nemico ucciso |
| Tomo della Conoscenza | +30% EXP |
| Idolo dell'Avidità | Oro x2, ma Schivata a 0% |
| Lama di Sangue | +10 ATK, ma subisci 3 danni per attacco |

**Reliquie Sbloccabili (Essenza)**
| Reliquia | Costo | Effetto |
|---|---|---|
| Corona del Re Folle | ✨1000 | Colpi SE o Critici +50% danni |
| Anello Vampirico Maggiore | ✨1500 | +2 HP per attacco a segno |
| Clessidra del Destino | ✨800 | -20% Schivata nemica |
| Armatura a Spilli | ✨600 | Rifletti 3 danni |
| Pergamena d'Oro | ✨700 | Cura 2 HP quando ottieni Oro |
| Campanella degli Spiriti | ✨1200 | 15% di negare un attacco |
| Pietra di Luna | ✨500 | +50% DEF in Difesa |
| Contratto Demoniaco | ✨1000 | Danni x2, -5 HP a fine combattimento (non letale) |
| Pozione Senza Fondo | ✨900 | 25% di non consumare le pozioni |
| Bussola Dimensionale | ✨1000 | Più Tesori e Misteri sulla mappa |

**Reliquie Sbloccabili (Imprese e Maestria)**
| Reliquia | Sblocco | Effetto |
|---|---|---|
| Cuore di Drago | Impresa "Il Sopravvissuto" | +50 HP Max |
| Sigillo Elementale | Impresa "Equilibrista" | Annulla debolezza difensiva |
| Spirito della Spada | Impresa "Lama di Cristallo" | +15 ATK se arma Lv.1 |
| Maschera Antigas | Impresa "Assaggiatore di Veleni" | Immunità trappole |
| Teschio di Sangue | Maestria Berserker Lv.5 | +1 HP Max per nemico ucciso |
| Pietra Filosofale | Maestria Alchimista Lv.5 | 20% chance XP → Oro |

</details>

### 🏕️ Campo Base (Hub di Meta-Progressione)
Tra una run e l'altra, spendi l'**Essenza Astrale** al Campo Base:

- **🔥 Il Fuoco dell'Anima** — 15 potenziamenti permanenti (HP, Oro, Schivata, Precisione, EXP, Sconti, ecc.), ognuno con più livelli.
- **⚒️ La Forgia Dimensionale** — Sblocca nuove reliquie, armi e consumabili leggendari.
- **🍺 La Taverna** — Recluta nuove classi di eroi.
- **📜 Grimorio e Imprese** — Monitora le tue sfide e i progressi di Maestria.
- **📚 L'Archivio di Aethelgard** — Consulta i tomi di Lore trovati nel gioco. Sbloccare e completare questi tomi ti conferisce delle **Sinergie dell'Archivio**, veri e propri buff passivi permanenti (es. +10% Danni contro i Boss).
- **🧪 La Tenda dello Speziale** — (Si sblocca salvando l'NPC nel labirinto). Ti permette di spendere piccole somme di Essenza per iniziare la run successiva con utili consumabili, come l'Antidoto Universale.

### 📜 12 Imprese (Achievement)
Sfide trasversali che sbloccano contenuti nascosti. Alcune si completano in una singola run, altre richiedono progressione cumulativa.

<details>
<summary>📜 Lista completa delle Imprese (clicca per espandere)</summary>

| Impresa | Obiettivo | Ricompensa |
|---|---|---|
| L'Ombra | Fuggi da 10 combattimenti in una run | Perk: Scarpisti |
| Fabbro Folle | 3 fusioni alla Forgia in una run | Arma: Spadone Infranto |
| Cannone di Vetro | Sconfiggi un Boss senza subire danni | Armatura: Veste Eterea |
| Danza con la Morte | Uccidi un nemico a 1 HP | Classe: Berserker |
| L'Avaro | Esci con 2000+ Oro | Tratto: Aristocratico |
| Genio Elementale | Fondi un'arma fino a Lv.5 | Classe: Alchimista |
| Il Sopravvissuto | Piano 10+ senza riposare al falò | Reliquia: Cuore di Drago |
| Epuratore di Demoni | 10 Boss totali sconfitti | Tratto: Cacciatore Etereo |
| Mani Bucate | Spendi 2000+ Oro dal mercante in una run | Arma: Zweihander d'Oro |
| Equilibrista | Finisci con Arma/Armatura di elementi diversi | Reliquia: Sigillo Elementale |
| Lama di Cristallo | Piano 15 senza cambiare arma iniziale | Reliquia: Spirito della Spada |
| Furia Cieca | Supera un piano mancando più di metà degli attacchi (min. 6) | Tratto: Titano |
| Tiratore Scelto | 5 colpi Super Efficaci su un Boss | Consumabile: Filtro Preciso |
| Assaggiatore di Veleni | Sopravvivi a 1 HP da un danno letale | Reliquia: Maschera Antigas |

</details>

### 🎭 7 Tratti di Partenza
Modificatori globali che alterano radicalmente lo stile di gioco:

| Tratto | Effetto | Sblocco |
|---|---|---|
| Nessun Tratto | Standard | Iniziale |
| Patto del Sangue | +50 ATK, cure bloccate | 10 morti |
| Tocco di Mida | No EXP, Oro x3 | 5000 Oro totali |
| Aristocratico | +500 Oro iniziali | Impresa "L'Avaro" |
| Cacciatore Etereo | Primo colpo nemico manca, -20% Schivata | Impresa "Epuratore" |
| Titano | +100 HP, Precisione/Schivata dimezzate | Impresa "Furia Cieca" |
| Benedetto | Scudo di Cristallo iniziale + resisti 1 colpo letale | Maestria Paladino Lv.5 |

### ☠️ I Patti del Caos (Endgame)
Una volta completata la prima run da 30 piani, puoi attivare fino a **5 Maledizioni** per moltiplicare le ricompense in Essenza:

| Patto | Effetto | Bonus Essenza |
|---|---|---|
| Durezza | HP nemici +30% | +25% |
| Furia | ATK nemici +30% | +25% |
| Carestia | Pozioni curano la metà | +25% |
| Inflazione | Prezzi mercante x2 | +25% |
| Labirinto Mortale | Trappole danni x2 | +25% |

Attivandoli tutti si raggiunge un moltiplicatore di **2.25x** sull'Essenza guadagnata!

### 🔄 Altre Meccaniche
- **⚒️ Fusione Equipaggiamento** — Al Falò, sacrifica un'arma o armatura per potenziarne un'altra. L'oggetto sacrificato dona metà dei suoi stats al primo.
- **9 Eventi Narrativi** — Incontri unici con scelte multiple e conseguenze variabili (Fontana Fatata, Bisca dei Goblin, Altare del Sangue, ecc.).
- **🔮 Stanza del Mistero** — Esito casuale: nemico potenziato, nemico debilitato, trappola o... niente.
- **📊 Calcolo Essenza** — Morte = 20% Oro → Essenza. Fuga = 100% Oro → Essenza. +50 per Boss. Patti moltiplicano. Modalità Infinita oltre Piano 30: bonus +50%.

---

## 📊 Contenuti in Numeri

| Categoria | Quantità |
|---|---|
| Classi giocabili | 6 |
| Tratti di partenza | 7 |
| Armi base | 14 |
| Armature base | 10 |
| Accessori (Monili) | 6 |
| Consumabili | 13 |
| Reliquie | 30 |
| Nemici comuni | 15 |
| Boss | 10 |
| Eventi narrativi | 9 |
| Imprese/Achievement | 12 |
| Patti del Caos | 5 |
| Potenziamenti permanenti | 15 |
| Elementi | 7 |
| Risonanze Elementali | 6 |

---

## 🚀 Installazione e Avvio

### Requisiti
- **Python 3.7+** installato sul sistema (Compatibilità nativa garantita su **Windows, macOS e Linux** senza dipendenze esterne come `colorama` o `msvcrt` in via esclusiva)
- Un terminale con supporto UTF-8 (per le icone emoji)

### Avvio
```bash
# Clona la repository
git clone https://github.com/tuousername/rogue.git
cd rogue

# (Windows) Abilita UTF-8 nel terminale
chcp 65001

# Avvia il gioco
python roguelike.py
```

Il file di salvataggio `profile.json` viene generato automaticamente al primo avvio.

### Struttura del Progetto
```text
rogue/
├── roguelike.py          # Menu principale, loop di gioco, evaluate_run
├── entities.py           # Classi Player/Enemy, generatori item, applicazione attributi
├── rooms.py              # Logica stanze, CombatSession (combattimento, falò, eventi)
├── inventory_menu.py     # Gestione dell'inventario, uso consumabili e stats
├── relic_effects.py      # Hook ed effetti ad attivazione per le Reliquie
├── archive.py            # Logica dei tomi e Sinergie dell'Archivio
├── data_manager.py       # Caricamento JSON, gestione salvataggio profilo
├── ui.py                 # Utilità cross-platform I/O (colori ANSI nativi, get_key)
├── constants.py          # Costanti di bilanciamento globale (es. chance drop)
├── profile.json          # Salvataggio giocatore (generato automaticamente)
└── data/
    ├── accessories.json  # Database accessori
    ├── armors.json       # Database armature
    ├── classes.json      # Classi e alberi di maestria
    ├── consumables.json  # Pozioni e consumabili
    ├── elements.json     # Sistema elementale e moltiplicatori
    ├── enemies.json      # Nemici comuni e boss
    ├── events.json       # Eventi narrativi a scelte multiple
    ├── lore.json         # Testi narrativi ambientali e di atmosfera
    ├── meta.json         # Tratti, patti, imprese, config stanze e pesi
    ├── relics.json       # Database reliquie
    └── weapons.json      # Database armi
```

---

## 🏗️ Architettura

Il gioco segue un'architettura **Data-Driven**:
- **Dati** (`data/*.json`) — Tutto il contenuto del gioco (classi, nemici, armi, eventi, bilanciamento) è definito in file JSON modificabili senza toccare il codice.
- **Logica** (`entities.py`, `rooms.py`) — Entità e stanze leggono i dati a runtime e applicano le regole.
- **Orchestrazione** (`roguelike.py`) — Menu, selezione classi/tratti/patti, loop di esplorazione e valutazione finale della run.
- **Persistenza** (`data_manager.py`) — Caricamento dati, gestione del profilo e salvataggio automatico.

---

## 📝 Roadmap

- [ ] Nuova classe: **Assassino** (sblocco Maestria Ladro Lv.5)
- [ ] Nuova classe: **Negromante** (sblocco Maestria Mago Lv.5)
- [ ] Nuovi accessori sbloccabili tramite Imprese e Maestria
- [ ] Sistema di Rune/Incastoni per la personalizzazione di Armi e Armature
- [ ] Boss con meccaniche speciali (fasi, immunità, pattern)
- [ ] Nuovi eventi narrativi e bivi ramificati

---

*Sviluppato con ❤️ e Python.*
