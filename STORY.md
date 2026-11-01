# 🌀 Il Canone di Aethelgard

Questo è il canone del mondo del gioco: chi sono i personaggi, cosa è successo, cosa è vero e quando il giocatore lo scopre. Tutta la lore del gioco (eventi, dialoghi del Campo, lettere, Bestiario, libri, finali) parte da qui.

Tre regole prima di tutto:

- **I dati del gioco vincono.** Se un testo che il giocatore ha già letto in partita contraddice questo documento, si corregge questo documento (o si cambia il testo nella stessa PR). L'appendice *Contraddizioni risolte* tiene traccia delle scelte fatte.
- **Un fatto nuovo si scrive qui nella stessa PR che lo mette nel gioco.** Un nome, una data, un legame fra due personaggi: se non è in questo documento, il prossimo autore non lo conosce.
- **I segreti hanno un momento.** La parte *La verità* dice cosa è vero; la *Scala delle rivelazioni* dice quando il giocatore può saperlo. Nessun testo anticipa un gradino.

L'obiettivo della v6 è almeno dieci volte la narrativa della v5 (circa 12.000 parole, misurate con `python tools/conta_testi.py`), quasi tutta fuori dalla partita: chi vuole leggere lo fa al Campo, nel Codice e nell'Archivio, chi vuole giocare non viene rallentato.

---

## Parte I · Come si scrive

### 1. Dove va il testo

La discesa deve restare veloce. Il testo lungo vive dove il giocatore sceglie di fermarsi.

| Dove | Cosa | Lunghezza |
|---|---|---|
| **In partita** | Scena di un evento | 1-3 frasi, al massimo 55 parole |
| | Esito di una scelta | 1-2 frasi, al massimo 30 parole |
| | Frase d'ingresso di una stanza, atmosfera di un bioma | 1-2 frasi, al massimo 30 parole |
| | Lettera insanguinata | 1 frase, al massimo 25 parole |
| | Battuta di un boss (inizio, fase, morte) | 1 frase, al massimo 25 parole |
| **Fuori partita** | Conversazione al Campo (un argomento) | 80-250 parole, divise in battute |
| | Voce del Bestiario (un livello) | 40-80 parole |
| | Capitolo di un libro dell'Archivio | 150-400 parole |
| | Ricordo di una vita prestata (classe) | 120-250 parole |
| | Epilogo di un finale | 3-6 frasi per variante |

Un testo in partita che supera la misura si spezza: la prima parte resta nella scena, il resto diventa una nota del Codice o una battuta al Campo.

### 2. Voce e forma

- **In partita si parla al giocatore in seconda persona, al presente.** «Trovi», «senti», «ti guarda». Mai «il giocatore», mai «l'eroe» nel racconto.
- **I dialoghi stanno fra apici singoli**: `'Nessuno passa,' dice.` Le iscrizioni, le parole incise e i titoli citati stanno fra caporali: `«Una volta sola»`.
- **Nessun numero delle regole nella lore.** I numeri (danni, percentuali, oro) stanno nelle descrizioni (`desc`), che il gioco controlla. La lore dice cosa si prova, non quanto vale.
- **Un dettaglio concreto vale più di tre aggettivi.** Non «un'atmosfera inquietante e opprimente», ma «il soffitto è basso, e qualcuno ci ha inciso dei segni con le unghie».
- **Il Labirinto non spiega se stesso.** I personaggi sanno cose diverse, a volte sbagliano, a volte mentono. La verità si ricompone mettendo insieme le voci.
- **Ironia sì, battute moderne no.** Borek può scherzare; nessuno dice «ok» o fa riferimenti al mondo di fuori.
- **Ortografia**: accenti giusti (è, perché, più, già), apostrofi dritti `'`, puntini di sospensione solo quando qualcuno si interrompe davvero.

### 3. Le voci dei personaggi

Ogni personaggio deve essere riconoscibile anche senza il suo nome davanti.

| Personaggio | Come parla |
|---|---|
| **Silas** | Frasi spezzate, date sbagliate e corrette («Giorno quattro... no. Cinque.»), immagini di stelle e inchiostro. Prende appunti mentre parla. |
| **Sir Alaric** | Formale, antico, poche parole. Non usa mai il tu per primo. Dice «gli Architetti» come si dice «mio padre». |
| **La Cartografa (Tessa)** | Entusiasta, precisa, misura tutto in passi e piani. Interrompe se stessa per segnare qualcosa sulla mappa. |
| **Lo Speziale (Ambrogio)** | Gentile, lento, parla per ricette e dosi. Chiede sempre se hai mangiato. Il rimorso arriva a metà frase. |
| **Borek** | Diretto, rumoroso, paragoni col metallo e con la birra. Chiama tutti «ragazzo». Quando è serio diventa improvvisamente breve. |
| **Elara** | Asciutta, pratica, frasi corte. Ripara qualcosa mentre parla. Non si lamenta mai, ma conta le cicatrici. |
| **Valerius** | Ricercato, vanitoso, ironico, frasi lunghe con un inciso di troppo. Sotto la vanità, paura. |
| **Il Viandante Cieco** | Conta a bassa voce (monete, passi, respiri). Parla della luce come di un dolore. |
| **Il Mercante Senza Volto** | Tutto è un prezzo. Non chiede oro: chiede ricordi, nomi, il colore di un tramonto. Cortese fino al gelo. |
| **Linnea** | Parla al plurale («noi ricordiamo»), per immagini d'acqua e di bosco. Confonde passato e presente. |
| **Kaelen il Muto** | Non parla: dalla bocca gli esce sabbia. Il testo descrive i suoi gesti e i segni che incide sul metallo. |
| **Il Fuoco** | Non parla a parole. Crepita, si abbassa, si alza, scalda una mano. Il testo descrive cosa fa sentire. |

### 4. Parole da usare con misura

Il tono si consuma ripetendo le stesse parole. `python tools/conta_testi.py` elenca le parole più usate in tutta la lore: se una parola è in cima alla lista, cercane un'altra. Oggi le più consumate sono **luce, labirinto, voce, porta, sangue, pietra, qualcuno, qualcosa**; da usare con particolare misura anche **sussurra, eco, antico, oscurità, brivido, abisso**. Il test dei doppioni (`--check`) impedisce due testi narrativi identici.

### 5. Checklist di una PR di lore

