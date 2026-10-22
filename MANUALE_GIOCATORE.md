# 📜 Manuale del Giocatore

Benvenuto nel **Labirinto degli Elementi e del Caos**. Ti attendono 30 piani di mostri, trappole, eventi e tesori, e in fondo il **DIO ANTICO**. Morirai, e più di una volta: ogni discesa però ti lascia qualcosa, e quella dopo andrai più a fondo.

---

## 🎮 Comandi

- **Frecce ⬆️⬇️** per spostarti nei menu, **Invio** per confermare.
- **Indietro**, in fondo ai sottomenu, torna alla schermata precedente senza consumare il turno.
- **Ctrl+C** chiude il gioco in qualsiasi momento.
- In **Impostazioni** (menu principale) scegli la velocità del testo narrativo: *Lenta*, *Normale*, *Veloce* o *Istantanea*.

Se colori o emoji non si vedono bene, usa un terminale con codifica UTF-8 (su Windows: *Windows Terminal*, oppure `chcp 65001`).

---

## 🧭 La discesa

1. **Scegli l'eroe e il tratto.** Dopo la prima vittoria puoi attivare anche i **Patti del Caos** (vedi sotto).
2. **Ogni piano ha 5 tappe.** A ogni tappa scegli fra **due porte**. Il tipo di stanza è sempre visibile; con il potenziamento *Sesto Senso* vedi anche quale nemico o evento ti aspetta.
3. **La quinta tappa è sempre un boss.**
4. **Superato il piano** recuperi un po' di HP (20 + 5 per piano) e scendi.
5. In qualsiasi bivio puoi scegliere **Fuga dal Labirinto**: porti a casa tutto l'Oro, convertito in Essenza.

Più scendi, più i nemici sono forti: ai primi piani incontri banditi, goblin e scheletri, verso il fondo idre di lava e leviatani. Anche i boss crescono con la profondità, e il DIO ANTICO compare **solo al piano 30**.

### Le stanze

| Stanza | Cosa succede |
|---|---|
| ⚔️ **Combattimento** | Un nemico adatto al piano. Vincendo ottieni Oro, EXP e a volte un oggetto. |
| 💰 **Mercante** | Compra armi, armature, monili e pozioni; vendi ciò che non ti serve. Dopo ogni acquisto il resto della merce rincara del 10%. |
| 🔥 **Falò** | *Riposa* (50% degli HP) **oppure** *affila l'arma* (+3 ATK per 50 Oro): una delle due, poi il falò si spegne. Prima puoi usare l'**Altare dell'Evoluzione** e la **purificazione** quante volte vuoi. |
| 💎 **Forziere** | Oro, a volte un monile, una pozione o una reliquia. |
| ⚠️ **Trappola** | Danni (evitabili con la schivata), a volte un oggetto fra gli ingranaggi. |
| 🎭 **Evento** | Una piccola storia con bivi, a volte in più scene: vedi *Gli eventi* qui sotto. Alcuni nascondono un artigiano prigioniero da liberare. |
| ❓ **Mistero** | Un nemico potenziato (che lascia un oggetto), uno debilitato, una trappola… o niente. |

### Gli eventi

Negli eventi le scelte contano, e non solo in quella stanza:

