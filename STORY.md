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
| | Battuta di un boss (inizio, fase, morte) | 1-2 frasi, al massimo 25 parole |
| **Fuori partita** | Conversazione al Campo (un argomento) | 80-250 parole, divise in battute |
| | Voce del Bestiario (un livello) | 40-80 parole |
| | Pagina dell'Atlante (storia di un bioma) | 80-200 parole |
| | Capitolo di un libro dell'Archivio | 80-400 parole |
| | Ricordo di una vita prestata (classe) | 70-250 parole |
| | Epilogo di un finale (una vita prestata) | 3-6 frasi, 40-120 parole |
| | Storia di un oggetto (Armeria) | 40-80 parole |

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
- **Dettagli già nel gioco:** ogni chiostro ha undici archi. Nel refettorio la tavola è apparecchiata per quaranta, con la sedia della Badessa a capotavola. Il registro dei voti è firmato da una sola mano per tutte le ultime novizie; l'ultima pagina dice «Restare». Le novizie hanno la bocca cucita con un filo d'argento. Sulla lavagna dell'aula di Sereth la firma è stata raschiata con una lama fino a incidere l'ardesia. Un copista di cenere scrive un elenco infinito di nomi, e quello del Ritornante c'è molte volte.

### ⛏️ Le Miniere della Testardaggine (piani 6-10)
- **Cos'era:** le gallerie dei Monti di Durn, nani e uomini insieme, gli ingranaggi dell'Era dell'Ambizioso Raggiungimento.
- **Chi ci vive:** minatori svuotati che scavano ancora, ingranaggi senzienti, carrelli posseduti, guardiani di basalto, lucciole del grisù.
- **Boss nativo:** **Il Caposquadra Sepolto**, che guidò l'ultima squadra sempre più in basso perché «sotto la prossima roccia» c'era l'uscita. Non ha mai dato l'ordine di risalire.
- **Pericolo:** il Gas del Silenzio, che toglie la voce e gli incantesimi.
- **Segreti:** la forgia di **Kaelen il Muto**; la galleria da cui la squadra di Borek non è uscita.
- **Temi:** la testardaggine, la fedeltà a un ordine sbagliato.
- **Dettagli già nel gioco:** lampade d'ottone ogni venti passi; canarini d'ottone a molla che fischiano quando arriva il Gas. Le gallerie basse erano dei bambini. Su una trave sono incisi gli undici nomi della squadra di Borek: sette cerchiati (risalirono con lui), quattro barrati. Il carro del pane per la squadra di Hadrek è fermo a metà strada («Tornate presto»). I cartelli dell'Ambizioso Raggiungimento dicono «Basta scavare». Uno degli ingranaggi giganti porta la firma del nonno di Borek.

### 🌪️ Le Guglie del Vento Urlante (piani 11-15)
- **Cos'era:** le torri dei tessitori di Valeriana e l'Osservatorio, dove si misuravano le stelle.
- **Chi ci vive:** sentinelle di nube, falchi astrali, corvi del tuono, spiriti dei ponti, astronomi caduti. Gli Spiriti della Tempesta sono i tessitori, costretti a tessere fulmini invece di seta.
- **Boss nativo:** **L'Astronoma delle Guglie**, che misurava le stelle dalla guglia più alta e le ha viste cadere. Fu la maestra di Silas.
- **Pericolo:** la Caduta Astrale: chi perde l'equilibrio non cade in basso, ma in un altro piano.
- **Segreti:** la mappa del cielo di Aethelgard com'era, incisa sul pavimento dell'Osservatorio; il campo di lavanda di Ilse, sospeso su una guglia.
- **Temi:** la curiosità, la perdita dei punti di riferimento.
- **Dettagli già nel gioco:** gli stendardi azzurri portano i nomi delle quaranta valli di Valeriana. Fra le guglie ci sono ponti di vento che si attraversano con una formula di Aetheria. Un corriere di Valeriana cerca da mille anni la casa a cui consegnare una lettera incompleta di un cavaliere alla figlia che piantava lavanda (Alaric a Ilse). Dalla grande lente dell'Osservatorio, girata verso il basso, si vede in fondo al Labirinto un occhio chiuso.

### 🫀 Il Ventre della Memoria (piani 16-20)
- **Cos'era:** il Mare Interno e le sue coste. Ora è un organismo: pareti traslucide come membrane, dentro oggetti e volti.
- **Chi ci vive:** ricordi annegati, volti nella membrana, sanguisughe madri, lacrime viventi, bambole di ricordi, meduse della memoria.
- **Boss nativo:** **Il Cuore del Ventre**. Batte al centro della Memoria; a ogni battito, in superficie, qualcuno dimentica qualcosa.
- **Pericolo:** la Dissoluzione dell'Io: il Labirinto ti digerisce un poco.
- **Segreti:** la sorgente di **Linnea**; la città capovolta i cui abitanti cadono verso l'alto; il punto dove il **Drago di Zaffiro** bevve troppo dal passato.
- **Temi:** la memoria come cibo, l'identità che si scioglie.
- **Dettagli già nel gioco:** galleggiano bambole di stoffa con il nome dei bambini che le avevano in braccio quando arrivò il mare. Al porto sommerso un vecchio aspetta il ritorno della flotta da mille anni. Nel Ventre il Ritornante può assistere al proprio funerale (la bara è vuota: «Non ancora»). Un lago mostra il suo riflesso invecchiato, che indica il fondo.

### 🔨 La Forgia del Caos (piani 21-25)
- **Cos'era:** le fucine delle Terre Alte di Ignis, dove dopo la Discordia gli Architetti tentarono di riforgiare insieme gli elementi.
- **Chi ci vive:** golem di scorie, martelli erranti, scudieri e apprendisti di scoria, crogioli ambulanti, scintille ribelli.
- **Boss nativo:** **Il Maestro di Forgia**. Gli Architetti gli chiesero di riforgiare gli elementi; ci prova ancora, colpo dopo colpo, su un'incudine che non c'è.
- **Pericolo:** l'Ebollizione Astrale, che brucia l'oro.
- **Segreti:** l'Incudine Cosmica; il crogiolo dove Elara perse il fratello; il primo tentativo di «riparare» il Normale.
- **Temi:** riparare ciò che non si può riparare, il lavoro come penitenza.
- **Dettagli già nel gioco:** sulla porta di una fucina c'è la lista degli apprendisti chiamati per la riforgiatura; accanto all'ultima data, «Tutti»; fra i nomi c'è «Corin di Ignis», con un piccolo cuore disegnato. Nel crogiolo di Elara ci sono impronte di due mani grandi e due piccole. Sul fondo c'è il lago d'oro fatto delle monete evaporate in mille anni, con i volti di chi le ha perse. Una foresta d'ossidiana suona ancora la ninnananna di Ignis.

### 👁️ La Soglia del Dio Antico (piani 26-30)
- **Cos'era:** Calaris, l'isola più alta di Aetheria, e la cittadella di Sereth. Ora piattaforme di volontà nel vuoto, elementi in collisione.
- **Chi ci vive:** frammenti di galassia, eco del Dio, frammenti del Prima, riflessi futuri, vuoti affamati, clessidre infrante.
- **Boss nativo:** **Il Custode della Soglia**, che c'era prima che il Labirinto avesse un nome e che «ti ha già visto». È l'ultimo servitore di Sereth; sa chi sei, e non lo dice.
- **Pericolo:** il Paradosso Temporale.
- **Segreti:** lo **specchio** oltre il Dio; la stanza vuota con una sedia («la fine del tempo»), dove Sereth sedeva a pensare.
- **Temi:** la colpa, il perdono, la tentazione del riposo.
- **Dettagli già nel gioco:** su un frammento di Calaris galleggiano un tavolino, una tazza di tè al bergamotto ancora tiepida e un trattato sul Normale con una nota a margine: «E se la fragilità fosse un diritto?». C'è una statua di marmo di un Architetto con il volto scalpellato via e le mani aperte in offerta. Una tavola apparecchiata per due ha il segnaposto «Tu»; l'altro è raschiato. Al piano 29 c'è l'ultimo bivacco di Orvin, con la mappa e la croce rossa («Piano trenta. Quasi.»). Le stelle della Soglia possono disporsi nella costellazione che c'era sopra il Campo la prima notte del Ritornante.

