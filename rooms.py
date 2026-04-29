import random
import time
from typing import List
from ui import Colors, clear_screen, delay_print, get_choice
from data_manager import GAME_DATA, PROFILE, MULTIPLIERS, get_element_icon
from entities import Player, Enemy, generate_weapon, generate_armor, generate_accessory, generate_potion, get_random_relic

def combat_room(player: Player, floor: int, enemy_instance: Enemy):
    if enemy_instance.modifier == "normal":
        delay_print(f"\n{random.choice(GAME_DATA['lore']['boss' if enemy_instance.is_boss else 'combat'])}")
        boss_tag = f"{Colors.MAGENTA} [BOSS]{Colors.RESET}" if enemy_instance.is_boss else ""
        delay_print(f"{Colors.RED}!!! Incontri un {enemy_instance.name.upper()}{boss_tag} [{get_element_icon(enemy_instance.element)}] !!!{Colors.RESET}", 0.04)
    
    boss_hit_taken = False
    if "clessidra_destino" in player.relic_ids: enemy_instance.base_dodge = max(0, enemy_instance.base_dodge - 20)
    shield_active = "scudo_cristallo" in player.relic_ids
    focused_attack = False
    resonance = player._get_resonance_element()
    burn_dmg = 0
    
    # Risonanza passiva pre-combattimento
    if resonance == "Acqua": enemy_instance.atk = max(1, int(enemy_instance.atk * 0.85)); print(f"{Colors.CYAN}✨ Risonanza d'Acqua! L'attacco del nemico è ridotto del 15%!{Colors.RESET}")
    if resonance == "Vento": player.temp_dodge = 15; print(f"{Colors.CYAN}✨ Risonanza di Vento! +15% Schivata!{Colors.RESET}")
    if resonance == "Terra": player.temp_def = 5; print(f"{Colors.CYAN}✨ Risonanza di Terra! +5 Difesa fissa!{Colors.RESET}")

    def on_enemy_death():
        print(f"\n{Colors.YELLOW}{Colors.BOLD}*** Hai sconfitto {enemy_instance.name}! ***{Colors.RESET}")
        if player.hp == 1: player.run_tracker["kill_1_hp_done"] = True
        if enemy_instance.is_boss and not boss_hit_taken: player.run_tracker["no_hit_boss_done"] = True
        
        g_drop = enemy_instance.gold_drop * 3 if player.midas else enemy_instance.gold_drop
        if "tasca_dorata" in player.relic_ids: g_drop = int(g_drop * 1.25)
        if "idolo_avidita" in player.relic_ids: g_drop *= 2
        g_drop = int(g_drop * (1 + PROFILE["perks"].get("banca_anima_lvl", 0) * 0.05))
        
        player.gold += g_drop
        if "pergamena_oro" in player.relic_ids: player.hp = min(player.max_hp, player.hp + 2); print(f"{Colors.GREEN}La Pergamena d'Oro ti guarisce di 2 HP!{Colors.RESET}")
        print(f"Ottieni {Colors.YELLOW}{g_drop} oro{Colors.RESET}.")
        player.gain_exp(enemy_instance.exp_drop)
        
        if "contratto_demoniaco" in player.relic_ids:
            player.hp -= 5; print(f"{Colors.RED}Il Contratto Demoniaco esige un tributo di sangue (5 HP)...{Colors.RESET}")
        
        if "cuore_troll" in player.relic_ids:
            player.max_hp += 2; player.hp += 2
            print(f"{Colors.GREEN}Il Cuore di Troll pulsa: +2 HP Massimi!{Colors.RESET}")
            
        if "teschio_sangue" in player.relic_ids:
            player.max_hp += 1; player.hp += 1
            print(f"{Colors.RED}Il Teschio di Sangue si nutre della morte: +1 HP Massimo!{Colors.RESET}")
            
        if "pietra_filosofale" in player.relic_ids and random.random() < 0.20:
            player.gold += enemy_instance.exp_drop; print(f"{Colors.YELLOW}La Pietra Filosofale trasforma l'XP in {enemy_instance.exp_drop} Oro!{Colors.RESET}"); enemy_instance.exp_drop = 0
        
        if enemy_instance.is_boss:
            player.bosses_killed += 1
            relic = get_random_relic(player)
            if relic: player.add_relic(relic)
            else:
                drop = generate_weapon(floor + 2, True) if random.random() > 0.5 else generate_armor(floor + 2, True)
                print(f"\n{Colors.MAGENTA}DROP LEGGENDARIO: {drop.display_name}!{Colors.RESET}")
                player.inventory.append(drop)
        elif enemy_instance.modifier == "hard":
            drop = generate_weapon(floor, False) if random.random() > 0.5 else generate_armor(floor, False)
            print(f"\n{Colors.MAGENTA}Il nemico lascia cadere: {drop.display_name}!{Colors.RESET}")
            player.inventory.append(drop)
        elif enemy_instance.modifier == "easy":
            print(f"\n{Colors.CYAN}Il nemico era troppo debole e non aveva nulla con sé.{Colors.RESET}")
        elif random.random() > 0.6:
            drop = generate_potion(floor)
            print(f"Trovi: {Colors.CYAN}{drop.display_name}{Colors.RESET}!")
            player.inventory.append(drop)
        input("\nPremi INVIO per continuare...")

    while enemy_instance.hp > 0 and player.hp > 0:
        player.temp_def = 0; player.temp_dodge = 0
        if player.role in["Guerriero", "Berserker"]:
            def_type, def_txt = "counter", "Difesa Aggressiva (Dimezza danni e Contrattacca)"
        elif player.role == "Ladro":
            def_type, def_txt = "focus", "Concentrazione (Dimezza danni, prossimo colpo Critico 100%)"
        else:
            def_type, def_txt = "recovery", "Riparo Magico (Dimezza danni e Cura 5% HP)"

        print(f"\n{Colors.BOLD}--- ⚔️ IN COMBATTIMENTO ⚔️ ---{Colors.RESET}")
        print(f"Tu: {Colors.GREEN}{player.hp}/{player.max_hp} HP{Colors.RESET} | {enemy_instance.name}: {Colors.RED}{enemy_instance.hp} HP{Colors.RESET}")
        print("1. Attacca")
        print(f"2. {def_txt}")
        print("3. Apri Inventario (Usa oggetto = Costa Turno)")
        print("4. Tenta la Fuga")
        
        choice = get_choice("Cosa fai? > ")
        is_defending = False
        
        if choice in['1', '2', '3', '4']: clear_screen()
            
        if choice == '1':
            if "lama_sangue" in player.relic_ids:
                player.hp -= 3
                print(f"{Colors.RED}La Lama di Sangue si nutre di te! Subisci 3 danni.{Colors.RESET}")
                if player.hp <= 0:
                    print(f"\n{Colors.RED}{Colors.BOLD}Sei stato consumato dalla tua stessa arma...{Colors.RESET}"); input("\nPremi INVIO per continuare..."); return
            
            multiplier = MULTIPLIERS.get(player.weapon.element, {}).get(enemy_instance.element, 1.0)
            if "lente_prismatica" in player.relic_ids:
                if multiplier > 1.0: multiplier = 2.0
                elif multiplier < 1.0: multiplier = 0.5
            
            if focused_attack:
                hit_chance = 100
                dmg_dealt = int(max(1, player.get_total_atk() + random.randint(-1, 2)) * multiplier * 2)
                eff = f"{Colors.GREEN}[CRITICO!]{Colors.RESET} " + (f"{Colors.GREEN}[SUPER EFFICACE!]{Colors.RESET}" if multiplier > 1.0 else "")
                focused_attack = False
            else:
                hit_chance = max(10, min(100, 85 + player.base_acc - enemy_instance.base_dodge + (15 if multiplier > 1.0 else -20 if multiplier < 1.0 else 0)))
                if "Ascia del Boia" in player.weapon.name: hit_chance -= 15
                dmg_dealt = int(max(1, player.get_total_atk() + random.randint(-1, 2)) * multiplier)
                eff = f"{Colors.GREEN}[SUPER EFFICACE!]{Colors.RESET}" if multiplier > 1.0 else f"{Colors.RED}[Poco efficace...]{Colors.RESET}" if multiplier < 1.0 else ""
                if "Ascia del Boia" in player.weapon.name and random.random() < 0.35: dmg_dealt *= 2; eff += f" {Colors.MAGENTA}[CRITICO DELL'ASCIA!]{Colors.RESET}"

            # Bonus critico da accessorio
            if player.accessory and player.accessory.bonus_type == "crit_chance" and not focused_attack:
                if random.randint(1, 100) <= player.accessory.bonus_value:
                    dmg_dealt *= 2; eff += f" {Colors.MAGENTA}[CRITICO!]{Colors.RESET}"

            if random.randint(1, 100) <= hit_chance:
                if player.class_id == "5" and PROFILE["class_lvl"].get("5", 1) >= 2 and player.hp < player.max_hp * 0.3: dmg_dealt = int(dmg_dealt * 1.5)
                if multiplier > 1.0 and enemy_instance.is_boss:
                    if "super_effective_hits" not in player.run_tracker: player.run_tracker["super_effective_hits"] = 0
                    player.run_tracker["super_effective_hits"] += 1
                if "corona_re_folle" in player.relic_ids and (multiplier > 1.0 or "[CRITICO!]" in eff): dmg_dealt = int(dmg_dealt * 1.5); eff += f" {Colors.MAGENTA}[CORONA DEL FOLLE!]{Colors.RESET}"
                if "contratto_demoniaco" in player.relic_ids: dmg_dealt *= 2
                # Risonanza Tenebra: ignora difesa nemica (danno pieno)
                if resonance == "Tenebra": dmg_dealt += 5; eff += f" {Colors.MAGENTA}[TENEBRA]{Colors.RESET}"
                enemy_instance.hp -= dmg_dealt
                print(f"\n-> Colpisci con {player.weapon.name} infliggendo {Colors.CYAN}{dmg_dealt} danni!{Colors.RESET} {eff}")
                if "anello_vampiro_max" in player.relic_ids: player.hp = min(player.max_hp, player.hp + 2); print(f"{Colors.RED}L'Anello Vampirico assorbe 2 HP!{Colors.RESET}")
                # Accessorio lifesteal
                if player.accessory and player.accessory.bonus_type == "lifesteal":
                    ls = player.accessory.bonus_value; player.hp = min(player.max_hp, player.hp + ls)
                    print(f"{Colors.RED}Il monile assorbe {ls} HP!{Colors.RESET}")
                # Risonanza Luce: cura a segno
                if resonance == "Luce":
                    player.hp = min(player.max_hp, player.hp + 3)
                    print(f"{Colors.YELLOW}✨ Risonanza di Luce: +3 HP!{Colors.RESET}")
                # Risonanza Fuoco: accumula ustione
                if resonance == "Fuoco": burn_dmg += 5
                
                if not player.cursed:
                    if player.mage_lifesteal and multiplier > 1.0:
                        h = max(1, dmg_dealt // 10); player.hp = min(player.max_hp, player.hp + h); print(f"{Colors.MAGENTA}Sintonia: Assorbi {h} HP!{Colors.RESET}")
                    if "artiglio_vampiro" in player.relic_ids:
                        player.hp = min(player.max_hp, player.hp + 5); print(f"{Colors.RED}Artiglio Vampirico ti cura 5 HP!{Colors.RESET}")
            else: 
                print(f"\n{Colors.YELLOW}-> Fallisci! {enemy_instance.name} schiva.{Colors.RESET}")
            
            if enemy_instance.hp <= 0:
                on_enemy_death()
                return
                
        elif choice == '2':
            is_defending = True
            if def_type == "counter":
                print(f"\n{Colors.BLUE}-> Sollevi la guardia, pronto a sfruttare l'attacco nemico!{Colors.RESET}")
                if player.class_id == "4" and PROFILE["class_lvl"].get("4", 1) >= 2:
                    player.hp = min(player.max_hp, player.hp + 3); print(f"{Colors.GREEN}Baluardo della Fede: Recuperi 3 HP!{Colors.RESET}")
            elif def_type == "focus": focused_attack = True; print(f"\n{Colors.BLUE}-> Studi il nemico nell'ombra. Il tuo prossimo attacco sarà devastante!{Colors.RESET}")
            elif def_type == "recovery":
                if player.cursed: print(f"\n{Colors.BLUE}-> Ti difendi, ma la Maledizione blocca il tuo recupero magico.{Colors.RESET}")
                else:
                    heal_amt = max(1, player.max_hp // 20); player.hp = min(player.max_hp, player.hp + heal_amt)
                    print(f"\n{Colors.BLUE}-> Evochi una barriera vitale. {Colors.GREEN}Recuperi {heal_amt} HP!{Colors.RESET}")
                    
        elif choice == '3':
            action = player.manage_inventory(in_combat=True)
            if action == "smoke_bomb": player.run_tracker["escapes"] += 1; return
            elif action == "fiala_caos":
                caos_dmg = random.randint(10, 100); enemy_instance.hp -= caos_dmg
                print(f"{Colors.MAGENTA}Esplosione caotica: {caos_dmg} danni puri!{Colors.RESET}")
                if enemy_instance.hp <= 0: on_enemy_death(); return
            elif action == "turn_used": pass 
            else: continue
            
        elif choice == '4':
            if enemy_instance.is_boss: print(f"\n{Colors.RED}-> Impossibile fuggire dai Boss!{Colors.RESET}"); continue
            
            if "bussola_perfetta" in player.relic_ids: f_chance = 100
            else: f_chance = max(10, min(90, 20 + player.get_dodge() - enemy_instance.base_dodge + (20 if PROFILE["perks"]["scarpisti"] else 0)))
                
            if random.randint(1, 100) <= f_chance:
                print(f"\n{Colors.YELLOW}-> Sei riuscito a scappare!{Colors.RESET}"); player.run_tracker["escapes"] += 1; input("\nPremi INVIO..."); return
            else: print(f"\n{Colors.RED}-> Tentativo di fuga fallito!{Colors.RESET}")
        else: continue
            
        # TURNO NEMICO
        if enemy_instance.hp > 0:
            en_multiplier = MULTIPLIERS.get(enemy_instance.element, {}).get(player.armor.element, 1.0)
            if "lente_prismatica" in player.relic_ids:
                if en_multiplier > 1.0: en_multiplier = 2.0
                elif en_multiplier < 1.0: en_multiplier = 0.5
            
            en_hit_chance = max(10, min(100, 85 + enemy_instance.base_acc - player.get_dodge() + (15 if en_multiplier > 1.0 else -20 if en_multiplier < 1.0 else 0)))

            if random.randint(1, 100) <= en_hit_chance:
                dmg_taken = max(0, int((enemy_instance.atk + random.randint(-1, 2)) * en_multiplier) - player.armor.defense - player.temp_def)
                if is_defending:
                    if "pietra_luna" in player.relic_ids: dmg_taken = max(0, int((enemy_instance.atk + random.randint(-1, 2)) * en_multiplier) - int(player.armor.defense * 1.5))
                    dmg_taken //= 2
                
                if "campanella_spiriti" in player.relic_ids and random.random() < 0.15: dmg_taken = 0; print(f"{Colors.CYAN}La Campanella degli Spiriti rintocca... L'attacco ti passa attraverso!{Colors.RESET}")
                
                if dmg_taken > 0 and shield_active:
                    print(f"{Colors.CYAN}<- {enemy_instance.name} ti colpisce... Ma lo Scudo di Cristallo assorbe il danno!{Colors.RESET}")
                    shield_active = False; dmg_taken = 0
                
                en_eff = f"{Colors.RED}[Sei vulnerabile!]{Colors.RESET}" if en_multiplier > 1.0 else f"{Colors.GREEN}[Resisti!]{Colors.RESET}" if en_multiplier < 1.0 else ""
                
                if dmg_taken > 0: 
                    boss_hit_taken = True
                    player.hp -= dmg_taken
                    dif = f"{Colors.BLUE}[DIFESA]{Colors.RESET}" if is_defending else ""
                    print(f"<- {enemy_instance.name} ti colpisce! Subisci {Colors.RED}{dmg_taken} danni{Colors.RESET}. {en_eff}{dif}")
                    
                    # Accessorio riflesso danni
                    reflect_total = 0
                    if "armatura_spilli" in player.relic_ids: reflect_total += 3
                    if player.accessory and player.accessory.bonus_type == "reflect": reflect_total += player.accessory.bonus_value
                    if reflect_total > 0:
                        enemy_instance.hp -= reflect_total; print(f"{Colors.YELLOW}Riflessi {reflect_total} danni a {enemy_instance.name}!{Colors.RESET}")
                        if enemy_instance.hp <= 0: on_enemy_death(); return
                    
                    if is_defending and def_type == "counter":
                        enemy_instance.hp -= dmg_taken
                        print(f"{Colors.YELLOW}   ⚔️ CONTRATTACCO! Restituisci {dmg_taken} danni a {enemy_instance.name}!{Colors.RESET}")
                        if enemy_instance.hp <= 0:
                            on_enemy_death()
                            return
                    
                    if player.hp <= 0 and player.benedetto_save:
                        player.hp = 1; player.benedetto_save = False
                        print(f"{Colors.YELLOW}La Benedizione ti salva dal colpo letale!{Colors.RESET}")
                        
                    if player.hp <= 0:
                        print(f"\n{Colors.RED}{Colors.BOLD}Sei caduto in battaglia contro {enemy_instance.name}...{Colors.RESET}")
                        input("\nPremi INVIO per continuare...")
                        return
                elif not shield_active and dmg_taken == 0:
                    print(f"<- {enemy_instance.name} attacca, ma la corazza blocca TUTTO! {en_eff}")
            else: print(f"{Colors.CYAN}<- {enemy_instance.name} attacca... ma riesci a schivarlo!{Colors.RESET}")
            
            # Risonanza Fuoco: danno ustione a fine turno nemico
            if burn_dmg > 0 and enemy_instance.hp > 0:
                enemy_instance.hp -= burn_dmg
                print(f"{Colors.RED}🔥 Risonanza di Fuoco: Ustione infligge {burn_dmg} danni!{Colors.RESET}")
                if enemy_instance.hp <= 0: on_enemy_death(); return

def mystery_room(player: Player, floor: int, active_pacts: List[str]):
    delay_print(f"\n{Colors.MAGENTA}--- LA STANZA DEL MISTERO ---{Colors.RESET}")
    print(f"❤️  HP: {Colors.GREEN}{player.hp}/{player.max_hp}{Colors.RESET} | 💰 Oro: {Colors.YELLOW}{player.gold}{Colors.RESET}\n")
    delay_print("Entri in un ambiente intriso di nebbia magica. I tuoi sensi sono annebbiati...", 0.03)
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
        for i, c in enumerate(ev["choices"]): print(f"{i+1}. {c['text']}")
        choice = get_choice("> ")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(ev["choices"]):
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
                elif action == "fight_elite":
                    print(f"{Colors.RED}{msg}{Colors.RESET}")
                    e = Enemy(floor + 5, True, player.active_pacts) # Elite
                    input("Premi INVIO per combattere..."); combat_room(player, floor, e)
                    if player.hp <= 0: return 
                elif action == "none": print(f"{Colors.CYAN}{msg}{Colors.RESET}")
                
                input("\nPremi INVIO per proseguire...")
                return
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
        elif action == '0': break

def treasure_room(player: Player, floor: int):
    delay_print(f"\n{Colors.YELLOW}{random.choice(GAME_DATA['lore']['treasure'])}{Colors.RESET}")
    gold = random.randint(30, 60) + (floor * 10)
    g = gold * 3 if player.midas else gold
    if "tasca_dorata" in player.relic_ids: g = int(g * 1.25)
    if "idolo_avidita" in player.relic_ids: g *= 2
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