- **Il riepilogo dice la verità.** Accanto a ogni scelta, fra parentesi, il gioco mostra cosa succede: `(-20 Oro; 50%: Reliquia)`, `(+12 ATK; -25 HP Max)`, `(60%: +120 Oro, altrimenti Combatti)`. Lo calcola dagli effetti reali, quindi non può sbagliare.
- **Opzioni che esistono perché sei tu.** Alcune scelte compaiono solo per certe classi, tratti, reliquie o oggetti chiave, e lo dicono con un'etichetta: `[Mago] Riaccendi la lanterna`, `[Tocco di Mida] Immergi la mano`, `[Occhio del Cacciatore] Guarda meglio le impronte`. Rigiocare lo stesso evento con un altro eroe apre strade diverse.
- **Scelte bloccate.** Le opzioni in rosso sono visibili ma non selezionabili. Ti manca qualcosa, per esempio "(Ti serve una chiave)", oppure l'oro per pagare.
- **Più scene.** Molti eventi proseguono dopo la prima scelta: un brindisi dopo che ti sei seduto al banchetto, un desiderio dopo la moneta nel pozzo.
- **Oggetti chiave.** Chiavi, mappe e lanterne trovate in un evento aprono scelte segrete in un altro, a volte molti piani più in basso.
- **Il Labirinto ricorda.** Alcune scelte lasciano un segno che resta fra una run e l'altra: chi hai aiutato, chi hai derubato, quante volte hai accettato un patto. Le volte successive i personaggi possono riconoscerti.
- **Conseguenze differite.** Certe scelte tornano qualche piano dopo: una delle porte mostrerà "✦ qualcosa ti stava aspettando".
- **Personaggi ricorrenti.** *Sir Alaric*, il Primo Paladino, e *Silas*, il Cercatore, hanno una storia in tre capitoli che prosegue da una run all'altra: al massimo un capitolo per run, sempre più in profondità. Le tue scelte cambiano ciò che ti diranno e il loro destino. Un indizio: una lettera sulle pareti parla di un cavaliere stanco e di un fiore di lavanda. E chi libera Alaric non incontrerà più il Cavaliere Oscuro.
- **Combattimenti negli eventi.** Le ricompense legate a uno scontro arrivano solo se lo vinci; se fuggi, l'evento finisce lì.

---

## ⚔️ Il combattimento

A ogni turno scegli una di queste azioni:

- **Attacca.** La probabilità di colpire dipende dalla tua precisione, dalla schivata del nemico e dagli elementi.
- **Difenditi.** Dimezza i danni del prossimo colpo, e ogni classe aggiunge un effetto:
  - **Difesa Aggressiva** (Guerriero, Berserker): restituisci al nemico i danni subiti;
  - **Concentrazione** (Ladro, Assassino): il colpo successivo è un critico garantito;
  - **Riparo Magico** (le altre classi): recuperi il 5% degli HP.
- **Apri l'inventario.** Usare un oggetto o cambiare equipaggiamento **costa il turno**; chiudere lo zaino senza fare nulla no.
- **Statistiche Eroe.** Gratis, in qualsiasi momento. Mostrano la tua **probabilità reale di colpire** contro il nemico che hai davanti.
- **Tenta la fuga.** Riesce più spesso se sei agile. Contro i boss è impossibile.

### Gli elementi

| | Più forte contro | Più debole contro |
|---|---|---|
| 🔥 Fuoco | 🌪️ Vento | 💧 Acqua |
| 💧 Acqua | 🔥 Fuoco | 🪨 Terra |
| 🪨 Terra | 💧 Acqua | 🌪️ Vento |
| 🌪️ Vento | 🪨 Terra | 🔥 Fuoco |
| ✨ Luce | 🌑 Tenebra | ✨ Luce |
| 🌑 Tenebra | ✨ Luce | 🌑 Tenebra |

- Un colpo **Super Efficace** fa il 50% di danni in più e ha +15% di precisione.
- Un colpo **Poco efficace** fa la metà dei danni e ha −20% di precisione.
- In difesa conta l'elemento della tua **armatura**: un nemico forte contro di lei ti colpisce più spesso e più forte.

### Le Risonanze

Se **arma e armatura hanno lo stesso elemento** (non Normale), si attiva una Risonanza per tutto lo scontro:

| Risonanza | Effetto |
|---|---|
| 🔥 Fuoco | Ogni colpo a segno accumula 5 danni di Ustione, inflitti al nemico a ogni suo turno |
| 💧 Acqua | L'attacco del nemico è ridotto del 15% |
| 🪨 Terra | +5 Difesa |
| 🌪️ Vento | +15% Schivata |
| ✨ Luce | Ogni colpo a segno ti cura di 3 HP |
| 🌑 Tenebra | +5 danni a ogni colpo |

La Risonanza si ricalcola subito se cambi equipaggiamento durante lo scontro. Il dilemma di sempre: *meglio l'arma più forte o quella più debole che tiene accesa la Risonanza?*

