import random
from ui import Colors, clear_screen, interactive_menu, display_msg, wait_enter
from data_manager import GAME_DATA, PROFILE_MANAGER, get_element_icon
from entities import Rune, generate_random_element
import runes as rune_rules
from archive import unlocked_archive_bonuses

def _use_consumable(player, item, real_idx, in_combat) -> str:
    cat = item.category
    res = ""
    if cat == "heal":
        heal_amt = item.heal_amount
        if player.alchemist_potions: heal_amt = int(heal_amt * 1.5)
        if "carestia" in player.active_pacts: heal_amt //= 2
        for r in player.relic_effects: heal_amt = r.on_item_heal(player, heal_amt)
        actual_heal = player.heal(heal_amt)
        display_msg(f"{Colors.GREEN}\nHai usato {item.display_name}! Recuperati {actual_heal} HP.{Colors.RESET}")
        res = "turn_used" if in_combat else ""
    elif cat == "smoke_bomb":
        if not in_combat:
            display_msg(f"{Colors.YELLOW}\nPuoi usare questo oggetto solo in combattimento!{Colors.RESET}")
            wait_enter("Premi INVIO...")
            return ""
        display_msg(f"{Colors.YELLOW}\nHai lanciato una Bomba Fumogena! Scappi dal combattimento!{Colors.RESET}")
        res = "smoke_bomb"
    elif cat == "chaos_tome":
        if not in_combat:
            display_msg(f"{Colors.YELLOW}\nPuoi usare questo oggetto solo in combattimento!{Colors.RESET}")
            wait_enter("Premi INVIO...")
            return ""
        new_el = generate_random_element()
        player.weapon.element = new_el
        player.weapon.refresh_display_name()
        display_msg(f"{Colors.MAGENTA}\nLeggi le antiche rune... La tua arma si impregna dell'elemento {get_element_icon(new_el)}!{Colors.RESET}")
        res = "turn_used"
    elif cat == "holy_water":
        display_msg(f"{Colors.YELLOW}\nBevi l'Acqua Santa...{Colors.RESET}")
        purified = False
        for eq in [player.weapon, player.armor, player.accessory]:
            if eq and getattr(eq, 'is_cursed', False):
                eq.is_cursed = False
                eq.curse_effect = ""
                eq.refresh_display_name()
                purified = True
        if purified:
            display_msg(f"{Colors.GREEN}Tutte le Maledizioni sul tuo equipaggiamento sono state purificate!{Colors.RESET}")
        else:
            display_msg("Non avevi equipaggiamento maledetto.")
        res = "turn_used" if in_combat else ""
    elif cat == "chaos_vial":
        display_msg(f"{Colors.MAGENTA}\nBevi la Fiala del Caos...{Colors.RESET}")
        eff = random.choice(["heal_full", "dmg", "gold", "max_hp", "element"])
        if eff == "heal_full":
            if player.heal(player.max_hp) > 0 or player.hp == player.max_hp: display_msg(f"{Colors.GREEN}Sei completamente curato!{Colors.RESET}")
            else: display_msg(f"{Colors.RED}La fiala ribolle, ma la maledizione blocca la cura.{Colors.RESET}")
        elif eff == "dmg":
            dmg = int(player.max_hp * 0.3)
            alive = player.take_damage(dmg)
            display_msg(f"{Colors.RED}Il liquido ti brucia dall'interno! Subisci {dmg} danni.{Colors.RESET}")
            if not alive:
                player.hp = 1
                player.run_tracker["1_hp_survive"] = True
        elif eff == "gold":
            g = random.randint(50, 150)
            player.gold += g
            display_msg(f"{Colors.YELLOW}La fiala si trasforma in {g} monete d'oro!{Colors.RESET}")
        elif eff == "max_hp":
            player.max_hp += 10
            player.hp += 10
            display_msg(f"{Colors.GREEN}Il tuo corpo si fortifica! +10 HP Max.{Colors.RESET}")
        elif eff == "element":
            new_el = generate_random_element()
            player.weapon.element = new_el
            player.weapon.refresh_display_name()
            display_msg(f"{Colors.CYAN}La tua arma si impregna dell'elemento {new_el}!{Colors.RESET}")
        res = "fiala_caos" if in_combat else ""
    elif cat == "antidote":
        display_msg(f"{Colors.GREEN}\nBevi l'Antidoto Universale! Tutti gli status alterati svaniscono.{Colors.RESET}")
        if hasattr(player, 'statuses'): player.statuses.clear()
        antidote_heal = item.heal_amount
        for r in player.relic_effects: antidote_heal = r.on_item_heal(player, antidote_heal)
        actual_heal = player.heal(antidote_heal)
        if actual_heal > 0: display_msg(f"{Colors.GREEN}Recuperati {actual_heal} HP.{Colors.RESET}")
        res = "turn_used" if in_combat else ""
    elif cat == "whetstone":
        display_msg(f"{Colors.CYAN}\nAffili l'arma: {player.weapon.display_name} ottiene +5 ATK permanente!{Colors.RESET}")
        player.weapon.atk += 5
        res = "turn_used" if in_combat else ""
    elif cat == "accuracy_potion":
        if not in_combat:
            display_msg(f"{Colors.YELLOW}\nPuoi usare questo oggetto solo in combattimento!{Colors.RESET}")
            wait_enter("Premi INVIO...")
            return ""
        display_msg(f"{Colors.CYAN}\nBevi il Filtro Preciso! I tuoi colpi non mancheranno più!{Colors.RESET}")
        player.temp_acc = 999  # Azzerato a fine combattimento
        res = "turn_used"
    elif cat == "rune_solvent":
        holders = [it for it in (player.weapon, player.armor) if it.runes]
        if not holders:
            display_msg(f"{Colors.YELLOW}\nNon hai rune incastonate nell'equipaggiamento.{Colors.RESET}"); wait_enter("Premi INVIO..."); return ""
        it = holders[0] if len(holders) == 1 else holders[interactive_menu([h.display_name for h in holders], "\nDa quale oggetto estrarre una runa?")]
        k = 0 if len(it.runes) == 1 else interactive_menu([rune_rules.describe(r) for r in it.runes], "\nQuale runa?")
        rid = it.runes.pop(k)
        it.refresh_display_name()
        player.inventory.append(Rune(rid))
        display_msg(f"{Colors.CYAN}\nIl solvente scioglie il castone: {rune_rules.rune(rid)['name']} torna nello zaino.{Colors.RESET}")
        res = "turn_used" if in_combat else ""
    elif cat == "socket_chisel":
        top = rune_rules.rules()["sockets"]["boss"]
        targets = [it for it in (player.weapon, player.armor) if it.sockets < top]
        if not targets:
            display_msg(f"{Colors.YELLOW}\nArma e armatura hanno già {top} incastoni.{Colors.RESET}"); wait_enter("Premi INVIO..."); return ""
        it = targets[0] if len(targets) == 1 else targets[interactive_menu([t.display_name for t in targets], "\nDove aprire un nuovo incastone?")]
        it.sockets += 1
        it.refresh_display_name()
        display_msg(f"{Colors.CYAN}\nLo scalpello apre un nuovo incastone: {it.display_name}.{Colors.RESET}")
        res = "turn_used" if in_combat else ""

    consume_item = True
    if cat == "heal" and player.thief_save and random.random() < 0.30:
        display_msg(f"{Colors.CYAN}Tasche Nascoste: la pozione non è stata consumata!{Colors.RESET}")
        consume_item = False
    for r in player.relic_effects:
        if not r.on_item_use(player, item): consume_item = False
    if consume_item: player.inventory.pop(real_idx)
    wait_enter("Premi INVIO...")
    return res

