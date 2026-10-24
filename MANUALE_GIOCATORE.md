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

1. **Scegli l'eroe e il tratto.** Dopo la prima vittoria scegli anche il grado di **Ascensione** (vedi *Modalità*).
2. **Ogni piano ha una mappa.** All'arrivo vedi tutto il piano: quattro file di stanze collegate, e in fondo il boss (★). A ogni tappa scegli una delle stanze collegate a quella in cui ti trovi: in giallo le stanze raggiungibili, in verde il percorso fatto, in grigio ciò che ormai è fuori strada. Pianifica: un falò due file più in basso vale una deviazione? Con il potenziamento *Sesto Senso* vedi anche quale nemico o evento ti aspetta.
3. **La quinta tappa è sempre un boss.**
4. **Superato il piano** recuperi un po' di HP (20 + 5 per piano) e scendi.
5. In qualsiasi bivio puoi scegliere **Fuga dal Labirinto**: porti a casa tutto l'Oro, convertito in Essenza.

Più scendi, più i nemici sono forti: ai primi piani incontri banditi, goblin e scheletri, verso il fondo idre di lava e leviatani. Anche i boss crescono con la profondità, e il DIO ANTICO compare **solo al piano 30**.

```text
  1      🎭 Evento      ❓ Mistero      💰 Mercante
             │         ╱          ╲          │
             │    ╱                    ╲     │
  2     💎 Forziere                     🎭 Evento📿
             │    ╲                    ╱     │
             │         ╲          ╱          │
  3     ❓ Mistero      👹 Scontro      💀 Trappola
             │         ╱          ╲          │
             │    ╱                    ╲     │
  4     👹 Scontro                      ❓ Mistero
                  ╲                    ╱
                       ╲          ╱
  ★                       👑 Boss
```

### 🩸 La Corruzione

Alcune scelte degli eventi sono **oscure**: pregare l'Altare del Sangue, accettare i doni del Labirinto, colpire chi è debole. Altre sono **pure**: bere alla Fontana Fatata, giurare sul tuo onore, spezzare un sigillo. Il riepilogo di ogni scelta mostra quanta Corruzione ti dà o ti toglie, ad esempio `(+100 Oro; -40 HP; +10 Corruzione)`.

La Corruzione va da 0 a 100 e vale per la sola discesa:
- **Potere.** Ogni 10 punti ti danno +2 ATK, e alcune opzioni proibite compaiono solo a chi è abbastanza corrotto, come `[Corruzione 50+] Chiedi di vedere il fondo`.
- **Sguardo Velato (da 50).** Il 25% delle volte il Labirinto ti offusca la vista: non vedi gli effetti di una scelta.
- **Voce del Labirinto (da 75).** Il 30% delle volte non vedi la mossa che il nemico prepara.

La vedi accanto agli HP sulla mappa e nelle Statistiche. Arrivare in fondo con il cuore nero apre un finale che gli altri non vedranno mai.

### 😈 La Nemesi

Il nemico comune o l'Élite che ti uccide **se ne ricorda**: diventa una **Nemesi**, con un nome, un rango e un tratto imparato da te, e si prende il 50% dell'Oro che avevi.

