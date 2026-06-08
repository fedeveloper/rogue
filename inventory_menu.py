import time
import random
from ui import Colors, clear_screen, get_choice, interactive_menu
from data_manager import PROFILE_MANAGER, get_element_icon
from entities import generate_random_element
from archive import is_book_unlocked

def show_inventory_menu(player, in_combat=False) -> str:
    while True:
        clear_screen()
        prompt = ""
        prompt += f"\n{Colors.MAGENTA}{Colors.BOLD}--- ZAINO E INVENTARIO ---{Colors.RESET}\n"
        prompt += f"❤️  HP: {Colors.GREEN}{player.hp}/{player.max_hp}{Colors.RESET} | 💰 Oro: {Colors.YELLOW}{player.gold}{Colors.RESET}\n"
        prompt += f"⚔️  Arma: {player.weapon.display_name} (+{player.get_total_atk()} ATK)\n"
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
                if item.type == "weapon": options.append(f"[Arma] {item.display_name} (+{item.atk}) - Lv.{item.level}")
                elif item.type == "armor": options.append(f"[Armatura] {item.display_name} (+{item.defense}) - Lv.{item.level}")
                elif item.type == "accessory": options.append(f"[Monile] {item.display_name} ({item.desc})")
                elif item.type == "consumable": options.append(f"[Oggetto] {item.display_name}{count_str}")
                    
        options.append("Chiudi Zaino")
        
        idx = interactive_menu(options, prompt)
        
        if idx == len(options) - 1: return "closed"
        
        if player.inventory and 0 <= idx < len(display_items):
            real_idx, item, _ = display_items[idx]
            
            if item.type == "consumable":
                if item.category == "heal":
                    heal_amt = item.heal_amount
                    if PROFILE_MANAGER._data["perks"].get("metabolismo"): heal_amt = int(heal_amt * 1.5)
                    actual_heal = player.heal(heal_amt)
                    print(f"{Colors.GREEN}\nHai usato {item.display_name}! Recuperati {actual_heal} HP.{Colors.RESET}")
                    player.inventory.pop(real_idx)
                    input("Premi INVIO...")
                    if in_combat: return "turn_used"
                elif item.category == "smoke_bomb":
                    if not in_combat:
                        print(f"{Colors.YELLOW}\nPuoi usare questo oggetto solo in combattimento!{Colors.RESET}")
                        input("Premi INVIO...")
                    else:
                        print(f"{Colors.YELLOW}\nHai lanciato una Bomba Fumogena! Scappi dal combattimento!{Colors.RESET}")
                        player.inventory.pop(real_idx)
                        input("Premi INVIO...")
                        return "fled"
                elif item.category == "chaos_tome":
                    if not in_combat:
                        print(f"{Colors.YELLOW}\nPuoi usare questo oggetto solo in combattimento!{Colors.RESET}")
                        input("Premi INVIO...")
                    else:
                        print(f"{Colors.MAGENTA}\nLeggi le antiche rune... Il Caos distrugge i nemici!{Colors.RESET}")
                        player.inventory.pop(real_idx)
                        input("Premi INVIO...")
                        return "chaos_tome"
                elif item.category == "holy_water":
                    print(f"{Colors.YELLOW}\nBevi l'Acqua Santa...{Colors.RESET}")
                    purified = False
                    for eq in [player.weapon, player.armor, player.accessory]:
                        if eq and getattr(eq, 'is_cursed', False):
                            eq.is_cursed = False
                            eq.curse_effect = ""
                            eq.name = eq.name.replace("Maledetto", "Purificato")
                            eq.display_name = f"{Colors.YELLOW}{eq.name}{Colors.RESET}"
                            purified = True
                    if purified:
                        print(f"{Colors.GREEN}Tutte le Maledizioni sul tuo equipaggiamento sono state purificate!{Colors.RESET}")
                    else:
                        print("Non avevi equipaggiamento maledetto.")
                    player.inventory.pop(real_idx)
                    input("Premi INVIO...")
                    if in_combat: return "turn_used"
                elif item.category == "chaos_vial":
                    print(f"{Colors.MAGENTA}\nBevi la Fiala del Caos...{Colors.RESET}")
                    eff = random.choice(["heal_full", "dmg", "gold", "max_hp", "element"])
                    if eff == "heal_full":
                        player.hp = player.max_hp
                        print(f"{Colors.GREEN}Sei completamente curato!{Colors.RESET}")
                    elif eff == "dmg":
                        dmg = int(player.max_hp * 0.3)
                        player.hp -= dmg
                        print(f"{Colors.RED}Il liquido ti brucia dall'interno! Subisci {dmg} danni.{Colors.RESET}")
                        if player.hp <= 0: player.hp = 1
                    elif eff == "gold":
                        g = random.randint(50, 150)
                        player.gold += g
                        print(f"{Colors.YELLOW}La fiala si trasforma in {g} monete d'oro!{Colors.RESET}")
                    elif eff == "max_hp":
                        player.max_hp += 10
                        player.hp += 10
                        print(f"{Colors.GREEN}Il tuo corpo si fortifica! +10 HP Max.{Colors.RESET}")
                    elif eff == "element":
                        new_el = generate_random_element()
                        player.weapon.element = new_el
                        print(f"{Colors.CYAN}La tua arma si impregna dell'elemento {new_el}!{Colors.RESET}")
                    player.inventory.pop(real_idx)
                    input("Premi INVIO...")
                    if in_combat: return "turn_used"
                elif item.category == "antidote":
                    print(f"{Colors.GREEN}\nBevi l'Antidoto Universale! Tutti gli status alterati svaniscono.{Colors.RESET}")
                    if hasattr(player, 'statuses'): player.statuses.clear()
                    actual_heal = player.heal(10)
                    if actual_heal > 0: print(f"{Colors.GREEN}Recuperati {actual_heal} HP.{Colors.RESET}")
                    player.inventory.pop(real_idx)
                    input("Premi INVIO...")
                    if in_combat: return "turn_used"
                elif item.category == "whetstone":
                    print(f"{Colors.CYAN}\nAffili l'arma: {player.weapon.display_name} ottiene +5 ATK permanente!{Colors.RESET}")
                    player.weapon.atk += 5
                    player.inventory.pop(real_idx)
                    input("Premi INVIO...")
                    if in_combat: return "turn_used"
            
            elif item.type == "weapon":
                old_w = player.weapon
                player.weapon = item
                player.inventory[real_idx] = old_w
                print(f"{Colors.GREEN}\n-> Equipaggiato: {player.weapon.display_name}!{Colors.RESET}")
                input("Premi INVIO...")
                if in_combat: return "turn_used"
                
            elif item.type == "armor":
                old_a = player.armor
                player.armor = item
                player.inventory[real_idx] = old_a
                print(f"{Colors.GREEN}\n-> Equipaggiato: {player.armor.display_name}!{Colors.RESET}")
                input("Premi INVIO...")
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
                print(f"{Colors.GREEN}\n-> Equipaggiato: {player.accessory.display_name}!{Colors.RESET}")
                input("Premi INVIO...")
                if in_combat: return "turn_used"


