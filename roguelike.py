import random
import time
import traceback
from ui import Colors, clear_screen, delay_print, get_choice
from data_manager import PROFILE, GAME_DATA, RAW_DATA, save_profile, get_element_icon
from entities import Player, Enemy
from rooms import combat_room, mystery_room, event_room, vendor_room, campfire_room, treasure_room, trap_room
from inventory_menu import show_inventory_menu

def evaluate_run(player: Player, floor: int, infinite: bool):
    print("\n" + ("="*50))
    if player.hp <= 0:
        delay_print(f"{Colors.RED}S E I   M O R T O.{Colors.RESET}")
        player.essence_gathered += int(player.gold * 0.20); PROFILE["stats"]["total_deaths"] += 1
    elif player.escaped:
        delay_print(f"{Colors.GREEN}S E I   F U G G I T O.{Colors.RESET}"); player.essence_gathered += player.gold
        
    player.essence_gathered += (player.bosses_killed * 50)
    
    pact_multi = 1.0 + sum([GAME_DATA["meta"]["pacts"][p]["bonus"] for p in player.active_pacts])
    final_essence = int(player.essence_gathered * pact_multi)
    if infinite and floor > 30: final_essence = int(final_essence * 1.5)
    
    PROFILE["essence"] += final_essence
    PROFILE["stats"]["total_gold"] += player.gold

    print(f"Piano raggiunto: {floor} | Boss: {player.bosses_killed}")
    print(f"Moltiplicatore Maledizioni: {pact_multi}x")
    print(f"Essenza Astrale ottenuta: {Colors.CYAN}✨ {final_essence}{Colors.RESET}")
    
    c_id = player.class_id
    xp_gained = (floor * 10) + (player.bosses_killed * 50)
    curr_xp = PROFILE["class_xp"].get(c_id, 0) + xp_gained
    curr_lvl = PROFILE["class_lvl"].get(c_id, 1)
    PROFILE["class_xp"][c_id] = curr_xp
    
    print(f"\n{Colors.MAGENTA}[ Maestria {player.role} ] +{xp_gained} XP (Totale: {curr_xp}){Colors.RESET}")
    reqs = GAME_DATA["meta"]["mastery_xp_requirements"]
    while curr_lvl < 5 and curr_xp >= reqs[str(curr_lvl + 1)]:
        curr_lvl += 1; PROFILE["class_lvl"][c_id] = curr_lvl
        print(f"{Colors.YELLOW}*** MAESTRIA SALITA AL LIVELLO {curr_lvl}! ***{Colors.RESET}")
        reward = GAME_DATA["classes"][c_id]["mastery"].get(str(curr_lvl), {"desc": "Nessun bonus disponibile (In Sviluppo).", "type": "null", "id": "null"})
        print(f"Sbloccato: {reward['desc']}")
        if reward.get("type") in ["unlock", "class"] and reward.get("id", "null") != "null" and reward.get("id") not in PROFILE["unlocked_ids"]:
            PROFILE["unlocked_ids"].append(reward.get("id"))
            
    print(f"\n{Colors.CYAN}[ Imprese ]{Colors.RESET}")
    max_w_lvl = max([i.level for i in player.inventory if i.type == 'weapon'] + [player.weapon.level])
    if "total_bosses" not in PROFILE["stats"]: PROFILE["stats"]["total_bosses"] = 0
    PROFILE["stats"]["total_bosses"] += player.bosses_killed
    
    feats_check = {
        "feat_pacifista": player.run_tracker.get("escapes", 0),
        "feat_fabbro": player.run_tracker.get("fusions", 0),
        "feat_vetro": 1 if player.run_tracker.get("no_hit_boss_done") else 0,
        "feat_suicida": 1 if player.run_tracker.get("kill_1_hp_done") else 0,
        "feat_avaro": player.gold if (player.escaped or (not infinite and floor > 30)) else 0,
        "feat_genio_elementale": 1 if max_w_lvl >= 5 else 0,
        "feat_sopravvissuto": 1 if floor >= 10 and not player.run_tracker.get("rested") else 0,
        "feat_epuratore": PROFILE["stats"]["total_bosses"],
        "feat_mani_bucate": player.run_tracker.get("gold_spent", 0),
        "feat_equilibrista": 1 if player.weapon.element != player.armor.element and player.weapon.element != "Normale" and player.armor.element != "Normale" and (player.escaped or (not infinite and floor > 30)) else 0,
        "feat_lama_cristallo": 1 if floor >= 15 and not player.run_tracker.get("weapon_changed") else 0,
        "feat_furia_cieca": 1 if player.run_tracker.get("blind_fury_done") else 0,
        "feat_tiratore_scelto": player.run_tracker.get("super_effective_hits", 0),
        "feat_assaggiatore": 1 if player.run_tracker.get("1_hp_survive") else 0
    }

    for f_id, f_data in GAME_DATA["meta"]["feats"].items():
        if f_id in PROFILE["completed_feats"]: continue
        if feats_check.get(f_id, 0) >= f_data["target"]:
            print(f"{Colors.GREEN}Impresa Completata: {f_data['name']}!{Colors.RESET}"); PROFILE["completed_feats"].append(f_id)
            if f_data["reward_type"] in ["unlock", "class"] and f_data["reward_id"] not in PROFILE["unlocked_ids"]: PROFILE["unlocked_ids"].append(f_data["reward_id"])
            elif f_data["reward_type"] == "perk": PROFILE["perks"][f_data["reward_id"]] = True
            elif f_data["reward_type"] == "trait": print(f"Nuovo Tratto Sbloccato: {f_data['name']}")

    print("="*50); save_profile(PROFILE)
    input(f"\n{Colors.CYAN}Premi INVIO per tornare al Menu Principale...{Colors.RESET}")