### ⏳ Le Eco (oltre il piano 30)
Il Dio, svegliandosi, ricorda il suo sogno e lo ripete più forte: i biomi tornano in un ordine diverso, con pericoli più duri e un nome (Eco II, Eco III…). Nelle Eco i luoghi conoscono il Ritornante: le voci dei Chiostri cantano il suo nome, i minatori lo salutano. Ogni trenta piani il Dio Antico è di nuovo lì, un po' più sveglio. L'Atlante ha quattro pagine sulle Eco (dal piano 31, 45, 61 e 91: quella del 45 racconta le creature che ricordano); nell'ultima, sotto la canzone, si sente una voce che ricorda una frase che comincia con «Ciò che è fragile».

---

**Atlante, seconda ondata (v6):** due pagine in più per bioma. Chiostri: *Le Undici Ore* (gli archi sono undici per le ore; i Chiostri sono fermi all'undicesima, l'ora del silenzio) e *La Fontana senz'Acqua* (le monete delle novizie, la statua di sale). Miniere: *La Canzone della Risalita* (i minatori di Hadrek la cantano scendendo) e *Le Tacche a Croce* (la riga finisce sotto la mano del Caposquadra). Guglie: *I Ponti di Vento* e *Le Quaranta Valli* (i colori segreti della seta rimasti nel vento). Ventre: *La Flotta che Aspetta* e *Le Membrane*. Forgia: *La Lista sulla Porta* (gli Apprendisti che si girano sono quelli senza data) e *Gli Alberi di Vetro*. Soglia: *La Sedia Rivolta al Buio* (piano 28) e *Lo Specchio della Verità* (dopo la vittoria).

## Parte VII · Il Campo

Il **Campo Base** è un cerchio di pietre intorno al Fuoco, in un punto del Labirinto che il Labirinto non vede. Chi ci arriva è al sicuro, ma solo finché il Fuoco arde.

- **Il Fuoco dell'Anima**: Ardel stesso. L'Essenza versata nel Fuoco torna come forza (i potenziamenti).
- **Chi ci vive:** i personaggi liberati o incontrati nelle discese, quando hanno un motivo per restare. Al Campo parlano più che in partita: è qui che raccontano la loro storia (vedi la Parte VIII).
- **Le strutture** sono pezzi di casa: il **Tavolo della Cartografa**, lo **Scrittoio di Silas**, l'**Altare della Purificazione**, la **Biblioteca dell'Arcano**, la **Sala d'Armi**. Ogni struttura nuova è un personaggio che decide di fermarsi.
- **La Taverna, la Forgia, il Grimorio, le botteghe**: il lavoro degli artigiani liberati (Speziale, Borek, Elara, Valerius).
- **L'Archivio di Aethelgard**: i libri ritrovati nelle discese. I primi sei danno un bonus; dalla v6 se ne aggiungono quindici di sola lettura (`data/books.json`, senza `bonus`), con capitoli che si aprono più avanti (`requires`). Chi li ha scritti:
  - *Trattato sulla Corruzione Elementale*: Ottavia Lune. L'ultimo capitolo (piano 20) ricorda la lavagna del maestro del Normale.
  - *Il Quaderno di Orvin il Cartografo*: Orvin. Il suo passo è di settantuno centimetri; la croce rossa l'ha sognata prima di disegnarla.
  - *Canti della Caduta*: canti delle novizie dei Chiostri; i sette sigilli degli Architetti, uno dei quali non volle mai essere trovato.
  - *Le Ricette di Mastro Ambrogio*: lo Speziale. L'ultima ricetta è la *Pozione del Conto*, una goccia per ogni persona curata.
  - *Il Registro della Squadra di Durn*: la squadra di **Hadrek**, quella che scese mentre Borek risaliva.
  - *Le Valli della Seta*: una guida di Valeriana (quaranta valli, le torri dei tessitori, ogni famiglia un colore segreto), con una postilla scritta dopo.
  - *Il Diario dell'Osservatorio*: l'allievo della Maestra delle stelle (le stelle non si guardano, si contano).
  - *Le Cronache del Mare Interno*: i porti, il Drago di Zaffiro che salutava i pescatori, il mare che si fermò.
  - *Il Libro delle Forge di Ignis*: la riforgiatura e la lista degli apprendisti fusi con il loro lavoro.
  - *Lettere di Ilse*: tre lettere di Ilse al padre e la lettera non finita di Alaric. **Berta** è la vecchia della valle della lavanda.
  - *Le Leggi di Galdor*: il re giusto, la carestia, il patto con un Architetto senza nome, il Re dei Goblin.
  - *L'Ordine dei Paladini*: il giuramento in tre parti (l'ultima: non chiedere mai cosa si custodisce), Alaric figlio di un fabbro, i Paladini Corrotti.
  - *I Taccuini di Calaris*: i taccuini di Sereth trovati alla Soglia, senza nome. Il terzo (il Vuoto come riposo) aspetta 40 boss, il quarto 50.
  - *Il Libro del Fuoco che Resta*: i sei Architetti fedeli, Ardel, il potere di riportare, il perché.
  - *Le Lezioni del Settimo Architetto*: gli appunti di Valerius, che lesse il nome del maestro e non lo scrive.
  - Terza ondata (diciannove libri):
    - *Il Breviario della Badessa*: le undici ore dei Chiostri, le novizie (Berenice canta stonata, Clelia ruba le pere, Agnese ha la voce più bella), il Voto nato dopo che una cosa sentì cantare Berenice.
    - *Il Taccuino di Fenn il Cercatore*: Fenn cercava il fratello **Arlo**, figlio di un orologiaio; il filo di Arlo finisce in un orologio fermo alle undici e un quarto.
    - *Il Manuale del Minatore di Durn*: le regole della Gilda, la canzone della risalita; Borek strappò la regola sul caposquadra che non vuole risalire, e firmò con una B.
    - *Le Leggende delle Sentinelle di Nube*: quaranta Sentinelle, una per valle, motto «Sopra»; la notte della Discordia ne cadde una sola, **Ivetta**, undici anni. Dire «Sopra» a una Sentinella di Nube a volte la ferma.
    - *Il Giornale di Bordo della Flotta di Port'Alba*: la **Gabbiana**, capitano **Edda Vael**; la flotta non affondò, scese nel Ventre e aspetta con le lanterne accese.
    - *Le Memorie di Malphas*: il medico che prese l'Essenza dei morenti; si tagliò la mano dopo aver lasciato andare l'Essenza di una novizia.
    - *Il Libro di Hob*: il boia che non diede mai un secondo colpo; Alaric gli strinse la mano senza pinze. L'ultimo condannato fu uno studente che aveva scritto «La Luce è malata».
    - *Il Canzoniere di Ignis*: le canzoni del suonatore **Gorm**; Hrodna vinse la scintilla cinque estati e rifiutò la sesta.
    - *Le Lettere di Mila*: lettere a Bran sotto un sasso; la casa con lo scudo, la giumenta Gerd, l'ultima lettera a settantanove anni.
    - *Il Diario di Corin, Apprendista*: valle di **Brasa**; Lisbet fu la prima a diventare parte del lavoro; «chiamatemi per nome: mi giro».
    - *Le Preghiere dei Grandi Templi*: la preghiera dei malati («non rendila perfetta: rendila sana»), che i sacerdoti smisero di dire.
    - *Le Favole del Bosco Vecchio*: raccolte da una maestra di Port'Alba; l'ultima, senza fine, è quella del viandante che si sveglia accanto al fuoco.
    - *Il Trattato sulle Rune dei Lapicidi*: una runa è una parola che la pietra tiene; il miglior lapicida incise per due anni segni non suoi sotto un'isola lontana, e la pietra si raffreddava.
    - *Il Grimorio Minore di Aetheria*: del maestro **Ruperto** («la magia si chiede, non si ordina»); l'Etere è la luce che resta.
    - *Il Registro del Mercante*: il Mercante era il tesoriere del cielo; ha comprato una per una le discese del Ritornante, «da restituire quando sarà il momento». Un conto aperto: «qualcuno sta pagando per tutti».
    - *Il Libro del Mendicante Ombra*: il canale fra chi dà e chi ha bisogno; ogni sera versa nel Fuoco quello che riceve.
    - *Il Quaderno delle Eco*: il Labirinto che ricorda; il Dio che torna «non riesce a dormire».
    - *Il Registro dei Custodi*: l'ordine delle porte; Alaric giurò come Paladino, non come Custode, e per questo non sa quando aprire. Il giuramento dei Custodi: aprire «il giorno in cui qualcuno avrà bisogno che si apra».
    - *Il Testamento di Galdor*: la figlia del re morì a sei anni nella carestia; fu Galdor a ordinare che il messaggio «non arrivasse».
  - Quarta ondata (dodici libri, capitoli lunghi):
    - *Le Cronache di Aurelia*: la città in cerchi, quattro porte (del Sole a oriente, del Fango a occidente), i quartieri (Templi, Studenti, Fabbri, Speziali, Concerie), le campane a undici rintocchi; il primo muro posato da un Architetto scese per ultimo. Alaric era figlio di un fabbro di serrature.
    - *Il Quaderno di Nerea*: trovato in una membrana del Ventre (forse sognato da Silas, forse vero). Nerea scese con la casa nella Valle delle Campane, aspettò Silas alla fontana senz'acqua, pianse fino al sale. I suoi occhi, come quelli di Silas, sono **grigio-verdi, come il mare d'inverno**.
    - *L'Erbario delle Paludi di Morva*: scritto da Isaura per le sue allieve traghettatrici; la bambina aveva sei anni e i capelli rossi; l'«erba del sonno» cresce dove un morto si addormenta davvero, e qualcuno l'ha trovata accanto a Isaura e alla bambina.
    - *Il Trattato sul Ritorno*: di «uno che ha guardato»; trentasette discese osservate; le ipotesi più vicine alla verità aspettano la vittoria e 40 boss, la conclusione (le lettere hanno la calligrafia del Ritornante) 50 boss.
    - *Il Libro del Drago di Zaffiro*: il Drago riportava a riva i pescatori morti; la corazza di scaglie la indossava Edda Vael; «non è alimentato dai rimpianti: li tiene».
    - *La Storia dell'Accademia della Luce Calma*: «Qui si impara a chiedere»; sette aule, quella del Normale in fondo al terzo piano; l'ultimo capitolo, di Valerius, dopo la vittoria e 40 boss.
    - *Il Diario della Maestra delle Stelle*: 1.145 stelle nelle notti limpide; Nerea aspettava Silas sulle scale contando i gradini; la Maestra sapeva che le luci cadute erano isole e diede a Silas la sua matita: «adesso conti tu».
    - *I Viaggi di Bertolo*: la figlia si chiamava **Rosella**; il Mercante gli disse che le persone che ami «non sono merce, sono debiti»; Bertolo lasciò la Tasca Dorata nel Labirinto.
    - *Il Libro delle Sette Cittadelle*: una cittadella per Architetto; solo quelle del Fuoco (una casa con la porta aperta a Ignis) e del Normale (su Calaris) restarono aperte; i due Architetti si volevano bene e bevevano il tè al bergamotto insieme. Ardel solo dopo la vittoria; il settimo, senza nome, dopo la vittoria e 40 boss.
    - *Le Cronache dei Paladini Corrotti*: del cavaliere **Severo**, che non bruciò Silas, ricominciò a dire la preghiera dei malati e si sedette accanto all'armatura di Maud.
    - *Il Libro dei Nomi del Ventre*: della bibliotecaria di Port'Alba **Adelina**, che salvò migliaia di nomi e perse il suo.
    - *Il Libro dei Sette Sigilli*: i sigilli della Prima Pietra (quello del Normale è una linea orizzontale, «come una persona sdraiata», e non si spezzò). Dopo la vittoria e 60 boss il Ritornante vi lascia un graffio, un ottavo segno.