def show_player_stats(player):
    clear_screen()
    print(f"\n{Colors.CYAN}{Colors.BOLD}--- STATISTICHE DELL'EROE ---{Colors.RESET}")
    print(f"Classe: {Colors.YELLOW}{player.role}{Colors.RESET} | Tratto: {Colors.MAGENTA}{getattr(player, 'trait_name', 'Nessuno')}{Colors.RESET}")
    print(f"❤️  HP: {Colors.GREEN}{player.hp}/{player.max_hp}{Colors.RESET} | 💰 Oro: {Colors.YELLOW}{player.gold}{Colors.RESET}")
    print(f"✨ EXP: {Colors.CYAN}{player.exp}/{player.max_exp}{Colors.RESET} (Livello {player.level})\n")
    
    print(f"{Colors.BOLD}--- ATTRIBUTI ---{Colors.RESET}")
    print(f"🗡️  Attacco Totale: {player.get_total_atk()} (Base arma: {player.weapon.atk})")
    print(f"🛡️  Difesa Totale: {player.armor.defense + player.temp_def} (Base armatura: {player.armor.defense})")
    print(f"🎯 Precisione: {player.base_acc}%")
    print(f"💨 Schivata: {player.get_dodge()}%")
    
    res_el = player._get_resonance_element()
    if res_el:
        res_desc = ""
        if res_el == "Acqua": res_desc = "Attacco nemico ridotto del 15%"
        elif res_el == "Vento": res_desc = "+15% Schivata in combattimento"
        elif res_el == "Terra": res_desc = "+5 Difesa fissa"
        elif res_el == "Tenebra": res_desc = "+5 Danni fissi ad ogni colpo"
        elif res_el == "Luce": res_desc = "Cura 3 HP a ogni tuo attacco"
        elif res_el == "Fuoco": res_desc = "Infliggi 5 danni da Ustione cumulabili per colpo"
        print(f"🔮 Risonanza Elementale: {Colors.CYAN}Attiva ({get_element_icon(res_el)} {res_el}) - {res_desc}{Colors.RESET}")
        
    print(f"\n{Colors.BOLD}--- EQUIPAGGIAMENTO ---{Colors.RESET}")
    print(f"Arma: {player.weapon.display_name}")
    print(f"Armatura: {player.armor.display_name}")
    print(f"Monile: {player.accessory.display_name if player.accessory else 'Nessuno'}")
    
    if player.active_pacts:
        print(f"\n{Colors.RED}{Colors.BOLD}--- PATTI DEL CAOS ---{Colors.RESET}")
        for p in player.active_pacts:
            print(f" - {p.upper()}")
            
    if player.relics:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}--- RELIQUIE ATTIVE ---{Colors.RESET}")
        for r in player.relics:
            print(f" - {r['name']}: {r['desc']}")
            
    archive_buffs = []
    if is_book_unlocked("bestiario", PROFILE_MANAGER._data): archive_buffs.append("Conoscenza (Bestiario): +10% Danni vs Boss")
    if is_book_unlocked("diario_silas", PROFILE_MANAGER._data): archive_buffs.append("Conoscenza (Silas): +5% Oro, +5% Fuga")
    if is_book_unlocked("cronache_ere", PROFILE_MANAGER._data): archive_buffs.append("Conoscenza (Ere Antiche): +5 Difesa")
    if archive_buffs:
        print(f"\n{Colors.CYAN}{Colors.BOLD}--- SINERGIE DELL'ARCHIVIO ---{Colors.RESET}")
        for b in archive_buffs: print(f" - {b}")
        
    print("\n")
    input("Premi INVIO per tornare all'esplorazione...")