# --- HUB E LOOP DI GIOCO ---
def base_camp_fire():
    while True:
        clear_screen()
        print(f"{Colors.CYAN}--- IL FUOCO DELL'ANIMA --- Essenza: ✨{PROFILE['essence']}{Colors.RESET}")
        
        perk_defs = [
            ("hp_lvl", "Vigore Ereditario", "+15 HP Max", 5, lambda l: 50 + (l*50), False),
            ("gold_lvl", "Tasche Profonde", "+20 Oro Iniziale", 3, lambda l: 100 + (l*100), False),
            ("discount_lvl", "Mercanteggiare", "-10% Prezzi Negozio", 3, lambda l: 150 + (l*100), False),
            ("sesto_senso", "Sesto Senso", "Prevedi bivi", 1, lambda l: 300, True),
            ("dodge_lvl", "Schivata Istintiva", "+2% Schivata Base", 5, lambda l: 100 + (l*50), False),
            ("acc_lvl", "Mira Perfetta", "+3% Precisione Base", 5, lambda l: 100 + (l*50), False),
            ("exp_lvl", "Studioso del Caos", "+5% EXP dai nemici", 3, lambda l: 300 + (l*300), False),
            ("farmacista", "Farmacista", "+1 Pozione iniziale", 1, lambda l: 1500, True),
            ("altare_benedizione", "Benedizione dell'Altare", "Inizi con 1 Reliquia casuale", 1, lambda l: 2000, True),
            ("riciclatore_lvl", "Riciclatore", "+10% ricavo vendite", 3, lambda l: 200 + (l*150), False),
            ("banca_anima_lvl", "Banca dell'Anima", "+5% Oro raccolto in totale", 3, lambda l: 250 + (l*250), False),
            ("artigiano_lvl", "Artigiano", "+1 ATK arma iniziale", 3, lambda l: 400 + (l*300), False),
            ("pelle_dura_lvl", "Pelle Dura", "+1 DEF armatura iniziale", 3, lambda l: 400 + (l*300), False),
            ("speranza_luce_lvl", "Speranza di Luce", "Recuperi HP ad ogni piano", 3, lambda l: 500 + (l*400), False)
        ]
        
        for i, (p_key, p_name, p_desc, p_max, p_cost_func, p_bool) in enumerate(perk_defs):
            lvl = PROFILE["perks"].get(p_key, 0)
            if p_bool:
                status = "SBLOCCATO" if lvl else "BLOCCATO"
                cost = "MAX" if lvl else f"✨{p_cost_func(0)}"
                print(f"{i+1:2}. {p_name}[{status}] ({p_desc}) - Costo: {cost}")
            else:
                cost = "MAX" if lvl >= p_max else f"✨{p_cost_func(lvl)}"
                print(f"{i+1:2}. {p_name}[Lv.{lvl}/{p_max}] ({p_desc}) - Costo: {cost}")
                
        print(" 0. Indietro")
        p_c = get_choice("> ")
        if p_c == '0': break
        
        try:
            idx = int(p_c) - 1
            if 0 <= idx < len(perk_defs):
                p_key, p_name, p_desc, p_max, p_cost_func, p_bool = perk_defs[idx]
                lvl = PROFILE["perks"].get(p_key, 0)
                cost = p_cost_func(0) if p_bool else p_cost_func(lvl)
                
                can_buy = (p_bool and not lvl) or (not p_bool and lvl < p_max)
                if can_buy and PROFILE['essence'] >= cost:
                    PROFILE['essence'] -= cost
                    if p_bool: PROFILE["perks"][p_key] = True
                    else: PROFILE["perks"][p_key] = lvl + 1
                    save_profile(PROFILE)
        except ValueError:
            pass