Il Campo cambia con la storia: più personaggi trovano pace, più il Fuoco è caldo; chi sceglie la Corruzione lo trova un poco più freddo al ritorno.

---

## Parte VIII · I personaggi

Ogni scheda dice chi è, cosa vuole, cosa nasconde, e le **tappe** del suo arco: ciò che i testi futuri (eventi in discesa e conversazioni al Campo) raccontano, nell'ordine. Le tappe già nel gioco sono segnate con ✓.

### Sir Alaric, il Primo Paladino
- **Chi è:** il primo Paladino degli Architetti, nato ad Aurelia nell'Era dell'Ambizioso Raggiungimento. Nella notte della Discordia gli Architetti gli ordinarono di custodire una porta: quella dietro cui avevano chiuso il Vuoto. Giurò sul sigillo di Luce. Gli Architetti tacquero; il giuramento no.
- **Cosa vuole:** riposare, e sapere se sua figlia **Ilse** è sopravvissuta.
- **Cosa nasconde:** la porta non conduce più a nulla perché il Vuoto è già dentro tutto il Labirinto. Lui lo sa da secoli, e continua a custodirla perché è l'unica cosa che ricorda di saper fare.
- **Il Cavaliere Oscuro:** il boss con quel nome è l'ombra che il giuramento proietta nel Labirinto, un'armatura vuota che combatte per abitudine. Liberare Alaric non toglie il boss: lo rende un guscio senza nessuno dentro.
- **Tappe:** ✓ la porta · ✓ il cavaliere stanco (la lavanda) · ✓ l'ultimo sigillo · ✓ il campo di lavanda sulle Guglie (la vanga di Ilse) · ✓ la lettera di Ilse («Per mio padre, alla porta»: la lavanda era fiorita) · ✓ il giorno della Luce crudele (gli Architetti, impauriti, gli ordinarono di custodire senza chiedere) · ✓ l'armatura di Ser Maud sulla strada («Arrivo, fratello. Aspettami.») · ✓ dietro il muro: una stanza vuota con le impronte di un solo paio di stivali · ✓ il Cavaliere senza nessuno (l'armatura che fa la ronda da sola, dieci passi e giro) · ✓ la lavanda alla porta · al Campo, come Luce: i ricordi di Aurelia.
- **Nota:** i capitoli dopo l'ultimo sigillo valgono sia se Alaric è stato liberato (una luce calma accompagna il giocatore) sia se il giocatore ha preso il suo posto (il sigillo sulla schiena prude).
- **Legami:** Ser Maud (la vita prestata del Paladino) era sua sorella d'ordine.
- **Dettagli già nel gioco:** Ilse coltivava un campo intero di lavanda a Valeriana.
- **Al Campo, come Luce (v6):** non parla; i suoi argomenti passano nel calore, come immagini. Da ragazzo soffiava nel mantice della bottega del padre, ad Aurelia. Ilse, a cinque anni, gli portò una piantina di lavanda e gli promise un campo «con le file dritte come le tue spade». Nel giorno del giuramento sentì la paura degli Architetti, e non chiese mai perché avessero paura. Conosceva per nome tutti i Paladini dell'Ordine, e li perse alla Luce. Al Campo, a volte, fa ancora la ronda (dieci passi e giro) e se ne vergogna. Non è mai riuscito a finire la lettera a Ilse. Dopo la vittoria mostra la stanza vuota dietro la porta; dopo la vittoria e 40 boss smette di fare la guardia.
- **Al Campo, terza ondata:** mostra Hob, il boia a cui strinse la mano; Severo, il suo allievo, seduto accanto a Maud; il giuramento dei Custodi, che non conosceva: aspetta che qualcuno bussi sulla sua luce (`alaric_bussato`). La vanga di Ilse nel campo delle Guglie: qualcuno ha tenuto le file dritte, e non si sa se Ilse sia sopravvissuta. Dopo la vittoria e 50 boss apre da solo l'arco della porta e si mette di lato.

### Silas, il Cercatore
- **Chi è:** un astronomo di Valeriana, allievo dell'Astronoma delle Guglie. È sceso per ritrovare la sorella **Nerea**, inghiottita dal Labirinto con la loro casa. Scrive tutto perché il Labirinto gli mangia i ricordi: ha già dimenticato il colore degli occhi di lei.
- **Cosa vuole:** arrivare al fondo e capire. Poi, quando ha visto lo specchio, tornare indietro senza sentirsi un vigliacco.
- **Cosa nasconde:** scende da molto più dei suoi «settantacinque giorni»: il tempo del Labirinto lo ha trattenuto per secoli. Ha visto il Ritornante morire molte volte e lo ha disegnato ogni volta. Il Fuoco non lo ha mai scelto, e Silas gliene vuole un po'.
- **Tappe:** ✓ il fuoco azzurro · ✓ il diario strappato · ✓ la soglia e lo specchio · ✓ in discesa: la ragazza che ascolta (la statua di Nerea) · ✓ l'Osservatorio (quattrocentododici borchie mancanti, la matita della Maestra) · ✓ la pagina antica nella membrana · ✓ la Maestra («il mio allievo peggiore») · ✓ un piano più in basso (il ritratto finito) · ✓ la cosa d'inchiostro, fatta delle sue parole di paura · ✓ il diario chiuso (portarlo in fondo, o ricominciare dal giorno uno) · ✓ al Campo: il fuoco azzurro, il diario, Nerea, le stelle, la Maestra, i ritratti, il Fuoco che non lo ha scelto, i settantacinque giorni, la statua nei Chiostri, lo specchio, la notte dell'abbandono, l'ultima pagina, dopo il Dio · in discesa: la statua di Nerea · l'Osservatorio · la pagina nella membrana.
- **Dettagli già nel gioco:** il suo fuoco azzurro nasce da una scheggia di vetro di stella dell'Osservatorio e non scalda. La notte della Discordia contò quattrocentododici stelle cadute. Il Ritornante, visto da lui, ha sempre la spalla sinistra un po' più bassa. Se il giocatore lo ha abbandonato, Silas non chiude più del tutto la mano sinistra. Sospetta che Nerea sia la statua di sale al secondo piano dei Chiostri, vicino alla fontana senz'acqua. La matita gli è stata data dalla Maestra (l'Astronoma), che gli bacchettava le dita perché guardava le stelle invece di contarle.
- **Dettagli della v6 (seconda ondata del Campo):** l'ultima annotazione del *Diario dell'Osservatorio* è sua: salì sulla guglia all'alba e la Maestra non volle scendere. Ha smesso di contare a duecento le volte che ha visto morire il Ritornante. Il Mercante si è rifiutato di vendergli il colore degli occhi di Nerea: «nessuno l'ha mai venduto, nemmeno tu». Delle quattrocentododici «stelle» che contò, solo cinque erano stelle: le altre erano isole di Aetheria con le luci accese. Ha portato un fiore di carta alla statua di sale e le ha letto il diario (flag `silas_nerea_trovata` se il giocatore gli dice che era lei).
- **Terza ondata del Campo:** non riesce ad aprire il quaderno di Nerea; se il giocatore gli dice il colore degli occhi lo scrive nel diario (`silas_occhi_nerea`). La Maestra gli diede la matita sulla guglia. Severo non lo bruciò. Conta i ritorni invece delle morti. Ha rimesso nella fontana la moneta verde di Nerea. Dopo la vittoria e 40 boss: «il riposo non è smettere di ricordare, è smettere di avere paura di dimenticare».

