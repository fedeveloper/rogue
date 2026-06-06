import time
import random
from ui import Colors, clear_screen, get_choice
from data_manager import PROFILE, get_element_icon
from entities import generate_random_element

def show_inventory_menu(player, in_combat=False) -> str:
    while True:
        clear_screen()
        print(f"\n{Colors.MAGENTA}{Colors.BOLD}--- ZAINO E INVENTARIO ---{Colors.RESET}")
        print(f"❤️  HP: {Colors.GREEN}{player.hp}/{player.max_hp}{Colors.RESET} | 💰 Oro: {Colors.YELLOW}{player.gold}{Colors.RESET}")
        print(f"⚔️  Arma: {player.weapon.display_name} (+{player.get_total_atk()} ATK)")
        print(f"🛡️  Armatura: {player.armor.display_name} (+{player.armor.defense} DEF)")
        acc_txt = f"{player.accessory.display_name} ({player.accessory.desc})" if player.accessory else "Nessuno"
        print(f"💍 Monile: {acc_txt}")
        res_el = player._get_resonance_element()
        if res_el: print(f"✨ {Colors.CYAN}RISONANZA ATTIVA: {get_element_icon(res_el)}!{Colors.RESET}")
        if player.relics:
            print(f"🌟 Reliquie attive:")
            for r in player.relics: print(f"   - {Colors.YELLOW}{r['name']}{Colors.RESET}: {r['desc']}")
        print("-" * 55)
        
        display_items = []
        if not player.inventory: print("L'inventario è vuoto.")
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
                if item.type == "weapon": print(f"{disp_idx+1}. [Arma] {item.display_name} (+{item.atk}) - Lv.{item.level}")
                elif item.type == "armor": print(f"{disp_idx+1}. [Armatura] {item.display_name} (+{item.defense}) - Lv.{item.level}")
                elif item.type == "accessory": print(f"{disp_idx+1}. [Monile] {item.display_name} ({item.desc})")
                elif item.type == "consumable": print(f"{disp_idx+1}. [Oggetto] {item.display_name}{count_str}")
                    
        print("\n0. Chiudi Zaino")
        choice = get_choice("Scegli un oggetto da usare/equipaggiare > ")
        if choice == '0': return "closed"
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(display_items):
                real_idx, item, count = display_items[idx]
                
                if item.type == "consumable":
                    if "Bomba Fumogena" in item.name:
                        player.inventory.pop(real_idx)
                        print(f"{Colors.YELLOW}Lanci la bomba fumogena! Fuga garantita.{Colors.RESET}")
                        time.sleep(1)
                        return "smoke_bomb"
                    elif "Fiala del Caos" in item.name:
                        if not in_combat:
                            print(f"{Colors.RED}Puoi usarla solo in combattimento!{Colors.RESET}")
                            time.sleep(1)
                            continue
                        player.inventory.pop(real_idx)
                        print(f"{Colors.MAGENTA}Lanci la Fiala del Caos!{Colors.RESET}")
                        time.sleep(1)
                        return "fiala_caos"
                    elif "Pietra per Affilare" in item.name:
                        player.weapon.atk += 5
                        player.inventory.pop(real_idx)
                        print(f"{Colors.GREEN}Arma affilata! Ora {player.weapon.name} ha {player.weapon.atk} ATK.{Colors.RESET}")
                        input("Premi INVIO...")
                        if in_combat: return "turn_used"
                    elif "Tomo del Caos" in item.name:
                        player.weapon.element = generate_random_element()
                        player.weapon.display_name = f"{player.weapon.name.split('[')[0]}[{get_element_icon(player.weapon.element)}]"
                        player.inventory.pop(real_idx)
                        print(f"{Colors.MAGENTA}Il caos avvolge l'arma! Nuovo elemento: {player.weapon.element}.{Colors.RESET}")
                        input("Premi INVIO...")
                        if in_combat: return "turn_used"
                    elif "Acqua Santa" in item.name:
                        player.inventory.pop(real_idx)
                        player.hp = min(player.max_hp, player.hp + 50)
                        if in_combat:
                            player.temp_def += 5
                            player.temp_dodge += 5
                        print(f"{Colors.GREEN}Bevi l'Acqua Santa: +50 HP e bonus difensivi temporanei! (HP: {player.hp}/{player.max_hp}){Colors.RESET}")
                        input("Premi INVIO...")
                        if in_combat: return "turn_used"
                    elif "Antidoto" in item.name:
                        player.inventory.pop(real_idx)
                        cured = len(player.statuses)
                        player.statuses.clear()
                        player.hp = min(player.max_hp, player.hp + item.heal_amount)
                        print(f"{Colors.GREEN}Bevi l'Antidoto: Curati {cured} stati alterati e recuperati {item.heal_amount} HP!{Colors.RESET}")
                        input("Premi INVIO...")
                        if in_combat: return "turn_used"
                    else:
                        if player.cursed:
                            print(f"{Colors.RED}La tua Maledizione rende inutile la pozione.{Colors.RESET}")
                            player.inventory.pop(real_idx)
                        else:
                            old_hp = player.hp
                            base_h = item.heal_amount
                            for effect in player.relic_effects: base_h = effect.on_heal(player, base_h)
                            if player.class_id == "6" and PROFILE["class_lvl"].get("6", 1) >= 2: base_h = int(base_h * 1.5)
                            h_amt = base_h // 2 if "carestia" in player.active_pacts else base_h
                            
                            player.hp = min(player.max_hp, player.hp + h_amt)
                            print(f"{Colors.GREEN}\n-> Recuperi {player.hp - old_hp} HP! (HP: {player.hp}/{player.max_hp}){Colors.RESET}")
                            if player.thief_save and random.random() < 0.3:
                                print(f"{Colors.CYAN}Abilità Ladro: Hai salvato la pozione!{Colors.RESET}")
                            else:
                                consume = True
                                for effect in player.relic_effects:
                                    if not effect.on_item_use(player, item.name): consume = False
                                if consume: player.inventory.pop(real_idx)
                        input("Premi INVIO...")
                        if in_combat: return "turn_used"
                        
                elif item.type == "weapon":
                    player.run_tracker["weapon_changed"] = True
                    old_w, player.weapon = player.weapon, item
                    player.inventory[real_idx] = old_w
                    print(f"{Colors.GREEN}\n-> Equipaggiato: {player.weapon.display_name}!{Colors.RESET}")
                    input("Premi INVIO...")
                    if in_combat: return "turn_used"
                elif item.type == "armor":
                    old_a, player.armor = player.armor, item
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
            else: 
                print(f"{Colors.RED}Scelta non valida.{Colors.RESET}")
                time.sleep(1)
        except ValueError:
            pass
