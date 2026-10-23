import random
from ui import Colors, display_msg

class RelicEffect:
    def __init__(self, relic_id=""):
        self.relic_id = relic_id

    def on_equip(self, player):
        pass

    def on_unequip(self, player):
        pass

    def on_combat_start(self, session):
        pass

    def on_before_attack(self, session) -> bool:
        # Return True to continue attack, False to cancel (e.g. death from recoil)
        return True

    def on_attack(self, session, dmg_dealt, multiplier, eff_text) -> tuple[int, str]:
        return dmg_dealt, eff_text

    def on_attack_landed(self, session, multiplier):
        pass

    def on_take_damage(self, session, dmg_taken, en_multiplier) -> int:
        return dmg_taken

    def on_enemy_death(self, session):
        pass

    def on_gold_gain(self, player, amount) -> int:
        return amount

    def on_heal(self, player, amount) -> int:
        return amount

    def on_item_heal(self, player, amount) -> int:
        """Cure dei consumabili (pozioni, antidoto): solo queste, non rubavita, livelli o falò."""
        return amount

    def get_atk_modifier(self, player) -> int:
        return 0

    def get_def_modifier(self, session) -> int:
        return 0

    def on_item_use(self, player, item) -> bool:
        # Return True to consume item, False to not consume it
        return True

    def get_dodge_modifier(self) -> int:
        return 0

    def get_acc_modifier(self) -> int:
        return 0

    def get_exp_modifier(self) -> float:
        return 0.0

    def get_escape_modifier(self) -> int:
        return 0

    def modify_multiplier(self, multiplier: float, is_defense: bool = False) -> float:
        return multiplier

    def modify_trap_damage(self, amount: int) -> int:
        return amount

    def modify_room_weights(self, weights: dict):
        pass

    def get_rune_bonus(self, key: str) -> int:
        """Un bonus con le stesse chiavi degli effetti delle rune (runes.RUNE_EFFECT_KEYS)."""
        return 0

    def get_rune_multiplier(self) -> float:
        """Quanto valgono in più le rune incastonate (0.5 = +50%)."""
        return 0.0

    def modify_enemy_status_damage(self, status: str, dmg: int) -> int:
        """Danni di veleno, sanguinamento e magma sul nemico."""
        return dmg

    def on_reaction(self, session, key: str):
        pass

    def get_audacity_bonus(self) -> int:
        """Punti di Audacia in più per ogni stanza rischiosa."""
        return 0

    # Regole che altri sistemi leggono dalla presenza della reliquia
    free_rune_extraction = False
    rune_drop_always = ()

# --- IMPLEMENTAZIONI ---

class ArtiglioVampiro(RelicEffect):
    def on_attack_landed(self, session, multiplier):
        session.player.heal(5)
        display_msg(f"{Colors.RED}Artiglio Vampirico ti cura 5 HP!{Colors.RESET}")

class LentePrismatica(RelicEffect):
    # Vantaggi e svantaggi raddoppiati: Super Efficace x2 invece di x1,5, Poco efficace x0,25 invece di x0,5
    def modify_multiplier(self, multiplier: float, is_defense: bool = False) -> float:
        if multiplier > 1.0: return 2.0
        elif multiplier < 1.0: return 0.25
        return multiplier

class ScudoCristallo(RelicEffect):
    def __init__(self):
        super().__init__("scudo_cristallo")
        self.active = True
    def on_combat_start(self, session):
        self.active = True
    def on_take_damage(self, session, dmg_taken, en_multiplier):
        if self.active and dmg_taken > 0:
            display_msg(f"{Colors.CYAN}<- {session.enemy.name} ti colpisce... Ma lo Scudo di Cristallo assorbe il danno!{Colors.RESET}")
            self.active = False
            return 0
        return dmg_taken

class TascaDorata(RelicEffect):
    def on_gold_gain(self, player, amount):
        return int(amount * 1.25)

class IdoloGuerra(RelicEffect):
    def on_equip(self, player):
        player.bonus_atk_relic += 5
    def on_unequip(self, player):
        player.bonus_atk_relic -= 5

class CaliceAlchimista(RelicEffect):
    def on_item_heal(self, player, amount):
        return int(amount * 1.5)

class MantelloNebbioso(RelicEffect):
    def get_dodge_modifier(self): return 15