### La Cartografa (Tessa)
- **Chi è:** **Tessa**, nipote di **Orvin il Cartografo**, che mappò i piani da 1 a 29 e non tornò dal trentesimo. Il suo nome il giocatore lo scopre solo al Campo.
- **Cosa vuole:** completare la mappa del nonno, e mettere sulla mappa ciò che il nonno non credeva (la Prima Pietra).
- **Cosa nasconde:** la croce rossa sulla mappa («qui ti aspetto») non l'ha disegnata lei: era già sulla mappa di Orvin, con la sua calligrafia.
- **Tappe:** ✓ perduta, senza provviste · ✓ ritrovata · ✓ la Prima Pietra · ✓ al Campo: le pergamene, il nome, il nonno, come si disegna un posto che cambia, il Viandante, le Guglie, la Prima Pietra, la croce rossa, la copia venduta, il Ventre, il piano che manca, la mappa intera · in discesa: la croce rossa · Orvin.
- **Dettagli già nel gioco:** misura tutto in passi (il suo è di sessantadue centimetri). Nella sua famiglia il nome si usa solo da bambini, poi si diventa il proprio lavoro; prima di Orvin la Cartografa era la madre di lui. Orvin scese l'ultima volta quando Tessa aveva nove anni («faccio il piano che manca e torno per cena»). Il Labirinto ha una «grammatica»: i chiostri hanno sempre undici archi, gli ingranaggi delle Miniere girano sempre verso le scale. Sotto la Prima Pietra la mappa non torna: c'è più spazio del dovuto. Ha venduto al Mercante il ricordo di chi le insegnò a temperare il carboncino. Messa intera, la mappa è una spirale con un punto vuoto al centro, più in basso del trenta.
- **Dettagli della v6:** il Mercante le vendette la mappa del piano dodici, quella che Nim stringeva cadendo; se il giocatore le dice il nome, lo scrive accanto al piano (`cartografa_nim`). Chi le insegnò a temperare il carboncino aveva le dita sporche di nero e sapeva di tabacco. Orvin accorciava il passo per camminarle accanto e correggeva le misure la sera. Da bambina aveva paura delle scale. Nella Forgia le incudini guardano sempre verso la scala che sale. Messe insieme, le pergamene fanno una spirale con il centro vuoto.
- **Terza ondata del Campo:** ha sovrapposto Aurelia ai Chiostri (il primo muro è sotto la Prima Pietra). Il passo del Ritornante è di settantaquattro centimetri, il sinistro un poco più corto. Ha scritto il nome di Edda Vael sulla mappa del Ventre. Lo spazio in più sotto la Prima Pietra è grande come una persona sdraiata: lo segna con una linea orizzontale. Sogna la croce rossa come Orvin, ma è lei ad aspettare. Lascerà un piano vuoto, per Tessa bambina.

