import random
import time
from typing import List
from ui import Colors, clear_screen, delay_print, get_choice
from data_manager import GAME_DATA, PROFILE, MULTIPLIERS, get_element_icon
from archive import is_book_unlocked
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
                self.player.hp -= 2
                print(f"{Colors.MAGENTA}La Maledizione dell'equipaggiamento drena 2 HP! ({self.player.hp}/{self.player.max_hp}){Colors.RESET}")
            if self.player.has_curse("gold_drain") and self.player.gold > 0:
                self.player.gold = max(0, self.player.gold - 5)
                print(f"{Colors.MAGENTA}La Maledizione divora 5 Oro! (Oro: {self.player.gold}){Colors.RESET}")
                
            expired = []
            for status, duration in self.player.statuses.items():
                if status == "poison":
                    dmg = 3 + self.floor
                    self.player.hp -= dmg
                    print(f"{Colors.GREEN}Il veleno ti infligge {dmg} danni! ({self.player.hp}/{self.player.max_hp}){Colors.RESET}")
                elif status == "bleed":
                    dmg = max(1, int(self.player.max_hp * 0.05))
                    self.player.hp -= dmg
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
        if not self.enemy.is_boss and random.random() < 0.15:
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
        
        g_drop = self.enemy.gold_drop * 3 if self.player.midas else self.enemy.gold_drop
        for r in self.player.relic_effects: g_drop = r.on_gold_gain(self.player, g_drop)
        g_drop = int(g_drop * (1 + PROFILE["perks"].get("banca_anima_lvl", 0) * 0.05))
        if is_book_unlocked("diario_silas", PROFILE): g_drop = int(g_drop * 1.05)
        
        self.player.gold += g_drop
        print(f"Ottieni {Colors.YELLOW}{g_drop} oro{Colors.RESET}.")
        self.player.gain_exp(self.enemy.exp_drop)
        
        for r in self.player.relic_effects: r.on_enemy_death(self)
        
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

    def execute_player_attack(self) -> bool:
        cancel_attack = False
        for r in self.player.relic_effects:
            if not r.on_before_attack(self): cancel_attack = True
        if cancel_attack: return False

        multiplier = MULTIPLIERS.get(self.player.weapon.element, {}).get(self.enemy.element, 1.0)
        for r in self.player.relic_effects: multiplier = r.modify_multiplier(multiplier)
        
        if self.focused_attack:
            hit_chance = 100
            dmg_dealt = int(max(1, self.player.get_total_atk() + random.randint(-1, 2)) * multiplier * 2)
            eff = f"{Colors.GREEN}[CRITICO!]{Colors.RESET} " + (f"{Colors.GREEN}[SUPER EFFICACE!]{Colors.RESET}" if multiplier > 1.0 else "")
            self.focused_attack = False
        else:
            hit_chance = max(10, min(100, 85 + self.player.base_acc - self.enemy.base_dodge + (15 if multiplier > 1.0 else -20 if multiplier < 1.0 else 0)))
            if "Ascia del Boia" in self.player.weapon.name: hit_chance -= 15
            dmg_dealt = int(max(1, self.player.get_total_atk() + random.randint(-1, 2)) * multiplier)
            eff = f"{Colors.GREEN}[SUPER EFFICACE!]{Colors.RESET}" if multiplier > 1.0 else f"{Colors.RED}[Poco efficace...]{Colors.RESET}" if multiplier < 1.0 else ""
            if "Ascia del Boia" in self.player.weapon.name and random.random() < 0.35:
                dmg_dealt *= 2
                eff += f" {Colors.MAGENTA}[CRITICO DELL'ASCIA!]{Colors.RESET}"
        
        if self.enemy.is_boss and is_book_unlocked("bestiario", PROFILE):
            dmg_dealt = int(dmg_dealt * 1.1)

        if self.player.accessory and self.player.accessory.bonus_type == "crit_chance" and not self.focused_attack:
            if random.randint(1, 100) <= self.player.accessory.bonus_value:
                dmg_dealt *= 2
                eff += f" {Colors.MAGENTA}[CRITICO!]{Colors.RESET}"

        if random.randint(1, 100) <= hit_chance:
            if self.player.class_id == "5" and PROFILE["class_lvl"].get("5", 1) >= 2 and self.player.hp < self.player.max_hp * 0.3:
                dmg_dealt = int(dmg_dealt * 1.5)
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
                self.player.hp = min(self.player.max_hp, self.player.hp + ls)
                print(f"{Colors.RED}Il monile assorbe {ls} HP!{Colors.RESET}")
            if self.resonance == "Luce":
                self.player.hp = min(self.player.max_hp, self.player.hp + 3)
                print(f"{Colors.YELLOW}✨ Risonanza di Luce: +3 HP!{Colors.RESET}")
            if self.resonance == "Fuoco":
                self.burn_dmg += 5
            
            if not self.player.cursed:
                if self.player.mage_lifesteal and multiplier > 1.0:
                    h = max(1, dmg_dealt // 10)
                    self.player.hp = min(self.player.max_hp, self.player.hp + h)
                    print(f"{Colors.MAGENTA}Sintonia: Assorbi {h} HP!{Colors.RESET}")
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
            if self.player.class_id == "4" and PROFILE["class_lvl"].get("4", 1) >= 2:
                self.player.hp = min(self.player.max_hp, self.player.hp + 3)
                print(f"{Colors.GREEN}Baluardo della Fede: Recuperi 3 HP!{Colors.RESET}")
        elif self.def_type == "focus":
            self.focused_attack = True
            print(f"\n{Colors.BLUE}-> Studi il nemico nell'ombra. Il tuo prossimo attacco sarà devastante!{Colors.RESET}")
        elif self.def_type == "recovery":
            if self.player.cursed:
                print(f"\n{Colors.BLUE}-> Ti difendi, ma la Maledizione blocca il tuo recupero magico.{Colors.RESET}")
            else:
                heal_amt = max(1, self.player.max_hp // 20)
                self.player.hp = min(self.player.max_hp, self.player.hp + heal_amt)
                print(f"\n{Colors.BLUE}-> Evochi una barriera vitale. {Colors.GREEN}Recuperi {heal_amt} HP!{Colors.RESET}")

    def player_turn(self) -> bool:
        self.player.temp_def = 0
        self.player.temp_dodge = 0
        self.is_defending = False

        if self.player.role in ["Guerriero", "Berserker"]:
            self.def_type, self.def_txt = "counter", "Difesa Aggressiva (Dimezza danni e Contrattacca)"
        elif self.player.role == "Ladro":
            self.def_type, self.def_txt = "focus", "Concentrazione (Dimezza danni, prossimo colpo Critico 100%)"
        else:
            self.def_type, self.def_txt = "recovery", "Riparo Magico (Dimezza danni e Cura 5% HP)"

        print(f"\n{Colors.BOLD}--- ⚔️ IN COMBATTIMENTO ⚔️ ---{Colors.RESET}")
        print(f"Tu: {Colors.GREEN}{self.player.hp}/{self.player.max_hp} HP{Colors.RESET} | {self.enemy.name}: {Colors.RED}{self.enemy.hp} HP{Colors.RESET}")
        print("1. Attacca")
        print(f"2. {self.def_txt}")
        print("3. Apri Inventario (Usa oggetto = Costa Turno)")
        print("4. Tenta la Fuga")
        
        choice = get_choice("Cosa fai? > ")
        
        if choice in ['1', '2', '3', '4']: clear_screen()
            
        if choice == '1':
            return self.execute_player_attack()
                
        elif choice == '2':
            self.execute_player_defense()
            return True
                    
        elif choice == '3':
            action = show_inventory_menu(self.player, in_combat=True)
            if action == "smoke_bomb":
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
            elif action == "turn_used":
                return True
            else:
                return self.player_turn()
            
        elif choice == '4':
            if self.enemy.is_boss:
                print(f"\n{Colors.RED}-> Impossibile fuggire dai Boss!{Colors.RESET}")
                return self.player_turn()
            
            f_chance = max(10, min(90, 20 + self.player.get_dodge() - self.enemy.base_dodge + (20 if PROFILE["perks"].get("scarpisti", False) else 0)))
            if is_book_unlocked("diario_silas", PROFILE): f_chance += 5
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

    def enemy_turn(self) -> bool:
        en_multiplier = MULTIPLIERS.get(self.enemy.element, {}).get(self.player.armor.element, 1.0)
        for r in self.player.relic_effects: en_multiplier = r.modify_multiplier(en_multiplier)
        
        en_hit_chance = max(10, min(100, 85 + self.enemy.base_acc - self.player.get_dodge() + (15 if en_multiplier > 1.0 else -20 if en_multiplier < 1.0 else 0)))

        if random.randint(1, 100) <= en_hit_chance:
            defense = self.player.armor.defense + self.player.temp_def
            if is_book_unlocked("cronache_ere", PROFILE): defense += 5
            dmg_taken = max(0, int((self.enemy.atk + random.randint(-1, 2)) * en_multiplier) - defense)
            if self.is_defending:
                dmg_taken //= 2
            
            for r in self.player.relic_effects: dmg_taken = r.on_take_damage(self, dmg_taken, en_multiplier)
            
            en_eff = f"{Colors.RED}[Sei vulnerabile!]{Colors.RESET}" if en_multiplier > 1.0 else f"{Colors.GREEN}[Resisti!]{Colors.RESET}" if en_multiplier < 1.0 else ""
            
            if dmg_taken > 0: 
                self.boss_hit_taken = True
                self.player.hp -= dmg_taken
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
                
                if self.player.hp <= 0 and self.player.benedetto_save:
                    self.player.hp = 1
                    self.player.benedetto_save = False
                    print(f"{Colors.YELLOW}La Benedizione ti salva dal colpo letale!{Colors.RESET}")
                    
                if self.player.hp <= 0:
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
    elif outcome == "empty":
        print(f"\n{Colors.GREEN}La nebbia si dirada. La stanza è vuota. Tiri un sospiro di sollievo.{Colors.RESET}")
        input("Premi INVIO per proseguire...")

def event_room(player: Player, event_id: str, floor: int):
    ev = GAME_DATA["events"][event_id]
    clear_screen()
    print(f"\n{Colors.MAGENTA}{Colors.BOLD}--- {ev['title']} ---{Colors.RESET}")
    print(f"❤️  HP: {Colors.GREEN}{player.hp}/{player.max_hp}{Colors.RESET} | 💰 Oro: {Colors.YELLOW}{player.gold}{Colors.RESET}\n")
    delay_print(ev["text"], 0.03)
    
    while True:
        print("\nScegli:")
        valid_choices = []
        for i, c in enumerate(ev["choices"]):
            req_item = c.get("requires_item", "")
            if req_item and req_item not in player.quest_items:
                print(f"{Colors.RED}{i+1}. {c['text']} (Non possiedi l'oggetto richiesto){Colors.RESET}")
            else:
                valid_choices.append(i)
                print(f"{i+1}. {c['text']}")
                
        choice = get_choice("> ")
        try:
            idx = int(choice) - 1
            if idx in valid_choices:
                action = ev["choices"][idx]["action"]
                msg = ev["choices"][idx].get("msg", "")
                msg_alt = ev["choices"][idx].get("msg_alt", "")
                
                if action == "heal_max":
                    player.max_hp += 10
                    if not player.cursed: player.hp = player.max_hp; print(f"{Colors.GREEN}Senti un potere immenso! HP Ripristinati!{Colors.RESET}")
                    else: print(f"{Colors.RED}L'acqua scivola via... la maledizione blocca la cura.{Colors.RESET}")
                elif action == "coin_toss":
                    if player.gold >= 20:
                        player.gold -= 20
                        if random.random() > 0.5:
                            r = get_random_relic(player)
                            if r: player.add_relic(r)
                            else: player.gold += 50; print(f"{Colors.YELLOW}{msg} (+50 Oro){Colors.RESET}")
                        else: print(f"{Colors.YELLOW}{msg_alt}{Colors.RESET}")
                    else: print(f"{Colors.RED}Oro insufficiente!{Colors.RESET}"); continue
                elif action == "trade_weapon":
                    if player.gold >= 50:
                        player.gold -= 50
                        drop = generate_weapon(floor + 2, True)
                        player.inventory.append(drop); print(f"{Colors.MAGENTA}Ottieni: {drop.display_name}!{Colors.RESET}")
                    else: print(f"{Colors.RED}Non hai abbastanza Oro.{Colors.RESET}"); continue
                elif action == "trade_relic":
                    player.hp -= 30
                    print(f"{Colors.RED}{msg}{Colors.RESET}")
                    if player.hp <= 0 and player.benedetto_save:
                        player.hp = 1; player.benedetto_save = False
                        print(f"{Colors.YELLOW}La Benedizione ti salva dal colpo letale!{Colors.RESET}")
                    if player.hp <= 0:
                        print(f"\n{Colors.RED}{Colors.BOLD}Il dissanguamento ti è stato fatale...{Colors.RESET}")
                        input("\nPremi INVIO per continuare...")
                        return
                    r = get_random_relic(player)
                    if r: player.add_relic(r)
                elif action == "blood_gold":
                    player.hp -= 40
                    g = 100 * 3 if player.midas else 100
                    player.gold += g; print(f"{Colors.RED}{msg} (+{g} Oro){Colors.RESET}.")
                    if player.hp <= 0 and player.benedetto_save:
                        player.hp = 1; player.benedetto_save = False
                        print(f"{Colors.YELLOW}La Benedizione ti salva dal colpo letale!{Colors.RESET}")
                    if player.hp <= 0:
                        print(f"\n{Colors.RED}{Colors.BOLD}Hai sacrificato troppa linfa vitale... Sei morto.{Colors.RESET}")
                        input("\nPremi INVIO per continuare...")
                        return
                elif action in ["fight_elite", "unlock_npc_fight"]:
                    print(f"{Colors.RED}{msg}{Colors.RESET}")
                    e = Enemy(floor + 5, True, player.active_pacts) # Elite
                    input("Premi INVIO per combattere..."); combat_room(player, floor, e)
                    if player.hp <= 0: return 
                    if action == "unlock_npc_fight" and player.hp > 0:
                        if "npc_unlocked" not in PROFILE: PROFILE["npc_unlocked"] = {}
                        PROFILE["npc_unlocked"]["speziale"] = True
                        from data_manager import save_profile
                        save_profile(PROFILE)
                        print(f"\n{Colors.GREEN}Il mostro è sconfitto! Raccogli le chiavi e liberi lo Speziale. Ti ringrazia e scappa verso il Campo Base.{Colors.RESET}")
                elif action == "unlock_npc_speziale":
                    player.hp -= 40
                    if player.hp <= 0 and player.benedetto_save:
                        player.hp = 1; player.benedetto_save = False
                        print(f"{Colors.YELLOW}La Benedizione ti salva dal colpo letale!{Colors.RESET}")
                    if player.hp <= 0:
                        print(f"\n{Colors.RED}{Colors.BOLD}Il dissanguamento ti è stato fatale...{Colors.RESET}")
                        input("\nPremi INVIO per continuare...")
                        return
                    print(f"{Colors.GREEN}{msg}{Colors.RESET}")
                    if "npc_unlocked" not in PROFILE: PROFILE["npc_unlocked"] = {}
                    PROFILE["npc_unlocked"]["speziale"] = True
                    from data_manager import save_profile
                    save_profile(PROFILE)
                elif action == "give_quest_item":
                    q_item = ev["choices"][idx].get("item_id", "")
                    if q_item and q_item not in player.quest_items:
                        player.quest_items.append(q_item)
                        print(f"{Colors.YELLOW}{msg}{Colors.RESET}")
                elif action == "use_quest_item":
                    q_item = ev["choices"][idx].get("item_id", "")
                    # Already checked for possession via valid_choices
                    print(f"{Colors.YELLOW}{msg}{Colors.RESET}")
                    if ev["choices"][idx].get("reward_weapon", False):
                        drop = generate_weapon(floor + 3, True)
                        player.inventory.append(drop); print(f"{Colors.MAGENTA}Trovi Arma Epica: {drop.display_name}!{Colors.RESET}")
                    rg = ev["choices"][idx].get("reward_gold", 0)
                    if rg > 0:
                        player.gold += rg
                        print(f"{Colors.YELLOW}Ottieni {rg} Oro!{Colors.RESET}")
                elif action == "none": print(f"{Colors.CYAN}{msg}{Colors.RESET}")
                
                input("\nPremi INVIO per proseguire...")
                return
            else:
                print(f"{Colors.RED}Selezione non valida o bloccata.{Colors.RESET}"); continue
        except ValueError: pass

def vendor_room(player: Player, floor: int):
    delay_print(f"\n{random.choice(GAME_DATA['lore']['vendor'])}")
    items_for_sale =[generate_weapon(floor + 1), generate_armor(floor + 1), generate_accessory(floor), generate_potion(floor), generate_potion(floor)]
    discount = 1.0 - (PROFILE["perks"]["discount_lvl"] * 0.10)
    for i in items_for_sale: 
        i.value = max(1, int(i.value * discount))
        if "inflazione" in player.active_pacts: i.value = int(i.value * 2)

    while True:
        clear_screen()
        print(f"\n{Colors.YELLOW}[ 💰 MERCANTE ] | Tuo Oro: {player.gold}{Colors.RESET}")
        if PROFILE["perks"]["discount_lvl"] > 0: print(f"{Colors.GREEN}(Sconto del {PROFILE['perks']['discount_lvl']*10}%!){Colors.RESET}")
        print("1. Guarda Merce (Compra)")
        print("2. Mostra Zaino (Vendi)")
        print("0. Saluta ed esci")
        action = get_choice("Scegli > ")
        
        if action == '1':
            while True:
                clear_screen()
                print(f"\n{Colors.CYAN}--- NEGOZIO (COMPRA) --- Tuo Oro: {player.gold}{Colors.RESET}")
                for i, item in enumerate(items_for_sale):
                    tipo = "Arma" if item.type=="weapon" else "Armatura" if item.type=="armor" else "Monile" if item.type=="accessory" else "Pozione"
                    print(f"{i+1}. [{tipo}] {item.display_name} - Prezzo: {Colors.YELLOW}{item.value} Oro{Colors.RESET}")
                print("0. Indietro")
                buy_choice = get_choice("Cosa compri? > ")
                if buy_choice == '0': break
                try:
                    idx = int(buy_choice) - 1
                    if 0 <= idx < len(items_for_sale):
                        item = items_for_sale[idx]
                        if player.gold >= item.value:
                            player.gold -= item.value; player.inventory.append(item)
                            if "gold_spent" not in player.run_tracker: player.run_tracker["gold_spent"] = 0
                            player.run_tracker["gold_spent"] += item.value
                            print(f"{Colors.GREEN}Hai comprato {item.name}!{Colors.RESET}"); items_for_sale.pop(idx); time.sleep(1)
                            for i_idx, remaining_item in enumerate(items_for_sale):
                                items_for_sale[i_idx].value = int(remaining_item.value * 1.1)
                        else: print(f"{Colors.RED}Oro insufficiente!{Colors.RESET}"); time.sleep(1)
                except ValueError: pass
        elif action == '2':
            while True:
                clear_screen()
                print(f"\n{Colors.CYAN}--- NEGOZIO (VENDI) ---{Colors.RESET}")
                if not player.inventory: print("Non hai nulla nello zaino da vendere.")
                else:
                    for i, item in enumerate(player.inventory):
                        print(f"{i+1}. {item.display_name} - Val di vendita: {Colors.YELLOW}{max(1, item.value // 2)} Oro{Colors.RESET}")
                print("0. Indietro")
                sell_choice = get_choice("Cosa vendi? > ")
                if sell_choice == '0': break
                try:
                    idx = int(sell_choice) - 1
                    if 0 <= idx < len(player.inventory):
                        item = player.inventory.pop(idx); gain = max(1, item.value // 2)
                        gain = int(gain * (1 + (PROFILE["perks"].get("riciclatore_lvl", 0) * 0.10)))
                        player.gold += gain; print(f"{Colors.GREEN}Hai venduto {item.name} per {gain} oro!{Colors.RESET}"); time.sleep(1)
                except ValueError: pass
        elif action == '0': break

def campfire_room(player: Player, floor: int):
    delay_print(f"\n{Colors.YELLOW}{random.choice(GAME_DATA['lore']['campfire'])}{Colors.RESET}")
    while True:
        clear_screen()
        print(f"\n{Colors.YELLOW}[ 🔥 FALÒ E FORGIA ] | Tuo Oro: {player.gold} | HP: {player.hp}/{player.max_hp}{Colors.RESET}")
        print("1. Riposa (Recupera 50% HP, il falò si spegnerà)")
        print(f"2. Affila Arma Base (Paga {Colors.YELLOW}50 Oro{Colors.RESET} per +3 ATK, il falò si spegnerà)")
        print(f"3. {Colors.MAGENTA}Altare dell'Evoluzione{Colors.RESET} (Fondi due armi/armature per potenziarle)")
        if any(getattr(item, 'is_cursed', False) for item in [player.weapon, player.armor, player.accessory] if item):
            print(f"4. {Colors.CYAN}Purifica Maledizione{Colors.RESET} (Paga {Colors.YELLOW}100 Oro{Colors.RESET} per rimuovere il malus da un pezzo equipaggiato)")
        print("0. Prosegui")
        
        action = get_choice("Scegli > ")
        if action == '1':
            player.run_tracker["rested"] = True
            player.hp = min(player.max_hp, player.hp + player.max_hp // 2)
            print(f"{Colors.GREEN}Ti riposi profondamente!{Colors.RESET}"); input("\nPremi INVIO..."); break
        elif action == '2':
            if player.gold >= 50:
                player.gold -= 50; player.weapon.atk += 3
                print(f"{Colors.GREEN}Arma migliorata: {player.weapon.atk} ATK!{Colors.RESET}"); input("\nPremi INVIO..."); break
            else: print(f"{Colors.RED}Oro insufficiente.{Colors.RESET}"); time.sleep(1.5)
        elif action == '3':
            while True:
                clear_screen()
                print(f"\n{Colors.MAGENTA}--- FUSIONE EQUIPAGGIAMENTO ---{Colors.RESET}")
                equips =[i for i in player.inventory if i.type in["weapon", "armor"]]
                if len(equips) < 2: print("Hai bisogno di almeno 2 armi/armature nello zaino per usare l'Altare."); input("Premi INVIO..."); break
                
                for i, item in enumerate(equips):
                    stat = f"+{item.atk} ATK" if item.type == "weapon" else f"+{item.defense} DEF"
                    print(f"{i+1}.[{item.type.upper()}] {item.display_name} {stat} (Lv.{item.level})")
                print("0. Indietro")
                
                c1 = get_choice("Seleziona il PRIMO oggetto (Base) > ")
                if c1 == '0': break
                c2 = get_choice("Seleziona il SECONDO oggetto (Sacrificio) > ")
                if c2 == '0': break
                
                try:
                    i1, i2 = int(c1)-1, int(c2)-1
                    if i1 != i2 and 0 <= i1 < len(equips) and 0 <= i2 < len(equips):
                        it1, it2 = equips[i1], equips[i2]
                        if it1.type == it2.type:
                            player.inventory.remove(it2)
                            if it1.type == "weapon": it1.atk += max(1, it2.atk // 2)
                            else: it1.defense += max(1, it2.defense // 2)
                            it1.level += 1
                            it1.display_name = f"Perfetto {it1.name.split('[')[0].strip()}[{get_element_icon(it1.element)}]"
                            player.run_tracker["fusions"] += 1
                            print(f"{Colors.GREEN}FUSIONE RIUSCITA! Il primo oggetto ha assorbito il secondo.{Colors.RESET}")
                            input("Premi INVIO per continuare...")
                            return 
                        else: print(f"{Colors.RED}Puoi fondere solo oggetti dello stesso tipo!{Colors.RESET}"); time.sleep(1.5)
                    else: print(f"{Colors.RED}Selezione non valida.{Colors.RESET}"); time.sleep(1.5)
                except ValueError: pass
        elif action == '4':
            cursed_items = [item for item in [player.weapon, player.armor, player.accessory] if item and getattr(item, 'is_cursed', False)]
            if not cursed_items:
                print(f"{Colors.YELLOW}Non hai equipaggiamenti maledetti addosso.{Colors.RESET}")
                time.sleep(1.5)
            elif player.gold < 100:
                print(f"{Colors.RED}Oro insufficiente per il rituale di purificazione (Richiede 100 Oro).{Colors.RESET}")
                time.sleep(1.5)
            else:
                while True:
                    clear_screen()
                    print(f"\n{Colors.CYAN}--- PURIFICAZIONE ---{Colors.RESET} Tuo Oro: {player.gold}")
                    for i, item in enumerate(cursed_items):
                        print(f"{i+1}. {item.display_name} (Malus: {item.curse_effect})")
                    print("0. Annulla")
                    c = get_choice("Quale oggetto purificare? > ")
                    if c == '0': break
                    try:
                        idx = int(c) - 1
                        if 0 <= idx < len(cursed_items):
                            player.gold -= 100
                            target_item = cursed_items[idx]
                            target_item.is_cursed = False
                            target_item.curse_effect = ""
                            target_item.display_name = target_item.display_name.replace(f"{Colors.MAGENTA}[MALEDETTO]{Colors.RESET} ", "")
                            print(f"{Colors.GREEN}Il rituale ha successo! La maledizione è spezzata.{Colors.RESET}")
                            input("\nPremi INVIO...")
                            return
                        else: print(f"{Colors.RED}Selezione non valida.{Colors.RESET}"); time.sleep(1.5)
                    except ValueError: pass
        elif action == '0': break

def treasure_room(player: Player, floor: int):
    delay_print(f"\n{Colors.YELLOW}{random.choice(GAME_DATA['lore']['treasure'])}{Colors.RESET}")
    gold = random.randint(30, 60) + (floor * 10)
    g = gold * 3 if player.midas else gold
    for r in player.relic_effects: g = r.on_gold_gain(player, g)
    g = int(g * (1 + PROFILE["perks"].get("banca_anima_lvl", 0) * 0.05))
    
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
        player.hp -= dmg
        if player.hp == 1: player.run_tracker["1_hp_survive"] = True
        print(f"{Colors.RED}Subisci {dmg} danni puri.{Colors.RESET} (HP: {player.hp}/{player.max_hp})")
        if player.hp <= 0 and player.benedetto_save:
            player.hp = 1; player.benedetto_save = False
            print(f"{Colors.YELLOW}La Benedizione ti salva dal colpo letale!{Colors.RESET}")
        if player.hp <= 0:
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