1. Ogni fatto nuovo è scritto in questo documento.
2. Nessun testo anticipa un gradino della *Scala delle rivelazioni*.
3. Le misure della tabella sono rispettate (in partita soprattutto).
4. `python tools/conta_testi.py` riporta i progressi nella descrizione della PR.
5. Nessun valore di gioco cambia: la lore della v6 non tocca numeri, regole né bilanciamento. Il golden master non deve cambiare per una PR di soli testi (le frasi d'atmosfera hanno un caso tutto loro: `texts.py`).

---

## Parte II · La verità (per chi scrive)

Questa parte è per gli autori. Il giocatore la scopre un pezzo per volta, nell'ordine della *Scala*.

### Il Labirinto

Il Labirinto, che i dotti chiamano la **Fauce del Caos**, non è una prigione costruita: è una ferita che si è chiusa male. Nacque mille anni fa, nella notte della **Grande Discordia**, quando un esperimento sull'Ottavo Elemento, il **Vuoto**, lacerò l'equilibrio degli altri sette. Gli elementi si separarono e diventarono ossessioni; le regioni di Aethelgard furono trascinate in profondità, una dentro l'altra, e diventarono i biomi.

I sei Architetti rimasti fedeli non riuscirono a richiudere la ferita. Fecero l'unica cosa possibile: la **avvolsero**. Il Labirinto è il loro guscio. Dentro custodisce due cose: il Vuoto, che non deve uscire, e il ricordo dell'**Equilibrio**, cioè Aethelgard com'era, che non deve andare perduto. Quel ricordo è lo **specchio** oltre la Soglia: chi lo guarda vede il mondo come sarebbe stato. Per questo il Labirinto è insieme carcere e reliquiario, e per questo trattiene chi muore: ogni anima svuotata (gli *Svuotati*) diventa un mattone del guscio.

### Il Rinnegato e Re Galdor

Gli Architetti erano sette, uno per elemento. Il settimo, l'Architetto del **Normale**, cioè della materia comune e della fragilità umana, si chiamava **Sereth**. Il suo nome è stato cancellato da ogni cronaca; nel gioco compare solo all'ultimo gradino della Scala.

Sereth non voleva diventare un dio. Voleva che gli uomini potessero **riposare**. Nell'Equilibrio la morte non era una fine ma un ritorno all'Essenza, e l'Essenza tornava in nuova vita: nessuno, mai, smetteva davvero di esistere. Dopo mille anni Sereth vide che la sua gente era stanca. Il Vuoto doveva essere un luogo dove l'Essenza potesse finalmente fermarsi.

Gli serviva un regno disposto a rischiare. Lo trovò al Sud, nelle **Valli di Galdor**, dove tre anni di carestia avevano reso il re **Galdor** disposto a tutto: Galdor chiese la fine della fame, Sereth gli promise la fine di ogni bisogno. Per questo le cronache non sono d'accordo su chi abbia «lacerato il velo»: lo fecero tutti e due. Galdor pagò per primo: le sue valli furono le prime a sprofondare, e lui governa ancora il suo popolo diventato goblin (il **Re dei Goblin**).

### Il Dio Antico

Nell'istante dell'esperimento Sereth si fuse con il Vuoto che stava creando. Quello che resta al fondo del Labirinto, al piano 30, è il **Dio Antico**: la parte di Sereth che vuole il riposo, e che sogna. Il Labirinto è il suo sogno tenuto in forma dal guscio degli Architetti. Quando il Dio dorme profondamente il Labirinto è calmo; più il Dio si sveglia, più il Labirinto diventa crudele (i gradi di **Ascensione**) e più ricorda se stesso, ripetendo i suoi piani in **Eco** sempre più dure (il **Ciclo**).

Sconfiggere il Dio non lo uccide: lo fa dormire. Per questo il giocatore può vincere e tornare a scendere.

### Il Fuoco del Campo

Dei sei Architetti fedeli, cinque si ritirarono nelle cittadelle del cielo e tacquero. Il sesto, **Ardel**, l'Architetto del **Fuoco** (del fuoco com'era prima: calore, focolare, veglia), rifiutò di andarsene. Si fece brace. Il **Fuoco del Campo** è ciò che resta di lui: l'ultima coscienza degli Architetti dentro il Labirinto.

Il Fuoco ha un solo potere: **riportare indietro**. Quando qualcuno che lui ha scelto muore laggiù, invece di diventare un mattone del guscio torna al Campo. Ma ogni ritorno costa ad Ardel una parte di sé. L'**Essenza** che il giocatore riporta non è solo una moneta: nutre il Fuoco, e i potenziamenti del **Fuoco dell'Anima** sono il Fuoco che, nutrito, restituisce forza. Le strutture costruite al Campo sono pezzi di casa intorno a una brace che si consuma.

Il Fuoco non parla. Si sente: crepita più forte quando arriva qualcuno di nuovo al Campo, si abbassa quando il giocatore sceglie la Corruzione, scalda la mano quando un personaggio trova pace.

### Il Ritornante

Il giocatore è il **Ritornante**: l'unico che il Fuoco riporta. Non ricorda chi era prima di svegliarsi la prima volta accanto alla brace, e ogni morte gli toglie qualcosa delle discese precedenti. I personaggi del Labirinto, invece, a volte ricordano lui: Silas lo ha disegnato, il Custode della Soglia lo ha «già visto», il Tristo Mietitore «aveva già scritto il suo nome».

**Il segreto ultimo:** il Ritornante è la parte di Sereth che si è pentita. Nell'istante della fusione Sereth si spezzò in due: la parte che voleva il riposo divenne il Dio, la parte che vide cosa stava facendo al mondo si staccò e cadde, senza nome e senza memoria, accanto al focolare di Ardel. Ardel la riconobbe e la scelse lo stesso. Ogni discesa è il rimorso che torna a guardare il proprio errore. Le **lettere insanguinate** sono tutte di sua mano, scritte in discese che non ricorda (finale *La Lettera Mai Scritta*).

### Le vite prestate

Il Ritornante non ha una vita sua da ricordare. Il Fuoco gli presta quelle degli eroi che ha raccolto nei mille anni: anime di caduti che Ardel ha strappato al guscio prima che diventassero mattoni. Ogni **classe** è una di queste vite. Combattere come Guerriero è indossare il ricordo di **Bran**; la **Maestria** di una classe è ricordare quella persona fino in fondo e, al livello più alto, lasciarla riposare. Sbloccare una classe è il Fuoco che restituisce un'altra vita.

### Le Nemesi e il rancore dei boss

Nel Labirinto anche i mostri ricordano, perché sono fatti della stessa Essenza del guscio. Chi uccide il Ritornante ne beve un poco di nome: per questo diventa qualcuno (una **Nemesi**) e lo aspetta. I boss che lo hanno ucciso più volte lo riconoscono.

### La Scala delle rivelazioni