def show_inventory_menu(player, in_combat=False) -> str:
    while True:
        clear_screen()
        prompt = ""
        prompt += f"\n{Colors.MAGENTA}{Colors.BOLD}--- ZAINO E INVENTARIO ---{Colors.RESET}\n"
        prompt += f"❤️  HP: {Colors.GREEN}{player.hp}/{player.max_hp}{Colors.RESET} | 💰 Oro: {Colors.YELLOW}{player.gold}{Colors.RESET}\n"
        traits = player.weapon.trait_text()
        prompt += f"⚔️  Arma: {player.weapon.display_name} (+{player.get_total_atk()} ATK)" + (f" · {traits}" if traits else "") + "\n"
        prompt += f"🛡️  Armatura: {player.armor.display_name} (+{player.armor.defense} DEF)\n"
        acc_txt = f"{player.accessory.display_name} ({player.accessory.desc})" if player.accessory else "Nessuno"
        prompt += f"💍 Monile: {acc_txt}\n"
        res_el = player._get_resonance_element()
        if res_el: prompt += f"✨ {Colors.CYAN}RISONANZA ATTIVA: {get_element_icon(res_el)}!{Colors.RESET}\n"
        prompt += f"Per visualizzare Reliquie, Patti e statistiche complete, usa la voce 'Statistiche Eroe' nel menu di Esplorazione.\n"
        prompt += "-" * 55 + "\nScegli un oggetto da usare/equipaggiare:"
        
        display_items = []
        options = []
        if not player.inventory: 
            prompt += "\nL'inventario è vuoto.\n"
        else:
            consumables_map = {}
            for i, item in enumerate(player.inventory):
                if item.type == "consumable":
                    if item.name not in consumables_map: consumables_map[item.name] = []
                    consumables_map[item.name].append(i)
                else: display_items.append((i, item, 1))
            for name, indices in consumables_map.items(): display_items.append((indices[0], player.inventory[indices[0]], len(indices)))
            display_items.sort(key=lambda x: (x[1].type, x[1].name))
            
            for disp_idx, (real_idx, item, count) in enumerate(display_items):
                count_str = f" {Colors.YELLOW}[x{count}]{Colors.RESET}" if count > 1 else ""
                # Il livello compare una volta sola: i generatori lo mettono già nel nome, "(lv.2)"
                lvl = "" if "(lv." in item.name else f" - Lv.{item.level}"
                if item.type == "weapon": options.append(f"[Arma] {item.display_name} (+{item.atk} ATK){lvl}" + (f" · {item.trait_text()}" if item.trait_text() else ""))
                elif item.type == "armor": options.append(f"[Armatura] {item.display_name} (+{item.defense} DEF){lvl}")
                elif item.type == "accessory": options.append(f"[Monile] {item.display_name} ({item.desc})")
                elif item.type == "consumable": options.append(f"[Oggetto] {item.display_name}{count_str}")
                elif item.type == "rune": options.append(f"[Runa] {item.display_name} ({item.desc})")
                    
        options.append("Chiudi Zaino")
        
        idx = interactive_menu(options, prompt)
        
        if idx == len(options) - 1: return "closed"
        
        if player.inventory and 0 <= idx < len(display_items):
            real_idx, item, _ = display_items[idx]
            
            if item.type == "consumable":
                res = _use_consumable(player, item, real_idx, in_combat)
                if res: return res

            elif item.type == "rune":
                display_msg(f"\n{Colors.CYAN}Le rune si incastonano al Falò, in un'arma o in un'armatura con un incastone libero (◇).{Colors.RESET}")
                wait_enter("Premi INVIO...")
            
            elif item.type == "weapon":
                old_w = player.weapon
                player.weapon = item
                player.inventory[real_idx] = old_w
                player.run_tracker["weapon_changed"] = True
                display_msg(f"{Colors.GREEN}\n-> Equipaggiato: {player.weapon.display_name}!{Colors.RESET}")
                wait_enter("Premi INVIO...")
                if in_combat: return "turn_used"
                
            elif item.type == "armor":
                old_a = player.armor
                player.armor = item
                player.inventory[real_idx] = old_a
                display_msg(f"{Colors.GREEN}\n-> Equipaggiato: {player.armor.display_name}!{Colors.RESET}")
                wait_enter("Premi INVIO...")
                if in_combat: return "turn_used"
                
            elif item.type == "accessory":
                old_acc = player.accessory
                if old_acc:
                    if old_acc.bonus_type == "max_hp":
                        player.max_hp -= old_acc.bonus_value
                        player.hp = min(player.hp, player.max_hp)
                    if old_acc.bonus_type == "dodge": player.base_dodge -= old_acc.bonus_value
                    if old_acc.bonus_type == "acc": player.base_acc -= old_acc.bonus_value
                
                player.accessory = item
                if player.accessory.bonus_type == "max_hp":
                    player.max_hp += player.accessory.bonus_value
                    player.hp += player.accessory.bonus_value
                if player.accessory.bonus_type == "dodge": player.base_dodge += player.accessory.bonus_value
                if player.accessory.bonus_type == "acc": player.base_acc += player.accessory.bonus_value
                    
                if old_acc: player.inventory[real_idx] = old_acc
                else: player.inventory.pop(real_idx)
                display_msg(f"{Colors.GREEN}\n-> Equipaggiato: {player.accessory.display_name}!{Colors.RESET}")
                wait_enter("Premi INVIO...")
                if in_combat: return "turn_used"