class BussolaPerfetta(RelicEffect):
    def get_escape_modifier(self): return 100

class OcchioCacciatore(RelicEffect):
    def get_acc_modifier(self): return 20

class CuoreTroll(RelicEffect):
    def on_enemy_death(self, session):
        session.player.max_hp += 2
        session.player.heal(2)
        display_msg(f"{Colors.GREEN}Il Cuore di Troll pulsa: +2 HP Massimi!{Colors.RESET}")

class TomoConoscenza(RelicEffect):
    def get_exp_modifier(self): return 0.3

class IdoloAvidita(RelicEffect):
    def on_gold_gain(self, player, amount):
        return amount * 2
    def get_dodge_modifier(self):
        return -999 # Forces dodge to 0

class LamaSangue(RelicEffect):
    def on_equip(self, player):
        player.bonus_atk_relic += 10
    def on_unequip(self, player):
        player.bonus_atk_relic -= 10
    def on_before_attack(self, session):
        display_msg(f"{Colors.RED}La Lama di Sangue si nutre di te! Subisci 3 danni.{Colors.RESET}")
        if not session.player.take_damage(3):
            display_msg(f"\n{Colors.RED}{Colors.BOLD}Sei stato consumato dalla tua stessa arma...{Colors.RESET}")
            # Rimuoviamo input, la gestione morte è nel main loop
            return False
        return True

class CoronaReFolle(RelicEffect):
    def on_attack(self, session, dmg_dealt, multiplier, eff_text):
        if multiplier > 1.0 or "[CRITICO!]" in eff_text:
            dmg_dealt = int(dmg_dealt * 1.5)
            eff_text += f" {Colors.MAGENTA}[CORONA DEL FOLLE!]{Colors.RESET}"
        return dmg_dealt, eff_text

class AnelloVampiroMax(RelicEffect):
    def on_attack_landed(self, session, multiplier):
        session.player.heal(2)
        display_msg(f"{Colors.RED}L'Anello Vampirico assorbe 2 HP!{Colors.RESET}")

class ClessidraDestino(RelicEffect):
    def on_combat_start(self, session):
        session.enemy.base_dodge = max(0, session.enemy.base_dodge - 20)

class ArmaturaSpilli(RelicEffect):
    def on_take_damage(self, session, dmg_taken, en_multiplier):
        if dmg_taken > 0:
            session.enemy.hp -= 3
            display_msg(f"{Colors.YELLOW}Riflessi 3 danni a {session.enemy.name}!{Colors.RESET}")
        return dmg_taken

class PergamenaOro(RelicEffect):
    def on_gold_gain(self, player, amount):
        player.heal(2)
        display_msg(f"{Colors.GREEN}La Pergamena d'Oro ti guarisce di 2 HP!{Colors.RESET}")
        return amount

class CampanellaSpiriti(RelicEffect):
    def on_take_damage(self, session, dmg_taken, en_multiplier):
        if random.random() < 0.15:
            display_msg(f"{Colors.CYAN}La Campanella degli Spiriti rintocca... L'attacco ti passa attraverso!{Colors.RESET}")
            return 0
        return dmg_taken

class PietraLuna(RelicEffect):
    def get_def_modifier(self, session) -> int:
        # +50% della Difesa dell'armatura mentre ti difendi
        return int(session.player.armor.defense * 0.5) if session.is_defending else 0

class ContrattoDemoniaco(RelicEffect):
    def on_attack(self, session, dmg_dealt, multiplier, eff_text):
        return dmg_dealt * 2, eff_text
    def on_enemy_death(self, session):
        # Il tributo non può uccidere: lascia almeno 1 HP
        tribute = min(5, session.player.hp - 1)
        if tribute > 0:
            session.player.hp -= tribute
            display_msg(f"{Colors.RED}Il Contratto Demoniaco esige un tributo di sangue ({tribute} HP)...{Colors.RESET}")

class PozioneInfinita(RelicEffect):
    def on_item_use(self, player, item):
        if getattr(item, "category", "") == "heal":
            if random.random() < 0.25:
                display_msg(f"{Colors.CYAN}Pozione Senza Fondo: La fiala si riempie di nuovo!{Colors.RESET}")
                return False
        return True