Ogni testo appartiene a un gradino. Un testo può accennare al gradino successivo, mai rivelare quelli dopo.

| Gradino | Quando | Cosa può sapere il giocatore |
|---|---|---|
| **1 · Il risveglio** | Prime discese, piani 1-10 | Si sveglia accanto a un fuoco che non brucia. Non ricorda il suo nome. Il Labirinto ha inghiottito un mondo, Aethelgard. Gli Architetti esistevano. Qualcuno lo riconosce, e non dovrebbe. |
| **2 · Le voci** | Piani 10-20, primi personaggi liberati | Esiste la Grande Discordia; c'entrano un re affamato (Galdor) e un Architetto rinnegato senza nome. Il Fuoco riporta indietro solo lui. Ogni ritorno costa qualcosa al Fuoco. Le classi sono vite di altri. |
| **3 · Lo specchio** | Piani 20-30, la prima vittoria | Il Labirinto è un guscio costruito dagli Architetti fedeli. Oltre la Soglia c'è uno specchio con Aethelgard com'era. Il Dio Antico non muore: dorme. Il Fuoco ha un nome, Ardel. |
| **4 · Il risveglio del Dio** | Ascensione, Eco del Ciclo, Archivio quasi completo | Il Dio si sveglia sempre di più. Il Rinnegato voleva dare riposo, non potere. Il Dio è ciò che resta di lui. |
| **5 · Il nome** | Finale *La Lettera Mai Scritta*, ultimi capitoli dell'Archivio | Il nome del Rinnegato è Sereth. Il Ritornante è la parte di lui che si è pentita. Le lettere sono sue. |

---

## Parte III · Cronologia

Gli anni si contano **dall'Equilibrio** (d.E.), cioè da quando gli Architetti fissarono gli elementi in armonia. Dopo la Discordia nessuno conta più gli anni dentro il Labirinto; in superficie, dove resta poco, si dice «dopo la Fauce». Oggi sono passati circa **mille anni dalla Discordia**.

| Anni | Era | Cosa succede |
|---|---|---|
| 1-300 d.E. | **Luce Calma** | Gli Architetti camminano fra gli uomini. Nascono Aurelia, l'Accademia della Luce Calma, i Grandi Templi. La morte è un ritorno all'Essenza. |
| 301-700 d.E. | **Ambizioso Raggiungimento** | Gli uomini imparano a distillare gli elementi. Nascono le armi elementali e l'Alchimia; si scavano i Monti di Durn; Aetheria diventa la patria dei maghi. Alaric diventa il Primo Paladino. |
| 701-997 d.E. | **Crepuscolo Lungo** | Il cielo diventa grigio cenere. Gli elementi si ribellano: incendi che non si spengono, acqua che non disseta. Sereth comincia a studiare il Vuoto. Gli Architetti si chiudono nelle cittadelle. |
| 997-999 d.E. | **La Carestia del Sud** | Tre raccolti perduti nelle Valli di Galdor. Galdor stringe il patto con Sereth. |
| 1000 d.E. | **La Grande Discordia** | In una notte l'esperimento fallisce. Il Vuoto si apre, gli elementi si separano, le regioni sprofondano. Ardel si fa brace. Alaric giura sulla porta. |
| Dopo la Fauce | **Il Labirinto** | Mille anni di discese. Il Labirinto cresce, mangia i bordi del mondo, sogna. Gli avventurieri scendono per l'Essenza, per i tesori, per i loro morti. Quasi nessuno torna. |

---

## Parte IV · Gli elementi

Nell'Equilibrio gli elementi erano fili di una stessa trama. Nel Labirinto ognuno è diventato un'ossessione.

| Elemento | Com'era | Cos'è diventato |
|---|---|---|
| 🔥 **Fuoco** | Calore del focolare, veglia | L'Eterna Rabbia: un incendio che brucia ciò che poteva essere. Solo il Fuoco del Campo è rimasto com'era. |
| 💧 **Acqua** | Vita, memoria che scorre | La Memoria del Sommerso: un oceano di ricordi altrui in cui si affoga. |
| 🪨 **Terra** | Sostegno, pazienza | La Fortezza Inviolata: roccia che rifiuta di cambiare, la testardaggine di chi non accetta la fine. |
| 💨 **Vento** | Voce, viaggio, polline | Il Lamento del Vuoto: segreti di chi non ha più bocca. |
| ✨ **Luce** | Verità, cura | La Divinità Crudele: una perfezione che brucia le imperfezioni, cioè tutto ciò che è umano. |
| 🌑 **Tenebra** | Riposo, sonno, intimità | L'Abbraccio della Verità: fredda ma onesta, l'unico posto dove nascondersi dallo sguardo degli Architetti. |
| ⚪ **Normale** | La materia comune, la vita fragile | La Fragilità Residua: ciò che resta quando l'Essenza è stata estratta. È l'elemento di Sereth. |

Il **Vuoto** non è un elemento: è l'assenza che Sereth cercò di rendere abitabile. Le **reazioni elementali** (quando due elementi si incontrano su un nemico) sono il ricordo dell'Equilibrio che torna per un istante; per questo l'Elementalista le sente come una musica.

---

## Parte V · Il mondo che fu

Aethelgard era un continente intorno a un mare interno. Ogni regione è sprofondata nel Labirinto e ne è diventata un pezzo.

| Regione | Dov'era | Elementi | Cosa ne resta |
|---|---|---|---|
| **Aurelia**, la capitale | Al centro, sul colle dei pilastri di Luce | Luce, Normale | I **Chiostri del Rimpianto**: l'Accademia della Luce Calma e i suoi monasteri. |
| **I Monti di Durn** | A Ovest, sopra le vene di ferro | Terra | Le **Miniere della Testardaggine**: le gallerie dei nani e degli uomini di miniera. Patria di Borek e di Kaelen. |
| **Valeriana**, le Valli della Seta | A Nord, nella nebbia | Vento, Acqua | Le **Guglie del Vento Urlante**: le torri dei tessitori e l'Osservatorio. I tessitori sono diventati gli Spiriti della Tempesta. Qui Ilse, la figlia di Alaric, coltivava la lavanda. |
| **Il Mare Interno** e le sue coste | Al centro del continente | Acqua | Il **Ventre della Memoria**: il mare è diventato un organismo che digerisce ricordi. Il Drago di Zaffiro ne era il guardiano. Linnea viveva nei boschi della costa. |
| **Le Terre Alte di Ignis** | A Est, fra vulcani e foreste d'ossidiana | Fuoco, Terra | La **Forgia del Caos**: le fucine dove gli Architetti cercarono di riforgiare gli elementi. |
| **L'Arcipelago di Aetheria** | Isole sospese nel cielo, sorrette da cristalli di Luce | Luce, Vento | Caddero nella notte della Discordia. I frammenti dei cristalli sono le **reliquie**. L'isola più alta, **Calaris**, ospitava la cittadella di Sereth: è sprofondata più in basso di tutte e oggi è la **Soglia del Dio Antico**. |
| **Le Valli di Galdor** | A Sud, terre di grano | Normale | Le prime a sprofondare. Non sono un bioma: sono sparse ovunque, come i goblin. |
| **Le Paludi di Morva** | A Sud-Ovest, fra canne e acqua nera | Tenebra, Acqua | Terra dei negromanti, che parlavano ai morti prima che i morti smettessero di andarsene. |