def mode_rule_lines(player) -> list:
    """Le regole della discesa in corso: i gradi di Ascensione, o i modificatori della Sfida del Giorno."""
    grades = GAME_DATA["modes"]["ascension"]["grades"]
    if player.daily:
        boon = GAME_DATA["modes"]["daily"]["boons"][player.daily["boon"]]
        return [f"{grades[i]['name']}: {grades[i]['desc']}" for i in player.daily["maluses"]] + [f"{boon['name']} (dono): {boon['desc']}"]
    return [f"{g['name']}: {g['desc']}" for g in grades[:player.ascension]]


def show_player_stats(player, session=None):
    clear_screen()
    display_msg(f"\n{Colors.CYAN}{Colors.BOLD}--- STATISTICHE DELL'EROE ---{Colors.RESET}")
    display_msg(f"Classe: {Colors.YELLOW}{player.role}{Colors.RESET} | Tratto: {Colors.MAGENTA}{player.trait_name}{Colors.RESET}")
    display_msg(f"❤️  HP: {Colors.GREEN}{player.hp}/{player.max_hp}{Colors.RESET} | 💰 Oro: {Colors.YELLOW}{player.gold}{Colors.RESET}")
    display_msg(f"✨ EXP: {Colors.CYAN}{player.exp}/{player.max_exp}{Colors.RESET} (Livello {player.level})\n")
    
    display_msg(f"{Colors.BOLD}--- ATTRIBUTI ---{Colors.RESET}")
    display_msg(f"🗡️  Attacco Totale: {player.get_total_atk()} (Base arma: {player.weapon.atk})")
    display_msg(f"🛡️  Difesa Totale: {player.get_total_def()} (Base armatura: {player.armor.defense})")
    if session:
        hit = session._calc_hit_chance(session.attack_multiplier())
        display_msg(f"🎯 Probabilità di colpire: {hit}% (contro {session.enemy.name})")
    else:
        display_msg(f"🎯 Probabilità di colpire: {player.get_hit_chance()}% (nemico neutro senza schivata)")
    if player.get_crit_chance() > 0: display_msg(f"💥 Probabilità di critico: {player.get_crit_chance()}%")
    if player.get_lifesteal() > 0: display_msg(f"🩸 Rubavita: {player.get_lifesteal()} HP per colpo")
    display_msg(f"💨 Schivata: {player.get_dodge()}%")
    if player.corruption:
        cfg = GAME_DATA["meta"]["corruption"]
        veil, voice = cfg["veil"]["threshold"], cfg["voice"]["threshold"]
        marks = [f"+{player.corruption_atk()} ATK"] + (["Sguardo Velato"] if player.corruption >= veil else []) + (["Voce del Labirinto"] if player.corruption >= voice else [])
        display_msg(f"🩸 Corruzione: {Colors.MAGENTA}{player.corruption}/{cfg['max']}{Colors.RESET} ({', '.join(marks)})")
    
    res_el = player._get_resonance_element()
    if res_el:
        res_desc = GAME_DATA["elements"].get("resonance", {}).get(res_el, {}).get("desc", "")
        display_msg(f"🔮 Risonanza Elementale: {Colors.CYAN}Attiva ({get_element_icon(res_el)} {res_el}) - {res_desc}{Colors.RESET}")
        
    display_msg(f"\n{Colors.BOLD}--- EQUIPAGGIAMENTO ---{Colors.RESET}")
    display_msg(f"Arma: {player.weapon.display_name}" + (f" · {player.weapon.trait_text()}" if player.weapon.trait_text() else ""))
    display_msg(f"Armatura: {player.armor.display_name}")
    display_msg(f"Monile: {player.accessory.display_name if player.accessory else 'Nessuno'}")
    
    mode_rules = mode_rule_lines(player)
    if mode_rules:
        display_msg(f"\n{Colors.RED}{Colors.BOLD}--- {'SFIDA DEL GIORNO' if player.daily else f'ASCENSIONE {player.ascension}'} ---{Colors.RESET}")
        for line in mode_rules: display_msg(f" - {line}")
            
    if player.relics:
        display_msg(f"\n{Colors.YELLOW}{Colors.BOLD}--- RELIQUIE ATTIVE ---{Colors.RESET}")
        for r in player.relics:
            display_msg(f" - {r['name']}: {r['desc']}")
            
    archive_buffs = [f"Conoscenza ({title}): {desc}" for title, desc in unlocked_archive_bonuses(PROFILE_MANAGER._data)]
    if archive_buffs:
        display_msg(f"\n{Colors.CYAN}{Colors.BOLD}--- SINERGIE DELL'ARCHIVIO ---{Colors.RESET}")
        for b in archive_buffs: display_msg(f" - {b}")
        
    display_msg("\n")
    wait_enter("Premi INVIO per tornare all'esplorazione...")