### Lo Speziale (Ambrogio)
- **Chi è:** **Ambrogio**, speziale di Aurelia, vecchio già prima di scendere. Lo chiamano tutti «lo Speziale»; dice il suo nome solo a chi lo ha liberato più volte.
- **Cosa vuole:** curare, e farsi perdonare.
- **Cosa nasconde:** nel Crepuscolo Lungo vendette a Sereth gli estratti con cui l'Architetto studiava il Vuoto, senza chiedere a cosa servissero. Ha sempre sospettato di aver aiutato la fine del mondo.
- **Tappe:** ✓ incatenato dalla magia del sangue · ✓ al Campo: hai mangiato?, la bottega, le catene, il nome, le ricette, Borek, Valerius, il Fuoco, il cliente senza nome, cosa comprava, il conto, la pozione che non cura.
- **Dettagli già nel gioco:** la bottega era dietro l'Accademia di Aurelia, con un mortaio d'ottone sopra la porta e un gatto che dormiva sulla bilancia. Le catene di sangue si sciolgono solo con il sangue di un altro offerto senza obbligo. Le pozioni dei forzieri seguono la sua ricetta (due gocce di salvia in più). Segna l'altezza della fiamma del Fuoco su un sasso a ogni ritorno: le tacche scendono. Il cliente era Sereth: comprava solo estratti di Normale (cento once nell'ultimo anno), firmava con un sigillo di cera bianca senza disegno, e la sera prima della Discordia disse che servivano «a far riposare chi è stanco». La «pozione del conto» si riempie di una goccia per ogni persona che cura.
- **Dettagli della v6:** il gatto della bottega si chiamava **Lardo** (non era grasso); a volte nei Chiostri si sente un gatto. Nella ricetta per le bruciature ha scritto talpa invece di tasso. L'estratto di Normale si fa lasciando una cosa comune in acqua di pozzo quaranta giorni: una goccia ogni quaranta giorni. Quando butta nel Fuoco la sabbia di Kaelen, una volta ha sentito crepitare il nome di Borek. Dopo la vittoria e 40 boss confessa di aver pensato, per un momento, che il cliente avesse ragione.
- **Terza ondata del Campo:** sa che Lardo dorme ancora sulla bilancia. Conosceva Malphas e gli vendeva salvia e arnica. Ha un barattolo vuoto con l'etichetta «erba del sonno». Dice ancora la preghiera dei malati su ogni rimedio. Ha distillato la sabbia di Kaelen: una goccia con la frase «Era colpa mia, ragazzo. Non tua». Ricetta per un fuoco stanco: persone intorno ogni sera, storie ad alta voce, nessuna fretta.

### Borek, il Maestro d'Armi
- **Chi è:** un nano dei Monti di Durn, maestro d'armi e forgiatore. Era il caposquadra di una squadra di minatori-soldati; è l'unico uscito dalla galleria crollata.
- **Cosa vuole:** forgiare armi degne, bere, non pensare alla galleria.
- **Cosa nasconde:** era l'allievo di **Kaelen il Muto**, e lo crede morto. Ha preso il comando della squadra al posto del Caposquadra Sepolto, che non voleva risalire, e li ha portati verso l'alto: solo lui ce l'ha fatta.
- **Tappe:** ✓ prigioniero dietro la grata · ✓ al Campo: l'acciaio, la birra, la grata, i Monti, la squadra, la galleria, il maestro, le voci delle Miniere, il vecchio, l'armaiola, il Caposquadra, perché forgia · in discesa: Kaelen vivo.
- **Dettagli già nel gioco:** l'acciaio buono «canta», quello del Labirinto è «pieno di rimpianto». Le armature che aggiustava da prigioniero hanno un punto debole sotto l'ascella sinistra. La squadra era di undici; sette risalirono con lui, quattro restarono con il Caposquadra, che si chiamava **Hadrek** e gli insegnò a leggere la roccia. La galleria crollò al terzo giorno di risalita. Tiene il martello di Kaelen, col manico consumato da due mani. Sa delle voci su un fabbro dalle mani di pietra e non vuole crederci.
- **Voce:** «ragazzo» per chiunque, anche per Alaric.
- **Dettagli della v6:** i nomi della squadra: con lui **Ulma** (cantava), **Brokk** (non parlava), i gemelli **Tor** e **Tir**, **Dagna** (la più giovane), **Fennir** (il cuoco), **Sigrun** (rideva quando aveva paura); con Hadrek **Orm**, **Gilda**, **Bodvar** e la vecchia **Ragna**. Lasciava il punto debole sotto l'ascella sinistra apposta. A Durn si lascia un boccale pieno per un anno a chi non torna; Borek ne lascia uno per Kaelen da quando sa che è vivo. Il manico del martello di Kaelen ha due impronte, una dentro l'altra.
- **Terza ondata del Campo:** la regola strappata diceva di portare su a forza il caposquadra che non vuole risalire. Ulma cantava la canzone della risalita quando la galleria crollò. Ha ritrovato il suo rivetto morbido nell'armatura di Severo e non la fonde. Chiede al Ritornante una tacca a croce accanto al Caposquadra (`borek_tacca`). Forgia con Kaelen la spada per un ragazzo, il primo acciaio senza rimpianto del Campo. Dopo la vittoria beve il boccale di Hadrek.

### Elara, l'Armaiola
- **Chi è:** armaiola delle Terre Alte di Ignis. Ha l'armatura in parte fusa addosso: è entrata nella Forgia del Caos a cercare il fratello **Corin**, apprendista del Maestro di Forgia.
- **Cosa vuole:** riparare. Armature, lame, persone.
- **Cosa nasconde:** Corin è diventato uno degli **Apprendisti di Scoria**. Lei lo ha già incontrato in combattimento, e non lo ha colpito.
- **Tappe:** ✓ legata al pilastro · ✓ al Campo: cosa ripara, le Terre Alte, l'armatura addosso, Corin, quello che si è girato, cosa si può riparare · in discesa: il crogiolo, Corin.
- **Dettagli già nel gioco:** a Ignis gli alberi d'ossidiana suonavano col vento, ogni casa aveva una forgia sempre accesa, e spegnerla voleva dire un lutto. Il ferro della Forgia le è colato addosso mentre si chinava. Corin ha una cicatrice sul mento; quando lei lo ha chiamato per nome si è girato, poi l'ha colpita.
- **Dettagli della v6:** sulla lista della fucina grande, accanto al nome di Corin, la data manca: dentro la scoria c'è ancora un pezzo di lui. La cicatrice sul mento se la fece a sette anni cadendo dalla scala della forgia di casa; il padre spense la forgia per consolarlo e i vicini pensarono a un lutto. Il padre faceva chiodi e cardini («le spade le fa chi ha paura, i cardini chi ha una casa») e spense la forgia quando Corin entrò nella riforgiatura; Elara la riaccese partendo. Tiene le Vesti di Brace di una certa **Lisbet**.
- **Terza ondata del Campo:** ha letto il diario di Corin: si era girato perché era ancora lui. Ha appeso le Vesti di Lisbet al Fuoco. Da bambina giocava davanti alla casa del Fuoco a Ignis. Sa che sul braccio di Corin c'è un punto di pelle viva. Dopo la vittoria e 40 boss scende a liberarlo un pezzo alla volta, raccontandogli la casa (il cavallo del vicino si chiamava Rapa).