def base_camp_forge():
    while True:
        clear_screen()
        print(f"{Colors.CYAN}--- FORGIA DIMENSIONALE --- Essenza: ✨{PROFILE['essence']}{Colors.RESET}")
        lkd =[i for cat in["weapons", "armors", "consumables", "relics"] for i in RAW_DATA[cat] if "unlock_id" in i and i["unlock_id"] not in PROFILE["unlocked_ids"]]
        if not lkd: print("Tutto sbloccato!")
        else:
            for i, it in enumerate(lkd):
                cost = it.get('unlock_cost', 0)
                cost_str = f"✨{cost}" if cost > 0 else "Sbloccabile tramite Imprese"
                print(f"{i+1}. {it['name']} ({it.get('desc', '')}) - Costo: {cost_str}")
        print("0. Indietro")
        fc = get_choice("> ")
        if fc == '0': break
        try:
            idx = int(fc)-1
            if 0<=idx<len(lkd):
                cost = lkd[idx].get("unlock_cost", 0)
                if PROFILE['essence']>=cost and cost>0:
                    PROFILE['essence']-=cost; PROFILE["unlocked_ids"].append(lkd[idx]["unlock_id"]); save_profile(PROFILE)
                    print(f"{Colors.GREEN}Sbloccato: {lkd[idx]['name']}!{Colors.RESET}")
                    for cat in["weapons", "armors", "consumables", "relics"]: GAME_DATA[cat] =[x for x in RAW_DATA[cat] if x.get("unlock_id") is None or x["unlock_id"] in PROFILE["unlocked_ids"]]
                    time.sleep(1)
        except ValueError: pass

def base_camp_tavern():
    while True:
        clear_screen()
        print(f"{Colors.CYAN}--- LA TAVERNA --- Essenza: ✨{PROFILE['essence']}{Colors.RESET}")
        lkc =[(c_id, c) for c_id, c in RAW_DATA["classes"].items() if not c.get("unlocked_by_default") and c_id not in PROFILE["unlocked_ids"] and c.get("unlock_id") not in PROFILE["unlocked_ids"]]
        if not lkc: print("Tutti reclutati!")
        else:
            for i, (c_id, c) in enumerate(lkc): print(f"{i+1}. {Colors.BOLD}{c['role']}{Colors.RESET} ({c['desc']}) - Costo: ✨{c.get('unlock_cost', 0)}")
        print("0. Indietro")
        cc = get_choice("> ")
        if cc == '0': break
        try:
            idx = int(cc)-1
            if 0<=idx<len(lkc) and PROFILE['essence']>=lkc[idx][1].get("unlock_cost", 0) and lkc[idx][1].get("unlock_cost", 0)>0:
                PROFILE['essence']-=lkc[idx][1]["unlock_cost"]; PROFILE["unlocked_ids"].append(lkc[idx][1]["unlock_id"]); save_profile(PROFILE)
                print(f"{Colors.GREEN}Reclutato: {lkc[idx][1]['role']}!{Colors.RESET}"); time.sleep(1)
        except ValueError: pass