- **Torna a cercarti.** Nelle discese successive compare una volta, in una stanza 😈 della mappa, fra 1 piano prima e 2 dopo quello in cui ti ha ucciso. L'etichetta dice chi è e quanto Oro ha con sé.
- **Cresce.** Ha il 10% di HP e Attacco in più per ogni rango. Se ti uccide di nuovo sale di rango (fino a 5: il Fortunato, il Persecutore, il Flagello, l'Incubo, la Fine) e aggiunge il tuo Oro al suo.
- **Si vendica di te.** Ognuna ha uno di questi tratti:

| Tratto | Effetto |
|---|---|
| Ha imparato a resistere | I colpi dell'elemento con cui ti ha ucciso gli fanno il 40% di danni in meno. |
| Più grosso di come lo ricordi | Ha il 20% di HP in più. |
| Conosce i tuoi movimenti | Ha +15 di Precisione. |
| Affamato di vendetta | Ha il 15% di Attacco in più. |

- **Sconfiggerla** restituisce tutto l'Oro che aveva e lascia un **trofeo**, un pezzo d'equipaggiamento epico. Vale 2 punti di Audacia, come un'Élite.
- Le Nemesi attive sono al massimo 3: una nuova scaccia la più vecchia. I **boss** non diventano Nemesi, ma ti riconoscono la volta dopo.
- Nel Codice, alla pagina *Nemesi*, trovi chi ti aspetta e chi hai già sconfitto.

### 🪦 L'Epitaffio e il Cimitero

Durante la discesa il gioco annota i momenti che contano: i biomi attraversati, gli eventi, le reliquie trovate, i boss abbattuti, le parole runiche composte, le Nemesi sconfitte, il finale scelto e come è finita. A fine partita ne fa un **epitaffio** di poche frasi: come è finita, fino a 3 fatti della discesa (prima il grado di Ascensione o la Sfida del Giorno, poi le Nemesi sconfitte, i boss, le parole runiche, le reliquie, l'ultimo evento, i biomi, la Corruzione alta) e chi o cosa ti ha ucciso. La stessa discesa dà sempre lo stesso epitaffio.

Gli epitaffi delle ultime 50 discese restano nel **Cimitero**, una pagina del Codice: lì leggi anche quale Nemesi è nata da quale morte.

### 🏁 I finali

Sconfitto il Dio Antico, scegli come finisce la tua storia fra i finali che ti sei guadagnato. Il primo è sempre disponibile; gli altri dipendono da quello che hai fatto in questa discesa e in quelle passate: i personaggi che hai liberato, le verità che hai ascoltato, le lettere che hai raccolto, la tua Corruzione. Ogni finale nuovo dà un premio in Essenza e finisce nel Codice. Nel Codice i finali che non hai ancora visto mostrano un indizio.

### I biomi

Il Labirinto cambia mentre scendi: ogni cinque piani entri in un **bioma** diverso, con la sua atmosfera. I nomi vengono dalle cronache di Aethelgard: *I Chiostri del Rimpianto*, *Le Miniere della Testardaggine*, *Le Guglie del Vento Urlante*, *Il Ventre della Memoria*, *La Forgia del Caos*, *La Soglia del Dio Antico*.

**📿 I Chiostri del Rimpianto (piani 1–5).** Le rovine di un'accademia della Luce Calma.
- **Più eventi, meno trappole.** E più creature di Luce e di Tenebra.
- **Nativi.** L'*Eco del Rimpianto*, la *Statua di Sale*, la *Novizia del Silenzio* (che sigilla la tua difesa), il *Corista Spento*, che si rigenera, il *Bibliotecario di Cenere*, che carica i suoi incantesimi, l'*Ombra del Novizio*, che ti prosciuga, e un boss, *La Badessa del Silenzio*, vivono solo qui.
- **Pericolo: Nostalgia Letale.** In ogni piano una stanza, segnata con 📿, ospita un'eco del passato: *La Voce Cara*, *La Statua di Sale*, *La Biblioteca di Cenere*, *Il Coro Spento* o *Il Lavabo dei Ricordi*. Fermarsi ad ascoltare può guarirti… o trasformarti in sale, e il Labirinto se ne ricorderà.
- **Segreto.** Al piano 3, sotto il marmo, si dice riposi la *Prima Pietra* posata dagli Architetti.

**🦇 Le Miniere della Testardaggine (piani 6–10).** Basalto, olio nero e ingranaggi che girano a vuoto.
- **Più forzieri, meno falò.** E più creature di Terra.
- **Nativi.** Il *Minatore Svuotato*, l'*Ingranaggio Senziente*, che si ripara spesso, la *Talpa Esplosiva* e il *Carrello Posseduto*, che caricano il colpo, la *Lucciola del Grisù*, imprevedibile, e il *Guardiano di Basalto*, che alza barriere. Il boss è *Il Caposquadra Sepolto*: carica i colpi e, quando la galleria crolla, si ripara dietro una barriera.
- **Pericolo: Gas del Silenzio.** In ogni scontro c'è il 35% di probabilità che il gas riempia la stanza. La tua Difesa dimezza ancora i danni, ma perde la tecnica della classe.
- **Stanze speciali:** *La Galleria del Gas*, *L'Ingranaggio Fermo*, *Il Carrello Abbandonato*, *Il Minatore Cieco*.

**🌀 Le Guglie del Vento Urlante (piani 11–15).** Ponti sospesi su nubi elettriche.
- **Più trappole, meno mercanti.** E più creature di Vento.
- **Nativi.** La *Sentinella di Nube*, il *Falco Astrale* e l'*Aquila di Tempesta*, difficilissimi da colpire, il *Corvo del Tuono*, che raccoglie il fulmine, lo *Spirito del Ponte*, che ti sigilla la difesa, e l'*Astronomo Caduto*. Il boss è *L'Astronoma delle Guglie*: ti sigilla la difesa e, sotto la pioggia di stelle, colpisce più forte.
- **Pericolo: Caduta Astrale.** Sui ponti sospesi puoi perdere l'equilibrio. Precipiti al piano successivo, senza riposo e senza il boss, e perdi il 40% dell'Oro. Puoi anche lasciarti cadere di proposito: un modo rischioso per saltare un boss.
- **Stanze speciali:** *Il Ponte Sospeso*, *Il Nido della Tempesta*, *L'Osservatorio del Vento*, *Il Fabbro del Cielo*.

**🌊 Il Ventre della Memoria (piani 16–20).** Pareti di membrana con dentro i volti dei morti.
- **Più eventi e misteri.** E più creature d'Acqua e di Tenebra.
- **Nativi.** Il *Ricordo Annegato*, che si rigenera, il *Volto nella Membrana*, che fa sanguinare, la *Medusa della Memoria*, che avvelena, la *Sanguisuga Madre* e la *Lacrima Vivente*, che ti prosciugano, e la *Bambola di Ricordi*, che sigilla la difesa. Il boss è *Il Cuore del Ventre*: avvelena, ti prosciuga e, quando comincia la digestione, si rigenera.
- **Pericolo: Dissoluzione dell'Io.** A ogni piano del Ventre perdi il 4% degli HP massimi. Li ritrovi tutti quando ne esci.
- **Stanze speciali:** *Il Volto nella Membrana*, *Il Giardino Appassito*, *Il Nido delle Sanguisughe*, *L'Eco della Madre*.

**🌋 La Forgia del Caos (piani 21–25).** Lava bianca, fumi neri, martelli ciclopici.
- **Più mercanti, meno falò.** E più creature di Fuoco.
- **Nativi.** Il *Golem di Scorie*, il *Martello Errante* e l'*Apprendista di Scoria*, che amano i colpi pesanti, lo *Scudiero di Scoria*, che alza barriere, la *Scintilla Ribelle*, imprevedibile, e il *Crogiolo Ambulante*, che si rifonde. Il boss è *Il Maestro di Forgia*: picchia duro e, con la Tempra, si copre di Scaglie che solo una reazione infrange.
- **Pericolo: Ebollizione Astrale.** Ogni colpo che subisci ha il 25% di probabilità di far bollire il 5% del tuo Oro.
- **Stanze speciali:** *L'Incudine Cosmica*, *La Colata d'Oro*, *Il Crogiolo delle Rune*, *Il Forgiatore Incatenato*.

**🌌 La Soglia del Dio Antico (piani 26–30).** Piattaforme di pura volontà nel vuoto.
- **Più misteri e forzieri.** E creature di Luce e di Tenebra.
- **Nativi.** Il *Frammento di Galassia*, l'*Eco del Dio Antico* e il *Frammento del Prima*, che sigilla e prosciuga, il *Riflesso Futuro*, che carica il colpo, il *Vuoto Affamato*, che ti divora, e la *Clessidra Infranta*, che si ripara. Il boss è *Il Custode della Soglia*: a metà della vita la sua Luce si rovescia in Tenebra.
- **Pericolo: Paradosso Temporale.** Dopo ogni tuo turno c'è il 10% di probabilità che tu agisca di nuovo; dopo ogni turno nemico, il 15% che il nemico agisca due volte (con una mossa non annunciata).
- **Stanze speciali:** *L'Occhio Chiuso*, *L'Eco del Tempo*, *La Biblioteca del Vuoto*, *La Porta del Ritorno*.

In ogni piano una stanza della mappa, segnata con l'icona del bioma, è una delle sue stanze speciali.

### Le stanze

| Stanza | Cosa succede |
|---|---|
| 👹 **Scontro** | Un nemico adatto al piano. La mappa mostra quanta EXP vale; vincendo ottieni anche Oro e a volte una pozione. |
| 👺 **Élite** | Dal piano 2. Un campione più duro (HP ×1,6, ATK ×1,3) che vale il doppio di EXP e Oro e lascia sempre una **reliquia o un pezzo d'equipaggiamento**, a volte epico. |
| 💰 **Mercante** | Compra armi, armature, monili e pozioni; vendi ciò che non ti serve. Dopo ogni acquisto il resto della merce rincara del 10%. |
| 🔥 **Falò** | *Riposa* (50% degli HP) **oppure** *affila l'arma* (+3 ATK per 50 Oro): una delle due, poi il falò si spegne. Prima puoi usare l'**Altare dell'Evoluzione**, la **purificazione** e le **Rune e Incastoni** quante volte vuoi. |
| 💎 **Forziere** | Oro, a volte un monile, una pozione o una reliquia. Dal piano 3 può essere **chiuso a chiave** (lo forzi pagando l'8% degli HP massimi, in cambio di un bottino garantito) o un **Mimic**: un mostro che, sconfitto, restituisce il doppio. La mappa mostra la probabilità del rischio, che cresce con la profondità. A volte il coperchio sembra respirare: può essere un Mimic, ma anche no. |
| 💀 **Trappola** | Custodisce sempre un oggetto. Scegli come affrontarla: **disinnescarla** (prova di Precisione, se riesce recuperi anche dell'Oro), **attraversarla di corsa** (prova di Schivata) o **tornare indietro** senza danni e senza bottino. Il menu mostra le probabilità e i danni in caso di fallimento; chi la affronta prende il bottino anche se la prova fallisce. |
| 🎭 **Evento** | Una piccola storia con bivi, a volte in più scene: vedi *Gli eventi* qui sotto. Alcuni nascondono un artigiano prigioniero da liberare. |
| ❓ **Mistero** | Un azzardo: un tesoro nascosto (Oro e un monile), una reliquia, un nemico potenziato (che lascia un oggetto), uno debilitato, una trappola… o niente. In media rende più di un forziere. Con il *Sesto Senso* la mappa mostra le probabilità. |

### L'Audacia

Ogni rischio corso nel piano riempie l'**Audacia** (🎲, accanto agli HP): +1 per uno scontro, una trappola affrontata o un mistero, +2 per un'Élite. Il boss del piano paga l'Audacia accumulata: +15% di Oro per punto, un pezzo d'equipaggiamento da 5 punti, epico da 7. A ogni piano si riparte da zero. Chi passa solo da forzieri ed eventi arriva al boss con il premio base; chi rischia ottiene molto di più, se sopravvive.

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
  - **Riparo Magico** (Mago): recuperi il 10% degli HP;
  - **Voto di Protezione** (Paladino): ti liberi da Veleno e Sanguinamento e recuperi il 5% degli HP;
  - **Mistura Reattiva** (Alchimista): recuperi il 5% degli HP e marchi il nemico con l'elemento della tua arma. Se poi ti colpisce, il marchio della tua armatura può scatenare una **reazione**, e con l'equipaggiamento iniziale (Fuoco e Terra) scatena il *Magma*;
  - **Sudario d'Ossa** (Negromante): strappi al nemico il 4% dei suoi HP massimi e li recuperi tu. Se gli restano pochi HP, può bastare ad abbatterlo.
- **Apri l'inventario.** Usare un oggetto o cambiare equipaggiamento **costa il turno**; chiudere lo zaino senza fare nulla no.
- **Statistiche Eroe.** Gratis, in qualsiasi momento. Mostrano la tua **probabilità reale di colpire** contro il nemico che hai davanti.
- **Tenta la fuga.** Riesce più spesso se sei agile. Contro i boss è impossibile.

### Gli intenti dei nemici

Prima di ogni tuo turno il nemico **annuncia la sua prossima mossa**, con i danni previsti:

```text
Tu: 210/210 HP | Badessa del Silenzio: 120/180 HP [marchio 💧 Acqua]
Intento del nemico: 💢 Colpo pesante (≈24 danni) — difenditi!
```

| Mossa | Cosa fa | Come rispondere |
|---|---|---|
| 👊 Attacco | Un attacco normale | — |
| 💢 Colpo pesante | La sua forza raddoppia prima della tua difesa | **Difenditi**: dimezzi il colpo (e la Difesa Aggressiva lo restituisce) |
| 🧱 Guardia | Non attacca; i tuoi colpi fanno il 50% dei danni | È il turno giusto per curarti, difenderti o usare un oggetto |
| 💚 Rigenerazione | Non attacca; recupera il 15% degli HP massimi (solo sotto il 60%, al massimo due volte) | Colpisci forte prima |
| 🧪 Colpo infetto | Se ti ferisce, infligge di sicuro il suo status (veleno, sanguinamento) | Difenditi o tieni pronto l'antidoto |
| 🩸 Prosciugamento | Un attacco che lo cura di tanti HP quanti te ne toglie | Difenditi: dimezzi sia il danno sia la sua cura |
| 🔒 Sigillo | Non attacca; al tuo prossimo turno non puoi difenderti | Cùrati o attacca adesso; il Sigillo dura un turno |
| ⏳ Carica | Non attacca; il turno dopo arriva il **Colpo caricato** (l'intento mostra già i danni) | Preparati: il turno dopo difenditi |
| 💥 Colpo caricato | Arriva sempre dopo la Carica: la sua forza triplica prima della tua difesa | **Difenditi**, o abbattilo prima |
| 💠 Barriera | Non attacca; riporta il suo scudo al 20% degli HP massimi (non si somma a quello che ha già), e lo scudo assorbe i danni dei tuoi attacchi | Lo scudo si consuma colpendo: conviene continuare ad attaccare |

Colpo pesante, Guardia, Sigillo, Carica e Barriera non si ripetono mai due volte di fila. I boss si rigenerano più spesso.

Quasi ogni nemico ha uno **stile**, che decide quali mosse preferisce. Dopo averlo sconfitto lo trovi scritto nel *Bestiario*:

| Stile | Mosse preferite | Chi lo usa, per esempio |
|---|---|---|
| **Bruto** | Colpi pesanti | Orco, Idra di Lava, Minatore Svuotato |
| **Predatore** | Carica e colpi pesanti | Lupo Mannaro, Arpia del Labirinto, Falco Astrale |
| **Difensore** | Guardia e Barriera | Gargoyle, Costrutto Magico, Paladino Corrotto |
| **Succhiavita** | Prosciugamento | Golem di Sale, Sirena Abissale |
| **Infetto** | Colpi infetti | Melma Acida, Manticora Infetta, Volto nella Membrana |
| **Mistico** | Sigillo e Rigenerazione | Chierico Corrotto, Cultista Cieco, Eco del Rimpianto |
| **Furia** | Colpi pesanti e cariche | Elementale del Fuoco, Spirito della Tempesta |

Goblin, Scheletri e Banditi, i primi nemici che incontri, combattono senza uno stile preciso. Alcuni nativi dei biomi e i Vampiri hanno mosse tutte loro.

### Le fasi dei boss

Ogni boss, arrivato a una soglia di HP (di solito il 50%), **cambia fase**: lo annuncia con un nome e una frase, e mostra cosa è cambiato. Il turno in cui si trasforma non attacca. Il DIO ANTICO ha tre fasi.

Una fase può:

- cambiargli l'**elemento** (il DIO ANTICO diventa quello che colpisce meglio la tua armatura);
- aumentargli l'**attacco**, o fargli **recuperare** HP;
- dargli uno **scudo**, che assorbe i danni dei tuoi attacchi finché non lo consumi;
- coprirlo di **Scaglie**: i tuoi attacchi fanno metà dei danni finché una **reazione elementale** non le infrange;
- rendere i suoi colpi **infetti** (sanguinamento più probabile);
- cambiargli le **mosse**: Sigillo, Carica, Prosciugamento, Barriera.

Le fasi che hai visto finiscono nel Codice, alla pagina *Fasi dei boss*; quelle che non hai ancora visto restano "???".

### Marchi e reazioni elementali

- **Il marchio.** Ogni tuo colpo a segno lascia sul nemico il **marchio** dell'elemento della tua arma, per due suoi turni.
- **L'armatura.** Quando ti **difendi** e il nemico ti colpisce, l'armatura lo marchia con il *suo* elemento.
- **La reazione.** Se un nemico marchiato riceve un elemento diverso, i due possono **reagire**:

| Reazione | Elementi | Effetto |
|---|---|---|
| 💨 Vapore | 🔥 + 💧 | Danni extra pari al 50% del tuo ATK; il nemico è Accecato (−25% Precisione) per 2 turni |
| 🔥 Incendio | 🔥 + 🌪️ | Danni extra pari al 100% del tuo ATK |
| 🌋 Magma | 🔥 + 🪨 | Il nemico perde il 5% degli HP massimi a ogni turno, per 3 turni |
| 🧊 Gelo | 💧 + 🌪️ | Il nemico perde il suo prossimo turno, anche un colpo pesante annunciato |
| 🟤 Fango | 💧 + 🪨 | Il nemico è Impantanato (−25% Schivata) per 3 turni |
| 🌀 Tempesta di Sabbia | 🪨 + 🌪️ | Il nemico è Accecato (−25% Precisione) per 3 turni |
| 🌗 Eclissi | ✨ + 🌑 | Danni extra pari al 150% del tuo ATK |

Il ritmo tipico è *colpisci, poi difenditi*, oppure *difenditi, poi colpisci*. Ed ecco il nuovo dilemma dell'equipaggiamento:
- **Stesso elemento** su arma e armatura: accende la **Risonanza**, ma non dà mai reazioni.
- **Elementi diversi**: rinunci alla Risonanza, ma puoi scatenare le reazioni.

Le reazioni che scopri finiscono nel **Codice**.

**Difesa.** L'armatura riduce ogni colpo della sua difesa, ma **non lo annulla mai**: almeno il 20% del colpo arriva sempre. Gli oggetti che trovi crescono con i nemici del piano in cui li trovi. Un'arma comune abbatte un nemico tipico in circa tre colpi; un'armatura comune ne assorbe circa il 40%, quella migliore poco più della metà.

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

- **Veleno e Sanguinamento.** Alcuni nemici li infliggono e tolgono a ogni turno una parte degli HP massimi (il 4% il veleno, il 5% il sanguinamento) finché durano. L'*Antidoto Universale* li toglie subito. Alcune armi speciali (Frusta di Spine, Pugnali del Vento, Falce del Mietitore, Balestra Gnomica, Tridente Oceanico) li infliggono ai nemici.
- **Equipaggiamento `[MALEDETTO]`.** Ha statistiche più alte del 30%, ma drena il 2% degli HP massimi a ogni turno, ruba Oro o (le armature) riduce la schivata. Si purifica al Falò per 100 Oro, oppure con l'*Acqua Santa*.

### Armi e armature speciali

Molte armi hanno un elemento casuale, ma quelle a tema hanno sempre il loro: il *Bastone dell'Alba* è di Luce, il *Tridente Oceanico* d'Acqua, e così via. Alcune hanno proprietà proprie, scritte nella loro descrizione:
- l'*Ascia del Boia*: −15% di precisione, ma 35% di critico;
- lo *Zweihander d'Oro*: più ATK quanto più oro porti;
- la *Veste Eterea*: +20% di schivata;
- le armature elementali, come le *Vesti di Brace* (Fuoco) o il *Giaco del Vento* (Vento, +8% di schivata): sempre del loro elemento, quindi utili per cercare una Risonanza o una reazione;
- le armature pesanti, come la *Corazza del Penitente*: tanta difesa, meno schivata.

L'enciclopedia nel [README](README.md) le elenca tutte.

### Reliquie, livelli e fusioni

- **Reliquie.** Artefatti passivi trovati sconfiggendo i boss, nei forzieri o negli eventi. Ne porti al massimo **4**: trovandone una quinta, scegli quale sacrificare. Molte si combinano con una strategia: veleno e sanguinamento (l'*Ago dell'Untore* li raddoppia), oro (la *Bilancia del Mercante* trasforma l'Oro in Attacco), reazioni elementali (il *Catalizzatore Antico*), difesa (il *Corno del Bastione*), rune (il *Cristallo Runico* le potenzia del 50%), Nemesi ed Élite (il *Marchio del Cacciatore*). L'enciclopedia nel README le elenca tutte.
- **Livelli.** Con l'EXP sali di livello: +15 HP massimi, cura completa, +2% di precisione e di schivata.
- **Altare dell'Evoluzione.** Al Falò, fondi due armi (o due armature) dello zaino: la prima assorbe metà delle statistiche della seconda e sale di livello. Le rune della prima restano; quelle della seconda tornano nello zaino.

### Rune e Incastoni

Armi e armature hanno degli **incastoni** (accanto al nome: `[Incastoni: ◇]` per un incastone libero, `[Incastoni: 🔪◇]` con una runa incastonata e uno libero): 1 per gli oggetti comuni, 2 per gli epici, 3 per i premi dei boss. Anche l'equipaggiamento iniziale ne ha uno.

- **Dove si trovano le rune.** Le lasciano le Élite (35%), i boss (60%), le trappole affrontate (15%), i tesori del Mistero (30%) e i Mimic (35%); il Mercante ne vende 1.
- **Incastonare.** Al Falò, voce *Rune e Incastoni*: incastonare è gratis e il falò resta acceso. Ogni runa va su un'arma, su un'armatura o su entrambe.
- **Estrarre.** Costa 30 Oro più 5 per piano, e la runa torna nello zaino. Cambiando arma le rune restano su quella vecchia: spostarle è una scelta.
- **Oggetti per le rune.** Il *Solvente Runico* estrae gratis una runa dall'equipaggiamento; lo *Scalpello Runico* (dalla Forgia) apre un incastone in più nell'arma o nell'armatura, fino a 3. Alcune armature hanno sempre più incastoni: la *Corazza Runica* almeno 2, l'*Armatura del Custode* 3.
- **Contano solo le rune dell'arma e dell'armatura equipaggiate.** Quelle che trovi finiscono nel Codice, alla pagina *Rune*.

| Runa | Famiglia | Dove | Effetto |
|---|---|---|---|
| 🔁 Runa dell'Eco | Elementale | Arma | I marchi della tua arma durano 1 turno in più. |
| 🌀 Runa della Catalisi | Elementale | Arma | Le reazioni elementali infliggono il 30% di danni in più. |
| 🌗 Runa del Contrasto | Elementale | Arma | I colpi Super Efficaci infliggono il 15% di danni in più. |
| 🌹 Runa della Spina | Status | Arma | I tuoi colpi hanno il 10% di probabilità di far sanguinare il nemico. |
| 🐍 Runa della Vipera | Status | Arma | I tuoi colpi hanno il 10% di probabilità di avvelenare il nemico. |
| 🎯 Runa dell'Occhio | Offensiva | Arma | +5% di probabilità di colpo critico. |
| 💪 Runa della Forza | Offensiva | Arma | +6% di Attacco. |
| 🩸 Runa del Sangue | Offensiva | Arma | Ti curi del 5% dei danni che infliggi con gli attacchi. |
| 🔪 Runa dell'Agguato | Offensiva | Arma | Il primo attacco di ogni scontro infligge il 50% di danni in più. |
| 🪨 Runa della Pietra | Difensiva | Armatura | +8% di Difesa dell'armatura. |
| 🍃 Runa del Vento | Difensiva | Armatura | +4% di Schivata. |
| 🌵 Runa del Rovo | Difensiva | Armatura | Chi ti ferisce subisce l'8% dei danni che ti ha inflitto. |
| 🌙 Runa della Quiete | Difensiva | Armatura | Quando ti difendi recuperi il 2% degli HP massimi. |
| 🪙 Runa dell'Avidità | Utilità | Arma o armatura | +10% di Oro raccolto. |
| 📘 Runa del Sapere | Utilità | Arma o armatura | +10% di EXP. |
| 🦁 Runa del Coraggio | Utilità | Arma o armatura | Ogni piano inizia con 1 punto di Audacia. |
| 👣 Runa del Passo | Utilità | Arma o armatura | +10 alle prove delle trappole. |

### Parole runiche

Certe combinazioni di rune **sullo stesso oggetto** formano una **parola runica**: oltre agli effetti delle singole rune ne aggiungono uno proprio, e il nome dell'oggetto la mostra fra «». Ogni runa vale per una sola parola; le parole di tre rune hanno la precedenza (servono un oggetto epico o un premio di boss). La prima volta che ne componi una al Falò viene annunciata e finisce nel Codice, alla pagina *Parole runiche*: di quelle che non conosci vedi quante rune servono e, se l'hai già trovata, la prima.

| Parola | Rune | Effetto in più |
|---|---|---|
| «Tempesta Elementale» | Runa della Catalisi + Runa del Contrasto | Le reazioni infliggono il 30% di danni in più e i colpi Super Efficaci il 10% in più. |
| «Veleno di Spine» | Runa della Spina + Runa della Vipera | I tuoi colpi hanno anche il 10% di probabilità di bruciare il nemico con il Magma. |
| «Colpo del Boia» | Runa della Forza + Runa dell'Occhio | +8% di probabilità di colpo critico. |
| «Bacio del Vampiro» | Runa del Sangue + Runa dell'Agguato | Ti curi di un altro 5% dei danni inflitti e il primo attacco di ogni scontro fa il 25% di danni in più. |
| «Prisma» | Runa dell'Eco + Runa della Catalisi + Runa del Contrasto | I tuoi colpi hanno l'8% di probabilità di congelare il nemico e i marchi durano 1 turno in più. |
| «Fortezza di Spine» | Runa della Pietra + Runa del Rovo | Chi ti ferisce subisce un altro 6% dei danni e la Difesa dell'armatura sale del 5%. |
| «Passo del Monaco» | Runa del Vento + Runa della Quiete | +4% di Schivata e difendendoti recuperi un altro 1% degli HP massimi. |
| «Patto del Mercante» | Runa dell'Avidità + Runa del Sapere | +10% di Oro e +10% di EXP. |
| «Cuore Temerario» | Runa del Coraggio + Runa del Passo | Ogni piano inizia con 1 punto di Audacia in più e +10 alle prove delle trappole. |
| «Egida Silente» | Runa della Pietra + Runa del Vento + Runa della Quiete | +6% di Difesa dell'armatura e +3% di Schivata. |

---

## 🧬 Gli eroi

| Eroe | Punti di forza | Come si sblocca |
|---|---|---|
| ⚔️ **Guerriero** | 120 HP, solido, contrattacca in difesa. Spada di Terra, cotta d'Acqua: *Fango* | Subito |
| 🗡️ **Ladro** | Schivata alta, 100 Oro iniziali, critico garantito dopo la Concentrazione. Pugnali di Vento, cuoio d'Acqua: *Gelo* | Subito |
| 🔮 **Mago** | Bastone di Fuoco potente e mira eccellente, ma solo 80 HP; si cura quando si difende. Vesti di Vento: *Incendio* | Subito |
| 🛡️ **Paladino** | 180 HP e Risonanza di Luce fin dall'inizio; difendendosi si libera da veleno e sanguinamento | Maestria Guerriero Lv.5 |
| 🪓 **Berserker** | L'ascia più forte, nessuna armatura | Impresa *Danza con la Morte* |
| 🧪 **Alchimista** | 4 pozioni iniziali e bombe di Fuoco; difendendosi lancia una fiala che prepara la reazione. Grembiule di Terra: *Magma* | Impresa *Genio Elementale* |
| 🥷 **Assassino** | 15% di critico innato e 20% di schivata, ma solo 75 HP. Pugnale di Vento, mantello di Terra: *Tempesta di Sabbia* | Maestria Ladro Lv.5 |
| 💀 **Negromante** | Risonanza di Tenebra fin dall'inizio; difendendosi ruba vita al nemico | Maestria Mago Lv.5 |

Ogni eroe parte con un equipaggiamento che ha già un'idea di gioco. Cinque classi hanno arma e armatura di elementi che **reagiscono** fra loro: il nome della reazione è in tabella. Paladino e Negromante portano lo stesso elemento e partono con la **Risonanza**. Il Berserker combatte a petto nudo.

### La Maestria

Ogni eroe ha un albero di **Maestria** a 5 livelli, che sale con l'esperienza accumulata nelle sue discese:

- **Lv.2** — un bonus personale (es. *Imboscata* dell'Assassino: il primo attacco di ogni scontro fa danni doppi).
- **Lv.3** — sblocca un oggetto (es. la *Bomba Fumogena* per il Ladro).
- **Lv.4** — un'**Eredità**: un bonus permanente per **tutti** gli eroi.
- **Lv.5** — sblocca una nuova classe, un tratto o una reliquia.

---

## 🎭 Tratti

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

---

## 🎮 Modalità

Dal menu principale:

- **Discesa standard** — 30 piani fino al DIO ANTICO.
- **📅 Sfida del Giorno** — sempre disponibile (vedi sotto).
- **Discesa infinita** — dopo la prima vittoria: si prosegue oltre il piano 30 finché resisti; se lo superi, l'Essenza finale vale ×1,5.

### Ascensione

Dopo la prima vittoria, a ogni partenza scegli un **grado di Ascensione**. Ogni grado aggiunge una regola a quelle dei gradi precedenti e aumenta l'Essenza finale. All'inizio è disponibile il grado 1; vincendo la discesa standard al grado più alto sblocchi il successivo, fino al **20**. Il grado scelto è indicato in cima alla mappa e nelle Statistiche dell'Eroe.

I cinque **Patti del Caos** delle versioni precedenti sono diventati gradi: *Labirinto Mortale*, *Inflazione*, *Carestia*, *Durezza* e *Furia* (questi ultimi due più leggeri, perché si sommano agli altri gradi).

| Grado | Nome | Regola che si aggiunge | Essenza |
|---|---|---|---|
| 1 | Campioni | Gli scontri d'Élite compaiono il doppio delle volte. | ×1,15 |
| 2 | Scale Fredde | Il riposo prima delle scale cura la metà. | ×1,3 |
| 3 | Labirinto Mortale | Le trappole infliggono danni doppi. | ×1,55 |
| 4 | Forzieri Avidi | Forzieri chiusi e Mimic sono il doppio più probabili (fino a uno su due). | ×1,7 |
| 5 | Boss Feroci | I boss hanno il 15% di HP in più. | ×1,85 |
| 6 | Inflazione | I prezzi del Mercante sono raddoppiati. | ×2,1 |
| 7 | Borsa Vuota | Parti con metà dell'Oro. | ×2,25 |
| 8 | Braci Deboli | Riposare al Falò cura il 30% degli HP invece del 50%. | ×2,4 |
| 9 | Occhi nel Buio | I nemici hanno +5 di Precisione. | ×2,55 |
| 10 | Campioni Temprati | Gli scontri d'Élite hanno il 20% di HP in più. | ×2,7 |
| 11 | Oggetti Inquieti | Gli oggetti maledetti compaiono il doppio delle volte. | ×2,85 |
| 12 | Avarizia | I nemici lasciano il 25% di Oro in meno. | ×3 |
| 13 | Carestia | Le pozioni curano la metà. | ×3,25 |
| 14 | Macchia | Inizi la discesa con 20 di Corruzione. | ×3,4 |
| 15 | Durezza | I nemici e i boss hanno il 15% di HP in più. | ×3,65 |
| 16 | Mercanti in Fuga | I Mercanti compaiono la metà delle volte. | ×3,8 |
| 17 | Boss Implacabili | I boss hanno il 10% di ATK in più. | ×3,95 |
| 18 | Nemici Coriacei | I nemici comuni hanno il 10% di HP in più. | ×4,1 |
| 19 | Furia | I nemici e i boss hanno il 10% di ATK in più. | ×4,35 |
| 20 | Il Dio si Sveglia | Il DIO ANTICO ha il 30% di HP in più. | ×4,65 |

### Sfida del Giorno

Una discesa al giorno, **uguale per chiunque la giochi quel giorno**:

- l'eroe e il tratto sono assegnati, anche se non li hai ancora sbloccati: è un modo per provarli;
- 2 **malus** presi dai gradi di Ascensione e un **dono**:

| Dono | Effetto |
|---|---|
| Borsa Piena | Parti con 150 Oro in più. |
| Dono Antico | Parti con una Reliquia casuale. |
| Scorte | Parti con 2 pozioni in più. |
| Nebbie Generose | Le Stanze del Mistero compaiono il doppio delle volte. |
| Taglie | I nemici lasciano il 50% di Oro in più. |
| Scale Calde | Il riposo prima delle scale cura il 50% in più. |

- ogni piano nasce dallo stesso seme: la mappa di un piano è la stessa qualunque strada tu abbia preso prima;
- conta solo il **primo tentativo** del giorno, che vale anche Essenza ×1,5; i tentativi successivi sono allenamento;
- **punteggio**: 100 per piano raggiunto, 250 per boss, 2000 per la vittoria, più un punto ogni 10 Oro;
- la schermata della sfida mostra il punteggio di oggi, la **serie** di giorni consecutivi, il record e le ultime sfide (lo storico tiene 30 giorni).

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
- **🔥 Il Fuoco del Campo** — chi incontri nel Labirinto può venire a scaldarsi qui. *Silas*, *la Cartografa*, *il Viandante Cieco* e, se lo hai liberato, *la luce di Alaric* compaiono quando le loro storie sono andate abbastanza avanti. Ti parlano in base a ciò che hai fatto e la prima volta ti lasciano un dono (✦). Qui costruisci anche, con l'Essenza:
  - *il Tavolo della Cartografa* (aiutala nel Labirinto): sulla mappa vedi quali storie ti aspettano nelle stanze speciali e negli eventi che tornano;
  - *lo Scrittoio di Silas* (salvalo): a ogni partenza scegli un dono fra +20 HP Max, +3 ATK e +100 Oro;
  - *l'Altare della Purificazione*: la Corruzione cresce del 25% in meno.
- **📖 Il Codice del Labirinto** — tutto ciò che hai scoperto, raccolto fra una run e l'altra, con la percentuale di completamento. Ciò che manca è segnato con ???.
  - *Reazioni elementali*: le combinazioni di elementi che hai scatenato almeno una volta.
  - *Finali*: quelli che hai visto, e un indizio per gli altri.
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

Si aggiungono **50 Essenza per ogni boss** sconfitto; poi si applicano il moltiplicatore del grado di **Ascensione** (o ×1,5 per il primo tentativo della **Sfida del Giorno**) e, oltre il piano 30 in **Modalità Infinita**, un ulteriore ×1,5.

---

## 💡 Consigli per sopravvivere

- **Guarda gli elementi prima di attaccare.** Un'arma Super Efficace colpisce più spesso e più forte: a volte conviene cambiarla, anche se costa un turno.
- **Difenditi contro i colpi forti.** Dimezzare un attacco del boss vale spesso più di un tuo colpo.
- **Non sottovalutare la fuga.** Uscire al momento giusto con tanto Oro rende più Essenza di una morte gloriosa.
- **Usa l'Altare dell'Evoluzione.** Le armi doppie nello zaino valgono più come materiale da fusione che come merce da vendere.
- **Libera gli artigiani.** Partire con un'arma o un monile scelto da te cambia l'inizio di ogni discesa.
- **Prova tutti gli eroi.** Le Eredità di Maestria (Lv.4) rafforzano tutti gli altri.