---

## Parte VI · I sei biomi e le Eco

Ogni bioma è una regione ricordata dal Labirinto. Ha un boss nativo, una gente, un pericolo e almeno un segreto.

### 📿 I Chiostri del Rimpianto (piani 1-5)
- **Cos'era:** l'Accademia della Luce Calma di Aurelia, dove si studiavano gli elementi, e i monasteri intorno. Marmo bianco venato di viola, biblioteche, cori.
- **Chi ci vive:** novizie e coristi spenti, bibliotecari di cenere, statue di sale (chi si è fermato ad ascoltare una voce cara), Eco del Rimpianto.
- **Boss nativo:** **La Badessa del Silenzio**, che guidava le preghiere dell'Accademia. Crede che il silenzio sia preghiera; è una gabbia (lo scrive Valerius nel suo grimorio). Vuole che tu resti per sempre ad ascoltare.
- **Pericolo:** la Nostalgia Letale. Le voci dei tuoi cari ti chiamano per nome.
- **Segreti:** la **Prima Pietra** degli Architetti sotto il marmo del piano 3; l'aula dove Sereth insegnava, con il suo nome raschiato dalla lavagna.
- **Temi:** il rimpianto, il sapere che non ha salvato nessuno.

### ⛏️ Le Miniere della Testardaggine (piani 6-10)
- **Cos'era:** le gallerie dei Monti di Durn, nani e uomini insieme, gli ingranaggi dell'Era dell'Ambizioso Raggiungimento.
- **Chi ci vive:** minatori svuotati che scavano ancora, ingranaggi senzienti, carrelli posseduti, guardiani di basalto, lucciole del grisù.
- **Boss nativo:** **Il Caposquadra Sepolto**, che guidò l'ultima squadra sempre più in basso perché «sotto la prossima roccia» c'era l'uscita. Non ha mai dato l'ordine di risalire.
- **Pericolo:** il Gas del Silenzio, che toglie la voce e gli incantesimi.
- **Segreti:** la forgia di **Kaelen il Muto**; la galleria da cui la squadra di Borek non è uscita.
- **Temi:** la testardaggine, la fedeltà a un ordine sbagliato.

### 🌪️ Le Guglie del Vento Urlante (piani 11-15)
- **Cos'era:** le torri dei tessitori di Valeriana e l'Osservatorio, dove si misuravano le stelle.
- **Chi ci vive:** sentinelle di nube, falchi astrali, corvi del tuono, spiriti dei ponti, astronomi caduti. Gli Spiriti della Tempesta sono i tessitori, costretti a tessere fulmini invece di seta.
- **Boss nativo:** **L'Astronoma delle Guglie**, che misurava le stelle dalla guglia più alta e le ha viste cadere. Fu la maestra di Silas.
- **Pericolo:** la Caduta Astrale: chi perde l'equilibrio non cade in basso, ma in un altro piano.
- **Segreti:** la mappa del cielo di Aethelgard com'era, incisa sul pavimento dell'Osservatorio; il campo di lavanda di Ilse, sospeso su una guglia.
- **Temi:** la curiosità, la perdita dei punti di riferimento.

### 🫀 Il Ventre della Memoria (piani 16-20)
- **Cos'era:** il Mare Interno e le sue coste. Ora è un organismo: pareti traslucide come membrane, dentro oggetti e volti.
- **Chi ci vive:** ricordi annegati, volti nella membrana, sanguisughe madri, lacrime viventi, bambole di ricordi, meduse della memoria.
- **Boss nativo:** **Il Cuore del Ventre**. Batte al centro della Memoria; a ogni battito, in superficie, qualcuno dimentica qualcosa.
- **Pericolo:** la Dissoluzione dell'Io: il Labirinto ti digerisce un poco.
- **Segreti:** la sorgente di **Linnea**; la città capovolta i cui abitanti cadono verso l'alto; il punto dove il **Drago di Zaffiro** bevve troppo dal passato.
- **Temi:** la memoria come cibo, l'identità che si scioglie.

### 🔨 La Forgia del Caos (piani 21-25)
- **Cos'era:** le fucine delle Terre Alte di Ignis, dove dopo la Discordia gli Architetti tentarono di riforgiare insieme gli elementi.
- **Chi ci vive:** golem di scorie, martelli erranti, scudieri e apprendisti di scoria, crogioli ambulanti, scintille ribelli.
- **Boss nativo:** **Il Maestro di Forgia**. Gli Architetti gli chiesero di riforgiare gli elementi; ci prova ancora, colpo dopo colpo, su un'incudine che non c'è.
- **Pericolo:** l'Ebollizione Astrale, che brucia l'oro.
- **Segreti:** l'Incudine Cosmica; il crogiolo dove Elara perse il fratello; il primo tentativo di «riparare» il Normale.
- **Temi:** riparare ciò che non si può riparare, il lavoro come penitenza.

### 👁️ La Soglia del Dio Antico (piani 26-30)
- **Cos'era:** Calaris, l'isola più alta di Aetheria, e la cittadella di Sereth. Ora piattaforme di volontà nel vuoto, elementi in collisione.
- **Chi ci vive:** frammenti di galassia, eco del Dio, frammenti del Prima, riflessi futuri, vuoti affamati, clessidre infrante.
- **Boss nativo:** **Il Custode della Soglia**, che c'era prima che il Labirinto avesse un nome e che «ti ha già visto». È l'ultimo servitore di Sereth; sa chi sei, e non lo dice.
- **Pericolo:** il Paradosso Temporale.
- **Segreti:** lo **specchio** oltre il Dio; la stanza vuota con una sedia («la fine del tempo»), dove Sereth sedeva a pensare.
- **Temi:** la colpa, il perdono, la tentazione del riposo.

