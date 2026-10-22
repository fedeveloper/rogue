<div align="center">

# 🌀 Il Labirinto degli Elementi e del Caos

**Un roguelite da terminale in cui ogni discesa è diversa, ogni morte ti rende più forte e ogni elemento conta.**

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![Dipendenze](https://img.shields.io/badge/Dipendenze-nessuna-brightgreen)
[![Test](https://github.com/fedeveloper/rogue/actions/workflows/tests.yml/badge.svg)](https://github.com/fedeveloper/rogue/actions/workflows/tests.yml)
![Piattaforme](https://img.shields.io/badge/Windows%20%7C%20macOS%20%7C%20Linux-grey)
![Licenza](https://img.shields.io/badge/Licenza-Uso_Personale-green)

</div>

---

Sotto le rovine di Aethelgard si apre un labirinto che cambia forma a ogni passo. Scegli un eroe, un tratto e — se hai il coraggio — un patto con il Caos. Poi scendi: **30 piani** di mostri, trappole, mercanti, falò ed eventi che ti costringono a scegliere. In fondo ti aspetta il **DIO ANTICO**.

Morirai. Spesso. Ma l'**Essenza Astrale** che riporti indietro resta: con essa sblocchi nuovi eroi, armi leggendarie, reliquie e potenziamenti permanenti. Ogni discesa ti avvicina un po' di più al fondo.

```text
!!! Incontri un GOBLIN [⚪ Normale] !!!

--- ⚔️ IN COMBATTIMENTO ⚔️ ---
Tu: 120/120 HP | Goblin: 11 HP
  > Attacca
    Difesa Aggressiva (Dimezza danni e Contrattacca)
    Apri Inventario (Usa oggetto = Costa Turno)
    Statistiche Eroe
    Tenta la Fuga
```

## 🚀 Gioca in 30 secondi

Serve solo **Python 3.9 o superiore**: nessuna libreria da installare.

```bash
git clone https://github.com/fedeveloper/rogue.git
cd rogue
python roguelike.py
```

> **Windows:** se le emoji non si vedono bene, esegui prima `chcp 65001` o usa *Windows Terminal*.

Si gioca **solo con la tastiera**: frecce ⬆️⬇️ per muoversi nei menu, **Invio** per confermare, **Ctrl+C** per uscire. Il salvataggio (`profile.json`) si crea da solo al primo avvio.

## ✨ Perché giocarci

- 🗺️ **Una mappa per ogni piano.** Quattro file di stanze collegate (combattimento, mercante, falò, forziere, trappola, evento o la *Stanza del Mistero*) e il boss in fondo, tutte visibili fin dall'arrivo: scegli il percorso, non solo la porta. Nemici e boss crescono con la profondità.
- 🌍 **Sei biomi, sei regole.** Ogni cinque piani il Labirinto cambia volto e legge: la *Nostalgia Letale* dei Chiostri, il *Gas del Silenzio* delle Miniere, la *Caduta Astrale* delle Guglie, la *Dissoluzione dell'Io* del Ventre, l'*Ebollizione Astrale* della Forgia e il *Paradosso Temporale* della Soglia. Ogni bioma ha i suoi nemici nativi e le sue stanze speciali.
- 🔥 **Combattimento tattico.** Il nemico **annuncia la sua mossa**, colpo pesante, guardia, rigenerazione o colpo infetto, e tu decidi se attaccare o difenderti. Sette elementi, vantaggi e svantaggi, **Risonanze** quando arma e armatura condividono l'elemento e **7 reazioni** (Vapore, Gelo, Eclissi…) quando li combini.
- 🧬 **8 classi** con alberi di Maestria a 5 livelli che sbloccano bonus, oggetti, reliquie e altre classi.
- 🎭 **7 tratti** e **5 Patti del Caos**: 3,584 combinazioni di partenza diverse.
- 📖 **Eventi che ricordano.** 46 storie a scene con opzioni che esistono solo per la tua classe, il tuo tratto o le tue reliquie: `[Mago]`, `[Tocco di Mida]`, `[Chiave Arrugginita]`. Il Labirinto ricorda chi hai aiutato e chi hai derubato, e certe scelte tornano a bussare qualche piano dopo.
- 🗝️ **Personaggi che ritornano.** *Sir Alaric*, il Primo Paladino, e *Silas*, il Cercatore, hanno storie in tre capitoli che proseguono di run in run. Le tue scelte decidono come finiscono, e se liberi Alaric il Cavaliere Oscuro non tornerà più.
- 🩸 **Corruzione.** Le scelte oscure danno potere e opzioni proibite, ma il Labirinto comincia a nasconderti le cose: gli effetti delle scelte, le mosse dei nemici.
- 🏁 **5 finali.** Uccidere il Dio, prenderne il posto, risvegliare Aethelgard… e un finale segreto per chi legge davvero il Labirinto.
- 🔥 **Un campo che ricorda.** Chi salvi nel Labirinto viene a scaldarsi al tuo fuoco, ti parla di ciò che hai fatto e ti aiuta a costruire.
- 🌟 **30 reliquie** che piegano le regole: danni raddoppiati, scudi, vampirismo, oro moltiplicato.
- 🏕️ **Meta-progressione profonda**: potenziamenti permanenti, una Forgia per sbloccare equipaggiamento, artigiani da liberare, un Archivio di lore con bonus, imprese da completare.
- ♾️ **Modalità Infinita** dopo la prima vittoria, per chi vuole spingersi oltre il piano 30.

## 🧬 Gli eroi

| Classe | HP | Stile | Maestria Lv.2 | Sblocco |
|---|---|---|---|---|
| ⚔️ **Guerriero** | 120 | Tank bilanciato, contrattacca quando si difende | Mano Pesante | Iniziale |
| 🗡️ **Ladro** | 85 | Agile e ricco, critico garantito dopo la Concentrazione | Tasche Nascoste | Iniziale |
| 🔮 **Mago** | 65 | Arma di Fuoco potente e mira eccellente, ma fragile | Sintonia | Iniziale |
| 🛡️ **Paladino** | 180 | Ultra-tank con Risonanza di Luce fin dall'inizio | Baluardo della Fede | Maestria Guerriero Lv.5 |
| 🪓 **Berserker** | 100 | Glass cannon: l'ascia più forte, nessuna armatura | Furia Sanguinaria | Impresa «Danza con la Morte» |
| 🧪 **Alchimista** | 95 | Quattro pozioni iniziali e bombe di Fuoco | Metabolismo Alterato | Impresa «Genio Elementale» |
| 🥷 **Assassino** | 75 | 20% di critico innato e schivata altissima, ma fragile | Imboscata | Maestria Ladro Lv.5 |
| 💀 **Negromante** | 70 | Risonanza di Tenebra fin dall'inizio | Raccolto d'Anime | Maestria Mago Lv.5 |

Ogni classe ha un **albero di Maestria** a 5 livelli. Si sale giocando con quella classe. Il **Lv.4** dà un bonus permanente a *tutti* gli eroi; il **Lv.5** sblocca una classe, un tratto o una reliquia. Assassino e Negromante, per esempio, si conquistano portando al massimo Ladro e Mago.

## 🎭 Tratti e Patti

All'inizio di ogni discesa scegli un **tratto**, che cambia le regole per tutta la partita:

| Tratto | Effetto | Sblocco |
|---|---|---|
| **Nessun Tratto** | Gioca con le regole standard. | Iniziale |
| **Patto del Sangue** | +50 ATK, ma HP Massimi dimezzati e le cure hanno effetto ZERO. | 10 morti |
| **Tocco di Mida** | Non ottieni EXP dai mostri, ma l'Oro è TRIPLICATO. | 5.000 Oro raccolti in totale |
| **Aristocratico** | Inizi con 500 Oro, ma i nemici non droppano più Oro. | Impresa «L'Avaro» |
| **Cacciatore Etereo** | Primo colpo nemico manca sempre al 100%. -20% Schivata totale. | Impresa «Epuratore di Demoni» |
| **Titano** | +100 HP Max. Precisione e Schivata dimezzate. | Impresa «Furia Cieca» |
| **Benedetto** | Inizi con una Reliquia difensiva e resisti al primo colpo letale. | Maestria Paladino Lv.5 |

Dopo la prima vittoria si sbloccano i **Patti del Caos**: maledizioni da attivare a piacere, una per una, in cambio di più Essenza. Con tutti e cinque il moltiplicatore arriva a **×2,25**.

| Patto | Effetto | Essenza |
|---|---|---|
| **Durezza** | HP di tutti i Nemici +30% | +25% |
| **Furia** | Attacco di tutti i Nemici +30% | +25% |
| **Carestia** | Le pozioni curano la metà | +25% |
| **Inflazione** | I prezzi del Mercante sono Raddoppiati | +25% |
| **Labirinto Mortale** | Le Trappole infliggono danni Doppi | +25% |

## ⚔️ Il combattimento

A ogni turno puoi **attaccare**, **difenderti** (ogni classe ha la sua difesa: contrattacco, concentrazione o riparo magico), usare un oggetto dallo zaino, consultare le statistiche o **tentare la fuga** (impossibile contro i boss). Le statistiche mostrano la tua **probabilità reale di colpire** contro il nemico che hai davanti.

**Elementi.** Un colpo *Super Efficace* fa il **50% di danni in più** e ha +15% di precisione; uno *Poco efficace* fa metà danni e −20% di precisione.

- 🔥 **Fuoco** batte 🌪️ **Vento** · 💧 **Acqua** batte 🔥 **Fuoco** · 🪨 **Terra** batte 💧 **Acqua** · 🌪️ **Vento** batte 🪨 **Terra**
- ✨ **Luce** e 🌑 **Tenebra** sono forti l'una contro l'altra e deboli contro sé stesse; ⚪ **Normale** è neutro.

**Risonanze.** Se arma e armatura hanno lo stesso elemento (non Normale), ottieni un bonus per tutto lo scontro. Si ricalcola subito se cambi equipaggiamento a metà combattimento.

| Elemento | Risonanza | Effetto |
|---|---|---|
| 💧 Acqua | Flusso | Attacco nemico ridotto del 15% |
| 🌪️ Vento | Raffica | +15% Schivata in combattimento |
| 🪨 Terra | Fortezza | +5 Difesa fissa |
| 🌑 Tenebra | Ombra | +5 Danni fissi ad ogni colpo |
| ✨ Luce | Benedizione | Cura 3 HP a ogni tuo attacco |
| 🔥 Fuoco | Ustione | Infliggi 5 danni da Ustione cumulabili per colpo |

**Status.** Alcuni nemici infliggono *Veleno* o *Sanguinamento*, che svaniscono a fine scontro (l'*Antidoto* li toglie subito). Alcune armi speciali li infliggono ai nemici.

**Maledizioni.** Gli oggetti `[MALEDETTO]` hanno statistiche altissime ma drenano HP od Oro, o rallentano. Si purificano al Falò (100 Oro) o con l'*Acqua Santa*.

## 🏕️ Il Campo Base

Fra una discesa e l'altra spendi l'**Essenza Astrale**:

- 🔥 **Il Fuoco dell'Anima** — 14 potenziamenti permanenti: HP, Oro, schivata, precisione, EXP, sconti, la *Speranza di Luce* (fino al 15% degli HP recuperati a ogni piano) e altro.
- ⚒️ **La Forgia Dimensionale** — sblocca armi, armature, monili, consumabili e reliquie.
- 🍺 **La Taverna** — le classi da conquistare e come ottenerle.
- 📜 **Grimorio e Imprese** — le sfide completate e i progressi di Maestria.
- 📚 **L'Archivio di Aethelgard** — 3 tomi di storia da sbloccare, ognuno con un bonus permanente.
- 📖 **Il Codice del Labirinto** — bestiario, personaggi, eventi, lettere insanguinate e reliquie scoperti fra una run e l'altra, con la percentuale di completamento. Ciò che manca è un `???` da riempire.
- 🧑‍🔧 **Gli artigiani** — salva lo *Speziale*, *Borek*, *Elara* e *Valerius* dagli eventi del labirinto: apriranno una bottega dove comprare consumabili, armi, armature e monili con cui iniziare la discesa successiva.

E in **Impostazioni** scegli la velocità del testo: lenta, normale, veloce o istantanea.

## 💰 L'Essenza

| Come finisce la discesa | Essenza ottenuta |
|---|---|
| ☠️ Morte | 20% dell'Oro posseduto |
| 🏃 Fuga dal labirinto | 100% dell'Oro posseduto |
| 🏆 Vittoria al piano 30 | 100% dell'Oro + 1.000 |

A questo si aggiungono **50 Essenza per ogni boss** sconfitto, il moltiplicatore dei **Patti** e, oltre il piano 30 in Modalità Infinita, un ulteriore **×1,5**.

## 📚 Enciclopedia

<details>
<summary>🌟 Le 30 reliquie</summary>

Si tengono al massimo 4 reliquie alla volta: trovandone un'altra scegli quale sacrificare.

| Reliquia | Effetto | Come ottenerla |
|---|---|---|
| **Artiglio Vampirico** | Ogni tuo attacco a segno ti cura di 5 HP. | Boss, forzieri, eventi |
| **Lente Prismatica** | Vantaggi e Svantaggi Elementali sono RADDOPPIATI: Super Efficace x2 invece di x1,5, Poco efficace x0,25 invece di x0,5. | Boss, forzieri, eventi |
| **Scudo di Cristallo** | Il primo danno che subisci in ogni combattimento è ridotto a 0. | Boss, forzieri, eventi |
| **Tasca Dorata** | Aumenta l'Oro trovato nei forzieri e dai mostri del 25%. | Boss, forzieri, eventi |
| **Idolo della Guerra** | Aumenta in modo permanente il tuo Attacco Base di +5. | Boss, forzieri, eventi |
| **Calice dell'Alchimista** | Le cure di pozioni e consumabili sono più forti del 50%. | Boss, forzieri, eventi |
| **Mantello Nebbioso** | Aumenta passivamente la Schivata del 15%. | Boss, forzieri, eventi |
| **Bussola Perfetta** | La Fuga riesce sempre al 100% (non funziona sui Boss). | Boss, forzieri, eventi |
| **Occhio del Cacciatore** | Aumenta la tua Precisione del 20%. | Boss, forzieri, eventi |
| **Spallacci di Rovo** | Se subisci danno da un attacco, il nemico subisce 5 Danni Puri. | Boss, forzieri, eventi |
| **Cuore di Troll** | Ottieni +2 HP Massimi ogni volta che uccidi un nemico. | Boss, forzieri, eventi |
| **Tomo della Conoscenza** | L'Esperienza ottenuta aumenta del 30%. | Boss, forzieri, eventi |
| **Idolo dell'Avidità** | Tutto l'Oro è RADDOPPIATO, ma non puoi più schivare (Schivata 0%). | Boss, forzieri, eventi |
| **Lama di Sangue** | Attacco +10, ma subisci 3 Danni ogni volta che decidi di attaccare. | Boss, forzieri, eventi |
| **Corona del Re Folle** | I colpi Super Efficaci o Critici infliggono il 50% di danni in più. | Forgia (✨1000) |
| **Anello Vampirico Maggiore** | Recuperi 2 HP extra ad ogni tuo attacco a segno. | Forgia (✨1500) |
| **Clessidra del Destino** | Riduce del 20% la Schivata di base di tutti i nemici. | Forgia (✨800) |
| **Armatura a Spilli** | Riflette 3 danni al nemico ogni volta che vieni colpito. | Forgia (✨600) |
| **Pergamena d'Oro** | Ogni volta che ottieni Oro in combattimento o tesori, recuperi 2 HP. | Forgia (✨700) |
| **Campanella degli Spiriti** | 15% di probabilità di negare un attacco nemico andato a segno. | Forgia (✨1200) |
| **Pietra di Luna** | La tua Difesa aumenta del 50% se usi Difesa/Riparo. | Forgia (✨500) |
| **Contratto Demoniaco** | Raddoppia i tuoi danni base, ma perdi 5 HP a fine combattimento (il tributo non può ucciderti). | Forgia (✨1000) |
| **Pozione Senza Fondo** | Le pozioni curative hanno il 25% di chance di non consumarsi. | Forgia (✨900) |
| **Bussola Dimensionale** | Aumenta probabilità di trovare Tesori e Stanze del Mistero. | Forgia (✨1000) |
| **Cuore di Drago** | +50 HP Max fissi, con i relativi HP subito disponibili. | Impresa «Il Sopravvissuto» |
| **Sigillo Elementale** | Annulla la debolezza elementale in difesa. | Impresa «Equilibrista» |
| **Spirito della Spada** | +15 ATK finché impugni un'arma di livello 1. | Impresa «Lama di Cristallo» |
| **Maschera Antigas** | Immunità totale ai danni delle Trappole. | Impresa «Assaggiatore di Veleni» |
| **Teschio di Sangue** | Ogni nemico sconfitto incrementa i tuoi HP Massimi di 1. | Maestria Berserker Lv.5 |
| **Pietra Filosofale** | A fine combattimento, 20% di chance di convertire l'XP in Oro sonante. | Maestria Alchimista Lv.5 |

</details>

<details>
<summary>⚔️ Le 24 armi</summary>

L'ATK reale cresce con il piano in cui l'arma viene trovata; le armi di elemento *Normale* ricevono un bonus di ATK.

| Arma | ATK base | Elemento | Caratteristiche | Come ottenerla |
|---|---|---|---|---|
| **Spada Corta** | 3 | Casuale | — | Disponibile da subito |
| **Ascia da Battaglia** | 4 | Casuale | — | Disponibile da subito |
| **Alabarda della Guardia** | 5 | Casuale | — | Disponibile da subito |
| **Spadone a Due Mani** | 6 | Casuale | — | Disponibile da subito |
| **Martello da Guerra** | 6 | Casuale | — | Disponibile da subito |
| **Katana Affilata** | 8 | Casuale | — | Disponibile da subito |
| **Lancia Perforante** | 9 | Casuale | — | Disponibile da subito |
| **Meteora Chiodata** | 11 | Casuale | — | Disponibile da subito |
| **Spada del Carnefice** | 15 | Casuale | Arma devastante ma sbilanciata: -10% Precisione. | Forgia (✨250) |
| **Falce Divora-Anime** | 18 | Casuale | Danni base spaventosi per le run più profonde. | Forgia (✨500) |
| **Spadone Infranto** | 25 | Casuale | Leggendario, ottenuto tramite Imprese. | Impresa «Fabbro Folle» |
| **Lama del Creatore** | 30 | Casuale | Un'arma leggendaria infusa con gli elementi primordiali. Si ottiene sconfiggendo il DIO ANTICO, il boss finale. | Vittoria al piano 30 |
| **Zweihander d'Oro** | 25 | Casuale | Arma massiccia d'oro puro. Più oro hai, più fa male: +1 ATK ogni 100 Oro posseduto (fino a +30). | Impresa «Mani Bucate» |
| **Ascia del Boia** | 25 | Casuale | Lenta ma letale: -15% Precisione, ma 35% di probabilità di colpo critico (danni doppi). | Maestria Berserker Lv.3 |
| **Falce del Mietitore** | 22 | 🌑 Tenebra | Estremamente letale. La lama è intrisa di buio. 20% di infliggere Sanguinamento. Sempre di elemento Tenebra. | Forgia (✨650) |
| **Spadone del Re Caduto** | 20 | Casuale | Un'arma colossale e inarrestabile. | Forgia (✨400) |
| **Lancia di Ghiaccio Eterno** | 16 | 💧 Acqua | Arma lunga con un nucleo gelido. Sempre di elemento Acqua. | Forgia (✨300) |
| **Frusta di Spine Corrotte** | 14 | Casuale | Attacchi veloci e crudeli. 30% di infliggere Sanguinamento. | Forgia (✨250) |
| **Martello Meteoritico** | 24 | 🔥 Fuoco | Massa enorme incandescente. Sempre di elemento Fuoco. | Forgia (✨700) |
| **Pugnali del Vento Tagliente** | 12 | 🌪️ Vento | Due lame invisibili e rapidissime. 25% di infliggere Sanguinamento. Sempre di elemento Vento. | Forgia (✨200) |
| **Bastone dell'Alba** | 17 | ✨ Luce | Canalizza la luce divina. Sempre di elemento Luce. | Forgia (✨450) |
| **Ascia del Minotauro** | 26 | Casuale | Un'arma mostruosa a doppia lama. | Forgia (✨800) |
| **Balestra Gnomica a Ripetizione** | 19 | Casuale | Ingegneria avanzata, scocca raffiche di dardi. Dardi avvelenati: 30% di infliggere Veleno. | Forgia (✨550) |
| **Tridente Oceanico** | 21 | 💧 Acqua | Arma letale associata alle maree. 20% di infliggere Veleno. Sempre di elemento Acqua. | Forgia (✨600) |

</details>

<details>
<summary>🛡️ Le 10 armature</summary>

| Armatura | DEF base | Caratteristiche | Come ottenerla |
|---|---|---|---|
| **Tunica del Viaggiatore** | 1 | — | Disponibile da subito |
| **Corazza di Cuoio** | 2 | — | Disponibile da subito |
| **Cotta di Maglia** | 4 | — | Disponibile da subito |
| **Corazza a Piastre** | 6 | — | Disponibile da subito |
| **Armatura Pesante Nanesca** | 8 | — | Disponibile da subito |
| **Armatura in Mithril** | 10 | — | Disponibile da subito |
| **Corazza di Scaglie di Drago** | 14 | — | Disponibile da subito |
| **Mantello Riflettente** | 9 | Leggera ma resistente: difesa vicina a quella del Mithril. | Forgia (✨300) |
| **Egida del Titano** | 20 | Un muro impenetrabile. | Forgia (✨600) |
| **Veste Eterea** | 0 | Difesa zero, ma +20% Schivata finché la indossi. | Impresa «Cannone di Vetro» |

</details>

<details>
<summary>💍 I 16 monili</summary>

| Monile | Effetto | Come ottenerlo |
|---|---|---|
| **Anello del Berserker** | +15% probabilità di infliggere colpo critico | Disponibile da subito |
| **Amuleto del Vampiro** | Assorbi 2 HP per ogni colpo a segno | Disponibile da subito |
| **Cintura di Ferro** | +15 HP Massimi | Disponibile da subito |
| **Collana del Vento** | +10% Schivata | Disponibile da subito |
| **Occhio del Cacciatore** | +15% Precisione | Disponibile da subito |
| **Spallacci a Spilli** | Rifletti 3 danni ogni volta che vieni colpito | Disponibile da subito |
| **Orecchino della Lince** | +10% Precisione | Disponibile da subito |
| **Bracciale del Titano** | +25 HP Massimi | Forgia (✨300) |
| **Anello del Re dei Ghiacci** | +12% Schivata | Disponibile da subito |
| **Amuleto Sanguisuga** | Assorbi 3 HP per ogni colpo a segno | Forgia (✨500) |
| **Veste di Piume Iridescenti** | +18% Schivata | Forgia (✨400) |
| **Anello del Ritorsore** | Rifletti 5 danni ogni volta che vieni colpito | Forgia (✨350) |
| **Corona di Spine** | Rifletti 8 danni ogni volta che vieni colpito | Forgia (✨600) |
| **Occhio di Falco Assoluto** | +25% Precisione | Forgia (✨300) |
| **Cuore di Pietra** | +35 HP Massimi | Forgia (✨450) |
| **Dente di Drago Antico** | +20% probabilità di infliggere colpo critico | Forgia (✨500) |

</details>

<details>
<summary>🧪 I 14 consumabili</summary>

| Consumabile | Effetto | Come ottenerlo |
|---|---|---|
| **Fiala di Sangue** | Cura 15 HP (di più ai piani profondi) | Disponibile da subito |
| **Pozione Minore** | Cura 25 HP (di più ai piani profondi) | Disponibile da subito |
| **Decotto alle Erbe** | Cura 35 HP (di più ai piani profondi) | Disponibile da subito |
| **Pozione Curativa** | Cura 50 HP (di più ai piani profondi) | Disponibile da subito |
| **Elisir Maggiore** | Cura 80 HP (di più ai piani profondi) | Disponibile da subito |
| **Lacrima di Fenice** | Cura 150 HP (di più ai piani profondi) | Disponibile da subito |
| **Elisir degli Dei** | Cura quasi completamente qualsiasi eroe. | Forgia (✨200) |
| **Pietra per Affilare** | Aumenta +5 ATK all'arma attuale in modo permanente. | Maestria Guerriero Lv.3 |
| **Bomba Fumogena** | Ti permette di fuggire all'istante da un combattimento (non funziona contro i Boss). | Maestria Ladro Lv.3 |
| **Tomo del Caos** | Cambia casualmente l'elemento dell'arma che impugni. | Maestria Mago Lv.3 |
| **Filtro Preciso** | Conferisce Precisione totale per questo combattimento. | Impresa «Tiratore Scelto» |
| **Acqua Santa** | Purifica tutte le Maledizioni sull'equipaggiamento indossato. | Maestria Paladino Lv.3 |
| **Fiala del Caos** | Effetto casuale su di te (cura totale, ustione non letale, oro, +10 HP Max o nuovo elemento all'arma). In combattimento esplode anche, infliggendo 10-100 danni puri al nemico. | Maestria Alchimista Lv.3 |
| **Antidoto Universale** | Cura tutti gli stati alterati (Veleno, Sanguinamento). | Disponibile da subito |

</details>

<details>
<summary>🏆 Le 14 imprese</summary>

| Impresa | Obiettivo | Ricompensa |
|---|---|---|
| **L'Ombra** | Scappa da 10 combattimenti in una singola run. | Potenziamento: Scarpisti (+20% Fuga) |
| **Fabbro Folle** | Fondi 3 oggetti all'Altare dell'Evoluzione in una run. | Sblocco: Spadone Infranto |
| **Cannone di Vetro** | Sconfiggi un Boss senza subire alcun danno. | Sblocco: Veste Eterea |
| **Danza con la Morte** | Sconfiggi un nemico avendo esattamente 1 HP rimanente. | Classe: Berserker |
| **L'Avaro** | Esci dal labirinto con almeno 2000 Oro non speso. | Tratto: Aristocratico |
| **Genio Elementale** | Fondi un'arma fino al Livello 5. | Classe: Alchimista |
| **Il Sopravvissuto** | Supera il Piano 10 senza MAI usare il riposo al Falò. | Sblocco: Cuore di Drago |
| **Epuratore di Demoni** | Sconfiggi 10 Boss in totale. | Tratto: Cacciatore Etereo |
| **Mani Bucate** | Spendi almeno 2000 Oro dal Mercante in una singola run. | Sblocco: Zweihander d'Oro |
| **Equilibrista** | Finisci una run con Arma e Armatura di elementi diversi. | Sblocco: Sigillo Elementale |
| **Lama di Cristallo** | Arriva al piano 15 senza mai cambiare l'arma iniziale. | Sblocco: Spirito della Spada |
| **Furia Cieca** | Supera un piano mancando più della metà dei tuoi attacchi (almeno 6 attacchi). | Tratto: Titano |
| **Tiratore Scelto** | Infliggi 5 colpi Super Efficaci ai Boss in una singola run. | Sblocco: Filtro Preciso |
| **Assaggiatore di Veleni** | Sopravvivi a un danno letale rimanendo a 1 HP (es. Benedizione o Fiala del Caos). | Sblocco: Maschera Antigas |

</details>

<details>
<summary>🎭 Gli eventi narrativi</summary>

46 storie e 58 scene: *La Fontana Fatata*, *Il Mendicante Ombra*, *Altare del Sangue*, *La Forgia Abissale*, *La Bisca dei Goblin*, *Il Cavaliere Caduto*, *L'Idolo Corrotto*, *Lo Specchio della Verità*, *L'Oasi Sotterranea*, *Il Cadavere del Saggio*, *La Porta Sigillata*, *Lo Speziale Prigioniero*, *Il Maestro d'Armi Prigioniero*, *L'Armaiola Imprigionata*, *L'Incantatore Intrappolato*, *Il Viandante Cieco*, *Il Buio Vivente*, *La Cartografa Perduta*, *La Sala dei Cento Corridoi*, *Il Pozzo dei Desideri*, *Il Banchetto dei Morti*, *La Bilancia di Aethelgard*, *La Voce nel Buio*, *La Voce del Labirinto*, *Il Giardino Sepolto*, *Il Cavaliere alla Porta*, *Il Cavaliere Stanco*, *L'Ultimo Sigillo*, *Il Cercatore*, *Il Diario Strappato*, *La Soglia*, *La Prima Pietra*… e qualcuno che torna a cercarti più in basso.

Ogni scelta mostra i suoi effetti reali, molte opzioni esistono solo per certe classi, tratti o reliquie, gli *oggetti chiave* di un evento aprono strade segrete in un altro e il Labirinto ricorda le tue decisioni da una run all'altra. Quattro eventi nascondono gli artigiani prigionieri.

</details>

## 📊 In numeri

| Contenuto | Quantità |
|---|---|
| Classi giocabili | 8 |
| Tratti di partenza | 7 |
| Patti del Caos | 5 |
| Armi | 24 (8 subito, 16 da sbloccare) |
| Armature | 10 (7 subito, 3 da sbloccare) |
| Monili | 16 (8 subito, 8 da sbloccare) |
| Consumabili | 14 (7 subito, 7 da sbloccare) |
| Reliquie | 30 (14 subito, 16 da sbloccare) |
| Nemici comuni | 37 |
| Boss | 21 |
| Eventi narrativi | 46 |
| Imprese | 14 |
| Tomi dell'Archivio | 3 |
| Potenziamenti permanenti | 14 |
| Elementi / Risonanze | 7 / 6 |
| Combinazioni di partenza (modalità × classe × tratto × patti) | 3584 |

## 🛠️ Per chi sviluppa

Il gioco è **data-driven**: classi, nemici, oggetti, reliquie, eventi, Maestrie, Risonanze e bonus dell'Archivio stanno in `data/*.json` e si bilanciano senza toccare il codice. Usa solo la libreria standard di Python.

```text
rogue/
├── roguelike.py       # Menu principale, Campo Base, scelta dell'eroe, ciclo dei piani, fine partita
├── floor_map.py       # Mappa del piano: file di stanze, percorsi, biomi, disegno
├── rooms.py           # Combattimento (CombatSession) e stanze: mercante, falò, forziere, trappola, mistero
├── events.py          # Motore degli eventi: scene, condizioni, effetti, memoria fra le run
├── entities.py        # Eroe, nemici e oggetti; generazione dell'equipaggiamento
├── relic_effects.py   # Effetti delle reliquie come hook (on_attack, on_take_damage, ...)
├── inventory_menu.py  # Zaino, consumabili e schermata delle statistiche
├── archive.py         # Archivio di Aethelgard e relativi bonus
├── camp.py            # Il Fuoco del Campo: personaggi e strutture
├── endings.py         # I finali multipli
├── codex.py           # Il Codice del Labirinto: ciò che hai scoperto fra le run
├── data_manager.py    # Caricamento dei dati e salvataggio del profilo
├── ui.py              # Terminale: colori, menu a frecce, output centralizzato
├── constants.py       # Costanti di bilanciamento
├── data/              # Tutti i contenuti del gioco in JSON
└── tests/             # Test automatici (unittest)
```

```bash
python -m unittest discover -s tests   # esegue i test, gli stessi della CI
```

I **test di contratto** (`tests/test_contracts.py`) verificano che ogni reliquia, monile, arma, armatura, consumabile, evento, tratto, patto, potenziamento, Maestria e impresa faccia esattamente ciò che dice la sua descrizione: un contenuto nuovo senza il suo contratto fa fallire i test.

- 📖 [**Manuale del Giocatore**](MANUALE_GIOCATORE.md) — strategie e regole in dettaglio.
- 🔧 [**Documentazione Tecnica**](DOCUMENTAZIONE_TECNICA.md) — architettura, formato dei dati, formule e come aggiungere contenuti.
- 📜 [**La Storia**](STORY.md) — il mondo di Aethelgard.
- 🤖 [**AGENTS.md**](AGENTS.md) — regole per contribuire (anche con assistenti IA): branch e pull request, test, niente dipendenze esterne.

## 📝 Roadmap

- [x] Classi **Assassino** e **Negromante**
- [x] Nemici e boss legati alla profondità
- [x] Impostazioni (velocità del testo)
- [ ] Sistema di Rune/Incastoni per armi e armature
- [x] Nemici che annunciano la mossa e reazioni elementali
- [ ] Boss con meccaniche speciali (fasi, immunità)
- [x] Eventi a scene, opzioni per classe e tratto, memoria fra le run
- [x] Personaggi ricorrenti (Sir Alaric, Silas) e il Codice del Labirinto
- [x] Mappa dei piani e primo bioma (I Chiostri del Rimpianto)
- [x] Regole per tutti e sei i biomi
- [x] Hub fra le run, finali multipli e Corruzione

---

<div align="center"><i>Sviluppato con ❤️ e Python. Buona discesa.</i></div>