### Valerius, l'Incantatore
- **Chi è:** mago di Aetheria, elegante e vanitoso, autore del **Grimorio di Valerius**. Fu rinchiuso nella gabbia di cristallo per aver scritto che il silenzio della Badessa è una gabbia.
- **Cosa vuole:** essere riconosciuto. E non avere paura.
- **Cosa nasconde:** fu allievo dell'Accademia quando Sereth insegnava, e conosce il suo nome. Ha paura che dirlo lo cancelli.
- **Tappe:** ✓ nella gabbia di cristallo · ✓ al Campo: i monili, le isole del cielo, la gabbia, il grimorio, l'Accademia, il maestro senza nome · il nome (ultimo gradino: Valerius è uno dei modi in cui il giocatore può sentirlo).
- **Dettagli già nel gioco:** è nato sull'isola più bassa di Aetheria, quella dei pescatori di nuvole. La gabbia era di silenzio. Ha notato che il Fuoco si abbassa di un capello quando lancia un incantesimo al Campo (l'Etere «si presta»). Sereth insegnava l'elemento Normale nell'aula in fondo al terzo piano dell'Accademia, quella con la lavagna d'ardesia; nell'ultima lezione scrisse «Ciò che è fragile ha diritto al riposo» e sotto il suo nome, che Valerius lesse.
- **Dettagli della v6:** il padre era il miglior pescatore di nuvole dell'isola più bassa; Valerius partì a dodici anni, e quando piove nel Labirinto assaggia la pioggia. Scrisse la frase sulla gabbia in rosso su un muro dei Chiostri; una novizia, **Agnese**, si mise a cantare sotto il velo (è lei la novizia del *Velo del Silenzio*), e lui la sentì per anni dalla gabbia. Prestò le sue scarpe vecchie a Teodor, che non le mise mai. Non lancia più incantesimi al Campo, per educazione verso il Fuoco.
- **Terza ondata del Campo:** ringrazia l'Etere, come gli insegnava Ruperto. Imparò dalla gabbia tutte le canzoni di Agnese (stonava l'ultima strofa). L'Arcimago lo bocciò due volte e gli chiese di scendere con lui; Valerius disse di no. Nell'aula del Normale il nome sotto la frase è cancellato. Il graffio sulla Prima Pietra è tiepido: la pietra lo ha accettato.

### Il Viandante Cieco
- **Chi è:** il cartografo di corte di Re Galdor. Sotto dettatura di Sereth disegnò le piante delle volte sotto Calaris, cioè la forma del Labirinto prima che esistesse («ho disegnato questo labirinto prima che esistesse»). Scese con i suoi **sette figli**, che reggevano le lanterne: sono le sette ombre che lo seguono. Diede gli occhi al Mercante Senza Volto in cambio di vedere il sogno del Dio; nelle orbite porta due monete d'oro. Ora vede solo al buio. Porta la **Lanterna Spenta**, che contiene l'ultima luce di Aetheria, raccolta da un cristallo mentre cadeva.
- **Cosa vuole:** contare. Monete, passi, giorni: finché conta, esiste.
- **Cosa nasconde:** ha visto in sogno il Ritornante seduto sul trono del Dio (finale *Il Nuovo Dio*) e ha paura di lui.
- **Tappe:** ✓ gli incontri in discesa · ✓ al Campo, lontano dal fuoco · la lanterna · cosa ha visto · la moneta con l'occhio.
- **Dettagli della v6:** le piante gliele dettava una voce gentile e stanca, dietro una tenda, che a volte chiedeva «è troppo?». Il figlio più piccolo si chiamava **Mattia**, aveva otto anni e reggeva la lanterna di latta; gli risponde «quasi» da mille anni. Una volta, cinquecento anni fa, smise di contare per un sonno e non c'era niente. Teme il sogno del trono; al giocatore che promette di non sedersi chiede di ricordare chi contava i suoi passi.
- **Terza ondata del Campo:** lavorava accanto al lapicida del muro sbagliato. Mattia adesso si siede accanto a chi arriva. La voce dietro la tenda gli offriva il tè al bergamotto, ricordava i nomi dei figli e lo mandò a casa il giorno prima della Discordia. Ha visto il Mercante e il Mendicante incrociarsi: una moneta, pesata, che pesava il giusto. Le monete negli occhi hanno il volto di Galdor giovane e il grano: valevano un pane. Dopo la vittoria e 40 boss conta all'indietro, verso lo zero.