### ⏳ Le Eco (oltre il piano 30)
Il Dio, svegliandosi, ricorda il suo sogno e lo ripete più forte: i biomi tornano in un ordine diverso, con pericoli più duri e un nome (Eco II, Eco III…). Nelle Eco i luoghi conoscono il Ritornante: le voci dei Chiostri cantano il suo nome, i minatori lo salutano. Ogni trenta piani il Dio Antico è di nuovo lì, un po' più sveglio.

---

## Parte VII · Il Campo

Il **Campo Base** è un cerchio di pietre intorno al Fuoco, in un punto del Labirinto che il Labirinto non vede. Chi ci arriva è al sicuro, ma solo finché il Fuoco arde.

- **Il Fuoco dell'Anima**: Ardel stesso. L'Essenza versata nel Fuoco torna come forza (i potenziamenti).
- **Chi ci vive:** i personaggi liberati o incontrati nelle discese, quando hanno un motivo per restare. Al Campo parlano più che in partita: è qui che raccontano la loro storia (vedi la Parte VIII).
- **Le strutture** sono pezzi di casa: il **Tavolo della Cartografa**, lo **Scrittoio di Silas**, l'**Altare della Purificazione**, la **Biblioteca dell'Arcano**, la **Sala d'Armi**. Ogni struttura nuova è un personaggio che decide di fermarsi.
- **La Taverna, la Forgia, il Grimorio, le botteghe**: il lavoro degli artigiani liberati (Speziale, Borek, Elara, Valerius).
- **L'Archivio di Aethelgard**: i libri ritrovati nelle discese.

Il Campo cambia con la storia: più personaggi trovano pace, più il Fuoco è caldo; chi sceglie la Corruzione lo trova un poco più freddo al ritorno.

---

## Parte VIII · I personaggi

Ogni scheda dice chi è, cosa vuole, cosa nasconde, e le **tappe** del suo arco: ciò che i testi futuri (eventi in discesa e conversazioni al Campo) raccontano, nell'ordine. Le tappe già nel gioco sono segnate con ✓.

### Sir Alaric, il Primo Paladino
- **Chi è:** il primo Paladino degli Architetti, nato ad Aurelia nell'Era dell'Ambizioso Raggiungimento. Nella notte della Discordia gli Architetti gli ordinarono di custodire una porta: quella dietro cui avevano chiuso il Vuoto. Giurò sul sigillo di Luce. Gli Architetti tacquero; il giuramento no.
- **Cosa vuole:** riposare, e sapere se sua figlia **Ilse** è sopravvissuta.
- **Cosa nasconde:** la porta non conduce più a nulla perché il Vuoto è già dentro tutto il Labirinto. Lui lo sa da secoli, e continua a custodirla perché è l'unica cosa che ricorda di saper fare.
- **Il Cavaliere Oscuro:** il boss con quel nome è l'ombra che il giuramento proietta nel Labirinto, un'armatura vuota che combatte per abitudine. Liberare Alaric non toglie il boss: lo rende un guscio senza nessuno dentro.
- **Tappe:** ✓ la porta · ✓ il cavaliere stanco (la lavanda) · ✓ l'ultimo sigillo · il campo di lavanda sulle Guglie · la lettera di Ilse · il giorno in cui la Luce divenne crudele · la confessione della porta vuota · al Campo, come Luce: i ricordi di Aurelia · la pace (o il peso del giuramento, se il giocatore ha preso il suo posto).
- **Legami:** Ser Maud (la vita prestata del Paladino) era sua sorella d'ordine.

