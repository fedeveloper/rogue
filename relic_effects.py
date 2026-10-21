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

    def on_item_use(self, player, item_name) -> bool:
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

# --- IMPLEMENTAZIONI ---

class ArtiglioVampiro(RelicEffect):
    def on_attack_landed(self, session, multiplier):
        session.player.heal(5)
        display_msg(f"{Colors.RED}Artiglio Vampirico ti cura 5 HP!{Colors.RESET}")

class LentePrismatica(RelicEffect):
    def modify_multiplier(self, multiplier: float, is_defense: bool = False) -> float:
        if multiplier > 1.0: return 2.0
        elif multiplier < 1.0: return 0.5
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
    def on_heal(self, player, amount):
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
    def on_take_damage(self, session, dmg_taken, en_multiplier):
        if session.is_defending:
            bonus_def = int(session.player.armor.defense * 0.5)
            dmg_taken = max(0, dmg_taken - (bonus_def // 2))
        return dmg_taken

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
    def on_item_use(self, player, item_name):
        if "Pozione" in item_name or "Fiala" in item_name:
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
    def __init__(self):
        super().__init__("spirito_spada")
        self.applied = False
    def on_equip(self, player):
        if player.weapon.level == 1:
            player.bonus_atk_relic += 15
            self.applied = True
    def on_unequip(self, player):
        if self.applied:
            player.bonus_atk_relic -= 15
            self.applied = False

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
    "maschera_antigas": MascheraAntigas
}

def create_relic_effect(relic_id: str) -> RelicEffect:
    if relic_id in RELIC_REGISTRY:
        effect = RELIC_REGISTRY[relic_id]()
        effect.relic_id = relic_id
        return effect
    return RelicEffect(relic_id)
