"""Le stanze della mappa: combattimento, mercante, falò (con rune e Tomo dell'Oblio), forziere, trappola e mistero.

Il combattimento vero e proprio è nel pacchetto `combat/` (`CombatSession`); qui restano le stanze che lo avviano.
`CombatSession`, `reaction_key` e i premi (`combat/rewards.py`) si importano anche da qui, come prima della divisione.
"""
import random
import time
from typing import List
from ui import Colors, delay_print, clear_screen, interactive_menu, display_msg, wait_enter
from data_manager import GAME_DATA, PROFILE_MANAGER
from codex import record_rune, record_runeword
from constants import CAMPFIRE_REST_PCT
from entities import Player, Enemy, generate_weapon, generate_armor, generate_accessory, generate_potion, generate_rune, generate_scroll, get_random_relic
import runes as rune_rules
import attributes
import effects
import magic
from epitaph import note
from entities import Rune
import modes
from combat import CombatSession, reaction_key
from combat.rewards import audacity_bonus, audacity_reward, audacity_text, gain_audacity, rune_drop, scroll_drop

def combat_room(player: Player, floor: int, enemy_instance: Enemy):
    session = CombatSession(player, floor, enemy_instance)
    session.start()

def mystery_odds() -> dict:
    """Probabilità (in %) degli esiti della stanza del Mistero, come le rivela il Sesto Senso."""
    outcomes = GAME_DATA["meta"]["rooms"]["mystery"]["outcomes"]
    total = sum(outcomes.values())
    return {k: round(w * 100 / total) for k, w in outcomes.items()}


MYSTERY_NAMES = {"hoard": "Tesoro", "relic": "Reliquia", "hard": "Mostro", "easy": "Preda", "trap": "Trappola", "spring": "Fonte",
                 "scroll": "Pergamena", "rune": "Runa", "empty": "Vuoto"}


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
    elif outcome == "spring":
        # Fonte d'Etere: tutto l'Etere a chi conosce incantesimi, una cura a chi non ne conosce
        if player.spells:
            gained = player.gain_ether(player.max_ether())
            display_msg(f"\n{Colors.CYAN}Una fonte di luce liquida sgorga dal pavimento. Ne bevi: +{gained} Etere ({player.ether}/{player.max_ether()}).{Colors.RESET}")
        else:
            healed = player.heal(player.max_hp * GAME_DATA["meta"]["rooms"]["mystery"]["spring_heal_pct"] // 100)
            display_msg(f"\n{Colors.CYAN}Una fonte di luce liquida sgorga dal pavimento. Non sai cosa farne, ma l'acqua è fresca: +{healed} HP.{Colors.RESET}")
        wait_enter("\nPremi INVIO per proseguire...")
    elif outcome == "scroll":
        display_msg(f"\n{Colors.MAGENTA}Su un leggio di pietra, una pergamena che nessuno ha mai letto.{Colors.RESET}")
        _gain_item(player, generate_scroll(floor), "La prendi")
        wait_enter("\nPremi INVIO per proseguire...")
    elif outcome == "rune":
        display_msg(f"\n{Colors.MAGENTA}Nella nebbia brilla un segno inciso nell'aria, che si condensa in una pietra.{Colors.RESET}")
        rune = generate_rune(floor)
        record_rune(rune.rune_id)
        _gain_item(player, rune, "La prendi")
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
    bonus = effects.total(player, "trap_chance_add")
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