def base_camp_grimoire():
    clear_screen()
    print(f"{Colors.CYAN}--- GRIMORIO ---{Colors.RESET}")
    for f_id, f in GAME_DATA["meta"]["feats"].items():
        st = f"{Colors.GREEN}[V]{Colors.RESET}" if f_id in PROFILE["completed_feats"] else f"{Colors.RED}[X]{Colors.RESET}"
        print(f"{st} {f['name']}: {f['desc']}")
    print(f"\n{Colors.CYAN}--- MAESTRIA CLASSI ---{Colors.RESET}")
    for c_id, c in RAW_DATA["classes"].items():
        if c.get("unlocked_by_default") or c_id in PROFILE["unlocked_ids"] or c.get("unlock_id") in PROFILE["unlocked_ids"]:
            print(f"{c['role']}: Lv.{PROFILE['class_lvl'].get(c_id, 1)} (XP: {PROFILE['class_xp'].get(c_id, 0)})")
    input("\nPremi INVIO per tornare indietro...")

def base_camp():
    while True:
        clear_screen()
        print(f"{Colors.MAGENTA}{Colors.BOLD}=== 🏕️ IL CAMPO BASE ==={Colors.RESET}")
        print(f"Essenza: {Colors.CYAN}✨ {PROFILE['essence']}{Colors.RESET}")
        print("1. Il Fuoco dell'Anima (Potenziamenti Base)")
        print("2. La Forgia Dimensionale (Sblocca Oggetti)")
        print("3. La Taverna (Recluta Eroi)")
        print("4. Grimorio e Imprese")
        print("0. Torna al Menu Principale")
        
        choice = get_choice("\nScegli > ")
        if choice == '1':
            base_camp_fire()
        elif choice == '2':
            base_camp_forge()
        elif choice == '3':
            base_camp_tavern()
        elif choice == '4':
            base_camp_grimoire()
        elif choice == '0':
            break