### Silas, il Cercatore
- **Chi è:** un astronomo di Valeriana, allievo dell'Astronoma delle Guglie. È sceso per ritrovare la sorella **Nerea**, inghiottita dal Labirinto con la loro casa. Scrive tutto perché il Labirinto gli mangia i ricordi: ha già dimenticato il colore degli occhi di lei.
- **Cosa vuole:** arrivare al fondo e capire. Poi, quando ha visto lo specchio, tornare indietro senza sentirsi un vigliacco.
- **Cosa nasconde:** scende da molto più dei suoi «settantacinque giorni»: il tempo del Labirinto lo ha trattenuto per secoli. Ha visto il Ritornante morire molte volte e lo ha disegnato ogni volta. Il Fuoco non lo ha mai scelto, e Silas gliene vuole un po'.
- **Tappe:** ✓ il fuoco azzurro · ✓ il diario strappato · ✓ la soglia e lo specchio · al Campo, la zuppa e le prime pagine · la maestra (l'Astronoma) · Nerea · i ritratti del Ritornante · perché il Fuoco non lo ha scelto · l'ultima pagina, scritta insieme.

### La Cartografa (Tessa)
- **Chi è:** **Tessa**, nipote di **Orvin il Cartografo**, che mappò i piani da 1 a 29 e non tornò dal trentesimo. Il suo nome il giocatore lo scopre solo al Campo.
- **Cosa vuole:** completare la mappa del nonno, e mettere sulla mappa ciò che il nonno non credeva (la Prima Pietra).
- **Cosa nasconde:** la croce rossa sulla mappa («qui ti aspetto») non l'ha disegnata lei: era già sulla mappa di Orvin, con la sua calligrafia.
- **Tappe:** ✓ perduta, senza provviste · ✓ ritrovata · ✓ la Prima Pietra · al Campo, il tavolo e le pergamene · Orvin · la croce rossa · il piano trenta · la mappa completa.

### Lo Speziale (Ambrogio)
- **Chi è:** **Ambrogio**, speziale di Aurelia, vecchio già prima di scendere. Lo chiamano tutti «lo Speziale»; dice il suo nome solo a chi lo ha liberato più volte.
- **Cosa vuole:** curare, e farsi perdonare.
- **Cosa nasconde:** nel Crepuscolo Lungo vendette a Sereth gli estratti con cui l'Architetto studiava il Vuoto, senza chiedere a cosa servissero. Ha sempre sospettato di aver aiutato la fine del mondo.
- **Tappe:** ✓ incatenato dalla magia del sangue · al Campo, la prima zuppa · le ricette di Aurelia · il cliente senza nome · la confessione · una pozione che non cura niente, se non lui.

### Borek, il Maestro d'Armi
- **Chi è:** un nano dei Monti di Durn, maestro d'armi e forgiatore. Era il caposquadra di una squadra di minatori-soldati; è l'unico uscito dalla galleria crollata.
- **Cosa vuole:** forgiare armi degne, bere, non pensare alla galleria.
- **Cosa nasconde:** era l'allievo di **Kaelen il Muto**, e lo crede morto. Ha preso il comando della squadra al posto del Caposquadra Sepolto, che non voleva risalire, e li ha portati verso l'alto: solo lui ce l'ha fatta.
- **Tappe:** ✓ prigioniero dietro la grata · al Campo, l'acciaio buono e quello cattivo · la birra di Durn · la squadra · il maestro · Kaelen vivo · la galleria.
- **Voce:** «ragazzo» per chiunque, anche per Alaric.

### Elara, l'Armaiola
- **Chi è:** armaiola delle Terre Alte di Ignis. Ha l'armatura in parte fusa addosso: è entrata nella Forgia del Caos a cercare il fratello **Corin**, apprendista del Maestro di Forgia.
- **Cosa vuole:** riparare. Armature, lame, persone.
- **Cosa nasconde:** Corin è diventato uno degli **Apprendisti di Scoria**. Lei lo ha già incontrato in combattimento, e non lo ha colpito.
- **Tappe:** ✓ legata al pilastro · al Campo, il lavoro sulle armature · Ignis prima della caduta · Corin · il crogiolo · cosa si può riparare.

### Valerius, l'Incantatore
- **Chi è:** mago di Aetheria, elegante e vanitoso, autore del **Grimorio di Valerius**. Fu rinchiuso nella gabbia di cristallo per aver scritto che il silenzio della Badessa è una gabbia.
- **Cosa vuole:** essere riconosciuto. E non avere paura.
- **Cosa nasconde:** fu allievo dell'Accademia quando Sereth insegnava, e conosce il suo nome. Ha paura che dirlo lo cancelli.
- **Tappe:** ✓ nella gabbia di cristallo · al Campo, i monili e le lezioni di Etere · Aetheria che cade · l'Accademia · il maestro senza nome · il nome (ultimo gradino: Valerius è uno dei modi in cui il giocatore può sentirlo).

### Il Viandante Cieco
- **Chi è:** un pellegrino che ha dato gli occhi per vedere il sogno del Dio. Ora vede solo al buio. Porta la **Lanterna Spenta**, che contiene l'ultima luce di Aetheria.
- **Cosa vuole:** contare. Monete, passi, giorni: finché conta, esiste.
- **Cosa nasconde:** ha visto in sogno il Ritornante seduto sul trono del Dio (finale *Il Nuovo Dio*) e ha paura di lui.
- **Tappe:** ✓ gli incontri in discesa · ✓ al Campo, lontano dal fuoco · la lanterna · cosa ha visto · la moneta con l'occhio.

### Il Mercante Senza Volto
- **Chi è:** un Architetto Minore, tesoriere del cielo. Rimase nel Labirinto a proteggere i tesori; il volto gli è svanito, sostituito dal riflesso dell'oro. Gestisce le stanze del Mercante in tutti i piani nello stesso momento.
- **Cosa vuole:** storie. L'oro lo accetta con disprezzo; ciò che compra davvero sono i ricordi.
- **Cosa nasconde:** tiene da parte i ricordi che compra. Ha anche quelli del Ritornante, delle discese che ha dimenticato.
- **Tappe:** frasi nelle stanze del Mercante · un baratto di ricordi · il registro · cosa ha comprato da te · cosa ti restituisce.
- **Legami:** il **Mendicante Ombra** è un altro Architetto Minore rimasto; i due non si parlano.

### Linnea, la Fata della Fontana
- **Chi è:** una ninfa dei boschi della costa del Mare Interno. Quando la foresta diventò pietra si gettò nell'ultima sorgente pura; l'acqua divenne Memoria, e lei la fontana. È la **Fontana Fatata** che compare nei piani.
- **Cosa vuole:** che qualcuno ricordi il bosco.
- **Cosa nasconde:** ogni volta che il Ritornante beve, lei vede un pezzo delle sue discese dimenticate. Sa più di lui su di lui.
- **Tappe:** la fontana · il bosco · cosa ha visto bevendo · al Campo, una goccia in un'ampolla · il bosco ricordato.

### Kaelen il Muto
- **Chi è:** il miglior forgiatore dei Monti di Durn. Cercò di forgiare una spada capace di tagliare il Caos; la spada esplose e gli trasformò le mani in granito. Dalla bocca gli esce sabbia.
- **Cosa vuole:** finire la spada.
- **Cosa nasconde:** sa che Borek è vivo, e non lo cerca perché si vergogna.
- **Tappe:** la forgia nelle Miniere · i segni sul metallo · il materiale giusto · Borek · la spada finita (che non taglia il Caos: lo ferma per un istante).

### Altri volti
- **Ilse**, figlia di Alaric, coltivatrice di lavanda a Valeriana. Morta nella Discordia; ha lasciato una lettera al padre.
- **Nerea**, sorella di Silas. È diventata una **Statua di Sale** nei Chiostri, ferma ad ascoltare una voce.
- **Orvin il Cartografo**, nonno di Tessa. Ha disegnato la croce rossa. È al piano 30, o lo era.
- **Corin**, fratello di Elara, ora Apprendista di Scoria.
- **Malphas**, il primo avventuriero che capì che il Labirinto non concede la morte: l'Artiglio Vampirico è la sua mano.
- **Re Galdor**, il Re dei Goblin. Un uomo giusto finché la fame non lo ha reso disposto a tutto.

---

## Parte IX · Le vite prestate (le classi)

Ogni classe è un caduto che il Fuoco ha salvato dal guscio. La Maestria della classe sblocca un **ricordo** per livello: chi era, cosa faceva la notte della Discordia, come è morto, cosa vuole per riposare. Al livello più alto il ricordo si chiude e la vita trova pace.

| Classe | Vita prestata | Chi era |
|---|---|---|
| 🛡️ **Guerriero** | **Bran di Aurelia** | Guardia della Porta del Sole. La notte della Discordia tenne la porta mentre la città fuggiva, finché la porta non sprofondò con lui. Il suo ricordo è il peso di chi resta fermo. |
| 🗡️ **Ladro** | **Nim** | Ladra di Valeriana, rubava mappe e le rivendeva. Rubò quella di Orvin; per questo conosce strade che nessun altro conosce. Il suo ricordo è la fuga, e il debito. |
| 🔮 **Mago** | **Teodor Vasse** | L'ultimo allievo dell'Accademia della Luce Calma. Ascoltò l'ultima lezione di Sereth senza capirla. Il suo ricordo è una domanda agli Architetti che non ha avuto risposta. |
| ✨ **Paladino** | **Ser Maud** | Sorella d'ordine di Alaric. Cercò di raggiungerlo alla porta e non ci riuscì. Il suo ricordo è una promessa rimasta a metà. |
| 🪓 **Berserker** | **Hrodna di Ignis** | Danzatrice delle feste del fuoco. Quando il Fuoco divenne rabbia, la rabbia entrò in lei. Il suo ricordo è il dolore che diventa forza. |
| 🧪 **Alchimista** | **Ottavia Lune** | Alchimista di Aetheria, allieva dell'Alchimista Supremo della Pietra Filosofale. Voleva invertire la Discordia con una formula. Il suo ricordo è il calcolo freddo dentro una realtà folle. |
| 🗡️ **Assassino** | **Corvo** | Sicario alla corte di Galdor. Uccise il messaggero degli Architetti che avrebbe potuto fermare l'esperimento. Il suo ricordo è una colpa precisa, con un nome e un volto. |
| 💀 **Negromante** | **Isaura di Morva** | Parlava ai morti delle paludi quando i morti ancora se ne andavano. Dopo la Discordia i morti smisero di andarsene, e lei smise di dormire. Il suo ricordo è il confine fra un uomo e un'ombra. |
| 🌈 **Elementalista** | **Ilio** | Un bambino di Aetheria nato la notte della Discordia, l'unico che possa tenere insieme tutti gli elementi. È la vita più vicina all'Equilibrio, e la più vicina alla verità di Sereth. |

---

## Parte X · I boss e le creature

Le creature non sono nate dal Labirinto: sono ciò che il Labirinto ha fatto di chi c'era. Ogni voce del Bestiario racconta, a livelli, cosa si vede (prima volta), come si comporta (dopo averne uccisi alcuni) e chi era (dopo averne uccisi molti).

### I boss nativi dei biomi
La Badessa del Silenzio (Chiostri), il Caposquadra Sepolto (Miniere), l'Astronoma delle Guglie (Guglie), il Cuore del Ventre (Ventre), il Maestro di Forgia (Forgia), il Custode della Soglia (Soglia): vedi la Parte VI.

### I signori del declino
| Boss | Chi è |
|---|---|
| **Re dei Goblin** | Galdor. Ha scambiato la dignità del suo popolo per la sopravvivenza; protegge ancora sudditi diventati parassiti. |
| **Cavaliere Oscuro** | L'ombra del giuramento di Alaric: un'armatura che custodisce per abitudine. |
| **Drago di Zaffiro** | Il guardiano del Mare Interno. Bevve troppo dal passato e rivive ogni perdita di Aethelgard. |
| **Angelo Caduto** | La voce degli Architetti, mandato a purificare il Labirinto. Scoprì che la Purezza era follia, si strappò le ali e cadde. Chiede perdono a chi incontra. |
| **Negromante Supremo** | Il maestro di Isaura di Morva. Ha capito che tra un uomo e un'ombra non c'è differenza, e ne ha fatto un esercito. |
| **Demone Maggiore** | La rabbia che ha consumato Ignis, diventata qualcuno. |
| **Lich Reietto** | L'archivista dell'Accademia, custode delle cronache che il Labirinto vuole cancellare (anche quella col nome di Sereth). |
| **Behemoth Terrestre** | Il sarcofago dei Monti di Durn, che si rifiuta di accettare la fine del mondo. |
| **Signore delle Tempeste** e **Sovrano delle Tempeste** | Due fratelli tessitori di Valeriana, che ancora si contendono il cielo che non c'è. |
| **Il Re Dimenticato** | Un sovrano più antico di Galdor, cancellato persino dalla memoria della polvere. Nessuno sa più il nome del suo regno, nemmeno lui. |
| **Golem dell'Eternità** | Costruito ad Aurelia per resistere alla fine dell'universo. Ci sta riuscendo. |
| **Leviatano dei Sotterranei** | Il predatore delle falde di Aethelgard; appare come ciò che l'osservatore teme di più. |
| **Drago d'Ossidiana** | Il fratello di fuoco del Drago di Zaffiro, nato nelle foreste d'ossidiana di Ignis. |
| **Lich Signore del Gelo** | Un negromante di Morva che si è congelato l'anima per non sentire più. |
| **Araldo Radioso** | Un servitore della Luce Crudele: annuncia perfezioni che bruciano. |
| **Cavaliere dell'Apocalisse** | Il primo dei cavalieri che gli Architetti mandarono nel Labirinto dopo Alaric. Si è convinto che la fine sia il suo compito. |
| **Madre delle Melme** | Ciò che resta della fertilità di Aethelgard lasciata marcire nel buio: da lei nascono tutte le creature infette. |
| **Il Tristo Mietitore** | La morte che nel Labirinto non può più compiere il suo lavoro. Aspetta il Ritornante perché è l'unico che muore davvero, e ogni volta torna. Ha già scritto il suo nome. |
| **DIO ANTICO** | Sereth, o la parte di lui che vuole riposare. Vedi la Parte II. |

### Le creature comuni
Gli **Scheletri** sono Svuotati che cercano ancora un'uscita; i **Goblin** sono la gente di Galdor; gli **Orchi** i lavoratori delle cave fusi con la Terra; gli **Elementali** concentrazioni di rabbia con un oggetto di Aethelgard nel cuore (un pettine, una chiave, una fibbia); gli **Spiriti della Tempesta** i tessitori di Valeriana; i **Paladini Corrotti** guerrieri della fede che hanno scambiato la protezione per la persecuzione; la **Melma Acida** la linfa della Terra marcita; il **Mimic** un forziere che ha imparato a desiderare. Le creature dei biomi sono la gente di quella regione (vedi la Parte VI).

---

## Parte XI · Reliquie e oggetti

Le **reliquie** sono frammenti dei cristalli di Aetheria e di altri pezzi del mondo che hanno resistito alla Discordia. Ogni reliquia porta il desiderio di chi l'ha posseduta: per questo «fa» qualcosa. Le armi e le armature hanno una storia breve (`flavor`); le reliquie una più lunga (`lore`). Reliquie notevoli: l'**Artiglio Vampirico** (la mano di Malphas), lo **Scudo di Cristallo** (un frammento della cupola di Aurelia), la **Lente Prismatica** (le lenti con cui gli Architetti guardavano gli elementi), la **Corona del Re Folle** (la corona di Galdor, pesante di lacrime), la **Pietra Filosofale** (l'ultima opera dell'Alchimista Supremo, maestro di Ottavia Lune). La **Lama del Creatore** contiene un atomo di ogni elemento: è stata forgiata con un frammento della Prima Pietra.

---

## Parte XII · Le lettere insanguinate

Le lettere incise sulle pareti sono tutte del Ritornante, scritte in discese che non ricorda (gradino 5). Fino a quel momento il giocatore le legge come messaggi di sconosciuti; i più attenti notano che sembrano sapere troppo di lui.

Nella v6 le lettere si raccolgono in **fili**: ogni filo è una **discesa dimenticata**, raccontata in 8-10 lettere in ordine. Chi completa un filo vede nel Codice come è finita quella discesa. I fili:

1. **La prima discesa**: il risveglio accanto al Fuoco, la paura, la prima morte.
2. **La discesa con Silas**: quando scesero insieme per tre piani, e Silas lo vide morire.
3. **La lavanda**: la discesa in cui trovò il campo di Ilse e non lo disse ad Alaric.
4. **Il debito del Mercante**: la discesa in cui vendette un ricordo al Mercante, e quale.
5. **La croce rossa**: la discesa in cui arrivò dove aspettava Orvin.
6. **La Nemesi**: la discesa in cui un goblin senza nome lo uccise tre volte di fila.
7. **Il patto del sangue**: la discesa passata agli altari, sempre più corrotta.
8. **Il sale**: la discesa in cui si fermò ad ascoltare una voce cara nei Chiostri, e quasi rimase.
9. **La galleria**: la discesa in cui incontrò la squadra di Borek, prima del crollo.
10. **La gabbia di cristallo**: la discesa in cui lasciò Valerius nella gabbia, e perché.
11. **Il fratello**: la discesa in cui vide Corin nella Forgia.
12. **La fontana**: la discesa in cui bevve da Linnea fino a vedere troppo.
13. **Il trono**: la discesa in cui si sedette sul trono del Dio, e si alzò.
14. **La Soglia**: la discesa in cui il Custode gli disse il suo nome, e lui lo dimenticò morendo.
15. **L'ultima lettera**: ciò che scrive dopo aver ricordato (è il finale *La Lettera Mai Scritta*).

Le 35 lettere della v5 restano com'erano e si distribuiscono fra i fili 1, 6, 7, 8 e 14, o restano sciolte come frammenti fuori da ogni filo.

---

## Parte XIII · I finali

I finali rispondono a una domanda sola: **vale la pena continuare a scendere?**

| Finale | Risposta |
|---|---|
| **Il Sonno Spezzato** | Sì, per ora. Il Dio dorme, il mondo non rinasce, nessuno scende per un po'. Il Fuoco si abbassa, sollevato. |
| **Il Nuovo Dio** | No: il Ritornante si siede sul trono e diventa ciò che Sereth era diventato. Il Fuoco al Campo si spegne di un altro poco. |
| **Aethelgard Rinasce** | Sì, fino in fondo: con la verità di Silas e la libertà di Alaric, il Ritornante attraversa lo specchio. Il guscio si apre, sorge il sole. |
| **Il Custode** | Non si sa: il Ritornante prende il posto di Alaric alla porta. Qualcuno, un giorno, verrà a liberarlo. |
| **La Lettera Mai Scritta** | La domanda cambia: il Ritornante ricorda di essere Sereth, e sceglie cosa fare del suo rimorso. |

Nella v6 ogni finale ha varianti secondo le scelte fatte: chi è stato salvato o tradito, quanta Corruzione, quali vite prestate hanno trovato pace.

---

## Parte XIV · Glossario

- **Aethelgard**: il mondo di prima, ora inghiottito dal Labirinto.
- **Architetti Astrali**: i sette esseri che fissarono gli elementi in armonia. Sei fedeli (cinque tacciono, uno è il Fuoco) e il Rinnegato.
- **Ardel**: l'Architetto del Fuoco, che si fece brace. È il Fuoco del Campo.
- **Calaris**: l'isola più alta di Aetheria, sede della cittadella di Sereth; oggi la Soglia.
- **Ciclo del Labirinto**: il Labirinto che ripete i suoi piani in Eco quando il Dio si sveglia.
- **Equilibrio**: lo stato del mondo prima della Discordia; il ricordo custodito nello specchio.
- **Essenza Astrale**: la materia delle anime e degli elementi. Nutre il Fuoco.
- **Fauce del Caos**: il nome dotto del Labirinto.
- **Grande Discordia**: la notte dell'anno 1000 d.E. in cui il Vuoto si aprì.
- **Nemesi**: una creatura che ha bevuto un poco del nome del Ritornante uccidendolo.
- **Prima Pietra**: la prima pietra posata dagli Architetti, sotto i Chiostri.
- **Risonanza**: l'accordo fra un'anima e un elemento.
- **Ritornante**: il giocatore. L'unico che il Fuoco riporta.
- **Sereth**: il nome cancellato del Rinnegato.
- **Svuotati**: i morti del Labirinto che hanno perso l'Essenza; diventano il guscio.
- **Vite prestate**: le classi, eroi caduti che il Fuoco ha salvato e presta al Ritornante.
- **Vuoto**: l'Ottavo Elemento, il riposo che Sereth voleva dare al mondo.

---

## Appendice · Contraddizioni risolte

Le versioni precedenti della lore (la vecchia versione di questo file e alcuni testi del gioco) dicevano cose diverse. Queste sono le scelte del canone.

| Contraddizione | Scelta |
|---|---|
| Chi lacerò il velo: «l'ambizione di Re Galdor» (Cronache delle Ere, nel gioco) o «l'Architetto Rinnegato» (vecchia lore)? | Tutti e due: Galdor chiese la fine della carestia, Sereth tentò il Vuoto per dargliela. |
| Sir Alaric è il boss «Cavaliere Oscuro» o il cavaliere degli eventi? | Il cavaliere degli eventi è Alaric; il boss è l'ombra del suo giuramento. |
| Il *Trattato sulla Corruzione Elementale* era di «Mastro Elara, Alchimista»; nel gioco Elara è un'armaiola di Ignis. | Il trattato è di **Ottavia Lune** (la vita prestata dell'Alchimista). Elara è l'armaiola. |
| Il Diario di Silas nella vecchia lore copriva i piani 1-30 in 75 giorni; nel gioco Silas è sempre un piano più in basso. | I «giorni» di Silas sono quelli che lui conta; nel Labirinto sono passati secoli. Il diario dell'Archivio è una parte del diario vero. |
| Nella vecchia lore il Mercante voleva «storie», e anche oro. | Accetta l'oro con disprezzo; compra davvero i ricordi. |
| I «Piani 1-10 / 11-20 / 21-30» della vecchia lore contro i sei biomi del gioco. | Valgono i sei biomi di cinque piani ciascuno. |
| «Il Dio Antico è il Labirinto stesso» (vecchia lore) e «il Labirinto è un meccanismo di conservazione» (epilogo di Silas). | Il Labirinto è il guscio degli Architetti intorno al sogno del Dio: sono vere tutte e due, viste da due parti. |
| Le lettere «di altri avventurieri» e il finale in cui sono tutte del Ritornante. | Sono tutte del Ritornante; finché non lo sa, sembrano di altri. |
