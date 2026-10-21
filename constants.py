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
WEAPON_LEVEL_SCALING = 1.5
ARMOR_LEVEL_SCALING = 1.2
CURSE_CHANCE = 0.15
CURSE_STAT_MULTIPLIER = 1.4

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