def play_game(infinite_mode=False):
    clear_screen()
    print(f"\n{Colors.CYAN}Scegli il tuo Eroe:{Colors.RESET}")
    avail_c = {c_id: c for c_id, c in RAW_DATA["classes"].items() if c.get("unlocked_by_default") or c_id in PROFILE["unlocked_ids"] or c.get("unlock_id") in PROFILE["unlocked_ids"]}
    
    avail_c_list = list(avail_c.items())
    for i, (c_id, c) in enumerate(avail_c_list): 
        print(f"{i+1}. {Colors.BOLD}{c['role'].upper()}{Colors.RESET} (Lv. Maestria: {PROFILE['class_lvl'].get(c_id, 1)})")
        
    while True:
        c_idx_str = get_choice("Classe (Numero): ")
        try:
            idx = int(c_idx_str) - 1
            if 0 <= idx < len(avail_c_list):
                c_choice = avail_c_list[idx][0]
                break
        except ValueError: pass
    
    avail_t_list =[]
    for t_id, t in GAME_DATA["meta"]["traits"].items():
        ul = True
        if t["unlock_req"] == "deaths_10" and PROFILE["stats"]["total_deaths"] < 10: ul = False
        elif t["unlock_req"] == "gold_5000" and PROFILE["stats"]["total_gold"] < 5000: ul = False
        elif t["unlock_req"] not in ["none", "deaths_10", "gold_5000"] and t["unlock_req"] not in PROFILE.get("completed_feats", []) and t["unlock_req"] not in PROFILE.get("unlocked_ids", []): ul = False
        if ul: avail_t_list.append((t_id, t))
        
    if len(avail_t_list) == 1:
        t_choice = avail_t_list[0][0]
    else:
        print(f"\n{Colors.CYAN}Scegli un Tratto di partenza:{Colors.RESET}")
        for i, (t_id, t) in enumerate(avail_t_list):
            print(f"{i+1}. {Colors.BOLD}{t['name']}{Colors.RESET} ({t['desc']})")
            
        while True:
            t_idx_str = get_choice("Tratto (Numero): ")
            try:
                idx = int(t_idx_str) - 1
                if 0 <= idx < len(avail_t_list):
                    t_choice = avail_t_list[idx][0]
                    break
            except ValueError: pass

    active_pacts = []
    if PROFILE["won_normal"]:
        print(f"\n{Colors.RED}I PATTI DEL CAOS{Colors.RESET}")
        print("Attiva le maledizioni per aumentare il moltiplicatore di Essenza.")
        avail_p = GAME_DATA["meta"]["pacts"]
        for p_id, p in avail_p.items():
            ans = get_choice(f"Attivare '{p['name']}'? ({p['desc']})[s/N]: ").lower()
            if ans == 's': active_pacts.append(p_id)

    player = Player(c_choice, t_choice, active_pacts)
    delay_print(f"\nLe porte si chiudono alle tue spalle, {player.role}.", 0.03); time.sleep(1)
    
    weights_def = GAME_DATA["meta"]["rooms"]["weights"].copy()
    for r in player.relic_effects: r.modify_room_weights(weights_def)
        
    cooldowns_def = GAME_DATA["meta"]["rooms"]["cooldowns"]
    room_cooldowns = {k: 0 for k in weights_def.keys()}
    
    floor = 1
    while player.hp > 0 and not player.escaped:
        if not infinite_mode and floor > 30:
            clear_screen()
            print(f"{Colors.YELLOW}{Colors.BOLD}="*50); delay_print("H A I   V I N T O ! ! !"); print("="*50 + Colors.RESET)
            PROFILE["won_normal"] = True; player.essence_gathered += 1000; break

        clear_screen()
        delay_print(f"\n{Colors.MAGENTA}{Colors.BOLD}==== PIANO {floor} ===={Colors.RESET}", 0.05)
        
        sp_lvl = PROFILE["perks"].get("speranza_luce_lvl", 0)
        if sp_lvl > 0 and player.hp < player.max_hp:
            player.hp = min(player.max_hp, player.hp + sp_lvl)
            print(f"{Colors.GREEN}La Speranza di Luce ti rigenera {sp_lvl} HP. ({player.hp}/{player.max_hp}){Colors.RESET}")
            
        if player.base_acc < 50: player.run_tracker["blind_fury_done"] = True
        
        for step in range(1, 6):
            if player.hp <= 0 or player.escaped: break
            
            for k in room_cooldowns:
                if room_cooldowns[k] > 0: room_cooldowns[k] -= 1
            
            if step == 5: doors =[{"type": "boss", "enemy": Enemy(floor, True, active_pacts)}]
            else:
                doors =[]
                while True:
                    avail_rooms, avail_weights = [],[]
                    
                    for rt, w in weights_def.items():
                        if room_cooldowns.get(rt, 0) <= 0:
                            avail_rooms.append(rt)
                            avail_weights.append(w)
                    
                    if not avail_rooms: 
                        avail_rooms, avail_weights = ["combat"],[100]

                    t1 = random.choices(avail_rooms, weights=avail_weights)[0]
                    t2 = random.choices(avail_rooms, weights=avail_weights)[0]
                    
                    if t1 == t2: continue 
                    combo = {t1, t2}
                    if combo == {"trap", "treasure"} or combo == {"trap", "vendor"} or combo == {"mystery", "mystery"}: 
                        continue 
                    break

                room_cooldowns[t1] = cooldowns_def.get(t1, 0) + 1
                room_cooldowns[t2] = cooldowns_def.get(t2, 0) + 1

                for rt in[t1, t2]:
                    d = {"type": rt}
                    if rt == "combat": d["enemy"] = Enemy(floor, False, active_pacts)
                    if rt == "event": d["event_id"] = random.choice(list(GAME_DATA["events"].keys()))
                    doors.append(d)
            
            while True:
                print(f"\n{Colors.CYAN}--- Piano {floor} | Esplorazione {step}/5 ---{Colors.RESET}")
                print(f"❤️  HP: {Colors.GREEN}{player.hp}/{player.max_hp}{Colors.RESET} | 💰 Oro: {Colors.YELLOW}{player.gold}{Colors.RESET}")
                
                for i, d in enumerate(doors):
                    t_str = d["type"].upper()
                    if PROFILE["perks"]["sesto_senso"]:
                        if d["type"] == "combat": t_str += f" ({d['enemy'].name} {get_element_icon(d['enemy'].element)})"
                        elif d["type"] == "event": t_str += f" ({GAME_DATA['events'][d['event_id']]['title']})"
                        elif d["type"] == "mystery": t_str += f" ({Colors.MAGENTA}Aura illeggibile{Colors.RESET})"
                    print(f"{i+1}. Entra: [{t_str}]")
                print("I. Apri Inventario")
                print("F. Fuga dal Labirinto")
                
                action = get_choice("Scelta > ").upper()
                if action == 'I': show_inventory_menu(player)
                elif action == 'F':
                    clear_screen(); print(f"{Colors.YELLOW}Fuggi portando in salvo le ricchezze.{Colors.RESET}")
                    player.escaped = True; break
                else:
                    try:
                        idx = int(action) - 1
                        if 0 <= idx < len(doors):
                            chosen_door = doors[idx]; clear_screen(); break
                    except ValueError: pass
            
            if player.hp <= 0 or player.escaped: break
            
            rt = chosen_door["type"]
            if rt in ("combat", "boss"): combat_room(player, floor, chosen_door["enemy"])
            elif rt == "vendor": vendor_room(player, floor)
            elif rt == "treasure": treasure_room(player, floor)
            elif rt == "trap": trap_room(player, floor, active_pacts)
            elif rt == "campfire": campfire_room(player, floor)
            elif rt == "event": event_room(player, chosen_door["event_id"], floor)
            elif rt == "mystery": mystery_room(player, floor, active_pacts)
        
        if player.hp > 0 and not player.escaped:
            delay_print(f"\n{Colors.YELLOW}{Colors.BOLD}*** PIANO {floor} SUPERATO! ***{Colors.RESET}", 0.05)
            heal = 20 + (floor * 5)
            if not player.cursed: player.hp = min(player.max_hp, player.hp + heal)
            print(f"Ti riposi prima delle scale. (HP: {player.hp}/{player.max_hp})")
            floor += 1
            if floor > PROFILE["max_floor"]: PROFILE["max_floor"] = floor
            input("\nPremi INVIO per scendere...")

    evaluate_run(player, floor, infinite_mode)

def main():
    try:
        while True:
            clear_screen()
            delay_print(f"{Colors.MAGENTA}{Colors.BOLD}=== IL LABIRINTO DEGLI ELEMENTI E DEL CAOS ==={Colors.RESET}", 0.01)
            print(f"\n{Colors.CYAN}[ MENU PRINCIPALE ]{Colors.RESET}")
            print("1. Inizia Run (Standard - 30 Piani)")
            print("2. Campo Base (Potenziamenti, Forgia, Taverna)")
            if PROFILE["won_normal"]: print(f"3. {Colors.RED}Inizia Run Infinita (Oltre i 30 Piani){Colors.RESET}")
            print("0. Esci dal gioco")
            
            choice = get_choice("\nScelta > ")
            if choice == '1': play_game(infinite_mode=False)
            elif choice == '2': base_camp()
            elif choice == '3' and PROFILE["won_normal"]: play_game(infinite_mode=True)
            elif choice == '0': clear_screen(); print("Arrivederci!"); break
    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}ERRORE IMPREVISTO! Il gioco è andato in crash:{Colors.RESET}")
        traceback.print_exc()
        input(f"\n{Colors.CYAN}Premi INVIO per uscire...{Colors.RESET}")

if __name__ == "__main__":
    main()