### Il Mercante Senza Volto
- **Chi è:** un Architetto Minore, tesoriere del cielo. Rimase nel Labirinto a proteggere i tesori; il volto gli è svanito, sostituito dal riflesso dell'oro. Gestisce le stanze del Mercante in tutti i piani nello stesso momento.
- **Cosa vuole:** storie. L'oro lo accetta con disprezzo; ciò che compra davvero sono i ricordi.
- **Cosa nasconde:** tiene da parte i ricordi che compra. Ha anche quelli del Ritornante, delle discese che ha dimenticato.
- **Tappe:** ✓ il baratto (il sapore del pane) · ✓ il registro (il Ritornante gli ha venduto il nome della prima persona che ha amato, per un'ora di vita al piano diciotto) · ✓ i due che non si parlano (lui e il Mendicante, tesorieri dello stesso tesoro: uno lo tiene, l'altro lo dà via) · ✓ il tesoro del cielo (migliaia di ricordi di Aethelgard in vasetti di vetro) · ✓ il riflesso (sotto l'oro, un uomo stanco con gli occhi chiari) · ✓ il vasetto degli occhi del Viandante (pagati: un sogno) · ✓ i tuoi ricordi, in una cassa a parte · ✓ il prezzo pagato: li restituisce, perché il Fuoco ha già pagato il conto · frasi nelle stanze del Mercante.
- **Legami:** il **Mendicante Ombra** è un altro Architetto Minore rimasto; i due non si parlano.

### Linnea, la Fata della Fontana
- **Chi è:** una ninfa dei boschi della costa del Mare Interno. Quando la foresta diventò pietra si gettò nell'ultima sorgente pura; l'acqua divenne Memoria, e lei la fontana. È la **Fontana Fatata** che compare nei piani.
- **Cosa vuole:** che qualcuno ricordi il bosco.
- **Cosa nasconde:** ogni volta che il Ritornante beve, lei vede un pezzo delle sue discese dimenticate. Sa più di lui su di lui.
- **Tappe:** ✓ la fontana che parla · ✓ il bosco nell'acqua · ✓ quello che ha visto (una discesa dimenticata) · ✓ l'albero di pietra (il più vecchio, gli parlava d'estate) · ✓ la sorgente vera, nel Ventre · ✓ una goccia in un'ampolla (al Campo: *L'Ampolla di Linnea*) · ✓ la fontana asciutta · ✓ il bosco ricordato (muschio e una felce) · ✓ al Campo: il calore, il nome del bosco, il pomeriggio della pietra, cosa sa di te, perché si consuma, il muschio.
- **Dettagli già nel gioco:** il bosco non aveva nome; gli uomini della costa lo chiamavano il Bosco Vecchio. Diventò pietra in un pomeriggio di fine estate, dalle radici alle foglie; gli uccelli sono rimasti nella pietra con le ali mezze aperte. Linnea ricorda che una volta il Ritornante ha scritto qualcosa con un sasso sul muro accanto alla fontana, e poi è andato a morire: lo tiene lei, finché non sarà il momento. Tenere i ricordi la consuma come il ritorno consuma il Fuoco: «siamo parenti, noi e lui».
- **Dettagli della v6:** nel Bosco Vecchio un pettirosso è rimasto di pietra con il becco aperto verso la sorgente. Gli uomini della costa prendevano solo la legna caduta; un ragazzo che tagliò un ramo vivo si perse tre giorni. La Memoria ha un sapore: per il Ritornante sa di fumo e di una lettera bruciata. Dopo la vittoria Linnea gli dice il nome del Fuoco, Ardel, che il Fuoco le ha detto una notte («la sua cosa più preziosa, e la più stanca»).
- **Terza ondata del Campo:** la maestra delle favole veniva alla sua sorgente; il pettirosso ha il becco bagnato. Adelina beveva da lei per ricordare il suo nome. Nelle discese del Ritornante ha visto qualcuno scrivere una lettera su un'isola alta e bruciarla senza mandarla (solo dopo la vittoria e 40 boss). Ardel le ha detto che un giorno il Ritornante non dovrà più tornare: avrà finito.

### Kaelen il Muto
- **Chi è:** il miglior forgiatore dei Monti di Durn. Cercò di forgiare una spada capace di tagliare il Caos; la spada esplose e gli trasformò le mani in granito. Dalla bocca gli esce sabbia.
- **Cosa vuole:** finire la spada.
- **Cosa nasconde:** sa che Borek è vivo, e non lo cerca perché si vergogna.
- **Tappe:** ✓ la forgia nel basalto · ✓ i segni sul metallo (incide parole squadrate a scalpello) · ✓ l'acciaio che canta · ✓ il martello di Borek («VIVO») · ✓ la spada esplosa (le schegge e la sagoma bruciata nel basalto) · ✓ il pezzo che manca (una goccia della Prima Pietra) · ✓ il messaggio per il Campo («Ragazzo. Fuoco. Buono. Scusa.») · ✓ la spada finita, che ferma il Caos per un istante · ✓ al Campo (dopo il messaggio): parlare a segni, il ragazzo, la spada, la sabbia, i Monti, dopo la spada.
- **Dettagli già nel gioco:** il granito gli arriva ai gomiti; le mani non sentono niente tranne il Fuoco del Campo. La sabbia che gli esce dalla bocca sono «parole non dette»: lo Speziale la spazza ogni mattina e la butta nel Fuoco.
- **Dettagli della v6:** lo Speziale gli fa da interprete per i segni nella cenere. Le sue mani sentono il Fuoco come acqua calda. Voleva tagliare il Caos per separarlo, come un nodo; il Caos non era annodato, era stanco. Con il flag `kaelen_borek` e 30 boss dice la sua prima parola da secoli, «Ragazzo», e Borek gli si siede accanto. Se le mani tornassero forgerebbe una spada semplice per un ragazzo che comincia.
- **Terza ondata del Campo:** conosceva Hadrek da giovane; sotto l'impugnatura del suo piccone incise «risali». Il granito si ritira di un dito da quando forgia con Borek (seicento anni, a quel ritmo). Con 35 boss dice la seconda parola, «Grazie», al Ritornante. Ha capito che il Caos non si taglia: si abbraccia, come fa il Fuoco. Lascia Borek battere da solo.

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

I ricordi sono in `data/vite.json` (sei per classe, uno per livello di Maestria) e si leggono nel Codice, *Vite prestate*. Il primo torna alla prima discesa con la classe. I ricordi che toccano il quarto gradino (il Vuoto come riposo) aspettano anche la vittoria e 40 boss: il quinto e il sesto di Teodor, il sesto di Isaura, gli ultimi tre di Ilio.

**Dettagli già nel gioco:**
- **Bran**: la sua compagna di turno era **Mila**, l'ultima arrivata in caserma, che aveva paura dei cavalli. Bran le disse di andare con l'ultimo carro; lei arrivò sulle colline, visse, e tenne appeso sulla porta uno scudo da guardia. Gerd russava.
- **Nim**: le guardie di Valeriana la chiamavano *il gatto grigio*. Rubò la mappa di Orvin e gliela riportò; per ripagarlo scese con lui al piano otto e lo tirò fuori da una frana. Morì cadendo fra due guglie con la mappa del piano dodici in mano: quella mappa è arrivata a Tessa, portata dal Mercante Senza Volto. Tessa non sa da dove venga.
- **Teodor**: figlio di un mugnaio, all'Accademia per una borsa di studio, spesso l'unico studente del corso sul Normale. Non fece la sua domanda («chi decide quando una cosa fragile ha bisogno di riposare?»); la gridò dal tetto la notte della Discordia, e la sua voce è rimasta nei Chiostri. Lesse il nome del maestro scritto sotto la frase dell'ultima lezione, e lo ha dimenticato.
- **Maud**: Alaric le mise la spada sulla spalla e le parlava di Ilse e della lavanda. Scese dopo la Discordia con un fazzoletto nel guanto («arrivo, fratello. Aspettami») e morì a poche file dalla porta, senza chiamarlo.
- **Hrodna**: danzatrice delle feste d'estate di Ignis, figlia di un fabbro. La notte della Discordia ballava a una festa di nozze quando il fuoco diventò rabbia ed entrò in lei. Morì danzando nella Forgia del Caos contro il Demone Maggiore.
- **Ottavia**: scrisse il *Trattato sulla Corruzione Elementale* (le malattie degli elementi). Odiava la Pietra Filosofale del suo maestro. La notte della Discordia versò la sua formula dei sette elementi nel cristallo; nel guscio trovò l'errore: non aveva contato il Vuoto.
- **Corvo**: per ordine di Galdor uccise il **messaggero** che gli Architetti fedeli mandarono a corte tre giorni prima della Discordia, e bruciò il messaggio. Il messaggero si chiamava **Ivo**.
- **Isaura**: accompagnava i morti verso l'Essenza su una barca piatta; il suo maestro è il Negromante Supremo. Nel Labirinto ritrovò la bambina morta di febbre che non era riuscita ad accompagnare e si addormentò con lei nei Chiostri: è l'unica ombra del Labirinto che dorme davvero.
- **Ilio**: sentiva una musica quando gli elementi si incontravano (Fuoco e Acqua una nota bassa e calda, Vento e Terra una nota lunga, Luce e Tenebra un silenzio pieno). Scese fino alla Soglia e si sedette sulla sedia di Sereth, rivolta verso il buio; non ne conosce il nome.

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

### Le discese dimenticate, seconda ondata
Otto fili nuovi in `data/lettere.json`: il gatto dei Chiostri (il Ritornante trovò Lardo sulla bilancia della bottega dello Speziale), il piccolo Goblin che lo morse e poi lo difese, la partita a carte con il Mercante (che gli restituì il ricordo del fuoco che non brucia, «non ha prezzo»), Ivetta sul ponte delle Campane (le disse che la rete aveva preso vivo il neonato), l'acqua per il pettirosso dentro la memoria di Linnea, la Gabbiana (lesse ad alta voce i cinquantadue nomi del ruolo di bordo), il nome senza data di Corin (che si mise davanti al Ritornante), la notte con la Badessa (che difese il canto di Agnese).

### Il Bestiario a livelli
Ogni creatura ha tre voci (`data/bestiario.json`): *Cosa si vede* (la prima volta che la incontri), *Come si comporta* (dopo `habits` sconfitte, i boss dopo `boss_habits`) e *Chi era* (dopo `story` sconfitte, i boss dopo `boss_story`). La terza voce di un boss può accennare al gradino della Scala che si raggiunge battendolo più volte: quella del DIO ANTICO racconta del Rinnegato che voleva dare riposo, senza nominarlo.

### Le creature comuni
Gli **Scheletri** sono Svuotati che cercano ancora un'uscita; i **Goblin** sono la gente di Galdor; gli **Orchi** i lavoratori delle cave fusi con la Terra; gli **Elementali** concentrazioni di rabbia con un oggetto di Aethelgard nel cuore (un pettine, una chiave, una fibbia); gli **Spiriti della Tempesta** i tessitori di Valeriana; i **Paladini Corrotti** guerrieri della fede che hanno scambiato la protezione per la persecuzione; la **Melma Acida** la linfa della Terra marcita; il **Mimic** un forziere che ha imparato a desiderare. Le creature dei biomi sono la gente di quella regione (vedi la Parte VI).

---

## Parte XI · Reliquie e oggetti

Le **reliquie** sono frammenti dei cristalli di Aetheria e di altri pezzi del mondo che hanno resistito alla Discordia. Ogni reliquia porta il desiderio di chi l'ha posseduta: per questo «fa» qualcosa. Le armi e le armature hanno una storia breve (`flavor`); le reliquie una più lunga (`lore`). Reliquie notevoli: l'**Artiglio Vampirico** (la mano di Malphas), lo **Scudo di Cristallo** (un frammento della cupola di Aurelia), la **Lente Prismatica** (le lenti con cui gli Architetti guardavano gli elementi), la **Corona del Re Folle** (la corona di Galdor, pesante di lacrime), la **Pietra Filosofale** (l'ultima opera dell'Alchimista Supremo, maestro di Ottavia Lune). La **Lama del Creatore** contiene un atomo di ogni elemento: è stata forgiata con un frammento della Prima Pietra.

### L'Armeria
Ogni arma, armatura, accessorio e reliquia ha una storia più lunga nel Codice, alla pagina *Armeria* (`data/armeria.json`): le armi, le armature e gli accessori si leggono quando li puoi trovare (subito, o dopo lo sblocco alla Forgia), le reliquie dopo averle trovate. Non conta nel completamento del Codice. Le storie non promettono effetti diversi da quelli dei dati. Fatti nuovi:
- Il boia di Aurelia si chiamava **Hob**, e piangeva di nascosto prima di ogni esecuzione. L'Ascia del Boia la vietò Alaric da Primo Paladino; i Paladini Corrotti la ripresero.
- **Port'Alba** era il porto più grande del Mare Interno, da cui partì la flotta che non tornò; i guardiani del suo faro portavano la *Cappa delle Maree*. I pescatori raccoglievano le scaglie cadute al Drago di Zaffiro e ne fecero la *Corazza di Scaglie di Drago*.
- Sotto Aurelia dormiva un **colosso di Terra** messo dagli Architetti a reggere la città: si spezzò per tenerla più a lungo. L'*Egida del Titano* è il suo petto, il *Bracciale del Titano* un suo frammento.
- **Malphas** era un medico di Aurelia nel Crepuscolo Lungo che prolungava le vite con l'Essenza dei morenti; i suoi allievi ridussero il suo artiglio ad anello.
- **Bertolo**, mercante di Valeriana, scese con la *Tasca Dorata* per riavere la figlia. **Fenn**, un Cercatore, diede l'occhio sinistro a una strega delle paludi per vedere l'Essenza.
- La *Pergamena d'Oro* è il contratto di Galdor; l'unica riga leggibile è «Il popolo non avrà più fame», e la firma dell'Architetto è grattata via. La *Bussola Perfetta* la fece un cartografo di corte per Galdor (il Viandante Cieco, senza che il testo lo dica).
- La *Campanella degli Spiriti* fu un regalo del Mercante a Silas, «forse un anticipo». Il *Contratto Demoniaco* è l'unico contratto che il Mercante dice di non aver scritto.
- Il *Teschio di Sangue* era di un Berserker di Ignis che danzò tre giorni nella Forgia; Hrodna diceva che ballava meglio di lei. Il *Velo del Silenzio* fu tessuto per l'unica novizia che non volle tacere: continuò a cantare sotto il velo.
- L'Arcimago dell'Accademia scese fino al piano trenta: lo scettro tornò da solo, l'anello restò con il suo dito.

### Le voci dei boss
Ogni boss ha due o tre battute per l'inizio dello scontro, il cambio di fase e la morte (`data/voci_boss.json`), scelte con il generatore dei testi: non cambiano nessun tiro di dado. Sono in partita, quindi brevi, e restano al primo gradino della Scala: il DIO ANTICO parla di stanchezza e di riposo senza dire di chi. Il Cavaliere Oscuro, morendo, nomina Ilse e la lavanda.

---

## Parte XII · Le lettere insanguinate

Le lettere incise sulle pareti sono tutte del Ritornante, scritte in discese che non ricorda (gradino 5). Fino a quel momento il giocatore le legge come messaggi di sconosciuti; i più attenti notano che sembrano sapere troppo di lui.

Nella v6 le lettere si raccolgono anche in **fili** (`data/lettere.json`): ogni filo è una **discesa dimenticata**, raccontata in 8 lettere in ordine, che si trovano incise sulle pietre dei falò e accanto ai forzieri. Chi completa un filo legge nel Codice (*Discese dimenticate*) come è finita quella discesa. I fili, con il gradino da cui si aprono:

1. **La prima discesa** (piano 1): il risveglio, la Badessa, la prima caduta mentre il Fuoco lo chiamava indietro.
2. **La discesa con Silas** (piano 4): tre piani insieme; morì tenendo la mano di Silas, che scriveva con l'altra. Per questo Silas lo ha visto morire.
3. **La lavanda** (piano 11): trovò il campo di Ilse prima di tutti e non diede il fiore ad Alaric.
4. **Il debito del Mercante** (piano 6): le fragole, il cielo d'estate, il nome del primo cane, il nome della prima persona amata.
5. **La croce rossa** (piano 20): arrivò al bivacco di Orvin al piano 29 e finì la sua mappa.
6. **La Nemesi** (piano 3): un goblin lo uccise tre volte e, sconfitto, gli disse grazie.
7. **Il patto del sangue** (piano 5): di altare in altare, fino al trono; il Fuoco sente ogni goccia data agli altari.
8. **Il sale** (piano 2): quasi diventò una statua; lo salvò una novizia con la bocca cucita.
9. **La galleria** (piano 7): era uno dei sette che risalirono con Borek, dietro di lui, quando la galleria crollò. Borek non lo sa.
10. **La gabbia di cristallo** (piano 9): lasciò Valerius nella gabbia per paura di quello che sapeva; Valerius lo chiamò con un nome.
11. **Il fratello** (piano 21): aiutò Elara a cercare Corin; con la ninnananna di Ignis, Corin sbagliò il ritmo di un colpo.
12. **La fontana** (piano 8): bevve da Linnea fino a vedere tutte le sue discese; l'unico a ringraziarla.
13. **Il trono** (vittoria): si sedette sul trono del Dio e si alzò quando sentì il Fuoco abbassarsi. È il sogno che il Viandante ha visto.
14. **La Soglia** (vittoria e 40 boss): il Custode gli disse il suo nome e una volta lo chiamò «maestro»; la sua stessa mano cancellò il nome dal muro.

Il quindicesimo filo è il finale *La Lettera Mai Scritta*. Le 35 lettere della v5 restano com'erano e si distribuiscono fra i fili 1, 6, 7, 8 e 14, o restano sciolte come frammenti fuori da ogni filo.

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

Nella v6, dopo il testo di ogni finale, un **epilogo** dice cosa fa in quel finale la vita prestata della classe con cui ci sei arrivato (`data/epiloghi.json`, un epilogo per finale e per classe): Bran, Nim, Teodor, Maud, Hrodna, Ottavia, Corvo, Isaura e Ilio reagiscono ognuno a modo suo. Gli epiloghi letti restano nel Codice, alla pagina *Finali*. Fatti nuovi: nel *Sonno Spezzato* Corvo incide il nome di Ivo su una pietra nelle Valli del Sud; in *Aethelgard Rinasce* la guardia alla Porta del Sole ha il viso di Mila, e Alaric chiama Maud per nome nel campo di lavanda; nella *Lettera Mai Scritta* la domanda di Teodor è scritta fra le lettere, e sotto il Ritornante scrive la risposta.

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
| Il Viandante Cieco dice di essere stato «il cartografo del re» e di aver «disegnato questo labirinto prima che esistesse»; Orvin è il cartografo dei piani. | Sono due cartografi: il Viandante era quello di corte di Re Galdor e disegnò, per Sereth, la forma delle volte; Orvin mappò i piani dopo. |
