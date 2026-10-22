# constants.py
# Raccolta delle costanti (magic numbers) per bilanciamento e configurazione

# --- RISORSE E RICOMPENSE ---
RATIO_GOLD_TO_ESSENCE_ON_DEATH = 0.20
BOSS_ESSENCE_BONUS = 50
XP_PER_FLOOR = 10
XP_PER_BOSS = 50

# --- POTENZIAMENTI PERMANENTI ---
SPERANZA_LUCE_PCT_PER_LVL = 0.05  # HP Max recuperati a ogni piano, per livello

# --- PROGRESSIONE E INFINITY MODE ---
INFINITE_MODE_THRESHOLD = 30
INFINITE_MODE_ESSENCE_MULTIPLIER = 1.5

# --- GENERAZIONE EQUIPAGGIAMENTO ---
# Gli oggetti crescono con i nemici del loro livello (entities.typical_enemy): un'arma tipica abbatte un nemico
# normale in WEAPON_TARGET_HITS colpi, un'armatura tipica assorbe ARMOR_TARGET_ABSORB del suo colpo.
# La statistica base dei dati è la qualità dell'oggetto: moltiplica la forza tipica invece di sommarsi.
WEAPON_TARGET_HITS = 3.0
ARMOR_TARGET_ABSORB = 0.4
WEAPON_QUALITY = (0.75, 60)  # qualità = 0.75 + base_atk / 60  (Spada Corta 0,80 … Lama del Creatore 1,25)
ARMOR_QUALITY = (0.6, 25)    # qualità = 0.6 + base_def / 25   (Veste Eterea 0,60 … Egida del Titano 1,40)
NORMAL_ELEMENT_BONUS = 1.1   # gli oggetti senza elemento compensano con statistiche un po' più alte
EPIC_MULTIPLIER = 1.35
CURSE_CHANCE = 0.15
CURSE_STAT_MULTIPLIER = 1.3

# --- DANNI E MALEDIZIONI ---
MIN_DAMAGE_PCT = 20       # un colpo a segno fa sempre almeno questa parte del danno grezzo, qualunque sia la difesa
CURSE_HP_DRAIN_PCT = 2    # la maledizione che drena vita toglie questa % degli HP massimi a ogni turno (minimo 2)
RECOVERY_HEAL_PCT = 10    # Riparo Magico: la difesa di Mago, Paladino, Alchimista e Negromante cura questa % degli HP massimi
BULWARK_HEAL_PCT = 5      # Baluardo della Fede (Paladino, Maestria Lv.2): cura extra in difesa, in % degli HP massimi
POISON_PCT, POISON_MIN = 4, 3  # il veleno toglie il 4% degli HP massimi a ogni turno, almeno 3 (come il sanguinamento, scala con la vittima)

# --- CRESCITA DEI NEMICI PER PIANO ---
ENEMY_HP_PER_FLOOR = 5
ENEMY_ATK_PER_FLOOR = 1.2
# I boss sono un multiplo del nemico tipico del loro piano (entities.typical_enemy); i valori base dei dati
# diventano la loro qualità: qualità = 0.75 + 0.25 · base / media dei boss
BOSS_HP_MULT = 2.2
BOSS_ATK_MULT = 1.8

# --- SELEZIONE NEMICI PER PROFONDITÀ ---
# Quanti nemici/boss (ordinati per forza) possono uscire a una data profondità
ENEMY_DEPTH_WINDOW = 6
BOSS_DEPTH_WINDOW = 5

# --- COMBATTIMENTO ---
BASE_HIT_CHANCE = 85

# --- IMPOSTAZIONI ---
# Moltiplicatore applicato ai ritardi di delay_print (0 = testo istantaneo)
TEXT_SPEEDS = {"lenta": 1.5, "normale": 1.0, "veloce": 0.3, "istantanea": 0.0}
DEFAULT_TEXT_SPEED = "normale"

# --- IMPRESE ---
BLIND_FURY_MIN_ATTACKS = 6

# --- EVENTI ---
BLOOD_LETTER_CHANCE = 0.15
