"""Il turno del nemico: intento annunciato, precisione, danni e mosse."""
import random

import effects
from ui import Colors, display_msg, wait_enter
from data_manager import GAME_DATA, MULTIPLIERS, get_element_icon
from constants import BASE_HIT_CHANCE, MIN_DAMAGE_PCT
from entities import STATUS_NAMES
from combat.rules import ATTACK_MOVES, HEAVY_MOVES


class EnemyActions:
    """Metodi di `CombatSession` (vedi `combat/session.py`)."""

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
            text += f" (≈{self.estimate_enemy_damage(m.get('damage_mult', 1), m.get('pierce_pct', 0))} danni)"
            if self.intent in HEAVY_MOVES: text += f" {Colors.RED}— difenditi!{Colors.RESET}"
            if self.intent == "drain": text += f" e si cura di altrettanto"
            if self.intent == "ether_drain": text += f" e ti toglie {m['ether_drain']} Etere"
            if self.intent == "spellcast": text += f": la tua Difesa ne ferma solo il {100 - m['pierce_pct']}%"
            if self.intent == "venom" and self.enemy.status_inflict: text += f" + {STATUS_NAMES.get(self.enemy.status_inflict['type'], '')} se ti ferisce"
        elif self.intent == "guard": text += f": i tuoi colpi faranno il {int(m['damage_taken_mult'] * 100)}% dei danni"
        elif self.intent == "heal": text += f": recupererà il {m['heal_pct']}% degli HP"
        elif self.intent == "seal": text += f": {Colors.RED}al tuo prossimo turno non potrai difenderti{Colors.RESET}"
        elif self.intent == "silence": text += f": {Colors.RED}per {m['silence_turns']} turni non potrai lanciare incantesimi{Colors.RESET}"
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

    def _calc_enemy_hit_chance(self, en_multiplier: float) -> int:
        blind = GAME_DATA["elements"]["conditions"]["blind"] if "blind" in self.enemy.statuses else 0
        return max(10, min(100, BASE_HIT_CHANCE + self.enemy.base_acc - blind - self.player.get_dodge() + (15 if en_multiplier > 1.0 else -20 if en_multiplier < 1.0 else 0)))

    def _enemy_multiplier(self) -> float:
        en_multiplier = MULTIPLIERS.get(self.enemy.element, {}).get(self.player.armor.element, 1.0)
        for r in self.player.relic_effects: en_multiplier = r.modify_multiplier(en_multiplier, is_defense=True)
        return en_multiplier

    def _enemy_attack_power(self) -> int:
        return max(1, int(self.enemy.atk * (1 - self._resonance_value("Acqua")))) if self.resonance == "Acqua" else self.enemy.atk

    def _player_defense(self, pierce_pct: int = 0) -> int:
        """La Difesa che riduce i colpi del nemico; un Incantesimo (pierce_pct) ne supera una parte."""
        defense = self.player.get_total_def() + self.spell_def + sum(r.get_def_modifier(self) for r in self.player.relic_effects)
        return defense * (100 - pierce_pct) // 100

    def estimate_enemy_damage(self, move_mult: float = 1.0, pierce_pct: int = 0) -> int:
        """Danno atteso dell'attacco annunciato, senza difesa attiva né effetti casuali (per l'intento)."""
        defense = self._player_defense(pierce_pct)
        raw = max(1, int(self._enemy_attack_power() * self._enemy_multiplier() * move_mult))
        return max(raw - defense, -(-raw * MIN_DAMAGE_PCT // 100))

    def _calc_enemy_damage(self, en_multiplier: float, move_mult: float = 1.0, pierce_pct: int = 0) -> int:
        defense = self._player_defense(pierce_pct)
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
        elif intent == "silence":
            self.mute_turns = self._move("silence")["silence_turns"]
            display_msg(f"{Colors.RED}<- 🤫 {self.enemy.name} ti ammutolisce: per {self.mute_turns} turni non potrai lanciare incantesimi.{Colors.RESET}")
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
            dmg_taken = self._calc_enemy_damage(en_multiplier, move_mult, self._move(move).get("pierce_pct", 0))
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
                
                reflect_total = dmg_taken * effects.total(self.player, "thorns_pct") // 100
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
                if move == "ether_drain" and self.player.ether:
                    lost = min(self.player.ether, self._move("ether_drain")["ether_drain"])
                    self.player.ether -= lost
                    display_msg(f"{Colors.MAGENTA}🌀 {self.enemy.name} ti risucchia {lost} Etere. ({self.player.ether}/{self.player.max_ether()}){Colors.RESET}")
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
