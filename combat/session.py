"""Lo scontro: stato della sessione, inizio, ciclo dei turni, status e maledizioni, Risonanza, fine e vittoria."""
import random

import effects
import nemesis
from ui import Colors, delay_print, display_msg, wait_enter
from data_manager import GAME_DATA, get_biome, get_element_icon
from codex import record_enemy_killed, record_enemy_seen, record_letter
from constants import NECRO_HARVEST_PCT, BLOOD_LETTER_CHANCE, CURSE_HP_DRAIN_PCT, POISON_MIN, POISON_PCT
from entities import STATUS_NAMES, Player, Enemy, generate_weapon, generate_armor, generate_potion, get_random_relic, set_sockets
from epitaph import note
from combat.rules import CONTROL_STATUSES
from combat.rewards import audacity_reward, rune_drop
from combat.actions import PlayerActions
from combat.enemy import EnemyActions
from combat.phases import Phases
from combat.reactions import Reactions
from combat.spells import Spells


class CombatSession(PlayerActions, Spells, Reactions, Phases, EnemyActions):
    def __init__(self, player: Player, floor: int, enemy: Enemy):
        self.player = player
        self.floor = floor
        self.enemy = enemy
        self.boss_hit_taken = False
        self.spell_def = 0       # Pelle di Pietra: Difesa in più per il resto dello scontro
        self.weakened = False    # Maledizione: si lancia una volta sola per nemico
        self.focused_attack = False
        self.resonance = player._get_resonance_element()
        self.burn_dmg = 0
        self.is_defending = False
        self.def_type = ""
        self.def_txt = ""
        self.first_enemy_attack = True
        self.hit_negated_by_relic = False
        self.first_player_attack = True
        self.intent = None  # la mossa che il nemico ha annunciato per il suo prossimo turno
        self.sealed = False  # Sigillo: al prossimo turno l'eroe non può difendersi
        self.mute_turns = 0  # Silenzio: per quanti turni dell'eroe gli incantesimi restano muti
        # Le regole di combattimento del bioma (Gas del Silenzio, Ebollizione Astrale, Paradosso Temporale)
        self.biome = get_biome(floor)
        self.rules = (self.biome or {}).get("rules", {})
        silence = self.rules.get("silence")
        self.silenced = bool(silence) and random.random() * 100 < silence["chance"]

        for r in self.player.relic_effects:
            r.on_combat_start(self)

    def process_statuses_and_curses(self, is_player_turn: bool):
        if is_player_turn:
            if self.player.has_curse("hp_drain"):
                drain = max(2, self.player.max_hp * CURSE_HP_DRAIN_PCT // 100)
                self.player.take_damage(drain)
                display_msg(f"{Colors.MAGENTA}La Maledizione dell'equipaggiamento drena {drain} HP! ({self.player.hp}/{self.player.max_hp}){Colors.RESET}")
            if self.player.has_curse("gold_drain") and self.player.gold > 0:
                self.player.gold = max(0, self.player.gold - 5)
                display_msg(f"{Colors.MAGENTA}La Maledizione divora 5 Oro! (Oro: {self.player.gold}){Colors.RESET}")
                
            expired = []
            for status, duration in self.player.statuses.items():
                if status == "poison":
                    dmg = max(POISON_MIN, self.player.max_hp * POISON_PCT // 100)
                    self.player.take_damage(dmg)
                    display_msg(f"{Colors.GREEN}Il veleno ti infligge {dmg} danni! ({self.player.hp}/{self.player.max_hp}){Colors.RESET}")
                elif status == "bleed":
                    dmg = max(1, int(self.player.max_hp * 0.05))
                    self.player.take_damage(dmg)
                    display_msg(f"{Colors.RED}Il sanguinamento ti infligge {dmg} danni! ({self.player.hp}/{self.player.max_hp}){Colors.RESET}")
                
                self.player.statuses[status] -= 1
                if self.player.statuses[status] <= 0: expired.append(status)
            for e in expired:
                del self.player.statuses[e]
                display_msg(f"{Colors.CYAN}L'effetto di {STATUS_NAMES.get(e, e)} è svanito dal tuo corpo.{Colors.RESET}")
        else:
            expired = []
            for status, duration in self.enemy.statuses.items():
                if status == "poison":
                    dmg = self._enemy_status_damage(status, max(POISON_MIN, self.enemy.max_hp * POISON_PCT // 100))
                    self.enemy.hp -= dmg
                    display_msg(f"{Colors.GREEN}Il veleno infligge {dmg} danni a {self.enemy.name}! ({self.enemy.hp}){Colors.RESET}")
                elif status == "bleed":
                    dmg = self._enemy_status_damage(status, max(5, int(self.enemy.hp * 0.05)))
                    self.enemy.hp -= dmg
                    display_msg(f"{Colors.RED}Il sanguinamento infligge {dmg} danni a {self.enemy.name}! ({self.enemy.hp}){Colors.RESET}")
                elif status == "scorch":
                    dmg = self._enemy_status_damage(status, max(1, self.enemy.max_hp * GAME_DATA["elements"]["conditions"]["scorch_pct"] // 100))
                    self.enemy.hp -= dmg
                    display_msg(f"{Colors.RED}🌋 Il magma brucia {self.enemy.name}: {dmg} danni! ({self.enemy.hp}){Colors.RESET}")
                if status in CONTROL_STATUSES: continue  # scadono alla fine del turno del nemico (_tick_enemy_conditions)
                
                self.enemy.statuses[status] -= 1
                if self.enemy.statuses[status] <= 0: expired.append(status)
            for e in expired:
                del self.enemy.statuses[e]
                display_msg(f"{Colors.CYAN}L'effetto di {STATUS_NAMES.get(e, e)} su {self.enemy.name} è svanito.{Colors.RESET}")

    def start(self):
        if self.enemy.modifier == "normal":
            delay_print(f"\n{random.choice(GAME_DATA['lore']['boss' if self.enemy.is_boss else 'combat'])}")
            if self.enemy.is_boss:
                delay_print(f"{Colors.MAGENTA}{Colors.BOLD}--- {self.enemy.title.upper()} ---{Colors.RESET}")
                if self.enemy.lore: delay_print(f"{Colors.YELLOW}\"{self.enemy.lore}\"{Colors.RESET}\n")
            
            boss_tag = f"{Colors.MAGENTA} [BOSS]{Colors.RESET}" if self.enemy.is_boss else ""
            delay_print(f"{Colors.RED}!!! Incontri un {self.enemy.name.upper()}{boss_tag} [{get_element_icon(self.enemy.element)}] !!!{Colors.RESET}", 0.04)
        
        record_enemy_seen(self.enemy.base_name)
        nem = getattr(self.enemy, "nemesis", None)
        if nem:
            trait = GAME_DATA["nemesis"]["traits"][nem["trait"]]
            delay_print(f"{Colors.MAGENTA}{Colors.BOLD}{nemesis.text('returns', nem)}{Colors.RESET}")
            display_msg(f"{Colors.MAGENTA}{trait['name']}: {trait['desc']}{Colors.RESET}")
        elif self.enemy.is_boss and (grudge := nemesis.boss_grudge(self.enemy.base_name)):
            display_msg(f"{Colors.RED}{grudge}{Colors.RESET}")
        # Chance to find a Bloody Letter before combat
        if not self.enemy.is_boss and random.random() < BLOOD_LETTER_CHANCE:
            idx = random.randrange(len(GAME_DATA['lore']['letters']))
            letter = GAME_DATA['lore']['letters'][idx]
            record_letter(idx)
            display_msg(f"\n{Colors.YELLOW}📜 Noti un messaggio inciso sulla parete:{Colors.RESET}")
            delay_print(f"\"{letter}\"\n", 0.05)
            self.player.gain_exp(10)

        self._announce_resonance()
        if self.silenced:
            display_msg(f"{Colors.MAGENTA}{self.biome['icon']} {self.biome['hazard']['name']}: un vapore verdastro riempie la stanza. La tua Difesa perde la sua tecnica.{Colors.RESET}")
        try:
            self._combat_loop()
        finally:
            self._end_combat()

    def _resonance_value(self, element: str) -> float:
        """Valore dell'effetto di Risonanza (da elements.json) se è quella attiva, altrimenti 0."""
        if self.resonance != element: return 0
        return GAME_DATA["elements"].get("resonance", {}).get(element, {}).get("value", 0)

    def _announce_resonance(self):
        data = GAME_DATA["elements"].get("resonance", {}).get(self.resonance)
        if data: display_msg(f"{Colors.CYAN}{data['announce']}{Colors.RESET}")

    def refresh_resonance(self):
        """Ricalcola la Risonanza dopo un cambio di equipaggiamento durante lo scontro."""
        new_res = self.player._get_resonance_element()
        if new_res == self.resonance: return
        if self.resonance: display_msg(f"{Colors.YELLOW}La Risonanza di {self.resonance} si spegne.{Colors.RESET}")
        self.resonance = new_res
        self._announce_resonance()
        self._apply_resonance_bonuses()

    def _apply_resonance_bonuses(self):
        self.player.temp_def = int(self._resonance_value("Terra"))
        self.player.temp_dodge = int(self._resonance_value("Vento"))

    def _end_combat(self):
        self.player.temp_dodge = self.player.temp_def = self.player.temp_acc = 0
        if self.player.hp <= 0:
            # Chi ti ha ucciso: a fine discesa può diventare una Nemesi (vedi nemesis.on_death)
            nem = getattr(self.enemy, "nemesis", None)
            self.player.run_tracker["killer"] = {"name": self.enemy.base_name, "is_boss": self.enemy.is_boss,
                                                 "display": nemesis.full_name(nem) if nem else self.enemy.base_name,
                                                 "nemesis_id": (getattr(self.enemy, "nemesis", None) or {}).get("id"),
                                                 "player_element": self.player.weapon.element}
        # Gli status sono effetti di combattimento: svaniscono a fine scontro
        if self.player.hp > 0 and self.player.statuses:
            names = ", ".join(STATUS_NAMES.get(s, s) for s in self.player.statuses)
            self.player.statuses.clear()
            display_msg(f"{Colors.CYAN}Lo scontro è finito: {names} svanisce dal tuo corpo.{Colors.RESET}")

    def _enemy_status_damage(self, status: str, dmg: int) -> int:
        for r in self.player.relic_effects: dmg = r.modify_enemy_status_damage(status, dmg)
        return dmg

    def _paradox(self, key: str) -> bool:
        rule = self.rules.get("paradox")
        return bool(rule) and random.random() * 100 < rule[key]

    def _combat_loop(self):
        while self.player.hp > 0 and self.enemy.hp > 0:
            self.check_phase()
            self.process_statuses_and_curses(is_player_turn=True)
            if self.player.hp <= 0:
                display_msg(f"\n{Colors.RED}{Colors.BOLD}Sei caduto a causa delle tue ferite...{Colors.RESET}")
                wait_enter("\nPremi INVIO per continuare...")
                break
                
            if not self.player_turn():
                break
            self.sealed = False  # il Sigillo vale per un solo turno
            if self.mute_turns: self.mute_turns -= 1
            if self.enemy.hp > 0 and self._paradox("player_repeat"):
                display_msg(f"{Colors.MAGENTA}⏳ Il tempo si riavvolge: agisci ancora!{Colors.RESET}")
                if not self.player_turn():
                    break
                
            # Il boss che cambia fase dopo il tuo turno usa il suo per trasformarsi
            if self.enemy.hp > 0 and self.check_phase(): self.intent = "transform"
            if self.enemy.hp > 0:
                self.process_statuses_and_curses(is_player_turn=False)
                if self.enemy.hp <= 0:
                    self.on_enemy_death()
                    break
                if not self.enemy_turn():
                    return
                if self._paradox("enemy_double"):
                    display_msg(f"{Colors.MAGENTA}⏳ Il tempo si lacera: {self.enemy.name} agisce di nuovo!{Colors.RESET}")
                    self.intent = self.enemy.choose_move()
                    if not self.enemy_turn():
                        return

    def on_enemy_death(self):
        display_msg(f"\n{Colors.YELLOW}{Colors.BOLD}*** Hai sconfitto {self.enemy.name}! ***{Colors.RESET}")
        record_enemy_killed(self.enemy.base_name)
        if self.player.hp == 1: self.player.run_tracker["kill_1_hp_done"] = True
        if self.player.spells and (self.mute_turns or self.silenced): self.player.run_tracker["kill_muted_done"] = True
        if self.enemy.is_boss and not self.boss_hit_taken: self.player.run_tracker["no_hit_boss_done"] = True
        
        g_drop = 0 if self.player.aristocrat else self.player.calculate_gold_gain(self.enemy.gold_drop)
        
        self.player.gold += g_drop
        display_msg(f"Ottieni {Colors.YELLOW}{g_drop} oro{Colors.RESET}.")
        # Le reliquie agiscono prima dell'EXP (es. la Pietra Filosofale converte l'EXP in Oro)
        for r in self.player.relic_effects: r.on_enemy_death(self)
        if self.player.necro_harvest:
            healed = self.player.heal(max(1, self.player.max_hp * NECRO_HARVEST_PCT // 100))
            if healed > 0: display_msg(f"{Colors.MAGENTA}Raccolto d'Anime: assorbi {healed} HP dal nemico caduto!{Colors.RESET}")
        if effects.total(self.player, "kill_heal_pct"):
            healed = self.player.heal(max(1, self.player.max_hp * effects.total(self.player, "kill_heal_pct") // 100))
            if healed > 0: display_msg(f"{Colors.GREEN}Talento: recuperi {healed} HP.{Colors.RESET}")
        if self.enemy.exp_drop > 0: self.player.gain_exp(self.enemy.exp_drop)
        
        if self.enemy.is_boss:
            self.player.bosses_killed += 1
            note(self.player, "boss", name=self.enemy.base_name)
            relic = get_random_relic(self.player)
            if relic: self.player.add_relic(relic)
            else:
                drop = set_sockets(generate_weapon(self.floor + 2, True) if random.random() > 0.5 else generate_armor(self.floor + 2, True), "boss")
                display_msg(f"\n{Colors.MAGENTA}DROP LEGGENDARIO: {drop.display_name}!{Colors.RESET}")
                if drop.flavor: display_msg(f"{Colors.YELLOW}Flavor: {drop.flavor}{Colors.RESET}")
                self.player.inventory.append(drop)
            audacity_reward(self.player, self.floor, self.enemy.gold_drop)
            rune_drop(self.player, self.floor, "boss")
        elif getattr(self.enemy, "nemesis", None):
            nem = self.enemy.nemesis
            note(self.player, "nemesis_defeated", name=nemesis.full_name(nem))
            gold = nemesis.defeat(nem)
            if not self.player.aristocrat: self.player.gold += gold
            display_msg(f"\n{Colors.YELLOW}{Colors.BOLD}{nemesis.text('defeated', nem)}{Colors.RESET}")
            trophy = generate_weapon(self.floor + 1, True) if random.random() > 0.5 else generate_armor(self.floor + 1, True)
            trophy.name = f"Trofeo: {trophy.name}"; trophy.refresh_display_name()
            display_msg(f"{Colors.MAGENTA}Trofeo di {nem['name']}: {trophy.display_name}!{Colors.RESET}")
            self.player.inventory.append(trophy)
        elif self.enemy.modifier == "elite":
            rule = GAME_DATA["meta"]["rooms"]["elite"]
            relic = get_random_relic(self.player) if random.random() * 100 < rule["relic_chance"] else None
            if relic: self.player.add_relic(relic)
            else:
                level, epic = self.floor + rule["loot_floor_bonus"], random.random() * 100 < rule["epic_chance"]
                drop = generate_weapon(level, epic) if random.random() > 0.5 else generate_armor(level, epic)
                display_msg(f"\n{Colors.MAGENTA}Il campione lascia cadere: {drop.display_name}!{Colors.RESET}")
                self.player.inventory.append(drop)
            rune_drop(self.player, self.floor, "elite")
        elif self.enemy.modifier == "hard":
            drop = generate_weapon(self.floor, False) if random.random() > 0.5 else generate_armor(self.floor, False)
            display_msg(f"\n{Colors.MAGENTA}Il nemico lascia cadere: {drop.display_name}!{Colors.RESET}")
            if drop.flavor: display_msg(f"{Colors.YELLOW}Flavor: {drop.flavor}{Colors.RESET}")
            self.player.inventory.append(drop)
        elif self.enemy.modifier == "easy":
            display_msg(f"\n{Colors.CYAN}Il nemico era troppo debole e non aveva nulla con sé.{Colors.RESET}")
        elif random.random() > 0.6:
            drop = generate_potion(self.floor)
            display_msg(f"Trovi: {Colors.CYAN}{drop.display_name}{Colors.RESET}!")
            self.player.inventory.append(drop)
        wait_enter("\nPremi INVIO per continuare...")