### Status e maledizioni

- **Veleno e Sanguinamento.** Alcuni nemici li infliggono e fanno danni a ogni turno fino alla fine dello scontro. L'*Antidoto Universale* li toglie subito. Alcune armi speciali (Frusta di Spine, Pugnali del Vento, Falce del Mietitore, Balestra Gnomica, Tridente Oceanico) li infliggono ai nemici.
- **Equipaggiamento `[MALEDETTO]`.** Ha statistiche molto più alte del normale, ma drena HP, ruba Oro o (le armature) riduce la schivata. Si purifica al Falò per 100 Oro, oppure con l'*Acqua Santa*.

### Armi e armature speciali

Molte armi hanno un elemento casuale, ma quelle a tema hanno sempre il loro: il *Bastone dell'Alba* è di Luce, il *Tridente Oceanico* d'Acqua, e così via. Alcune hanno proprietà proprie, scritte nella loro descrizione:
- l'*Ascia del Boia*: −15% di precisione, ma 35% di critico;
- lo *Zweihander d'Oro*: più ATK quanto più oro porti;
- la *Veste Eterea*: +20% di schivata.

L'enciclopedia nel [README](README.md) le elenca tutte.

### Reliquie, livelli e fusioni

- **Reliquie.** Artefatti passivi trovati sconfiggendo i boss, nei forzieri o negli eventi. Ne porti al massimo **4**: trovandone una quinta, scegli quale sacrificare.
- **Livelli.** Con l'EXP sali di livello: +15 HP massimi, cura completa, +2% di precisione e di schivata.
- **Altare dell'Evoluzione.** Al Falò, fondi due armi (o due armature) dello zaino: la prima assorbe metà delle statistiche della seconda e sale di livello.

---

## 🧬 Gli eroi

| Eroe | Punti di forza | Come si sblocca |
|---|---|---|
| ⚔️ **Guerriero** | 120 HP, solido, contrattacca in difesa | Subito |
| 🗡️ **Ladro** | Schivata alta, 100 Oro iniziali, critico garantito dopo la Concentrazione | Subito |
| 🔮 **Mago** | Bastone di Fuoco potente e mira eccellente, ma solo 65 HP | Subito |
| 🛡️ **Paladino** | 180 HP e Risonanza di Luce fin dall'inizio | Maestria Guerriero Lv.5 |
| 🪓 **Berserker** | L'ascia più forte, nessuna armatura | Impresa *Danza con la Morte* |
| 🧪 **Alchimista** | 4 pozioni iniziali e bombe di Fuoco | Impresa *Genio Elementale* |
| 🥷 **Assassino** | 20% di critico innato e 30% di schivata, ma solo 75 HP | Maestria Ladro Lv.5 |
| 💀 **Negromante** | Risonanza di Tenebra fin dall'inizio | Maestria Mago Lv.5 |

### La Maestria

Ogni eroe ha un albero di **Maestria** a 5 livelli, che sale con l'esperienza accumulata nelle sue discese:

- **Lv.2** — un bonus personale (es. *Imboscata* dell'Assassino: il primo attacco di ogni scontro fa danni doppi).
- **Lv.3** — sblocca un oggetto (es. la *Bomba Fumogena* per il Ladro).
- **Lv.4** — un'**Eredità**: un bonus permanente per **tutti** gli eroi.
- **Lv.5** — sblocca una nuova classe, un tratto o una reliquia.

---

## 🎭 Tratti e Patti del Caos

**Tratti.** Si sceglie un tratto a ogni partenza:

| Tratto | Effetto |
|---|---|
| Nessun Tratto | Regole standard |
| Patto del Sangue | +50 ATK, ma HP massimi dimezzati e nessuna cura ha effetto |
| Tocco di Mida | Oro ×3, ma niente EXP dai mostri |
| Aristocratico | +500 Oro iniziali, ma i nemici non lasciano Oro |
| Cacciatore Etereo | Il primo attacco nemico di ogni scontro manca sempre, ma −20% Schivata |
| Titano | +100 HP, ma precisione e schivata dimezzate |
| Benedetto | Inizi con lo Scudo di Cristallo e resisti al primo colpo letale |

**Patti del Caos.** Dopo la prima vittoria puoi attivare all'inizio di ogni discesa fino a 5 maledizioni. Ognuna aggiunge +25% all'Essenza finale, fino a **×2,25** con tutte e cinque:

| Patto | Effetto |
|---|---|
| Durezza | HP dei nemici +30% |
| Furia | Attacco dei nemici +30% |
| Carestia | Le pozioni curano la metà |
| Inflazione | Prezzi del mercante raddoppiati |
| Labirinto Mortale | Le trappole fanno danni doppi |

---

## 🏕️ Il Campo Base

Tra una discesa e l'altra spendi l'**Essenza Astrale**:

- **🔥 Fuoco dell'Anima** — 14 potenziamenti permanenti. Tra questi:
  - *Speranza di Luce*: recuperi fino al 15% degli HP massimi a ogni piano;
  - *Benedizione dell'Altare*: inizi con una reliquia casuale;
  - *Sesto Senso*: vedi cosa c'è dietro le porte.
- **⚒️ Forgia Dimensionale** — sblocca armi, armature, monili, consumabili e reliquie, che da quel momento possono comparire nel labirinto. Le categorie diverse dalle reliquie si aprono liberando l'artigiano corrispondente.
- **🍺 Taverna** — mostra le classi ancora da conquistare.
- **📜 Grimorio** — imprese completate e livelli di Maestria.
- **📚 Archivio di Aethelgard** — tre tomi da sbloccare scendendo nel labirinto. Ognuno dà un bonus permanente: più Oro e fuga, danni contro i boss, difesa.
- **📖 Il Codice del Labirinto** — tutto ciò che hai scoperto, raccolto fra una run e l'altra, con la percentuale di completamento. Ciò che manca è segnato con ???.
  - *Bestiario*: nemici e boss incontrati e sconfitti; la loro storia si legge solo dopo averli battuti.
  - *Personaggi*: i capitoli vissuti con Alaric e Silas, e il segno lasciato dalle tue scelte.
  - *Eventi*: quali hai visto e quante volte.
  - *Lettere insanguinate*: i messaggi letti sulle pareti prima degli scontri.
  - *Reliquie*: quelle che hai trovato almeno una volta, con la loro lore.
- **🧑‍🔧 Gli artigiani** — liberali dagli eventi del labirinto:
  - lo *Speziale* (consumabili);
  - *Borek* (armi);
  - *Elara* (armature);
  - *Valerius* (monili).

  Ognuno vende per poca Essenza un oggetto con cui iniziare la discesa successiva: uno per bottega a ogni partenza.

### Come si guadagna l'Essenza

| Fine della discesa | Essenza |
|---|---|
| ☠️ Morte | 20% dell'Oro posseduto |
| 🏃 Fuga dal labirinto | 100% dell'Oro |
| 🏆 Vittoria al piano 30 | 100% dell'Oro + 1.000 (e la leggendaria *Lama del Creatore*) |

Si aggiungono **50 Essenza per ogni boss** sconfitto, il moltiplicatore dei Patti e, oltre il piano 30 in **Modalità Infinita**, un ulteriore ×1,5.

---

## 💡 Consigli per sopravvivere

- **Guarda gli elementi prima di attaccare.** Un'arma Super Efficace colpisce più spesso e più forte: a volte conviene cambiarla, anche se costa un turno.
- **Difenditi contro i colpi forti.** Dimezzare un attacco del boss vale spesso più di un tuo colpo.
- **Non sottovalutare la fuga.** Uscire al momento giusto con tanto Oro rende più Essenza di una morte gloriosa.
- **Usa l'Altare dell'Evoluzione.** Le armi doppie nello zaino valgono più come materiale da fusione che come merce da vendere.
- **Libera gli artigiani.** Partire con un'arma o un monile scelto da te cambia l'inizio di ogni discesa.
- **Prova tutti gli eroi.** Le Eredità di Maestria (Lv.4) rafforzano tutti gli altri.
