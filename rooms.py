import random
import time
from typing import List
from ui import Colors, delay_print, clear_screen, get_choice, interactive_menu
from data_manager import GAME_DATA, PROFILE_MANAGER, MULTIPLIERS, get_element_icon
from archive import is_book_unlocked
from constants import BASE_HIT_CHANCE, BLOOD_LETTER_CHANCE
from entities import Player, Enemy, generate_weapon, generate_armor, generate_accessory, generate_potion, get_random_relic
from inventory_menu import show_inventory_menu

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

        for r in self.player.relic_effects:
            r.on_combat_start(self)

    def process_statuses_and_curses(self, is_player_turn: bool):
        if is_player_turn:
            if self.player.has_curse("hp_drain"):
                self.player.take_damage(2)
                print(f"{Colors.MAGENTA}La Maledizione dell'equipaggiamento drena 2 HP! ({self.player.hp}/{self.player.max_hp}){Colors.RESET}")
            if self.player.has_curse("gold_drain") and self.player.gold > 0:
                self.player.gold = max(0, self.player.gold - 5)
                print(f"{Colors.MAGENTA}La Maledizione divora 5 Oro! (Oro: {self.player.gold}){Colors.RESET}")
                
            expired = []
            for status, duration in self.player.statuses.items():
                if status == "poison":
                    dmg = 3 + self.floor
                    self.player.take_damage(dmg)
                    print(f"{Colors.GREEN}Il veleno ti infligge {dmg} danni! ({self.player.hp}/{self.player.max_hp}){Colors.RESET}")
                elif status == "bleed":
                    dmg = max(1, int(self.player.max_hp * 0.05))
                    self.player.take_damage(dmg)
                    print(f"{Colors.RED}Il sanguinamento ti infligge {dmg} danni! ({self.player.hp}/{self.player.max_hp}){Colors.RESET}")
                
                self.player.statuses[status] -= 1
                if self.player.statuses[status] <= 0: expired.append(status)
            for e in expired:
                del self.player.statuses[e]
                print(f"{Colors.CYAN}L'effetto di {e} è svanito dal tuo corpo.{Colors.RESET}")
        else:
            expired = []
            for status, duration in self.enemy.statuses.items():
                if status == "poison":
                    dmg = 3 + self.floor
                    self.enemy.hp -= dmg
                    print(f"{Colors.GREEN}Il veleno infligge {dmg} danni a {self.enemy.name}! ({self.enemy.hp}){Colors.RESET}")
                elif status == "bleed":
                    dmg = max(5, int(self.enemy.hp * 0.05))
                    self.enemy.hp -= dmg
                    print(f"{Colors.RED}Il sanguinamento infligge {dmg} danni a {self.enemy.name}! ({self.enemy.hp}){Colors.RESET}")
                
                self.enemy.statuses[status] -= 1
                if self.enemy.statuses[status] <= 0: expired.append(status)
            for e in expired:
                del self.enemy.statuses[e]
                print(f"{Colors.CYAN}L'effetto di {e} su {self.enemy.name} è svanito.{Colors.RESET}")

    def start(self):
        if self.enemy.modifier == "normal":
            delay_print(f"\n{random.choice(GAME_DATA['lore']['boss' if self.enemy.is_boss else 'combat'])}")
            if self.enemy.is_boss:
                delay_print(f"{Colors.MAGENTA}{Colors.BOLD}--- {self.enemy.title.upper()} ---{Colors.RESET}")
                if self.enemy.lore: delay_print(f"{Colors.YELLOW}\"{self.enemy.lore}\"{Colors.RESET}\n")
            
            boss_tag = f"{Colors.MAGENTA} [BOSS]{Colors.RESET}" if self.enemy.is_boss else ""
            delay_print(f"{Colors.RED}!!! Incontri un {self.enemy.name.upper()}{boss_tag} [{get_element_icon(self.enemy.element)}] !!!{Colors.RESET}", 0.04)
        
        # Chance to find a Bloody Letter before combat
        if not self.enemy.is_boss and random.random() < BLOOD_LETTER_CHANCE:
            letter = random.choice(GAME_DATA['lore']['letters'])
            print(f"\n{Colors.YELLOW}📜 Noti un messaggio inciso sulla parete:{Colors.RESET}")
            delay_print(f"\"{letter}\"\n", 0.05)
            self.player.gain_exp(10)

        if self.resonance == "Acqua":
            self.enemy.atk = max(1, int(self.enemy.atk * 0.85))
            print(f"{Colors.CYAN}✨ Risonanza d'Acqua! L'attacco del nemico è ridotto del 15%!{Colors.RESET}")
        if self.resonance == "Vento":
            self.player.temp_dodge = 15
            print(f"{Colors.CYAN}✨ Risonanza di Vento! +15% Schivata!{Colors.RESET}")
        if self.resonance == "Terra":
            self.player.temp_def = 5
            print(f"{Colors.CYAN}✨ Risonanza di Terra! +5 Difesa fissa!{Colors.RESET}")

        try:
            self._combat_loop()
        finally:
            self.player.temp_dodge = self.player.temp_def = self.player.temp_acc = 0

    def _combat_loop(self):
        while self.player.hp > 0 and self.enemy.hp > 0:
            self.process_statuses_and_curses(is_player_turn=True)
            if self.player.hp <= 0:
                print(f"\n{Colors.RED}{Colors.BOLD}Sei caduto a causa delle tue ferite...{Colors.RESET}")
                input("\nPremi INVIO per continuare...")
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
        print(f"\n{Colors.YELLOW}{Colors.BOLD}*** Hai sconfitto {self.enemy.name}! ***{Colors.RESET}")
        if self.player.hp == 1: self.player.run_tracker["kill_1_hp_done"] = True
        if self.enemy.is_boss and not self.boss_hit_taken: self.player.run_tracker["no_hit_boss_done"] = True
        
        g_drop = self.player.calculate_gold_gain(self.enemy.gold_drop)
        
        self.player.gold += g_drop
        print(f"Ottieni {Colors.YELLOW}{g_drop} oro{Colors.RESET}.")
        # Le reliquie agiscono prima dell'EXP (es. la Pietra Filosofale converte l'EXP in Oro)
        for r in self.player.relic_effects: r.on_enemy_death(self)
        if self.enemy.exp_drop > 0: self.player.gain_exp(self.enemy.exp_drop)
        
        if self.enemy.is_boss:
            self.player.bosses_killed += 1
            relic = get_random_relic(self.player)
            if relic: self.player.add_relic(relic)
            else:
                drop = generate_weapon(self.floor + 2, True) if random.random() > 0.5 else generate_armor(self.floor + 2, True)
                print(f"\n{Colors.MAGENTA}DROP LEGGENDARIO: {drop.display_name}!{Colors.RESET}")
                if drop.flavor: print(f"{Colors.YELLOW}Flavor: {drop.flavor}{Colors.RESET}")
                self.player.inventory.append(drop)
        elif self.enemy.modifier == "hard":
            drop = generate_weapon(self.floor, False) if random.random() > 0.5 else generate_armor(self.floor, False)
            print(f"\n{Colors.MAGENTA}Il nemico lascia cadere: {drop.display_name}!{Colors.RESET}")
            if drop.flavor: print(f"{Colors.YELLOW}Flavor: {drop.flavor}{Colors.RESET}")
            self.player.inventory.append(drop)
        elif self.enemy.modifier == "easy":
            print(f"\n{Colors.CYAN}Il nemico era troppo debole e non aveva nulla con sé.{Colors.RESET}")
        elif random.random() > 0.6:
            drop = generate_potion(self.floor)
            print(f"Trovi: {Colors.CYAN}{drop.display_name}{Colors.RESET}!")
            self.player.inventory.append(drop)
        input("\nPremi INVIO per continuare...")

    def _calc_hit_chance(self, multiplier: float) -> int:
        hit_chance = BASE_HIT_CHANCE + self.player.base_acc + self.player.temp_acc - self.enemy.base_dodge + (15 if multiplier > 1.0 else -20 if multiplier < 1.0 else 0)
        hit_chance += self.player.weapon.get_hit_chance_modifier()
        for r in self.player.relic_effects: hit_chance += r.get_acc_modifier()
        return max(10, min(100, hit_chance))

    def _calc_base_damage(self, multiplier: float) -> tuple[int, str]:
        dmg_dealt = int(max(1, self.player.get_total_atk() + random.randint(-1, 2)) * multiplier)
        eff = f"{Colors.GREEN}[SUPER EFFICACE!]{Colors.RESET}" if multiplier > 1.0 else f"{Colors.RED}[Poco efficace...]{Colors.RESET}" if multiplier < 1.0 else ""
        return self.player.weapon.on_attack(dmg_dealt, eff)

    def execute_player_attack(self) -> bool:
        cancel_attack = False
        for r in self.player.relic_effects:
            if not r.on_before_attack(self): cancel_attack = True
        if cancel_attack: return False

        multiplier = MULTIPLIERS.get(self.player.weapon.element, {}).get(self.enemy.element, 1.0)
        for r in self.player.relic_effects: multiplier = r.modify_multiplier(multiplier)
        
        was_focused = self.focused_attack
        if self.focused_attack:
            hit_chance = 100
            dmg_dealt = int(max(1, self.player.get_total_atk() + random.randint(-1, 2)) * multiplier * 2)
            eff = f"{Colors.GREEN}[CRITICO!]{Colors.RESET} " + (f"{Colors.GREEN}[SUPER EFFICACE!]{Colors.RESET}" if multiplier > 1.0 else "")
            self.focused_attack = False
        else:
            hit_chance = self._calc_hit_chance(multiplier)
            dmg_dealt, eff = self._calc_base_damage(multiplier)
        
        if self.enemy.is_boss and is_book_unlocked("bestiario", PROFILE_MANAGER._data):
            dmg_dealt = int(dmg_dealt * 1.1)

        if self.player.accessory and self.player.accessory.bonus_type == "crit_chance" and not was_focused:
            if random.randint(1, 100) <= self.player.accessory.bonus_value:
                dmg_dealt *= 2
                eff += f" {Colors.MAGENTA}[CRITICO!]{Colors.RESET}"

        if random.randint(1, 100) <= hit_chance:
            dmg_dealt = int(dmg_dealt * self.player.get_class_damage_multiplier())
            if multiplier > 1.0 and self.enemy.is_boss:
                if "super_effective_hits" not in self.player.run_tracker: self.player.run_tracker["super_effective_hits"] = 0
                self.player.run_tracker["super_effective_hits"] += 1
            
            for r in self.player.relic_effects:
                dmg_dealt, eff = r.on_attack(self, dmg_dealt, multiplier, eff)

            if self.resonance == "Tenebra":
                dmg_dealt += 5
                eff += f" {Colors.MAGENTA}[TENEBRA]{Colors.RESET}"
            
            self.enemy.hp -= dmg_dealt
            print(f"\n-> Colpisci con {self.player.weapon.name} infliggendo {Colors.CYAN}{dmg_dealt} danni!{Colors.RESET} {eff}")
            
            for r in self.player.relic_effects: r.on_attack_landed(self, multiplier)

            if self.player.accessory and self.player.accessory.bonus_type == "lifesteal":
                ls = self.player.accessory.bonus_value
                self.player.heal(ls)
                print(f"{Colors.RED}Il monile assorbe {ls} HP!{Colors.RESET}")
            if self.resonance == "Luce":
                self.player.heal(3)
                print(f"{Colors.YELLOW}✨ Risonanza di Luce: +3 HP!{Colors.RESET}")
            if self.resonance == "Fuoco":
                self.burn_dmg += 5
            
            self.player.on_attack_landed(dmg_dealt, multiplier)
        else:
            print(f"\n{Colors.YELLOW}-> Fallisci! {self.enemy.name} schiva.{Colors.RESET}")
        
        if self.enemy.hp <= 0:
            self.on_enemy_death()
            return False
        return True

    def execute_player_defense(self):
        self.is_defending = True
        if self.def_type == "counter":
            print(f"\n{Colors.BLUE}-> Sollevi la guardia, pronto a sfruttare l'attacco nemico!{Colors.RESET}")
            self.player.on_defense_started()
        elif self.def_type == "focus":
            self.focused_attack = True
            print(f"\n{Colors.BLUE}-> Studi il nemico nell'ombra. Il tuo prossimo attacco sarà devastante!{Colors.RESET}")
        elif self.def_type == "recovery":
            if self.player.cursed:
                print(f"\n{Colors.BLUE}-> Ti difendi, ma la Maledizione blocca il tuo recupero magico.{Colors.RESET}")
            else:
                heal_amt = max(1, self.player.max_hp // 20)
                self.player.heal(heal_amt)
                print(f"\n{Colors.BLUE}-> Evochi una barriera vitale. {Colors.GREEN}Recuperi {heal_amt} HP!{Colors.RESET}")

    def player_turn(self) -> bool:
        # I bonus di Risonanza devono restare attivi per tutto il combattimento
        self.player.temp_def = 5 if self.resonance == "Terra" else 0
        self.player.temp_dodge = 15 if self.resonance == "Vento" else 0
        self.is_defending = False

        self.def_type, self.def_txt = self.player.get_defense_action()

        prompt = f"\n{Colors.BOLD}--- ⚔️ IN COMBATTIMENTO ⚔️ ---{Colors.RESET}\nTu: {Colors.GREEN}{self.player.hp}/{self.player.max_hp} HP{Colors.RESET} | {self.enemy.name}: {Colors.RED}{self.enemy.hp} HP{Colors.RESET}"
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
            if action == "smoke_bomb":
                if self.enemy.is_boss:
                    print(f"\n{Colors.RED}-> Il fumo si dirada all'istante: impossibile fuggire dai Boss!{Colors.RESET}")
                    return True
                self.player.run_tracker["escapes"] += 1
                return False
            elif action == "fiala_caos":
                caos_dmg = random.randint(10, 100)
                self.enemy.hp -= caos_dmg
                print(f"{Colors.MAGENTA}Esplosione caotica: {caos_dmg} danni puri!{Colors.RESET}")
                if self.enemy.hp <= 0:
                    self.on_enemy_death()
                    return False
                return True
            elif action == "turn_used" or action == "antidote":
                clear_screen()
                return True
            else:
                return self.player_turn()
                
        elif idx == 3:
            from inventory_menu import show_player_stats
            show_player_stats(self.player)
            return self.player_turn()
            
        elif idx == 4:
            if self.enemy.is_boss:
                print(f"\n{Colors.RED}-> Impossibile fuggire dai Boss!{Colors.RESET}")
                return self.player_turn()
            
            f_chance = max(10, min(90, 20 + self.player.get_dodge() - self.enemy.base_dodge + (20 if PROFILE_MANAGER.get_perk("scarpisti", False) else 0)))
            if is_book_unlocked("diario_silas", PROFILE_MANAGER._data): f_chance += 5
            for r in self.player.relic_effects:
                mod = r.get_escape_modifier()
                if mod > 0: f_chance = mod
                
            if random.randint(1, 100) <= f_chance:
                print(f"\n{Colors.YELLOW}-> Sei riuscito a scappare!{Colors.RESET}")
                self.player.run_tracker["escapes"] += 1
                input("\nPremi INVIO...")
                return False
            else:
                print(f"\n{Colors.RED}-> Tentativo di fuga fallito!{Colors.RESET}")
                return True
        else:
            return self.player_turn()

    def _calc_enemy_hit_chance(self, en_multiplier: float) -> int:
        return max(10, min(100, BASE_HIT_CHANCE + self.enemy.base_acc - self.player.get_dodge() + (15 if en_multiplier > 1.0 else -20 if en_multiplier < 1.0 else 0)))

    def _calc_enemy_damage(self, en_multiplier: float) -> int:
        defense = self.player.armor.defense + self.player.temp_def
        if is_book_unlocked("cronache_ere", PROFILE_MANAGER._data): defense += 5
        dmg_taken = max(0, int((self.enemy.atk + random.randint(-1, 2)) * en_multiplier) - defense)
        if self.is_defending: dmg_taken //= 2
        for r in self.player.relic_effects: dmg_taken = r.on_take_damage(self, dmg_taken, en_multiplier)
        return dmg_taken

    def enemy_turn(self) -> bool:
        en_multiplier = MULTIPLIERS.get(self.enemy.element, {}).get(self.player.armor.element, 1.0)
        for r in self.player.relic_effects: en_multiplier = r.modify_multiplier(en_multiplier, is_defense=True)
        
        en_hit_chance = self._calc_enemy_hit_chance(en_multiplier)

        if random.randint(1, 100) <= en_hit_chance:
            dmg_taken = self._calc_enemy_damage(en_multiplier)
            if self.enemy.hp <= 0:
                self.on_enemy_death()
                return False
            
            en_eff = f"{Colors.RED}[Sei vulnerabile!]{Colors.RESET}" if en_multiplier > 1.0 else f"{Colors.GREEN}[Resisti!]{Colors.RESET}" if en_multiplier < 1.0 else ""
            
            if dmg_taken > 0: 
                self.boss_hit_taken = True
                dif = f"{Colors.BLUE}[DIFESA]{Colors.RESET}" if self.is_defending else ""
                print(f"<- {self.enemy.name} ti colpisce! Subisci {Colors.RED}{dmg_taken} danni{Colors.RESET}. {en_eff}{dif}")
                
                if getattr(self.enemy, 'status_inflict', None):
                    s_data = self.enemy.status_inflict
                    if random.randint(1, 100) <= s_data.get("chance", 100):
                        s_type = s_data["type"]
                        self.player.statuses[s_type] = max(self.player.statuses.get(s_type, 0), s_data["duration"])
                        print(f"{Colors.MAGENTA}Sei stato afflitto da {s_type.upper()}!{Colors.RESET}")
                
                reflect_total = 0
                if self.player.accessory and self.player.accessory.bonus_type == "reflect": reflect_total += self.player.accessory.bonus_value
                if reflect_total > 0:
                    self.enemy.hp -= reflect_total
                    print(f"{Colors.YELLOW}Riflessi {reflect_total} danni a {self.enemy.name}!{Colors.RESET}")
                    if self.enemy.hp <= 0:
                        self.on_enemy_death()
                        return False
                
                if self.is_defending and self.def_type == "counter":
                    self.enemy.hp -= dmg_taken
                    print(f"{Colors.YELLOW}   ⚔️ CONTRATTACCO! Restituisci {dmg_taken} danni a {self.enemy.name}!{Colors.RESET}")
                    if self.enemy.hp <= 0:
                        self.on_enemy_death()
                        return False
                
                alive = self.player.take_damage(dmg_taken)
                if not alive:
                    print(f"\n{Colors.RED}{Colors.BOLD}Sei caduto in battaglia contro {self.enemy.name}...{Colors.RESET}")
                    input("\nPremi INVIO per continuare...")
                    return False
            elif dmg_taken == 0:
                print(f"<- {self.enemy.name} attacca, ma la corazza blocca TUTTO! {en_eff}")
        else:
            print(f"{Colors.CYAN}<- {self.enemy.name} attacca... ma riesci a schivarlo!{Colors.RESET}")
        
        if self.burn_dmg > 0 and self.enemy.hp > 0:
            self.enemy.hp -= self.burn_dmg
            print(f"{Colors.RED}🔥 Risonanza di Fuoco: Ustione infligge {self.burn_dmg} danni!{Colors.RESET}")
            if self.enemy.hp <= 0:
                self.on_enemy_death()
                return False
        return True

def combat_room(player: Player, floor: int, enemy_instance: Enemy):
    session = CombatSession(player, floor, enemy_instance)
    session.start()

def mystery_room(player: Player, floor: int, active_pacts: List[str]):
    delay_print(f"\n{Colors.MAGENTA}--- LA STANZA DEL MISTERO ---{Colors.RESET}")
    print(f"❤️  HP: {Colors.GREEN}{player.hp}/{player.max_hp}{Colors.RESET} | 💰 Oro: {Colors.YELLOW}{player.gold}{Colors.RESET}\n")
    delay_print(f"{random.choice(GAME_DATA['lore']['mystery'])}", 0.03)
    time.sleep(1)

    outcome = random.choice(["hard", "easy", "trap", "empty"])

    if outcome == "hard":
        print(f"\n{Colors.RED}Dall'oscurità emerge un mostro eccezionalmente feroce!{Colors.RESET}")
        input("Premi INVIO per difenderti...")
        combat_room(player, floor, Enemy(floor, False, active_pacts, modifier="hard"))
    elif outcome == "easy":
        print(f"\n{Colors.CYAN}Scorgi un nemico ferito e confuso che vaga nella nebbia.{Colors.RESET}")
        input("Premi INVIO per attaccare...")
        combat_room(player, floor, Enemy(floor, False, active_pacts, modifier="easy"))
    elif outcome == "trap":
        trap_room(player, floor, active_pacts)
    else:
        print(f"\n{Colors.GREEN}La nebbia si dirada. La stanza è vuota. Tiri un sospiro di sollievo.{Colors.RESET}")
        input("Premi INVIO per proseguire...")

def _handle_event_action(player: Player, floor: int, action: str, msg: str, msg_alt: str, ev: dict, idx: int) -> bool:
    if action == "heal_max":
        player.max_hp += 10
        if not player.cursed: player.heal(player.max_hp); print(f"{Colors.GREEN}Senti un potere immenso! HP Ripristinati!{Colors.RESET}")
        else: print(f"{Colors.RED}L'acqua scivola via... la maledizione blocca la cura.{Colors.RESET}")
    elif action == "coin_toss":
        if player.gold >= 20:
            player.gold -= 20
            if random.random() > 0.5:
                r = get_random_relic(player)
                if r: player.add_relic(r)
                else: player.gold += 50; print(f"{Colors.YELLOW}{msg} (+50 Oro){Colors.RESET}")
            else: print(f"{Colors.YELLOW}{msg_alt}{Colors.RESET}")
        else: print(f"{Colors.RED}Oro insufficiente!{Colors.RESET}")
    elif action == "trade_weapon":
        if player.gold >= 50:
            player.gold -= 50
            drop = generate_weapon(floor + 2, True)
            player.inventory.append(drop); print(f"{Colors.MAGENTA}Ottieni: {drop.display_name}!{Colors.RESET}")
        else: print(f"{Colors.RED}Non hai abbastanza Oro.{Colors.RESET}")
    elif action == "trade_relic":
        print(f"{Colors.RED}{msg}{Colors.RESET}")
        alive = player.take_damage(30)
        if not alive:
            print(f"\n{Colors.RED}{Colors.BOLD}Il dissanguamento ti è stato fatale...{Colors.RESET}")
            return False
        r = get_random_relic(player)
        if r: player.add_relic(r)
    elif action == "blood_gold":
        g = 100 * 3 if player.midas else 100
        player.gold += g; print(f"{Colors.RED}{msg} (+{g} Oro){Colors.RESET}.")
        alive = player.take_damage(40)
        if not alive:
            print(f"\n{Colors.RED}{Colors.BOLD}Hai sacrificato troppa linfa vitale... Sei morto.{Colors.RESET}")
            return False
    elif action == "fight_elite" or action.startswith("unlock_npc_fight"):
        print(f"{Colors.RED}{msg}{Colors.RESET}")
        e = Enemy(floor + 5, True, player.active_pacts)
        input("Premi INVIO per combattere..."); combat_room(player, floor, e)
        if player.hp <= 0: return False
        if action.startswith("unlock_npc_fight_") and player.hp > 0:
            npc_name = action.replace("unlock_npc_fight_", "")
            PROFILE_MANAGER.unlock_npc(npc_name)
            PROFILE_MANAGER.save()
            print(f"\n{Colors.GREEN}Il mostro è sconfitto! Raccogli le chiavi e liberi il prigioniero. Ti ringrazia e scappa verso il Campo Base.{Colors.RESET}")
    elif action.startswith("unlock_npc_"):
        if action.startswith("unlock_npc_fight"): return True
        npc_name = action.replace("unlock_npc_", "")
        alive = player.take_damage(40)
        if not alive:
            print(f"\n{Colors.RED}{Colors.BOLD}Il dissanguamento ti è stato fatale...{Colors.RESET}")
            return False
        print(f"{Colors.GREEN}{msg}{Colors.RESET}")
        PROFILE_MANAGER.unlock_npc(npc_name)
        PROFILE_MANAGER.save()
    elif action == "give_quest_item":
        q_item = ev["choices"][idx].get("item_id", "")
        if q_item and q_item not in player.quest_items:
            player.quest_items.append(q_item)
            print(f"{Colors.YELLOW}{msg}{Colors.RESET}")
    elif action == "use_quest_item":
        print(f"{Colors.YELLOW}{msg}{Colors.RESET}")
        if ev["choices"][idx].get("reward_weapon", False):
            drop = generate_weapon(floor + 3, True)
            player.inventory.append(drop); print(f"{Colors.MAGENTA}Trovi Arma Epica: {drop.display_name}!{Colors.RESET}")
        rg = ev["choices"][idx].get("reward_gold", 0)
        if rg > 0:
            player.gold += rg
            print(f"{Colors.YELLOW}Ottieni {rg} Oro!{Colors.RESET}")
    elif action == "none":
        print(f"{Colors.CYAN}{msg}{Colors.RESET}")
    
    return True

def event_room(player: Player, event_id: str, floor: int):
    ev = GAME_DATA["events"][event_id]
    clear_screen()
    
    first_time = True
    
    while True:
        if first_time:
            print(f"\n{Colors.MAGENTA}{Colors.BOLD}--- {ev['title']} ---{Colors.RESET}")
            print(f"❤️  HP: {Colors.GREEN}{player.hp}/{player.max_hp}{Colors.RESET} | 💰 Oro: {Colors.YELLOW}{player.gold}{Colors.RESET}\n")
            delay_print(ev["text"], 0.03)
            prompt = "\nScegli:"
            first_time = False
        else:
            clear_screen()
            prompt = f"\n{Colors.MAGENTA}{Colors.BOLD}--- {ev['title']} ---{Colors.RESET}\n❤️  HP: {Colors.GREEN}{player.hp}/{player.max_hp}{Colors.RESET} | 💰 Oro: {Colors.YELLOW}{player.gold}{Colors.RESET}\n\n{ev['text']}\nScegli:"
            
        valid_choices = []
        options = []
        
        for i, c in enumerate(ev["choices"]):
            req_item = c.get("requires_item", "")
            if req_item and req_item not in player.quest_items:
                options.append(f"{Colors.RED}{c['text']} (Non possiedi l'oggetto richiesto){Colors.RESET}")
            else:
                valid_choices.append(i)
                options.append(c['text'])
                
        idx = interactive_menu(options, prompt)
        
        if idx in valid_choices:
            action = ev["choices"][idx]["action"]
            msg = ev["choices"][idx].get("msg", "")
            msg_alt = ev["choices"][idx].get("msg_alt", "")
            
            if not _handle_event_action(player, floor, action, msg, msg_alt, ev, idx): return
            
            input("\nPremi INVIO per proseguire...")
            return

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
                        print(f"{Colors.GREEN}Hai comprato {item.name}!{Colors.RESET}"); items_for_sale.pop(idx_compra); time.sleep(1)
                        for i_idx, remaining_item in enumerate(items_for_sale):
                            items_for_sale[i_idx].value = int(remaining_item.value * 1.1)
                    else: print(f"{Colors.RED}Oro insufficiente!{Colors.RESET}"); time.sleep(1)
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
                    player.gold += gain; print(f"{Colors.GREEN}Hai venduto {item.name} per {gain} oro!{Colors.RESET}"); time.sleep(1)
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
            print(f"{Colors.GREEN}Ti riposi profondamente!{Colors.RESET}"); input("\nPremi INVIO..."); break
        elif idx == 1:
            if player.gold >= 50:
                player.gold -= 50; player.weapon.atk += 3
                print(f"{Colors.GREEN}Arma migliorata: {player.weapon.atk} ATK!{Colors.RESET}"); input("\nPremi INVIO..."); break
            else: print(f"{Colors.RED}Oro insufficiente.{Colors.RESET}"); time.sleep(1.5)
        elif idx == 2:
            while True:
                clear_screen()
                prompt_forge = f"\n{Colors.MAGENTA}--- FUSIONE EQUIPAGGIAMENTO ---{Colors.RESET}\n"
                equips =[i for i in player.inventory if i.type in["weapon", "armor"]]
                if len(equips) < 2: 
                    print(prompt_forge + "Hai bisogno di almeno 2 armi/armature nello zaino per usare l'Altare."); input("Premi INVIO..."); break
                
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
                        if not it1.name.startswith("Perfetto "): it1.name = f"Perfetto {it1.name}"
                        it1.refresh_display_name()
                        player.run_tracker["fusions"] += 1
                        print(f"{Colors.GREEN}FUSIONE RIUSCITA! Il primo oggetto ha assorbito il secondo.{Colors.RESET}")
                        input("Premi INVIO per continuare...")
                        return 
                    else: print(f"{Colors.RED}Puoi fondere solo oggetti dello stesso tipo!{Colors.RESET}"); time.sleep(1.5)
                else: print(f"{Colors.RED}Selezione non valida o oggetto uguale.{Colors.RESET}"); time.sleep(1.5)
        elif options[idx].startswith(f"{Colors.CYAN}Purifica"):
            cursed_items = [item for item in [player.weapon, player.armor, player.accessory] if item and getattr(item, 'is_cursed', False)]
            if player.gold < 100:
                print(f"{Colors.RED}Oro insufficiente per il rituale di purificazione (Richiede 100 Oro).{Colors.RESET}")
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
                        print(f"{Colors.GREEN}Il rituale ha successo! La maledizione è spezzata.{Colors.RESET}")
                        input("\nPremi INVIO...")
                        return

def treasure_room(player: Player, floor: int):
    delay_print(f"\n{Colors.YELLOW}{random.choice(GAME_DATA['lore']['treasure'])}{Colors.RESET}")
    gold = random.randint(30, 60) + (floor * 10)
    g = player.calculate_gold_gain(gold)
    
    player.gold += g
    print(f"{Colors.GREEN}Trovate {g} monete d'oro!{Colors.RESET}")
    
    if random.random() < 0.15:
        r = get_random_relic(player)
        if r: player.add_relic(r)
    elif random.random() < 0.20:
        drop = generate_accessory(floor)
        print(f"C'era anche: {Colors.CYAN}{drop.display_name}{Colors.RESET}!"); player.inventory.append(drop)
    elif random.random() > 0.4:
        drop = generate_potion(floor)
        print(f"C'era anche: {Colors.CYAN}{drop.display_name}{Colors.RESET}!"); player.inventory.append(drop)
    input("\nPremi INVIO per continuare...")

def trap_room(player: Player, floor: int, active_pacts: List[str]):
    delay_print(f"\n{random.choice(GAME_DATA['lore']['trap'])}")
    delay_print(f"{Colors.RED}È UNA TRAPPOLA!{Colors.RESET}", 0.05)
    
    if random.randint(1, 100) <= player.get_dodge(): 
        print(f"{Colors.GREEN}Schivi il meccanismo! Ne esci illeso!{Colors.RESET}")
    else:
        dmg = random.randint(15, 30) + (floor * 3)
        if "trappole" in active_pacts: dmg *= 2
        for r in player.relic_effects: dmg = r.modify_trap_damage(dmg)
        print(f"{Colors.RED}Subisci {dmg} danni puri.{Colors.RESET}")
        alive = player.take_damage(dmg)
        print(f"(HP: {player.hp}/{player.max_hp})")
        if not alive:
            print(f"\n{Colors.RED}{Colors.BOLD}La trappola ti è stata fatale...{Colors.RESET}")
            input("\nPremi INVIO per continuare...")
            return
            
    if random.randint(1, 100) <= 20:
        print(f"\n{Colors.GREEN}Tra gli ingranaggi spezzati della trappola noti qualcosa brillare...{Colors.RESET}")
        roll = random.random()
        if roll > 0.7: drop = generate_accessory(floor)
        elif roll > 0.5: drop = generate_weapon(floor, False)
        else: drop = generate_armor(floor, False)
        print(f"{Colors.MAGENTA}Hai trovato: {drop.display_name}!{Colors.RESET}")
        player.inventory.append(drop)

    input("\nPremi INVIO per continuare...")