class CuoreDrago(RelicEffect):
    def on_equip(self, player):
        # Gli HP arrivano insieme al massimo: non è una cura, quindi vale anche con il Patto del Sangue
        player.max_hp += 50
        player.hp = min(player.max_hp, player.hp + 50)
    def on_unequip(self, player):
        player.max_hp -= 50
        player.hp = min(player.hp, player.max_hp)

class SpiritoSpada(RelicEffect):
    # Segue l'arma impugnata: vale finché è di livello 1
    def get_atk_modifier(self, player):
        return 15 if player.weapon.level == 1 else 0

class TeschioSangue(RelicEffect):
    def on_enemy_death(self, session):
        session.player.max_hp += 1
        session.player.heal(1)
        display_msg(f"{Colors.RED}Il Teschio di Sangue si nutre della morte: +1 HP Massimo!{Colors.RESET}")

class PietraFilosofale(RelicEffect):
    def on_enemy_death(self, session):
        if random.random() < 0.20:
            session.player.gold += session.enemy.exp_drop
            display_msg(f"{Colors.YELLOW}La Pietra Filosofale trasforma l'XP in {session.enemy.exp_drop} Oro!{Colors.RESET}")
            session.enemy.exp_drop = 0

class BussolaDimensionale(RelicEffect):
    def modify_room_weights(self, weights: dict):
        if "treasure" in weights: weights["treasure"] += 15.0
        if "mystery" in weights: weights["mystery"] += 15.0

class SpallacciRovo(RelicEffect):
    def on_take_damage(self, session, dmg_taken, en_multiplier):
        if dmg_taken > 0:
            session.enemy.hp -= 5
            display_msg(f"{Colors.YELLOW}Gli Spallacci di Rovo trafiggono {session.enemy.name} per 5 Danni Puri!{Colors.RESET}")
        return dmg_taken

class SigilloElementale(RelicEffect):
    def modify_multiplier(self, multiplier: float, is_defense: bool = False) -> float:
        if is_defense and multiplier > 1.0:
            return 1.0
        return multiplier

class MascheraAntigas(RelicEffect):
    def modify_trap_damage(self, amount: int) -> int:
        display_msg(f"{Colors.CYAN}La Maschera Antigas filtra le tossine e disinnesca il pericolo! Danno annullato.{Colors.RESET}")
        return 0


class AgoUntore(RelicEffect):
    def modify_enemy_status_damage(self, status, dmg):
        return dmg * 2 if status in ("poison", "bleed") else dmg

class FialaCremisi(RelicEffect):
    def on_attack_landed(self, session, multiplier):
        if session.enemy.hp > 0 and random.randint(1, 100) <= 20:
            session.enemy.statuses["bleed"] = max(session.enemy.statuses.get("bleed", 0), 2)
            display_msg(f"{Colors.RED}Fiala Cremisi: {session.enemy.name} sanguina!{Colors.RESET}")

class SporaNera(RelicEffect):
    def on_combat_start(self, session):
        session.enemy.statuses["poison"] = max(session.enemy.statuses.get("poison", 0), 3)

