import random
import time
from typing import List
from ui import Colors, delay_print, clear_screen, interactive_menu, display_msg, wait_enter
from data_manager import GAME_DATA, PROFILE_MANAGER, MULTIPLIERS, get_element_icon
from archive import get_archive_bonus
from codex import record_enemy_killed, record_enemy_seen, record_letter, record_reaction
from constants import BASE_HIT_CHANCE, BLOOD_LETTER_CHANCE
from entities import STATUS_NAMES, Player, Enemy, generate_weapon, generate_armor, generate_accessory, generate_potion, get_random_relic
from inventory_menu import show_inventory_menu

# Effetti di controllo delle reazioni: scadono alla fine del turno del nemico, non all'inizio
CONTROL_STATUSES = ("stun", "blind", "slow")
# Mosse del nemico che sono attacchi
ATTACK_MOVES = ("attack", "heavy", "venom")


def reaction_key(a: str, b: str):
    """La reazione fra due elementi, nell'ordine in cui compare in elements.json, o None."""
    reactions = GAME_DATA["elements"].get("reactions", {})
    return next((k for k in (f"{a}+{b}", f"{b}+{a}") if k in reactions), None)


class CombatSession:
    def __init__(self, player: Player, floor: int, enemy: Enemy):
        self.player = player
        self.floor = floor
        self.enemy = enemy
        self.boss_hit_taken = False
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

        for r in self.player.relic_effects:
            r.on_combat_start(self)

    def process_statuses_and_curses(self, is_player_turn: bool):
        if is_player_turn:
            if self.player.has_curse("hp_drain"):
                self.player.take_damage(2)
                display_msg(f"{Colors.MAGENTA}La Maledizione dell'equipaggiamento drena 2 HP! ({self.player.hp}/{self.player.max_hp}){Colors.RESET}")
            if self.player.has_curse("gold_drain") and self.player.gold > 0:
                self.player.gold = max(0, self.player.gold - 5)
                display_msg(f"{Colors.MAGENTA}La Maledizione divora 5 Oro! (Oro: {self.player.gold}){Colors.RESET}")
                
            expired = []
            for status, duration in self.player.statuses.items():
                if status == "poison":
                    dmg = 3 + self.floor
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
                    dmg = 3 + self.floor
                    self.enemy.hp -= dmg
                    display_msg(f"{Colors.GREEN}Il veleno infligge {dmg} danni a {self.enemy.name}! ({self.enemy.hp}){Colors.RESET}")
                elif status == "bleed":
                    dmg = max(5, int(self.enemy.hp * 0.05))
                    self.enemy.hp -= dmg
                    display_msg(f"{Colors.RED}Il sanguinamento infligge {dmg} danni a {self.enemy.name}! ({self.enemy.hp}){Colors.RESET}")
                elif status == "scorch":
                    dmg = max(1, self.enemy.max_hp * GAME_DATA["elements"]["conditions"]["scorch_pct"] // 100)
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
        # Chance to find a Bloody Letter before combat
        if not self.enemy.is_boss and random.random() < BLOOD_LETTER_CHANCE:
            idx = random.randrange(len(GAME_DATA['lore']['letters']))
            letter = GAME_DATA['lore']['letters'][idx]
            record_letter(idx)
            display_msg(f"\n{Colors.YELLOW}📜 Noti un messaggio inciso sulla parete:{Colors.RESET}")
            delay_print(f"\"{letter}\"\n", 0.05)
            self.player.gain_exp(10)

        self._announce_resonance()
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
        # Gli status sono effetti di combattimento: svaniscono a fine scontro
        if self.player.hp > 0 and self.player.statuses:
            names = ", ".join(STATUS_NAMES.get(s, s) for s in self.player.statuses)
            self.player.statuses.clear()
            display_msg(f"{Colors.CYAN}Lo scontro è finito: {names} svanisce dal tuo corpo.{Colors.RESET}")

    def _combat_loop(self):
        while self.player.hp > 0 and self.enemy.hp > 0:
            self.process_statuses_and_curses(is_player_turn=True)
            if self.player.hp <= 0:
                display_msg(f"\n{Colors.RED}{Colors.BOLD}Sei caduto a causa delle tue ferite...{Colors.RESET}")
                wait_enter("\nPremi INVIO per continuare...")
                break
                
            if not self.player_turn():
                break
                
            if self.enemy.hp > 0:
                self.process_statuses_and_curses(is_player_turn=False)
                if self.enemy.hp <= 0:
                    self.on_enemy_death()
                    break
                if not self.enemy_turn():
                    return

    def on_enemy_death(self):
        display_msg(f"\n{Colors.YELLOW}{Colors.BOLD}*** Hai sconfitto {self.enemy.name}! ***{Colors.RESET}")
        record_enemy_killed(self.enemy.base_name)
        if self.player.hp == 1: self.player.run_tracker["kill_1_hp_done"] = True
        if self.enemy.is_boss and not self.boss_hit_taken: self.player.run_tracker["no_hit_boss_done"] = True
        
        g_drop = 0 if self.player.aristocrat else self.player.calculate_gold_gain(self.enemy.gold_drop)
        
        self.player.gold += g_drop
        display_msg(f"Ottieni {Colors.YELLOW}{g_drop} oro{Colors.RESET}.")
        # Le reliquie agiscono prima dell'EXP (es. la Pietra Filosofale converte l'EXP in Oro)
        for r in self.player.relic_effects: r.on_enemy_death(self)
        if self.player.necro_harvest:
            healed = self.player.heal(max(1, self.player.max_hp // 10))
            if healed > 0: display_msg(f"{Colors.MAGENTA}Raccolto d'Anime: assorbi {healed} HP dal nemico caduto!{Colors.RESET}")
        if self.enemy.exp_drop > 0: self.player.gain_exp(self.enemy.exp_drop)
        
        if self.enemy.is_boss:
            self.player.bosses_killed += 1
            relic = get_random_relic(self.player)
            if relic: self.player.add_relic(relic)
            else:
                drop = generate_weapon(self.floor + 2, True) if random.random() > 0.5 else generate_armor(self.floor + 2, True)
                display_msg(f"\n{Colors.MAGENTA}DROP LEGGENDARIO: {drop.display_name}!{Colors.RESET}")
                if drop.flavor: display_msg(f"{Colors.YELLOW}Flavor: {drop.flavor}{Colors.RESET}")
                self.player.inventory.append(drop)
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

    def _calc_hit_chance(self, multiplier: float) -> int:
        slow = GAME_DATA["elements"]["conditions"]["slow"] if "slow" in self.enemy.statuses else 0
        return self.player.get_hit_chance(self.enemy.base_dodge - slow, multiplier)

    # ------------------------------------------------------------- marchi e reazioni elementali
    def apply_element(self, element: str):
        """Marchia il nemico con un elemento; se porta già un marchio di un elemento compatibile, scatena la reazione."""
        if not element or element == "Normale" or self.enemy.hp <= 0: return
        mark = self.enemy.mark
        if mark and mark[0] != element and (key := reaction_key(mark[0], element)):
            self._trigger_reaction(key)
            return
        if not mark or mark[0] != element:
            display_msg(f"{Colors.CYAN}{self.enemy.name} porta il marchio {get_element_icon(element)}.{Colors.RESET}")
        self.enemy.mark = [element, GAME_DATA["elements"]["marks"]["duration"]]

    def _trigger_reaction(self, key: str):
        r = GAME_DATA["elements"]["reactions"][key]
        self.enemy.mark = None
        record_reaction(key)
        self.player.run_tracker["reactions"] = self.player.run_tracker.get("reactions", 0) + 1
        msg = f"{Colors.MAGENTA}{Colors.BOLD}⚡ REAZIONE: {r['icon']} {r['name'].upper()}!{Colors.RESET}"
        if r.get("bonus_pct"):
            dmg = self.player.get_total_atk() * r["bonus_pct"] // 100
            self.enemy.hp -= dmg
            msg += f" {Colors.CYAN}{dmg} danni extra.{Colors.RESET}"
        if r.get("status"):
            s_type, turns = r["status"]["type"], r["status"]["duration"]
            self.enemy.statuses[s_type] = max(self.enemy.statuses.get(s_type, 0), turns)
            msg += f" {Colors.MAGENTA}{self.enemy.name}: {STATUS_NAMES[s_type]}.{Colors.RESET}"
        display_msg(msg)

    def _tick_enemy_conditions(self):
        """Fine del turno del nemico: scadono marchio, Accecato e Impantanato."""
        if self.enemy.mark:
            self.enemy.mark[1] -= 1
            if self.enemy.mark[1] <= 0: self.enemy.mark = None
        for s in [s for s in self.enemy.statuses if s in ("blind", "slow")]:
            self.enemy.statuses[s] -= 1
            if self.enemy.statuses[s] <= 0: del self.enemy.statuses[s]

    # ------------------------------------------------------------- intenti
    def _move(self, move_id: str) -> dict:
        return GAME_DATA["moves"]["moves"][move_id]

    def choose_intent(self):
        self.intent = "stunned" if "stun" in self.enemy.statuses else self.enemy.choose_move()

    def intent_text(self) -> str:
        if self.intent == "stunned": return f"🧊 {Colors.CYAN}Congelato: perderà il turno{Colors.RESET}"
        m = self._move(self.intent)
        text = f"{m['icon']} {Colors.BOLD}{m['name']}{Colors.RESET}"
        if self.intent in ATTACK_MOVES:
            text += f" (≈{self.estimate_enemy_damage(m.get('damage_mult', 1))} danni)"
            if self.intent == "heavy": text += f" {Colors.RED}— difenditi!{Colors.RESET}"
            if self.intent == "venom" and self.enemy.status_inflict: text += f" + {STATUS_NAMES.get(self.enemy.status_inflict['type'], '')} se ti ferisce"
        elif self.intent == "guard": text += f": i tuoi colpi faranno il {int(m['damage_taken_mult'] * 100)}% dei danni"
        elif self.intent == "heal": text += f": recupererà il {m['heal_pct']}% degli HP"
        return text

    def enemy_status_text(self) -> str:
        parts = []
        if self.enemy.mark: parts.append(f"marchio {get_element_icon(self.enemy.mark[0])}")
        parts += [STATUS_NAMES.get(s, s) for s in self.enemy.statuses]
        return f" [{', '.join(parts)}]" if parts else ""

    def attack_multiplier(self) -> float:
        multiplier = MULTIPLIERS.get(self.player.weapon.element, {}).get(self.enemy.element, 1.0)
        for r in self.player.relic_effects: multiplier = r.modify_multiplier(multiplier)
        return multiplier

    def _calc_base_damage(self, multiplier: float) -> tuple[int, str]:
        dmg_dealt = int(max(1, self.player.get_total_atk() + random.randint(-1, 2)) * multiplier)
        eff = f"{Colors.GREEN}[SUPER EFFICACE!]{Colors.RESET}" if multiplier > 1.0 else f"{Colors.RED}[Poco efficace...]{Colors.RESET}" if multiplier < 1.0 else ""
        return self.player.weapon.on_attack(dmg_dealt, eff)

    def execute_player_attack(self) -> bool:
        cancel_attack = False
        for r in self.player.relic_effects:
            if not r.on_before_attack(self): cancel_attack = True
        if cancel_attack: return False

        multiplier = self.attack_multiplier()
        
        was_focused = self.focused_attack
        if self.focused_attack:
            hit_chance = 100
            dmg_dealt = int(max(1, self.player.get_total_atk() + random.randint(-1, 2)) * multiplier * 2)
            eff = f"{Colors.GREEN}[CRITICO!]{Colors.RESET} " + (f"{Colors.GREEN}[SUPER EFFICACE!]{Colors.RESET}" if multiplier > 1.0 else "")
            self.focused_attack = False
        else:
            hit_chance = self._calc_hit_chance(multiplier)
            dmg_dealt, eff = self._calc_base_damage(multiplier)
        
        if self.enemy.is_boss:
            dmg_dealt = int(dmg_dealt * (1 + get_archive_bonus("boss_dmg_pct", PROFILE_MANAGER._data) / 100))

        crit = self.player.get_crit_chance()
        if crit > 0 and not was_focused and random.randint(1, 100) <= crit:
            dmg_dealt *= 2
            eff += f" {Colors.MAGENTA}[CRITICO!]{Colors.RESET}"

        # Imboscata (Assassino): il primo attacco di ogni scontro, anche se manca, consuma il bonus.
        # Non si somma all'attacco concentrato, che è già un critico garantito.
        ambush = self.player.assassin_ambush and self.first_player_attack and not was_focused
        self.first_player_attack = False
        if ambush:
            dmg_dealt *= 2
            eff += f" {Colors.MAGENTA}[IMBOSCATA!]{Colors.RESET}"

        self.player.run_tracker["floor_attacks"] += 1
        if random.randint(1, 100) <= hit_chance:
            self.player.run_tracker["floor_hits"] += 1
            dmg_dealt = int(dmg_dealt * self.player.get_class_damage_multiplier())
            if multiplier > 1.0 and self.enemy.is_boss:
                if "super_effective_hits" not in self.player.run_tracker: self.player.run_tracker["super_effective_hits"] = 0
                self.player.run_tracker["super_effective_hits"] += 1
            
            for r in self.player.relic_effects:
                dmg_dealt, eff = r.on_attack(self, dmg_dealt, multiplier, eff)

            if self.resonance == "Tenebra":
                dmg_dealt += int(self._resonance_value("Tenebra"))
                eff += f" {Colors.MAGENTA}[TENEBRA]{Colors.RESET}"
            if self.intent == "guard":
                dmg_dealt = int(dmg_dealt * self._move("guard")["damage_taken_mult"])
                eff += f" {Colors.BLUE}[GUARDIA]{Colors.RESET}"
            
            self.enemy.hp -= dmg_dealt
            display_msg(f"\n-> Colpisci con {self.player.weapon.name} infliggendo {Colors.CYAN}{dmg_dealt} danni!{Colors.RESET} {eff}")
            self.apply_element(self.player.weapon.element)
            
            for r in self.player.relic_effects: r.on_attack_landed(self, multiplier)

            ls = self.player.get_lifesteal()
            stolen = self.player.heal(ls) if ls > 0 else 0
            if stolen > 0: display_msg(f"{Colors.RED}Rubavita: assorbi {stolen} HP!{Colors.RESET}")
            if self.resonance == "Luce":
                healed = self.player.heal(int(self._resonance_value("Luce")))
                if healed > 0: display_msg(f"{Colors.YELLOW}✨ Risonanza di Luce: +{healed} HP!{Colors.RESET}")
            if self.resonance == "Fuoco":
                self.burn_dmg += int(self._resonance_value("Fuoco"))

            s_data = self.player.weapon.status_inflict
            if s_data and self.enemy.hp > 0 and random.randint(1, 100) <= s_data.get("chance", 100):
                s_type = s_data["type"]
                self.enemy.statuses[s_type] = max(self.enemy.statuses.get(s_type, 0), s_data["duration"])
                display_msg(f"{Colors.MAGENTA}{self.enemy.name} è afflitto da {STATUS_NAMES.get(s_type, s_type).upper()}!{Colors.RESET}")
            
            self.player.on_attack_landed(dmg_dealt, multiplier)
        else:
            display_msg(f"\n{Colors.YELLOW}-> Fallisci! {self.enemy.name} schiva.{Colors.RESET}")
        
        if self.enemy.hp <= 0:
            self.on_enemy_death()
            return False
        return True

    def execute_player_defense(self):
        self.is_defending = True
        self.player.on_defense_started()
        if self.def_type == "counter":
            display_msg(f"\n{Colors.BLUE}-> Sollevi la guardia, pronto a sfruttare l'attacco nemico!{Colors.RESET}")
        elif self.def_type == "focus":
            self.focused_attack = True
            display_msg(f"\n{Colors.BLUE}-> Studi il nemico nell'ombra. Il tuo prossimo attacco sarà devastante!{Colors.RESET}")
        elif self.def_type == "recovery":
            if self.player.cursed:
                display_msg(f"\n{Colors.BLUE}-> Ti difendi, ma la Maledizione blocca il tuo recupero magico.{Colors.RESET}")
            else:
                heal_amt = max(1, self.player.max_hp // 20)
                self.player.heal(heal_amt)
                display_msg(f"\n{Colors.BLUE}-> Evochi una barriera vitale. {Colors.GREEN}Recuperi {heal_amt} HP!{Colors.RESET}")

    def player_turn(self) -> bool:
        """Turno del giocatore. Ritorna False se lo scontro finisce (fuga, morte del nemico o del giocatore).

        Le voci che non consumano il turno (statistiche, inventario chiuso senza usare nulla,
        fuga impossibile dai boss) ripresentano il menu nello stesso ciclo.
        """
        while True:
            # I bonus di Risonanza devono restare attivi per tutto il combattimento
            self._apply_resonance_bonuses()
            self.is_defending = False

            self.def_type, self.def_txt = self.player.get_defense_action()
            if self.intent is None: self.choose_intent()

            prompt = (f"\n{Colors.BOLD}--- ⚔️ IN COMBATTIMENTO ⚔️ ---{Colors.RESET}\nTu: {Colors.GREEN}{self.player.hp}/{self.player.max_hp} HP{Colors.RESET} | "
                      f"{self.enemy.name}: {Colors.RED}{self.enemy.hp}/{self.enemy.max_hp} HP{Colors.RESET}{self.enemy_status_text()}\n"
                      f"Intento del nemico: {self.intent_text()}")
            options = [
                "Attacca",
                self.def_txt,
                "Apri Inventario (Usa oggetto = Costa Turno)",
                "Statistiche Eroe",
                "Tenta la Fuga"
            ]

            idx = interactive_menu(options, prompt)
            clear_screen()

            if idx == 0:
                return self.execute_player_attack()

            elif idx == 1:
                self.execute_player_defense()
                return True

            elif idx == 2:
                action = show_inventory_menu(self.player, in_combat=True)
                self.refresh_resonance()
                if action == "smoke_bomb":
                    if self.enemy.is_boss:
                        display_msg(f"\n{Colors.RED}-> Il fumo si dirada all'istante: impossibile fuggire dai Boss!{Colors.RESET}")
                        return True
                    self.player.run_tracker["escapes"] += 1
                    return False
                elif action == "fiala_caos":
                    caos_dmg = random.randint(10, 100)
                    self.enemy.hp -= caos_dmg
                    display_msg(f"{Colors.MAGENTA}Esplosione caotica: {caos_dmg} danni puri!{Colors.RESET}")
                    if self.enemy.hp <= 0:
                        self.on_enemy_death()
                        return False
                    return True
                elif action == "turn_used" or action == "antidote":
                    clear_screen()
                    return True

            elif idx == 3:
                from inventory_menu import show_player_stats
                show_player_stats(self.player, self)

            elif idx == 4:
                if self.enemy.is_boss:
                    display_msg(f"\n{Colors.RED}-> Impossibile fuggire dai Boss!{Colors.RESET}")
                    continue

                if random.randint(1, 100) <= self._calc_escape_chance():
                    display_msg(f"\n{Colors.YELLOW}-> Sei riuscito a scappare!{Colors.RESET}")
                    self.player.run_tracker["escapes"] += 1
                    wait_enter("\nPremi INVIO...")
                    return False
                display_msg(f"\n{Colors.RED}-> Tentativo di fuga fallito!{Colors.RESET}")
                return True

    def _calc_escape_chance(self) -> int:
        f_chance = 20 + self.player.get_dodge() - self.enemy.base_dodge + (20 if PROFILE_MANAGER.get_perk("scarpisti", False) else 0)
        f_chance += get_archive_bonus("escape", PROFILE_MANAGER._data)
        f_chance = max(10, min(90, f_chance))
        for r in self.player.relic_effects:
            mod = r.get_escape_modifier()
            if mod > 0: f_chance = mod
        return f_chance

    def _calc_enemy_hit_chance(self, en_multiplier: float) -> int:
        blind = GAME_DATA["elements"]["conditions"]["blind"] if "blind" in self.enemy.statuses else 0
        return max(10, min(100, BASE_HIT_CHANCE + self.enemy.base_acc - blind - self.player.get_dodge() + (15 if en_multiplier > 1.0 else -20 if en_multiplier < 1.0 else 0)))

    def _enemy_multiplier(self) -> float:
        en_multiplier = MULTIPLIERS.get(self.enemy.element, {}).get(self.player.armor.element, 1.0)
        for r in self.player.relic_effects: en_multiplier = r.modify_multiplier(en_multiplier, is_defense=True)
        return en_multiplier

    def _enemy_attack_power(self) -> int:
        return max(1, int(self.enemy.atk * (1 - self._resonance_value("Acqua")))) if self.resonance == "Acqua" else self.enemy.atk

    def estimate_enemy_damage(self, move_mult: float = 1.0) -> int:
        """Danno atteso dell'attacco annunciato, senza difesa attiva né effetti casuali (per l'intento)."""
        defense = self.player.get_total_def() + sum(r.get_def_modifier(self) for r in self.player.relic_effects)
        return max(0, int(self._enemy_attack_power() * self._enemy_multiplier() * move_mult) - defense)

    def _calc_enemy_damage(self, en_multiplier: float, move_mult: float = 1.0) -> int:
        defense = self.player.get_total_def() + sum(r.get_def_modifier(self) for r in self.player.relic_effects)
        en_atk = self._enemy_attack_power()
        dmg_taken = max(0, int((en_atk + random.randint(-1, 2)) * en_multiplier * move_mult) - defense)
        if self.is_defending: dmg_taken //= 2
        before_relics = dmg_taken
        for r in self.player.relic_effects: dmg_taken = r.on_take_damage(self, dmg_taken, en_multiplier)
        # Se una reliquia ha annullato il colpo, ha già stampato il suo messaggio
        self.hit_negated_by_relic = before_relics > 0 and dmg_taken == 0
        return dmg_taken

    def enemy_turn(self) -> bool:
        """Il nemico esegue la mossa annunciata (un attacco, se non ne aveva annunciata nessuna)."""
        intent, self.intent = self.intent or "attack", None
        if "stun" in self.enemy.statuses:
            del self.enemy.statuses["stun"]
            display_msg(f"{Colors.CYAN}<- 🧊 {self.enemy.name} è congelato e perde il turno!{Colors.RESET}")
            result = True
        elif intent == "guard":
            display_msg(f"{Colors.BLUE}<- {self.enemy.name} resta in guardia.{Colors.RESET}")
            result = True
        elif intent == "heal":
            healed = min(self.enemy.max_hp - self.enemy.hp, self.enemy.max_hp * self._move("heal")["heal_pct"] // 100)
            self.enemy.hp += healed
            self.enemy.heals_used += 1
            display_msg(f"{Colors.GREEN}<- 💚 {self.enemy.name} si rigenera: +{healed} HP. ({self.enemy.hp}/{self.enemy.max_hp}){Colors.RESET}")
            result = True
        else:
            result = self._enemy_attack(intent)
        if not result or self.enemy.hp <= 0 or self.player.hp <= 0: return result
        self._tick_enemy_conditions()
        if self.burn_dmg > 0:
            self.enemy.hp -= self.burn_dmg
            display_msg(f"{Colors.RED}🔥 Risonanza di Fuoco: Ustione infligge {self.burn_dmg} danni!{Colors.RESET}")
            if self.enemy.hp <= 0:
                self.on_enemy_death()
                return False
        return True

    def _enemy_attack(self, move: str) -> bool:
        en_multiplier = self._enemy_multiplier()
        move_mult = self._move(move).get("damage_mult", 1)
        
        en_hit_chance = self._calc_enemy_hit_chance(en_multiplier)
        # Cacciatore Etereo: il primo attacco nemico di ogni scontro manca sempre
        if self.first_enemy_attack and self.player.ethereal_hunter: en_hit_chance = 0
        self.first_enemy_attack = False

        if random.randint(1, 100) <= en_hit_chance:
            dmg_taken = self._calc_enemy_damage(en_multiplier, move_mult)
            if self.enemy.hp <= 0:
                self.on_enemy_death()
                return False
            
            en_eff = f"{Colors.RED}[Sei vulnerabile!]{Colors.RESET}" if en_multiplier > 1.0 else f"{Colors.GREEN}[Resisti!]{Colors.RESET}" if en_multiplier < 1.0 else ""
            
            if dmg_taken > 0: 
                self.boss_hit_taken = True
                dif = f"{Colors.BLUE}[DIFESA]{Colors.RESET}" if self.is_defending else ""
                heavy = f"{Colors.RED}[COLPO PESANTE]{Colors.RESET} " if move == "heavy" else ""
                display_msg(f"<- {heavy}{self.enemy.name} ti colpisce! Subisci {Colors.RED}{dmg_taken} danni{Colors.RESET}. {en_eff}{dif}")
                
                if getattr(self.enemy, 'status_inflict', None):
                    s_data = self.enemy.status_inflict
                    if move == "venom" or random.randint(1, 100) <= s_data.get("chance", 100):
                        s_type = s_data["type"]
                        self.player.statuses[s_type] = max(self.player.statuses.get(s_type, 0), s_data["duration"])
                        display_msg(f"{Colors.MAGENTA}Sei stato afflitto da {STATUS_NAMES.get(s_type, s_type).upper()}!{Colors.RESET}")
                
                reflect_total = 0
                if self.player.accessory and self.player.accessory.bonus_type == "reflect": reflect_total += self.player.accessory.bonus_value
                if reflect_total > 0:
                    self.enemy.hp -= reflect_total
                    display_msg(f"{Colors.YELLOW}Riflessi {reflect_total} danni a {self.enemy.name}!{Colors.RESET}")
                    if self.enemy.hp <= 0:
                        self.on_enemy_death()
                        return False
                
                if self.is_defending and self.def_type == "counter":
                    self.enemy.hp -= dmg_taken
                    display_msg(f"{Colors.YELLOW}   ⚔️ CONTRATTACCO! Restituisci {dmg_taken} danni a {self.enemy.name}!{Colors.RESET}")
                    if self.enemy.hp <= 0:
                        self.on_enemy_death()
                        return False
                
                alive = self.player.take_damage(dmg_taken)
                if not alive:
                    display_msg(f"\n{Colors.RED}{Colors.BOLD}Sei caduto in battaglia contro {self.enemy.name}...{Colors.RESET}")
                    wait_enter("\nPremi INVIO per continuare...")
                    return False
            elif not self.hit_negated_by_relic:
                display_msg(f"<- {self.enemy.name} attacca, ma la corazza blocca TUTTO! {en_eff}")
            if self.is_defending:
                # In guardia, l'armatura marchia con il suo elemento chi ti colpisce: è così che si combinano due elementi
                self.apply_element(self.player.armor.element)
                if self.enemy.hp <= 0:
                    self.on_enemy_death()
                    return False
        else:
            display_msg(f"{Colors.CYAN}<- {self.enemy.name} attacca... ma riesci a schivarlo!{Colors.RESET}")
        return True

def combat_room(player: Player, floor: int, enemy_instance: Enemy):
    session = CombatSession(player, floor, enemy_instance)
    session.start()

def mystery_room(player: Player, floor: int, active_pacts: List[str]):
    delay_print(f"\n{Colors.MAGENTA}--- LA STANZA DEL MISTERO ---{Colors.RESET}")
    display_msg(f"❤️  HP: {Colors.GREEN}{player.hp}/{player.max_hp}{Colors.RESET} | 💰 Oro: {Colors.YELLOW}{player.gold}{Colors.RESET}\n")
    delay_print(f"{random.choice(GAME_DATA['lore']['mystery'])}", 0.03)
    time.sleep(1)

    outcome = random.choice(["hard", "easy", "trap", "empty"])

    if outcome == "hard":
        display_msg(f"\n{Colors.RED}Dall'oscurità emerge un mostro eccezionalmente feroce!{Colors.RESET}")
        wait_enter("Premi INVIO per difenderti...")
        combat_room(player, floor, Enemy(floor, False, active_pacts, modifier="hard"))
    elif outcome == "easy":
        display_msg(f"\n{Colors.CYAN}Scorgi un nemico ferito e confuso che vaga nella nebbia.{Colors.RESET}")
        wait_enter("Premi INVIO per attaccare...")
        combat_room(player, floor, Enemy(floor, False, active_pacts, modifier="easy"))
    elif outcome == "trap":
        trap_room(player, floor, active_pacts)
    else:
        display_msg(f"\n{Colors.GREEN}La nebbia si dirada. La stanza è vuota. Tiri un sospiro di sollievo.{Colors.RESET}")
        wait_enter("Premi INVIO per proseguire...")

def vendor_room(player: Player, floor: int):
    delay_print(f"\n{random.choice(GAME_DATA['lore']['vendor'])}")
    items_for_sale =[generate_weapon(floor + 1), generate_armor(floor + 1), generate_accessory(floor), generate_potion(floor), generate_potion(floor)]
    discount = 1.0 - (PROFILE_MANAGER.get_perk("discount_lvl", 0) * 0.10)
    for i in items_for_sale: 
        i.value = max(1, int(i.value * discount))
        if "inflazione" in player.active_pacts: i.value = int(i.value * 2)

    while True:
        clear_screen()
        prompt = f"\n{Colors.YELLOW}[ 💰 MERCANTE ] | Tuo Oro: {player.gold}{Colors.RESET}\n"
        if PROFILE_MANAGER.get_perk("discount_lvl", 0) > 0: prompt += f"{Colors.GREEN}(Sconto del {PROFILE_MANAGER.get_perk('discount_lvl', 0)*10}%!){Colors.RESET}\n"
        
        options = ["Guarda Merce (Compra)", "Mostra Zaino (Vendi)", "Saluta ed esci"]
        idx = interactive_menu(options, prompt)
        
        if idx == 0:
            while True:
                clear_screen()
                prompt_compra = f"\n{Colors.CYAN}--- NEGOZIO (COMPRA) --- Tuo Oro: {player.gold}{Colors.RESET}\nScegli cosa comprare:"
                options_compra = []
                for i, item in enumerate(items_for_sale):
                    tipo = "Arma" if item.type=="weapon" else "Armatura" if item.type=="armor" else "Monile" if item.type=="accessory" else "Pozione"
                    options_compra.append(f"[{tipo}] {item.display_name} - Prezzo: {Colors.YELLOW}{item.value} Oro{Colors.RESET}")
                idx_compra = interactive_menu(options_compra, prompt_compra, cancellable=True)
                if idx_compra == -1: break
                
                if 0 <= idx_compra < len(items_for_sale):
                    item = items_for_sale[idx_compra]
                    if player.gold >= item.value:
                        player.gold -= item.value; player.inventory.append(item)
                        if "gold_spent" not in player.run_tracker: player.run_tracker["gold_spent"] = 0
                        player.run_tracker["gold_spent"] += item.value
                        display_msg(f"{Colors.GREEN}Hai comprato {item.name}!{Colors.RESET}"); items_for_sale.pop(idx_compra); time.sleep(1)
                        for i_idx, remaining_item in enumerate(items_for_sale):
                            items_for_sale[i_idx].value = int(remaining_item.value * 1.1)
                    else: display_msg(f"{Colors.RED}Oro insufficiente!{Colors.RESET}"); time.sleep(1)
        elif idx == 1:
            while True:
                clear_screen()
                prompt_vendi = f"\n{Colors.CYAN}--- NEGOZIO (VENDI) ---{Colors.RESET}\nScegli cosa vendere:"
                options_vendi = []
                if not player.inventory: prompt_vendi += "\nNon hai nulla nello zaino da vendere.\n"
                else:
                    for i, item in enumerate(player.inventory):
                        options_vendi.append(f"{item.display_name} - Val di vendita: {Colors.YELLOW}{max(1, item.value // 2)} Oro{Colors.RESET}")
                idx_vendi = interactive_menu(options_vendi, prompt_vendi, cancellable=True)
                if idx_vendi == -1: break
                
                if player.inventory and 0 <= idx_vendi < len(player.inventory):
                    item = player.inventory.pop(idx_vendi); gain = max(1, item.value // 2)
                    gain = int(gain * (1 + (PROFILE_MANAGER.get_perk("riciclatore_lvl", 0) * 0.10)))
                    player.gold += gain; display_msg(f"{Colors.GREEN}Hai venduto {item.name} per {gain} oro!{Colors.RESET}"); time.sleep(1)
        elif idx == 2: break

def campfire_room(player: Player, floor: int):
    delay_print(f"\n{Colors.YELLOW}{random.choice(GAME_DATA['lore']['campfire'])}{Colors.RESET}")
    while True:
        clear_screen()
        prompt = f"\n{Colors.YELLOW}[ 🔥 FALÒ E FORGIA ] | Tuo Oro: {player.gold} | HP: {player.hp}/{player.max_hp}{Colors.RESET}\n"
        options = [
            "Riposa (Recupera 50% HP, il falò si spegnerà)",
            f"Affila Arma Base (Paga {Colors.YELLOW}50 Oro{Colors.RESET} per +3 ATK, il falò si spegnerà)",
            f"{Colors.MAGENTA}Altare dell'Evoluzione{Colors.RESET} (Fondi due armi/armature per potenziarle)"
        ]
        
        has_cursed = any(getattr(item, 'is_cursed', False) for item in [player.weapon, player.armor, player.accessory] if item)
        if has_cursed:
            options.append(f"{Colors.CYAN}Purifica Maledizione{Colors.RESET} (Paga {Colors.YELLOW}100 Oro{Colors.RESET} per rimuovere il malus da un pezzo equipaggiato)")
            
        options.append("Prosegui")
        
        idx = interactive_menu(options, prompt)
        
        if options[idx] == "Prosegui": break
        elif idx == 0:
            player.run_tracker["rested"] = True
            player.heal(player.max_hp // 2)
            display_msg(f"{Colors.GREEN}Ti riposi profondamente!{Colors.RESET}"); wait_enter("\nPremi INVIO..."); break
        elif idx == 1:
            if player.gold >= 50:
                player.gold -= 50; player.weapon.atk += 3
                display_msg(f"{Colors.GREEN}Arma migliorata: {player.weapon.atk} ATK!{Colors.RESET}"); wait_enter("\nPremi INVIO..."); break
            else: display_msg(f"{Colors.RED}Oro insufficiente.{Colors.RESET}"); time.sleep(1.5)
        elif idx == 2:
            while True:
                clear_screen()
                prompt_forge = f"\n{Colors.MAGENTA}--- FUSIONE EQUIPAGGIAMENTO ---{Colors.RESET}\n"
                equips =[i for i in player.inventory if i.type in["weapon", "armor"]]
                if len(equips) < 2: 
                    display_msg(prompt_forge + "Hai bisogno di almeno 2 armi/armature nello zaino per usare l'Altare."); wait_enter("Premi INVIO..."); break
                
                options_forge = []
                for i, item in enumerate(equips):
                    stat = f"+{item.atk} ATK" if item.type == "weapon" else f"+{item.defense} DEF"
                    options_forge.append(f"[{item.type.upper()}] {item.display_name} {stat} (Lv.{item.level})")
                i1 = interactive_menu(options_forge, prompt_forge + "Seleziona il PRIMO oggetto (Base):", cancellable=True)
                if i1 == -1: break
                
                i2 = interactive_menu(options_forge, prompt_forge + "Seleziona il SECONDO oggetto (Sacrificio):", cancellable=True)
                if i2 == -1: break
                
                if i1 != i2 and 0 <= i1 < len(equips) and 0 <= i2 < len(equips):
                    it1, it2 = equips[i1], equips[i2]
                    if it1.type == it2.type:
                        player.inventory.remove(it2)
                        if it1.type == "weapon": it1.atk += max(1, it2.atk // 2)
                        else: it1.defense += max(1, it2.defense // 2)
                        it1.level += 1
                        if it1.type == "weapon": player.run_tracker["max_fused_weapon_lvl"] = max(player.run_tracker.get("max_fused_weapon_lvl", 0), it1.level)
                        if not it1.name.startswith("Perfetto "): it1.name = f"Perfetto {it1.name}"
                        it1.refresh_display_name()
                        player.run_tracker["fusions"] += 1
                        display_msg(f"{Colors.GREEN}FUSIONE RIUSCITA! Il primo oggetto ha assorbito il secondo.{Colors.RESET}")
                        wait_enter("Premi INVIO per continuare...")
                        break
                    else: display_msg(f"{Colors.RED}Puoi fondere solo oggetti dello stesso tipo!{Colors.RESET}"); time.sleep(1.5)
                else: display_msg(f"{Colors.RED}Selezione non valida o oggetto uguale.{Colors.RESET}"); time.sleep(1.5)
        elif options[idx].startswith(f"{Colors.CYAN}Purifica"):
            cursed_items = [item for item in [player.weapon, player.armor, player.accessory] if item and getattr(item, 'is_cursed', False)]
            if player.gold < 100:
                display_msg(f"{Colors.RED}Oro insufficiente per il rituale di purificazione (Richiede 100 Oro).{Colors.RESET}")
                time.sleep(1.5)
            else:
                while True:
                    clear_screen()
                    prompt_purify = f"\n{Colors.CYAN}--- PURIFICAZIONE ---{Colors.RESET} Tuo Oro: {player.gold}\nQuale oggetto purificare?"
                    options_purify = []
                    for i, item in enumerate(cursed_items):
                        options_purify.append(f"{item.display_name} (Malus: {item.curse_effect})")
                    p_idx = interactive_menu(options_purify, prompt_purify, cancellable=True)
                    if p_idx == -1: break
                    
                    if 0 <= p_idx < len(cursed_items):
                        player.gold -= 100
                        target_item = cursed_items[p_idx]
                        target_item.is_cursed = False
                        target_item.curse_effect = ""
                        target_item.refresh_display_name()
                        display_msg(f"{Colors.GREEN}Il rituale ha successo! La maledizione è spezzata.{Colors.RESET}")
                        wait_enter("\nPremi INVIO...")
                        break

def treasure_room(player: Player, floor: int):
    delay_print(f"\n{Colors.YELLOW}{random.choice(GAME_DATA['lore']['treasure'])}{Colors.RESET}")
    gold = random.randint(30, 60) + (floor * 10)
    g = player.calculate_gold_gain(gold)
    
    player.gold += g
    display_msg(f"{Colors.GREEN}Trovate {g} monete d'oro!{Colors.RESET}")
    
    if random.random() < 0.15:
        r = get_random_relic(player)
        if r: player.add_relic(r)
    elif random.random() < 0.20:
        drop = generate_accessory(floor)
        display_msg(f"C'era anche: {Colors.CYAN}{drop.display_name}{Colors.RESET}!"); player.inventory.append(drop)
    elif random.random() > 0.4:
        drop = generate_potion(floor)
        display_msg(f"C'era anche: {Colors.CYAN}{drop.display_name}{Colors.RESET}!"); player.inventory.append(drop)
    wait_enter("\nPremi INVIO per continuare...")

def trap_room(player: Player, floor: int, active_pacts: List[str]):
    delay_print(f"\n{random.choice(GAME_DATA['lore']['trap'])}")
    delay_print(f"{Colors.RED}È UNA TRAPPOLA!{Colors.RESET}", 0.05)
    
    if random.randint(1, 100) <= player.get_dodge(): 
        display_msg(f"{Colors.GREEN}Schivi il meccanismo! Ne esci illeso!{Colors.RESET}")
    else:
        dmg = random.randint(15, 30) + (floor * 3)
        if "trappole" in active_pacts: dmg *= 2
        for r in player.relic_effects: dmg = r.modify_trap_damage(dmg)
        display_msg(f"{Colors.RED}Subisci {dmg} danni puri.{Colors.RESET}")
        alive = player.take_damage(dmg)
        display_msg(f"(HP: {player.hp}/{player.max_hp})")
        if not alive:
            display_msg(f"\n{Colors.RED}{Colors.BOLD}La trappola ti è stata fatale...{Colors.RESET}")
            wait_enter("\nPremi INVIO per continuare...")
            return
            
    if random.randint(1, 100) <= 20:
        display_msg(f"\n{Colors.GREEN}Tra gli ingranaggi spezzati della trappola noti qualcosa brillare...{Colors.RESET}")
        roll = random.random()
        if roll > 0.7: drop = generate_accessory(floor)
        elif roll > 0.5: drop = generate_weapon(floor, False)
        else: drop = generate_armor(floor, False)
        display_msg(f"{Colors.MAGENTA}Hai trovato: {drop.display_name}!{Colors.RESET}")
        player.inventory.append(drop)

    wait_enter("\nPremi INVIO per continuare...")

