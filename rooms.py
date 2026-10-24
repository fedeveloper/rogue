import random
import time
from typing import List
from ui import Colors, delay_print, clear_screen, interactive_menu, display_msg, wait_enter
from data_manager import GAME_DATA, PROFILE_MANAGER, MULTIPLIERS, get_biome, get_element_icon
from archive import get_archive_bonus
from codex import record_enemy_killed, record_enemy_seen, record_letter, record_phase, record_reaction, record_rune, record_runeword, record_spell
from constants import CAMPFIRE_REST_PCT, BASE_HIT_CHANCE, BLOOD_LETTER_CHANCE, CURSE_HP_DRAIN_PCT, MIN_DAMAGE_PCT, POISON_MIN, POISON_PCT
from entities import STATUS_NAMES, Player, Enemy, generate_weapon, generate_armor, generate_accessory, generate_potion, generate_rune, generate_scroll, get_random_relic, set_sockets
import runes as rune_rules
import attributes
import magic
import nemesis
from epitaph import note
from entities import Rune
from inventory_menu import show_inventory_menu
import modes

# Effetti di controllo delle reazioni: scadono alla fine del turno del nemico, non all'inizio
CONTROL_STATUSES = ("stun", "blind", "slow")
# Mosse del nemico che sono attacchi
ATTACK_MOVES = ("attack", "heavy", "venom", "drain", "unleash")
# Attacchi da cui conviene difendersi: l'intento lo dice
HEAVY_MOVES = ("heavy", "unleash")


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
        if self.enemy.is_boss and not self.boss_hit_taken: self.player.run_tracker["no_hit_boss_done"] = True
        
        g_drop = 0 if self.player.aristocrat else self.player.calculate_gold_gain(self.enemy.gold_drop)
        
        self.player.gold += g_drop
        display_msg(f"Ottieni {Colors.YELLOW}{g_drop} oro{Colors.RESET}.")
        # Le reliquie agiscono prima dell'EXP (es. la Pietra Filosofale converte l'EXP in Oro)
        for r in self.player.relic_effects: r.on_enemy_death(self)
        if self.player.necro_harvest:
            healed = self.player.heal(max(1, self.player.max_hp // 10))
            if healed > 0: display_msg(f"{Colors.MAGENTA}Raccolto d'Anime: assorbi {healed} HP dal nemico caduto!{Colors.RESET}")
        if attributes.value(self.player, "kill_heal_pct"):
            healed = self.player.heal(max(1, self.player.max_hp * attributes.value(self.player, "kill_heal_pct") // 100))
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
        self.enemy.mark = [element, GAME_DATA["elements"]["marks"]["duration"] + self.player.rune_value("mark_duration_add")]

    def _trigger_reaction(self, key: str):
        r = GAME_DATA["elements"]["reactions"][key]
        self.enemy.mark = None
        if self.enemy.ward is not None:
            self.enemy.ward = None
            display_msg(f"{Colors.YELLOW}{Colors.BOLD}La reazione infrange le Scaglie di {self.enemy.name}!{Colors.RESET}")
        record_reaction(key)
        self.player.run_tracker["reactions"] = self.player.run_tracker.get("reactions", 0) + 1
        self.player.gain_ether(magic.rules()["gain"]["reaction"])
        msg = f"{Colors.MAGENTA}{Colors.BOLD}⚡ REAZIONE: {r['icon']} {r['name'].upper()}!{Colors.RESET}"
        if r.get("bonus_pct"):
            dmg = self.player.get_total_atk() * r["bonus_pct"] // 100 * (100 + self.player.rune_value("reaction_dmg_pct") + attributes.value(self.player, "reaction_dmg_pct")) // 100
            self.enemy.hp -= dmg
            msg += f" {Colors.CYAN}{dmg} danni extra.{Colors.RESET}"
        if r.get("status"):
            s_type, turns = r["status"]["type"], r["status"]["duration"]
            self.enemy.statuses[s_type] = max(self.enemy.statuses.get(s_type, 0), turns)
            msg += f" {Colors.MAGENTA}{self.enemy.name}: {STATUS_NAMES[s_type]}.{Colors.RESET}"
        display_msg(msg)
        for relic in self.player.relic_effects: relic.on_reaction(self, key)

    def _tick_enemy_conditions(self):
        """Fine del turno del nemico: scadono marchio, Accecato e Impantanato."""
        if self.enemy.mark:
            self.enemy.mark[1] -= 1
            if self.enemy.mark[1] <= 0: self.enemy.mark = None
        for s in [s for s in self.enemy.statuses if s in ("blind", "slow")]:
            self.enemy.statuses[s] -= 1
            if self.enemy.statuses[s] <= 0: del self.enemy.statuses[s]

    # ------------------------------------------------------------- fasi dei boss
    def check_phase(self) -> bool:
        """Se il boss è sceso sotto la soglia della sua prossima fase, ci entra. True se ha cambiato fase."""
        e = self.enemy
        changed = False
        while e.hp > 0 and e.phase < len(e.phases) and e.hp * 100 <= e.max_hp * e.phases[e.phase]["at_pct"]:
            ph = e.phases[e.phase]
            e.phase += 1
            changed = True
            record_phase(e.base_name, e.phase)
            display_msg(f"\n{Colors.RED}{Colors.BOLD}⚠ {e.name.upper()}: {ph['name'].upper()}{Colors.RESET}\n{Colors.YELLOW}{ph['text']}{Colors.RESET}")
            for line in self._apply_phase(ph): display_msg(f"{Colors.MAGENTA}  · {line}{Colors.RESET}")
        if changed: self.intent = None
        return changed

    def _apply_phase(self, ph: dict) -> List[str]:
        """Applica gli effetti di una fase e restituisce cosa è cambiato, da mostrare al giocatore."""
        e, out = self.enemy, []
        if "element" in ph:
            element = ph["element"]
            if element == "counter":
                # Diventa l'elemento che colpisce meglio la tua armatura
                armor = self.player.armor.element
                element = max(GAME_DATA["elements"]["list"], key=lambda el: (MULTIPLIERS.get(el, {}).get(armor, 1.0), el == e.element))
            e.element, e.mark = element, None
            out.append(f"Ora è di elemento {get_element_icon(element)}.")
        if "atk_mult" in ph:
            e.atk = int(e.atk * ph["atk_mult"])
            out.append(f"Attacco +{round((ph['atk_mult'] - 1) * 100)}%.")
        if "heal_pct" in ph:
            healed = min(e.max_hp - e.hp, e.max_hp * ph["heal_pct"] // 100)
            e.hp += healed
            out.append(f"Recupera {healed} HP ({e.hp}/{e.max_hp}).")
        if "shield_pct" in ph:
            e.shield += e.max_hp * ph["shield_pct"] // 100
            out.append(f"Uno scudo di {e.shield} assorbe i danni dei tuoi attacchi.")
        if "ward" in ph:
            e.ward = ph["ward"]
            out.append(f"Scaglie: i tuoi attacchi fanno il {round(ph['ward'] * 100)}% dei danni finché una reazione elementale non le infrange.")
        if "status_inflict" in ph:
            e.status_inflict = dict(ph["status_inflict"])
            out.append(f"I suoi colpi infliggono {STATUS_NAMES[ph['status_inflict']['type']]} ({ph['status_inflict']['chance']}%).")
        if "moves" in ph:
            e.moves = dict(ph["moves"])
            new = [self._move(m)["name"] for m in ph["moves"] if m not in ("attack",)]
            out.append("Mosse: " + ", ".join(new) + ".")
        return out

    def _absorb(self, dmg: int, eff: str) -> tuple:
        """Scaglie e scudo riducono i danni degli attacchi dell'eroe."""
        if self.enemy.ward is not None:
            dmg = int(dmg * self.enemy.ward)
            eff += f" {Colors.BLUE}[SCAGLIE]{Colors.RESET}"
        if self.enemy.shield > 0:
            # Le armi con shield_mult consumano lo scudo più in fretta: ogni punto di danno ne toglie shield_mult
            mult = self.player.weapon.traits.get("shield_mult", 1)
            taken = min(self.enemy.shield, dmg * mult)
            self.enemy.shield -= taken
            dmg -= -(-taken // mult)
            eff += f" {Colors.BLUE}[SCUDO -{taken}{', infranto' if not self.enemy.shield else ''}]{Colors.RESET}"
        return dmg, eff

    # ------------------------------------------------------------- intenti
    def _move(self, move_id: str) -> dict:
        return GAME_DATA["moves"]["moves"][move_id]

    def choose_intent(self):
        self.intent = "stunned" if "stun" in self.enemy.statuses else self.enemy.choose_move()
        # Corruzione alta: il Labirinto a volte nasconde la mossa che il nemico prepara
        voice = GAME_DATA["meta"]["corruption"]["voice"]
        self.intent_hidden = self.player.corruption >= voice["threshold"] and random.random() * 100 < voice["chance"]

    def intent_text(self) -> str:
        if getattr(self, "intent_hidden", False): return f"❔ {Colors.MAGENTA}??? (il Labirinto ti nasconde la sua mossa){Colors.RESET}"
        if self.intent == "stunned": return f"🧊 {Colors.CYAN}Congelato: perderà il turno{Colors.RESET}"
        m = self._move(self.intent)
        text = f"{m['icon']} {Colors.BOLD}{m['name']}{Colors.RESET}"
        if self.intent in ATTACK_MOVES:
            text += f" (≈{self.estimate_enemy_damage(m.get('damage_mult', 1))} danni)"
            if self.intent in HEAVY_MOVES: text += f" {Colors.RED}— difenditi!{Colors.RESET}"
            if self.intent == "drain": text += f" e si cura di altrettanto"
            if self.intent == "venom" and self.enemy.status_inflict: text += f" + {STATUS_NAMES.get(self.enemy.status_inflict['type'], '')} se ti ferisce"
        elif self.intent == "guard": text += f": i tuoi colpi faranno il {int(m['damage_taken_mult'] * 100)}% dei danni"
        elif self.intent == "heal": text += f": recupererà il {m['heal_pct']}% degli HP"
        elif self.intent == "seal": text += f": {Colors.RED}al tuo prossimo turno non potrai difenderti{Colors.RESET}"
        elif self.intent == "charge":
            text += f": il turno dopo arriva il Colpo caricato (≈{self.estimate_enemy_damage(self._move('unleash')['damage_mult'])} danni)"
        elif self.intent == "shield": text += f": scudo di {self.enemy.max_hp * m['shield_pct'] // 100}"
        return text

    def enemy_status_text(self) -> str:
        parts = []
        if self.enemy.mark: parts.append(f"marchio {get_element_icon(self.enemy.mark[0])}")
        if self.enemy.shield: parts.append(f"scudo {self.enemy.shield}")
        if self.enemy.ward is not None: parts.append("scaglie")
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
        first_strike = self.first_player_attack and self.player.rune_value("first_strike_pct")
        self.first_player_attack = False
        if ambush:
            dmg_dealt *= 2
            eff += f" {Colors.MAGENTA}[IMBOSCATA!]{Colors.RESET}"

        self.player.run_tracker["floor_attacks"] += 1
        if random.randint(1, 100) <= hit_chance:
            self.player.run_tracker["floor_hits"] += 1
            self.player.gain_ether(magic.rules()["gain"]["hit"] + attributes.value(self.player, "ether_on_hit"))
            dmg_dealt = int(dmg_dealt * self.player.get_class_damage_multiplier())
            # L'attributo con cui scala l'arma (Forza, Destrezza o Arcano) e i talenti che aumentano i danni
            dmg_dealt = dmg_dealt * (100 + attributes.weapon_bonus(self.player) + attributes.value(self.player, "dmg_pct")) // 100
            # Rune dell'arma: Contrasto sui colpi Super Efficaci, Agguato sul primo attacco dello scontro
            if multiplier > 1.0 and self.player.rune_value("super_effective_pct"):
                dmg_dealt = dmg_dealt * (100 + self.player.rune_value("super_effective_pct")) // 100
            if first_strike:
                dmg_dealt = dmg_dealt * (100 + first_strike) // 100
                eff += f" {Colors.MAGENTA}[AGGUATO]{Colors.RESET}"
            if multiplier > 1.0 and self.enemy.is_boss:
                if "super_effective_hits" not in self.player.run_tracker: self.player.run_tracker["super_effective_hits"] = 0
                self.player.run_tracker["super_effective_hits"] += 1
            
            for r in self.player.relic_effects:
                dmg_dealt, eff = r.on_attack(self, dmg_dealt, multiplier, eff)

            if self.resonance == "Tenebra":
                dmg_dealt += int(self._resonance_value("Tenebra"))
                eff += f" {Colors.MAGENTA}[TENEBRA]{Colors.RESET}"
            if self.intent == "guard":
                if self.player.weapon.traits.get("guard_break"):
                    eff += f" {Colors.YELLOW}[SFONDI LA GUARDIA]{Colors.RESET}"
                else:
                    dmg_dealt = int(dmg_dealt * self._move("guard")["damage_taken_mult"])
                    eff += f" {Colors.BLUE}[GUARDIA]{Colors.RESET}"
            dmg_dealt, eff = self._absorb(dmg_dealt, eff)
            nem = getattr(self.enemy, "nemesis", None)
            if nem and nemesis.resisted(nem, self.player.weapon.element) < 1:
                dmg_dealt = int(dmg_dealt * nemesis.resisted(nem, self.player.weapon.element))
                eff += f" {Colors.BLUE}[RESISTE]{Colors.RESET}"
            
            self.enemy.hp -= dmg_dealt
            display_msg(f"\n-> Colpisci con {self.player.weapon.name} infliggendo {Colors.CYAN}{dmg_dealt} danni!{Colors.RESET} {eff}")
            self.apply_element(self.player.weapon.element)
            
            for r in self.player.relic_effects: r.on_attack_landed(self, multiplier)

            ls = self.player.get_lifesteal() + dmg_dealt * self.player.rune_value("lifesteal_pct") // 100
            stolen = self.player.heal(ls) if ls > 0 else 0
            if stolen > 0: display_msg(f"{Colors.RED}Rubavita: assorbi {stolen} HP!{Colors.RESET}")
            if self.resonance == "Luce":
                healed = self.player.heal(int(self._resonance_value("Luce")))
                if healed > 0: display_msg(f"{Colors.YELLOW}✨ Risonanza di Luce: +{healed} HP!{Colors.RESET}")
            if self.resonance == "Fuoco":
                self.burn_dmg += int(self._resonance_value("Fuoco"))

            for s_type, key, turns in rune_rules.ON_HIT_STATUSES:
                chance = self.player.rune_value(key)
                if chance and self.enemy.hp > 0 and random.randint(1, 100) <= chance:
                    self.enemy.statuses[s_type] = max(self.enemy.statuses.get(s_type, 0), turns)
                    display_msg(f"{Colors.MAGENTA}La runa colpisce: {self.enemy.name} è afflitto da {STATUS_NAMES[s_type].upper()}!{Colors.RESET}")
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

    def execute_player_defense(self) -> bool:
        """La difesa della classe (defenses.json). False se la tecnica abbatte il nemico."""
        defense = GAME_DATA["defenses"].get(self.def_type, {})
        self.is_defending = True
        self.player.gain_ether(magic.rules()["gain"]["defend"])
        self.player.on_defense_started()
        if self.player.rune_value("defend_heal_pct"):
            healed = self.player.heal(max(1, self.player.max_hp * self.player.rune_value("defend_heal_pct") // 100))
            if healed: display_msg(f"{Colors.GREEN}Runa della Quiete: recuperi {healed} HP.{Colors.RESET}")
        if self.def_type == "silenced":
            display_msg(f"\n{Colors.BLUE}-> Ti ripari come puoi: nel gas la tecnica non ti riesce.{Colors.RESET}")
        elif self.def_type == "counter":
            display_msg(f"\n{Colors.BLUE}-> Sollevi la guardia, pronto a sfruttare l'attacco nemico!{Colors.RESET}")
        elif self.def_type == "focus":
            self.focused_attack = True
            display_msg(f"\n{Colors.BLUE}-> Studi il nemico nell'ombra. Il tuo prossimo attacco sarà devastante!{Colors.RESET}")
        elif self.def_type == "recovery":
            if self.player.cursed:
                display_msg(f"\n{Colors.BLUE}-> Ti difendi, ma la Maledizione blocca il tuo recupero magico.{Colors.RESET}")
            else:
                heal_amt = max(1, self.player.max_hp * defense["heal_pct"] // 100)
                self.player.heal(heal_amt)
                display_msg(f"\n{Colors.BLUE}-> Evochi una barriera vitale. {Colors.GREEN}Recuperi {heal_amt} HP!{Colors.RESET}")
        elif self.def_type == "cleanse":
            purified = [STATUS_NAMES[s] for s in ("poison", "bleed") if self.player.statuses.pop(s, None)]
            healed = self.player.heal(max(1, self.player.max_hp * defense["heal_pct"] // 100))
            display_msg(f"\n{Colors.BLUE}-> Pronunci il Voto e alzi lo scudo."
                        + (f" {Colors.CYAN}Ti liberi da {' e '.join(purified)}.{Colors.RESET}" if purified else "")
                        + (f" {Colors.GREEN}Recuperi {healed} HP.{Colors.RESET}" if healed else f"{Colors.RESET}"))
        elif self.def_type == "mark":
            healed = self.player.heal(max(1, self.player.max_hp * defense["heal_pct"] // 100))
            display_msg(f"\n{Colors.BLUE}-> Ti ripari, bevi un sorso e lanci una fiala contro il nemico."
                        + (f" {Colors.GREEN}Recuperi {healed} HP.{Colors.RESET}" if healed else f"{Colors.RESET}"))
            self.apply_element(self.player.weapon.element)
        elif self.def_type == "siphon":
            stolen = min(self.enemy.hp, max(1, self.enemy.max_hp * defense["drain_pct"] // 100))
            self.enemy.hp -= stolen
            healed = self.player.heal(stolen)
            display_msg(f"\n{Colors.BLUE}-> Il sudario si stringe attorno al nemico: gli strappi {stolen} HP."
                        + (f" {Colors.GREEN}Recuperi {healed} HP.{Colors.RESET}" if healed else f"{Colors.RESET}"))
        if self.enemy.hp <= 0:
            self.on_enemy_death()
            return False
        return True

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
            if self.silenced: self.def_type, self.def_txt = "silenced", "Difesa (Dimezza danni; il gas soffoca la tecnica)"
            if self.sealed: self.def_txt = f"{Colors.RED}🔒 Difesa sigillata (non puoi difenderti in questo turno){Colors.RESET}"
            if self.intent is None: self.choose_intent()

            prompt = (f"\n{Colors.BOLD}--- ⚔️ IN COMBATTIMENTO ⚔️ ---{Colors.RESET}\nTu: {Colors.GREEN}{self.player.hp}/{self.player.max_hp} HP{Colors.RESET}"
                      + (f" {Colors.CYAN}✨ {self.player.ether}/{self.player.max_ether()} Etere{Colors.RESET}" if self.player.spells else "") + " | "
                      f"{self.enemy.name}: {Colors.RED}{self.enemy.hp}/{self.enemy.max_hp} HP{Colors.RESET}{self.enemy_status_text()}\n"
                      f"Intento del nemico: {self.intent_text()}")
            # Le azioni per nome: la voce degli incantesimi c'è solo per chi ne conosce
            actions = [("attack", "Attacca"), ("defend", self.def_txt)]
            if self.player.spells: actions.append(("spell", f"Lancia un incantesimo ({self.player.ether}/{self.player.max_ether()} Etere)"))
            actions += [("inventory", "Apri Inventario (Usa oggetto = Costa Turno)"), ("stats", "Statistiche Eroe"), ("flee", "Tenta la Fuga")]

            idx = interactive_menu([text for _, text in actions], prompt)
            clear_screen()
            action = actions[idx][0] if 0 <= idx < len(actions) else None

            if action == "attack":
                return self.execute_player_attack()

            elif action == "spell":
                spell_id = self.choose_spell()
                if spell_id is None: continue
                return self.cast_spell(spell_id)

            elif action == "defend":
                if self.sealed:
                    display_msg(f"\n{Colors.RED}-> Il Sigillo ti blocca: in questo turno non puoi difenderti.{Colors.RESET}")
                    continue
                return self.execute_player_defense()

            elif action == "inventory":
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

            elif action == "stats":
                from inventory_menu import show_player_stats
                show_player_stats(self.player, self)

            elif action == "flee":
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

    # ------------------------------------------------------------- incantesimi
    def choose_spell(self):
        """Il menu degli incantesimi: quello scelto, o None per tornare indietro (non costa il turno)."""
        options = [magic.label(self.player, sid) for sid in self.player.spells] + ["Indietro"]
        idx = interactive_menu(options, f"\n{Colors.CYAN}{Colors.BOLD}--- INCANTESIMI --- ✨ {self.player.ether}/{self.player.max_ether()} Etere{Colors.RESET}")
        clear_screen()
        if not 0 <= idx < len(self.player.spells): return None
        sid = self.player.spells[idx]
        fx = magic.spell(sid)["effects"]
        if self.player.ether < magic.cost(self.player, sid):
            display_msg(f"\n{Colors.RED}-> Non hai abbastanza Etere per {magic.spell(sid)['name']}.{Colors.RESET}")
            return None
        if fx.get("escape") and self.enemy.is_boss:
            display_msg(f"\n{Colors.RED}-> Dai boss non si fugge, nemmeno con il vento.{Colors.RESET}")
            return None
        if fx.get("weaken_pct") and self.weakened:
            display_msg(f"\n{Colors.RED}-> {self.enemy.name} porta già la tua Maledizione.{Colors.RESET}")
            return None
        return sid

    def spell_damage(self, spell_id: str, pct: int) -> int:
        """Danni di un incantesimo: ATK × pct, elemento contro il nemico, Arcano (prima di Guardia, Scaglie e scudo)."""
        element = magic.spell(spell_id)["element"]
        mult = MULTIPLIERS.get(element, {}).get(self.enemy.element, 1.0)
        power = 100 + attributes.value(self.player, "spell_pct") + self.player.weapon.traits.get("spell_pct", 0)
        return max(1, int(self.player.get_total_atk() * pct / 100 * mult) * power // 100)

    def cast_spell(self, spell_id: str) -> bool:
        """Lancia un incantesimo: costa il turno e il suo Etere. False se il nemico muore."""
        s, fx = magic.spell(spell_id), magic.spell(spell_id)["effects"]
        self.player.ether -= magic.cost(self.player, spell_id)
        record_spell(spell_id)
        display_msg(f"\n{Colors.CYAN}-> {s['icon']} Lanci {s['name']}!{Colors.RESET}")
        if fx.get("cleanse"):
            removed = [STATUS_NAMES[k] for k in ("poison", "bleed") if self.player.statuses.pop(k, None)]
            if removed: display_msg(f"{Colors.CYAN}Ti liberi da {' e '.join(removed)}.{Colors.RESET}")
        if "heal_pct" in fx:
            healed = self.player.heal(self.player.max_hp * fx["heal_pct"] // 100)
            display_msg(f"{Colors.GREEN}Recuperi {healed} HP. ({self.player.hp}/{self.player.max_hp}){Colors.RESET}")
        if "def_pct" in fx:
            self.spell_def += self.player.armor.defense * fx["def_pct"] // 100
            display_msg(f"{Colors.CYAN}La pelle ti si indurisce: +{self.spell_def} Difesa per il resto dello scontro.{Colors.RESET}")
        if "weaken_pct" in fx:
            self.weakened = True
            self.enemy.atk = max(1, self.enemy.atk * (100 - fx["weaken_pct"]) // 100)
            display_msg(f"{Colors.MAGENTA}{self.enemy.name} si indebolisce: ATK {self.enemy.atk}.{Colors.RESET}")
        if fx.get("escape"):
            self.player.run_tracker["escapes"] += 1
            display_msg(f"{Colors.YELLOW}Il vento ti solleva e ti porta lontano dallo scontro.{Colors.RESET}")
            wait_enter("\nPremi INVIO...")
            return False
        if fx.get("dispel") and (self.enemy.shield or self.enemy.ward is not None):
            self.enemy.shield, self.enemy.ward = 0, None
            display_msg(f"{Colors.YELLOW}Lo scudo e le Scaglie di {self.enemy.name} si dissolvono!{Colors.RESET}")
        if "damage_pct" in fx:
            pct, eff = fx["damage_pct"], ""
            if "detonate_pct" in fx and self.enemy.mark:
                pct, eff = fx["detonate_pct"], f" {Colors.MAGENTA}[DETONAZIONE {get_element_icon(self.enemy.mark[0])}]{Colors.RESET}"
                self.enemy.mark = None
            dmg = self.spell_damage(spell_id, pct)
            if MULTIPLIERS.get(s["element"], {}).get(self.enemy.element, 1.0) > 1.0: eff += f" {Colors.GREEN}[SUPER EFFICACE!]{Colors.RESET}"
            if self.intent == "guard":
                dmg = int(dmg * self._move("guard")["damage_taken_mult"])
                eff += f" {Colors.BLUE}[GUARDIA]{Colors.RESET}"
            dmg, eff = self._absorb(dmg, eff)
            nem = getattr(self.enemy, "nemesis", None)
            if nem and nemesis.resisted(nem, s["element"]) < 1:
                dmg = int(dmg * nemesis.resisted(nem, s["element"]))
                eff += f" {Colors.BLUE}[RESISTE]{Colors.RESET}"
            self.enemy.hp -= dmg
            display_msg(f"{s['name']} infligge {Colors.CYAN}{dmg} danni{Colors.RESET} a {self.enemy.name}!{eff}")
            if "drain_pct" in fx and dmg > 0:
                healed = self.player.heal(dmg * fx["drain_pct"] // 100)
                if healed: display_msg(f"{Colors.GREEN}Assorbi {healed} HP.{Colors.RESET}")
            if "status" in fx and self.enemy.hp > 0:
                st = fx["status"]
                self.enemy.statuses[st["type"]] = max(self.enemy.statuses.get(st["type"], 0), st["duration"])
                display_msg(f"{Colors.MAGENTA}{self.enemy.name}: {STATUS_NAMES[st['type']]} per {st['duration']} turni.{Colors.RESET}")
            if s["element"] != "Normale": self.apply_element(s["element"])
        if self.enemy.hp <= 0:
            self.on_enemy_death()
            return False
        return True

    def _calc_escape_chance(self) -> int:
        f_chance = 20 + self.player.get_dodge() - self.enemy.base_dodge + (20 if PROFILE_MANAGER.get_perk("scarpisti", False) else 0)
        f_chance += get_archive_bonus("escape", PROFILE_MANAGER._data) + attributes.value(self.player, "escape")
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
        defense = self.player.get_total_def() + self.spell_def + sum(r.get_def_modifier(self) for r in self.player.relic_effects)
        raw = max(1, int(self._enemy_attack_power() * self._enemy_multiplier() * move_mult))
        return max(raw - defense, -(-raw * MIN_DAMAGE_PCT // 100))

    def _calc_enemy_damage(self, en_multiplier: float, move_mult: float = 1.0) -> int:
        defense = self.player.get_total_def() + self.spell_def + sum(r.get_def_modifier(self) for r in self.player.relic_effects)
        en_atk = self._enemy_attack_power()
        raw = max(1, int((en_atk + random.randint(-1, 2)) * en_multiplier * move_mult))
        # La difesa riduce il colpo, ma non lo annulla mai: resta almeno MIN_DAMAGE_PCT del danno grezzo
        dmg_taken = max(raw - defense, -(-raw * MIN_DAMAGE_PCT // 100))
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
        elif intent == "transform":
            display_msg(f"{Colors.MAGENTA}<- {self.enemy.name} usa il suo turno per trasformarsi.{Colors.RESET}")
            result = True
        elif intent == "seal":
            self.sealed = True
            display_msg(f"{Colors.RED}<- 🔒 {self.enemy.name} ti sigilla: al prossimo turno non potrai difenderti.{Colors.RESET}")
            result = True
        elif intent == "charge":
            self.enemy.charged = True
            display_msg(f"{Colors.RED}<- ⏳ {self.enemy.name} raccoglie le forze. Il prossimo colpo sarà devastante.{Colors.RESET}")
            result = True
        elif intent == "shield":
            # Lo scudo non si somma: la Barriera lo riporta al suo valore, così colpendo si avanza sempre
            gain = self.enemy.max_hp * self._move("shield")["shield_pct"] // 100
            self.enemy.shield = max(self.enemy.shield, gain)
            display_msg(f"{Colors.BLUE}<- 💠 {self.enemy.name} alza una barriera: scudo {self.enemy.shield}.{Colors.RESET}")
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
                heavy = f"{Colors.RED}[{self._move(move)['name'].upper()}]{Colors.RESET} " if move in HEAVY_MOVES else ""
                display_msg(f"<- {heavy}{self.enemy.name} ti colpisce! Subisci {Colors.RED}{dmg_taken} danni{Colors.RESET}. {en_eff}{dif}")
                
                if getattr(self.enemy, 'status_inflict', None):
                    s_data = self.enemy.status_inflict
                    if move == "venom" or random.randint(1, 100) <= s_data.get("chance", 100):
                        s_type = s_data["type"]
                        self.player.statuses[s_type] = max(self.player.statuses.get(s_type, 0), s_data["duration"])
                        display_msg(f"{Colors.MAGENTA}Sei stato afflitto da {STATUS_NAMES.get(s_type, s_type).upper()}!{Colors.RESET}")
                
                reflect_total = dmg_taken * self.player.rune_value("thorns_pct") // 100
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
                if move == "drain":
                    drained = min(self.enemy.max_hp - self.enemy.hp, int(dmg_taken * self._move("drain")["heal_ratio"]))
                    self.enemy.hp += drained
                    display_msg(f"{Colors.RED}🩸 {self.enemy.name} si nutre della tua vita: +{drained} HP. ({self.enemy.hp}/{self.enemy.max_hp}){Colors.RESET}")
                if not alive:
                    display_msg(f"\n{Colors.RED}{Colors.BOLD}Sei caduto in battaglia contro {self.enemy.name}...{Colors.RESET}")
                    wait_enter("\nPremi INVIO per continuare...")
                    return False
                boil = self.rules.get("boil")
                if boil and self.player.gold > 0 and random.random() * 100 < boil["chance"]:
                    lost = max(1, self.player.gold * boil["gold_pct"] // 100)
                    self.player.gold -= lost
                    display_msg(f"{Colors.YELLOW}{self.biome['icon']} {self.biome['hazard']['name']}: {lost} Oro ti bolle via dalla borsa. (Oro: {self.player.gold}){Colors.RESET}")
            elif not self.hit_negated_by_relic:
                display_msg(f"<- {self.enemy.name} attacca, ma il colpo non ti ferisce. {en_eff}")
            if self.is_defending:
                # In guardia, l'armatura marchia con il suo elemento chi ti colpisce: è così che si combinano due elementi
                self.apply_element(self.player.armor.element)
                if self.enemy.hp <= 0:
                    self.on_enemy_death()
                    return False
        else:
            display_msg(f"{Colors.CYAN}<- {self.enemy.name} attacca... ma riesci a schivarlo!{Colors.RESET}")
        return True

def audacity_bonus(audacity: int) -> dict:
    """Cosa aggiunge l'Audacia al bottino del boss: oro in più (in %) e un oggetto, epico alle soglie più alte."""
    rule = GAME_DATA["meta"]["rooms"]["audacity"]
    return {"gold_pct": audacity * rule["gold_pct_per_point"], "item": audacity >= rule["item_at"], "epic": audacity >= rule["epic_at"]}


def audacity_text(audacity: int) -> str:
    bonus = audacity_bonus(audacity)
    if not audacity: return "nessun premio extra dal boss"
    parts = [f"+{bonus['gold_pct']}% oro"]
    if bonus["item"]: parts.append("oggetto epico" if bonus["epic"] else "oggetto")
    return "boss: " + ", ".join(parts)


def gain_audacity(player: Player, room_type: str) -> int:
    points = GAME_DATA["meta"]["rooms"]["audacity"]["points"].get(room_type, 0)
    if points: points += sum(r.get_audacity_bonus() for r in player.relic_effects)
    player.audacity += points
    return points


def audacity_reward(player: Player, floor: int, boss_gold: int):
    """Il premio del boss per i rischi corsi nel piano."""
    if player.audacity <= 0: return
    bonus = audacity_bonus(player.audacity)
    display_msg(f"\n{Colors.RED}🎲 Audacia {player.audacity}: il Labirinto premia chi ha rischiato.{Colors.RESET}")
    if not player.aristocrat:
        extra = player.calculate_gold_gain(boss_gold * bonus["gold_pct"] // 100)
        player.gold += extra
        display_msg(f"Ottieni altri {Colors.YELLOW}{extra} oro{Colors.RESET}.")
    if bonus["item"]:
        drop = generate_weapon(floor + 2, bonus["epic"]) if random.random() > 0.5 else generate_armor(floor + 2, bonus["epic"])
        display_msg(f"{Colors.MAGENTA}Premio dell'Audacia: {drop.display_name}!{Colors.RESET}")
        player.inventory.append(drop)


def combat_room(player: Player, floor: int, enemy_instance: Enemy):
    session = CombatSession(player, floor, enemy_instance)
    session.start()

def mystery_odds() -> dict:
    """Probabilità (in %) degli esiti della stanza del Mistero, come le rivela il Sesto Senso."""
    outcomes = GAME_DATA["meta"]["rooms"]["mystery"]["outcomes"]
    total = sum(outcomes.values())
    return {k: round(w * 100 / total) for k, w in outcomes.items()}


MYSTERY_NAMES = {"hoard": "Tesoro", "relic": "Reliquia", "hard": "Mostro", "easy": "Preda", "trap": "Trappola", "empty": "Vuoto"}


def mystery_room(player: Player, floor: int, active_pacts: List[str]):
    delay_print(f"\n{Colors.MAGENTA}--- LA STANZA DEL MISTERO ---{Colors.RESET}")
    display_msg(f"❤️  HP: {Colors.GREEN}{player.hp}/{player.max_hp}{Colors.RESET} | 💰 Oro: {Colors.YELLOW}{player.gold}{Colors.RESET}\n")
    delay_print(f"{random.choice(GAME_DATA['lore']['mystery'])}", 0.03)
    time.sleep(1)

    outcomes = GAME_DATA["meta"]["rooms"]["mystery"]["outcomes"]
    outcome = random.choices(list(outcomes), weights=list(outcomes.values()))[0]
    relic = get_random_relic(player) if outcome == "relic" else None
    if outcome == "relic" and not relic: outcome = "hoard"

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
    elif outcome == "hoard":
        display_msg(f"\n{Colors.YELLOW}La nebbia nascondeva il deposito di qualcuno che non è mai tornato a prenderlo.{Colors.RESET}")
        rule = GAME_DATA["meta"]["rooms"]["mystery"]
        _gain_gold(player, int(rule["hoard_gold_mult"] * _chest_gold(floor)))
        _gain_item(player, generate_accessory(floor))
        rune_drop(player, floor, "mystery_hoard")
        wait_enter("\nPremi INVIO per proseguire...")
    elif outcome == "relic":
        display_msg(f"\n{Colors.MAGENTA}Al centro della stanza, sospesa nel nulla, pulsa una reliquia.{Colors.RESET}")
        player.add_relic(relic)
        wait_enter("\nPremi INVIO per proseguire...")
    else:
        display_msg(f"\n{Colors.GREEN}La nebbia si dirada. La stanza è vuota. Tiri un sospiro di sollievo.{Colors.RESET}")
        wait_enter("Premi INVIO per proseguire...")

def vendor_room(player: Player, floor: int):
    delay_print(f"\n{random.choice(GAME_DATA['lore']['vendor'])}")
    items_for_sale =[generate_weapon(floor + 1), generate_armor(floor + 1), generate_accessory(floor), generate_potion(floor), generate_potion(floor)]
    items_for_sale += [generate_rune(floor) for _ in range(rune_rules.rules()["vendor_stock"])]
    if magic.available(): items_for_sale += [generate_scroll(floor) for _ in range(magic.rules()["vendor_stock"])]
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
                    tipo = {"weapon": "Arma", "armor": "Armatura", "accessory": "Monile", "rune": "Runa"}.get(item.type, "Pozione")
                    options_compra.append(f"[{tipo}] {item.display_name} - Prezzo: {Colors.YELLOW}{item.value} Oro{Colors.RESET}")
                idx_compra = interactive_menu(options_compra, prompt_compra, cancellable=True)
                if idx_compra == -1: break
                
                if 0 <= idx_compra < len(items_for_sale):
                    item = items_for_sale[idx_compra]
                    if player.gold >= item.value:
                        player.gold -= item.value; player.inventory.append(item)
                        if item.type == "rune": record_rune(item.rune_id)
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

RUNE_WORKSHOP = f"{Colors.CYAN}🔷 Rune e Incastoni{Colors.RESET} (incastonare è gratis; il falò resta acceso)"


def _socketable(player: Player) -> list:
    """Armi e armature dell'eroe, equipaggiate per prime: (oggetto, etichetta)."""
    out = [(player.weapon, "equipaggiata"), (player.armor, "equipaggiata")]
    out += [(i, "nello zaino") for i in player.inventory if i.type in ("weapon", "armor")]
    return out


def rune_workshop(player: Player, floor: int):
    """Al Falò: incastonare una runa (gratis) o estrarla (Oro), così le rune passano da un oggetto all'altro."""
    cost = 0 if any(r.free_rune_extraction for r in player.relic_effects) else rune_rules.extract_cost(floor)
    while True:
        clear_screen()
        bag = [i for i in player.inventory if i.type == "rune"]
        lines = [f"\n{Colors.CYAN}--- 🔷 RUNE E INCASTONI ---{Colors.RESET} | Oro: {player.gold}",
                 f"Arma: {player.weapon.display_name}", f"Armatura: {player.armor.display_name}",
                 "Rune nello zaino: " + (", ".join(r.display_name for r in bag) if bag else "nessuna")]
        options = [f"Incastona una runa", f"Estrai una runa ({cost} Oro: torna nello zaino)"]
        idx = interactive_menu(options, "\n".join(lines), cancellable=True)
        if idx == -1: return
        if idx == 0:
            if not bag:
                display_msg(f"{Colors.RED}Non hai rune nello zaino.{Colors.RESET}"); wait_enter(); continue
            r_idx = interactive_menu([rune_rules.describe(r.rune_id) for r in bag], "\nQuale runa?", cancellable=True)
            if r_idx == -1: continue
            rune = bag[r_idx]
            targets = [(it, where) for it, where in _socketable(player) if rune_rules.free_sockets(it) > 0 and rune_rules.fits(rune.rune_id, it.type)]
            if not targets:
                display_msg(f"{Colors.RED}Nessun oggetto adatto ha un incastone libero ({rune_rules.SLOT_NAMES[rune_rules.rune(rune.rune_id)['slot']]}).{Colors.RESET}"); wait_enter(); continue
            t_idx = interactive_menu([f"{it.display_name} ({where})" for it, where in targets], f"\nIn quale oggetto incastonare {rune.display_name}?", cancellable=True)
            if t_idx == -1: continue
            item = targets[t_idx][0]
            before = rune_rules.active_words(item)
            player.inventory.remove(rune)
            item.runes.append(rune.rune_id)
            item.refresh_display_name()
            display_msg(f"{Colors.GREEN}La runa si fonde con il metallo: {item.display_name}.{Colors.RESET}")
            for wid in rune_rules.active_words(item):
                if wid in before: continue
                record_runeword(wid)
                w = rune_rules.word(wid)
                note(player, "runeword", name=w["name"])
                display_msg(f"{Colors.MAGENTA}{Colors.BOLD}✨ Le rune si accordano: PAROLA RUNICA «{w['name']}»!{Colors.RESET} {w['desc']}")
            wait_enter()
        else:
            holders = [(it, where) for it, where in _socketable(player) if it.runes]
            if not holders:
                display_msg(f"{Colors.RED}Nessun oggetto ha rune incastonate.{Colors.RESET}"); wait_enter(); continue
            if player.gold < cost:
                display_msg(f"{Colors.RED}Oro insufficiente: estrarre una runa costa {cost} Oro.{Colors.RESET}"); wait_enter(); continue
            h_idx = interactive_menu([f"{it.display_name} ({where})" for it, where in holders], "\nDa quale oggetto?", cancellable=True)
            if h_idx == -1: continue
            item = holders[h_idx][0]
            k = interactive_menu([rune_rules.describe(rid) for rid in item.runes], "\nQuale runa estrarre?", cancellable=True)
            if k == -1: continue
            rid = item.runes.pop(k)
            item.refresh_display_name()
            player.gold -= cost
            player.inventory.append(Rune(rid, floor))
            display_msg(f"{Colors.GREEN}Hai estratto {rune_rules.rune(rid)['name']} (-{cost} Oro).{Colors.RESET}"); wait_enter()


MEDITATE = f"{Colors.CYAN}Medita{Colors.RESET} (recuperi tutto l'Etere, il falò si spegnerà)"
OBLIVION = f"{Colors.MAGENTA}Leggi il Tomo dell'Oblio{Colors.RESET} (redistribuisci i punti abilità; il falò resta acceso)"


def read_oblivion(player: Player, tome):
    """Il Tomo dell'Oblio: i punti spesi tornano da spendere e si redistribuiscono subito."""
    player.inventory.remove(tome)
    refunded = attributes.reset(player)
    display_msg(f"{Colors.MAGENTA}Le pagine si svuotano mentre le leggi: dimentichi come sei cresciuto. {refunded} punti tornano da spendere.{Colors.RESET}")
    wait_enter("\nPremi INVIO...")
    attributes.spend_points(player)


def campfire_room(player: Player, floor: int):
    delay_print(f"\n{Colors.YELLOW}{random.choice(GAME_DATA['lore']['campfire'])}{Colors.RESET}")
    while True:
        clear_screen()
        prompt = f"\n{Colors.YELLOW}[ 🔥 FALÒ E FORGIA ] | Tuo Oro: {player.gold} | HP: {player.hp}/{player.max_hp}{Colors.RESET}\n"
        rest_pct = round(CAMPFIRE_REST_PCT * modes.rule("campfire_heal_mult"))
        options = [
            f"Riposa (Recupera {rest_pct}% HP, il falò si spegnerà)",
            f"Affila Arma Base (Paga {Colors.YELLOW}50 Oro{Colors.RESET} per +3 ATK, il falò si spegnerà)",
            f"{Colors.MAGENTA}Altare dell'Evoluzione{Colors.RESET} (Fondi due armi/armature per potenziarle)"
        ]
        
        has_cursed = any(getattr(item, 'is_cursed', False) for item in [player.weapon, player.armor, player.accessory] if item)
        if has_cursed:
            options.append(f"{Colors.CYAN}Purifica Maledizione{Colors.RESET} (Paga {Colors.YELLOW}100 Oro{Colors.RESET} per rimuovere il malus da un pezzo equipaggiato)")
            
        if player.spells: options.append(MEDITATE)
        options.append(RUNE_WORKSHOP)
        tome = next((i for i in player.inventory if i.type == "consumable" and i.category == "respec"), None)
        if tome: options.append(OBLIVION)
        options.append("Prosegui")
        
        idx = interactive_menu(options, prompt)
        
        if options[idx] == "Prosegui": break
        elif options[idx] == RUNE_WORKSHOP: rune_workshop(player, floor)
        elif options[idx] == OBLIVION: read_oblivion(player, tome)
        elif options[idx] == MEDITATE:
            gained = player.gain_ether(player.max_ether())
            display_msg(f"{Colors.CYAN}Chiudi gli occhi davanti al fuoco e lasci che l'Etere torni: +{gained} ({player.ether}/{player.max_ether()}).{Colors.RESET}")
            wait_enter("\nPremi INVIO..."); break
        elif idx == 0:
            player.run_tracker["rested"] = True
            player.heal(player.max_hp * rest_pct // 100)
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
                        # Le rune dell'oggetto sacrificato tornano nello zaino; quelle della base restano incastonate
                        player.inventory.extend(Rune(rid, floor) for rid in getattr(it2, "runes", []))
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

def scroll_drop(player: Player, floor: int, source: str):
    """Una pergamena con la probabilità della fonte (`spells.json`, `rules.drops`)."""
    if magic.roll_drop(source) and magic.available():
        s = generate_scroll(floor)
        display_msg(f"{Colors.CYAN}Trovi una pergamena: {s.display_name}! (Si legge dallo zaino){Colors.RESET}")
        player.inventory.append(s)


def rune_drop(player: Player, floor: int, source: str):
    """Una runa con la probabilità della fonte (`runes.json`, `rules.drops`)."""
    if rune_rules.roll_drop(source, attributes.value(player, "rune_drop_add")) or any(source in r.rune_drop_always for r in player.relic_effects):
        r = generate_rune(floor)
        record_rune(r.rune_id)
        display_msg(f"{Colors.CYAN}Trovi una runa: {r.display_name}! (Si incastona al Falò){Colors.RESET}")
        player.inventory.append(r)
    scroll_drop(player, floor, source)  # le stesse fonti possono custodire anche una pergamena


def _chest_gold(floor: int) -> int:
    return random.randint(30, 60) + (floor * 10)


def _gain_gold(player: Player, amount: int):
    g = player.calculate_gold_gain(amount)
    player.gold += g
    display_msg(f"{Colors.GREEN}Trovate {g} monete d'oro!{Colors.RESET}")


def _gear(level: int, epic: bool = False):
    return generate_weapon(level, epic) if random.random() < 0.5 else generate_armor(level, epic)


def _gain_item(player: Player, drop, text: str = "C'era anche"):
    display_msg(f"{text}: {Colors.CYAN}{drop.display_name}{Colors.RESET}!")
    player.inventory.append(drop)


def chest_risks(floor: int) -> dict:
    """Probabilità (in %) che un forziere del piano sia un Mimic o sia chiuso a chiave: crescono con la profondità."""
    rules, mult = GAME_DATA["meta"]["rooms"]["treasure"], modes.rule("chest_risk_mult")
    # Il moltiplicatore dell'Ascensione vale anche sul tetto, ma un forziere su due resta un forziere vero
    return {k: min(50.0, mult * max(0.0, min(r["max"], (floor - r["from_floor"] + 1) * r["pct_per_floor"]))) if floor >= r["from_floor"] else 0.0
            for k, r in rules.items() if k in ("mimic", "locked")}


def treasure_room(player: Player, floor: int):
    delay_print(f"\n{Colors.YELLOW}{random.choice(GAME_DATA['lore']['treasure'])}{Colors.RESET}")
    rules, risks = GAME_DATA["meta"]["rooms"]["treasure"], chest_risks(floor)
    roll = random.random() * 100
    kind = "mimic" if roll < risks["mimic"] else "locked" if roll < risks["mimic"] + risks["locked"] else "open"

    if kind == "locked":
        cost = max(1, player.max_hp * rules["locked"]["hp_cost_pct"] // 100)
        prompt = (f"\n{Colors.YELLOW}Il forziere è chiuso da una serratura arrugginita. Dentro, qualcosa di pesante tintinna.{Colors.RESET}\n"
                  f"❤️  HP: {player.hp}/{player.max_hp}")
        if interactive_menu([f"Forza la serratura (-{cost} HP, bottino garantito)", "Lascialo stare"], prompt) != 0:
            display_msg(f"{Colors.CYAN}Lasci il forziere alla polvere.{Colors.RESET}")
            wait_enter("\nPremi INVIO per continuare..."); return
        display_msg(f"{Colors.RED}Le dita sanguinano sul metallo: -{cost} HP.{Colors.RESET}")
        if not player.take_damage(cost):
            wait_enter("\nPremi INVIO per continuare..."); return
        _gain_gold(player, _chest_gold(floor))
        _gain_item(player, generate_accessory(floor) if random.random() < 0.5 else generate_potion(floor))
        wait_enter("\nPremi INVIO per continuare..."); return

    # Il Mimic a volte si tradisce, ma anche un forziere vero può sembrare respirare; il Sesto Senso non sbaglia
    if PROFILE_MANAGER.get_perk("sesto_senso", False):
        tell = kind == "mimic"
        hint = f"{Colors.MAGENTA}Il Sesto Senso ti avverte: quel forziere ha fame.{Colors.RESET}" if tell else ""
    else:
        tell = random.random() * 100 < rules["mimic"]["tell" if kind == "mimic" else "false_tell"]
        hint = f"{Colors.MAGENTA}Il coperchio sembra sollevarsi appena, come un respiro.{Colors.RESET}" if tell else ""
    if hint:
        if interactive_menu(["Aprilo comunque", "Lascialo stare"], f"\n{hint}\n❤️  HP: {player.hp}/{player.max_hp}") != 0:
            display_msg(f"{Colors.CYAN}Ti allontani senza voltare le spalle al forziere.{Colors.RESET}")
            wait_enter("\nPremi INVIO per continuare..."); return

    if kind == "mimic":
        display_msg(f"\n{Colors.RED}{Colors.BOLD}Il forziere spalanca una bocca di denti: è un MIMIC!{Colors.RESET}")
        wait_enter("Premi INVIO per difenderti...")
        mimic = Enemy(floor, False, player.active_pacts, name="Mimic")
        combat_room(player, floor, mimic)
        if player.hp > 0 and mimic.hp <= 0:
            display_msg(f"\n{Colors.YELLOW}Nel ventre del Mimic c'è il bottino di chi lo ha aperto prima di te.{Colors.RESET}")
            _gain_gold(player, 2 * _chest_gold(floor))
            _gain_item(player, _gear(floor + rules["loot_floor_bonus"]), "Hai trovato")
            rune_drop(player, floor, "mimic")
            wait_enter("\nPremi INVIO per continuare...")
        return

    _gain_gold(player, _chest_gold(floor))
    if random.random() * 100 < rules["relic_chance"]:
        r = get_random_relic(player)
        if r: player.add_relic(r)
    elif random.random() < 0.20:
        _gain_item(player, generate_accessory(floor))
    elif random.random() > 0.4:
        _gain_item(player, generate_potion(floor))
    wait_enter("\nPremi INVIO per continuare...")


def trap_chances(player: Player) -> dict:
    """Probabilità (in %) di superare la trappola disinnescandola (Precisione) o attraversandola di corsa (Schivata)."""
    rules = GAME_DATA["meta"]["rooms"]["trap"]
    precision = player.base_acc + player.temp_acc + player.weapon.get_hit_chance_modifier() + sum(r.get_acc_modifier() for r in player.relic_effects)
    stats = {"disarm": precision, "dash": player.get_dodge()}
    bonus = player.rune_value("trap_chance_add")
    return {k: int(max(rules["min_chance"], min(rules["max_chance"], rules[k]["base"] + stats[k] * rules[k]["per_point"] + bonus))) for k in stats}


def trap_damage(player: Player, floor: int, active_pacts: List[str], base: int) -> int:
    dmg = base + floor * 3
    if "trappole" in active_pacts: dmg *= 2
    for r in player.relic_effects: dmg = r.modify_trap_damage(dmg)
    return dmg


def trap_room(player: Player, floor: int, active_pacts: List[str]) -> bool:
    """La trappola custodisce un bottino: chi la affronta lo ottiene sempre, e se fallisce la prova paga in HP.
    Restituisce True se il giocatore l'ha affrontata."""
    delay_print(f"\n{random.choice(GAME_DATA['lore']['trap'])}")
    delay_print(f"{Colors.RED}È UNA TRAPPOLA!{Colors.RESET} {Colors.YELLOW}Oltre il meccanismo, qualcosa brilla.{Colors.RESET}", 0.05)
    rules, chances = GAME_DATA["meta"]["rooms"]["trap"], trap_chances(player)
    lo, hi = (trap_damage(player, floor, active_pacts, base) for base in (15, 30))
    prompt = (f"\n❤️  HP: {Colors.GREEN}{player.hp}/{player.max_hp}{Colors.RESET} | Se la prova fallisce: {Colors.RED}{lo}-{hi} danni{Colors.RESET}"
              f"\nCome affronti la trappola?")
    options = [f"Disinnescala (Precisione: {chances['disarm']}%, recuperi anche dei pezzi)",
               f"Attraversala di corsa (Schivata: {chances['dash']}%)",
               "Torna indietro (niente bottino, nessun danno)"]
    idx = interactive_menu(options, prompt)
    if idx not in (0, 1):
        display_msg(f"{Colors.CYAN}Ti ritiri lentamente. Il meccanismo resta in attesa del prossimo sventurato.{Colors.RESET}")
        wait_enter("\nPremi INVIO per continuare...")
        return False

    way = "disarm" if idx == 0 else "dash"
    if random.randint(1, 100) <= chances[way]:
        display_msg(f"{Colors.GREEN}{'Blocchi il meccanismo con un clic soddisfatto.' if way == 'disarm' else 'Passi tra le lame un istante prima che si chiudano.'}{Colors.RESET}")
        if way == "disarm":
            base, per_floor = rules["salvage_gold"]
            _gain_gold(player, base + floor * per_floor)
    else:
        dmg = trap_damage(player, floor, active_pacts, random.randint(15, 30))
        display_msg(f"{Colors.RED}Il meccanismo scatta! Subisci {dmg} danni puri.{Colors.RESET}")
        alive = player.take_damage(dmg)
        display_msg(f"(HP: {player.hp}/{player.max_hp})")
        if not alive:
            player.run_tracker["death_cause"] = "trap"
            display_msg(f"\n{Colors.RED}{Colors.BOLD}La trappola ti è stata fatale...{Colors.RESET}")
            wait_enter("\nPremi INVIO per continuare...")
            return True

    epic = random.random() * 100 < rules["epic_chance"]
    loot = _gear(floor + rules["loot_floor_bonus"], epic) if random.random() * 100 < rules["gear_chance"] else generate_accessory(floor)
    _gain_item(player, loot, f"{Colors.MAGENTA}Il bottino della trappola è tuo{Colors.RESET}")
    rune_drop(player, floor, "trap")
    wait_enter("\nPremi INVIO per continuare...")
    return True