class BilanciaMercante(RelicEffect):
    def get_atk_modifier(self, player) -> int:
        return min(10, max(0, player.gold) // 100)

class MonetaTraghettatore(RelicEffect):
    def on_enemy_death(self, session):
        if session.enemy.is_boss and not session.player.aristocrat:
            session.player.gold += 100
            display_msg(f"{Colors.YELLOW}Moneta del Traghettatore: +100 Oro.{Colors.RESET}")

class DenteOro(RelicEffect):
    def on_gold_gain(self, player, amount):
        return amount * 115 // 100
    def get_exp_modifier(self) -> float:
        return 0.05

class RuneBonus(RelicEffect):
    """Reliquie che danno un effetto con le stesse chiavi delle rune."""
    BONUS = {}
    def get_rune_bonus(self, key):
        return self.BONUS.get(key, 0)

class Catalizzatore(RuneBonus):
    BONUS = {"reaction_dmg_pct": 50}

class CristalloMarea(RelicEffect):
    def on_reaction(self, session, key):
        healed = session.player.heal(max(1, session.player.max_hp * 5 // 100))
        if healed: display_msg(f"{Colors.CYAN}Cristallo di Marea: +{healed} HP.{Colors.RESET}")

class SpecchioElementi(RuneBonus):
    BONUS = {"mark_duration_add": 2}

class PiastraCustode(RuneBonus):
    BONUS = {"def_pct": 10}

class CornoBastione(RelicEffect):
    def on_take_damage(self, session, dmg_taken, en_multiplier):
        return dmg_taken // 2 if session.is_defending else dmg_taken

class RovoAntico(RuneBonus):
    BONUS = {"thorns_pct": 20}

class AmuletoQuiete(RuneBonus):
    BONUS = {"defend_heal_pct": 5}

class CristalloRunico(RelicEffect):
    def get_rune_multiplier(self):
        return 0.5

class MartelloLapicida(RelicEffect):
    free_rune_extraction = True

class PietraParlante(RelicEffect):
    rune_drop_always = ("elite",)

class MarchioCacciatore(RelicEffect):
    def on_attack(self, session, dmg_dealt, multiplier, eff_text):
        if session.enemy.modifier == "elite" or getattr(session.enemy, "nemesis", None):
            return int(dmg_dealt * 1.3), eff_text + f" {Colors.RED}[PREDA]{Colors.RESET}"
        return dmg_dealt, eff_text

class StendardoAudacia(RelicEffect):
    def get_audacity_bonus(self):
        return 1

class TeschioRivale(RelicEffect):
    def on_enemy_death(self, session):
        if getattr(session.enemy, "nemesis", None):
            session.player.max_hp += 20; session.player.hp += 20
            display_msg(f"{Colors.MAGENTA}Teschio del Rivale: +20 HP massimi.{Colors.RESET}")

class LanternaCartografo(RelicEffect):
    def modify_room_weights(self, weights: dict):
        if "event" in weights: weights["event"] += 10.0
        if "mystery" in weights: weights["mystery"] += 10.0

RELIC_REGISTRY = {
    "artiglio_vampiro": ArtiglioVampiro,
    "lente_prismatica": LentePrismatica,
    "scudo_cristallo": ScudoCristallo,
    "tasca_dorata": TascaDorata,
    "idolo_guerra": IdoloGuerra,
    "calice_alchimista": CaliceAlchimista,
    "mantello_nebbioso": MantelloNebbioso,
    "bussola_perfetta": BussolaPerfetta,
    "occhio_cacciatore": OcchioCacciatore,
    "cuore_troll": CuoreTroll,
    "tomo_conoscenza": TomoConoscenza,
    "idolo_avidita": IdoloAvidita,
    "lama_sangue": LamaSangue,
    "corona_re_folle": CoronaReFolle,
    "anello_vampiro_max": AnelloVampiroMax,
    "clessidra_destino": ClessidraDestino,
    "armatura_spilli": ArmaturaSpilli,
    "pergamena_oro": PergamenaOro,
    "campanella_spiriti": CampanellaSpiriti,
    "pietra_luna": PietraLuna,
    "contratto_demoniaco": ContrattoDemoniaco,
    "pozione_infinita": PozioneInfinita,
    "cuore_drago": CuoreDrago,
    "spirito_spada": SpiritoSpada,
    "teschio_sangue": TeschioSangue,
    "pietra_filosofale": PietraFilosofale,
    "bussola_dimensionale": BussolaDimensionale,
    "spallacci_rovo": SpallacciRovo,
    "sigillo_elementale": SigilloElementale,
    "maschera_antigas": MascheraAntigas,
    "ago_untore": AgoUntore, "fiala_cremisi": FialaCremisi, "spora_nera": SporaNera,
    "bilancia_mercante": BilanciaMercante, "moneta_traghettatore": MonetaTraghettatore, "dente_oro": DenteOro,
    "catalizzatore": Catalizzatore, "cristallo_marea": CristalloMarea, "specchio_elementi": SpecchioElementi,
    "piastra_custode": PiastraCustode, "corno_bastione": CornoBastione, "rovo_antico": RovoAntico, "amuleto_quiete": AmuletoQuiete,
    "cristallo_runico": CristalloRunico, "martello_lapicida": MartelloLapicida, "pietra_parlante": PietraParlante,
    "marchio_cacciatore": MarchioCacciatore, "stendardo_audacia": StendardoAudacia, "teschio_rivale": TeschioRivale,
    "lanterna_cartografo": LanternaCartografo,
}

def create_relic_effect(relic_id: str) -> RelicEffect:
    if relic_id in RELIC_REGISTRY:
        effect = RELIC_REGISTRY[relic_id]()
        effect.relic_id = relic_id
        return effect
    return RelicEffect(relic_id)
