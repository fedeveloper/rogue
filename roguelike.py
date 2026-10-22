import random
import shutil
import sys
import time
import traceback
from ui import Colors, clear_screen, delay_print, interactive_menu, display_msg, wait_enter
from data_manager import PROFILE_MANAGER, GAME_DATA, RAW_DATA, get_biome, update_game_data
from entities import Player
from rooms import combat_room, mystery_room, vendor_room, campfire_room, treasure_room, trap_room
from events import event_room
from floor_map import ROWS, SIDES, TALL_MAP_ROWS, generate_floor_map, reachable, render_map, room_label
from inventory_menu import show_inventory_menu, show_player_stats
from archive import show_archive
from codex import show_codex
from constants import TEXT_SPEEDS, SPERANZA_LUCE_PCT_PER_LVL, RATIO_GOLD_TO_ESSENCE_ON_DEATH, BOSS_ESSENCE_BONUS, XP_PER_FLOOR, XP_PER_BOSS, INFINITE_MODE_THRESHOLD, INFINITE_MODE_ESSENCE_MULTIPLIER, BLIND_FURY_MIN_ATTACKS

def _update_class_mastery(player: Player, floor: int):
    c_id = player.class_id
    xp_gained = (floor * XP_PER_FLOOR) + (player.bosses_killed * XP_PER_BOSS)
    curr_xp = PROFILE_MANAGER.get_class_xp(c_id, 0) + xp_gained
    curr_lvl = PROFILE_MANAGER.get_class_lvl(c_id, 1)
    PROFILE_MANAGER.set_class_xp(c_id, curr_xp)
    
    display_msg(f"\n{Colors.MAGENTA}[ Maestria {player.role} ] +{xp_gained} XP (Totale: {curr_xp}){Colors.RESET}")
    reqs = GAME_DATA["meta"]["mastery_xp_requirements"]
    while curr_lvl < 5 and curr_xp >= reqs[str(curr_lvl + 1)]:
        curr_lvl += 1; PROFILE_MANAGER.set_class_lvl(c_id, curr_lvl)
        display_msg(f"{Colors.YELLOW}*** MAESTRIA SALITA AL LIVELLO {curr_lvl}! ***{Colors.RESET}")
        reward = GAME_DATA["classes"][c_id]["mastery"].get(str(curr_lvl), {"desc": "Nessun bonus disponibile (In Sviluppo).", "type": "null", "id": "null"})
        display_msg(f"Sbloccato: {reward['desc']}")
        if reward.get("type") in ["unlock", "class"] and reward.get("id", "null") != "null" and reward.get("id") not in PROFILE_MANAGER.unlocked_ids:
            PROFILE_MANAGER.unlocked_ids.append(reward.get("id"))

def _check_feats(player: Player, floor: int, infinite: bool):
    display_msg(f"\n{Colors.CYAN}[ Imprese ]{Colors.RESET}")
    if "total_bosses" not in PROFILE_MANAGER.stats: PROFILE_MANAGER.stats["total_bosses"] = 0
    PROFILE_MANAGER.stats["total_bosses"] += player.bosses_killed
    
    feats_check = {
        "feat_pacifista": player.run_tracker.get("escapes", 0),
        "feat_fabbro": player.run_tracker.get("fusions", 0),
        "feat_vetro": 1 if player.run_tracker.get("no_hit_boss_done") else 0,
        "feat_suicida": 1 if player.run_tracker.get("kill_1_hp_done") else 0,
        "feat_avaro": player.gold if (player.escaped or (not infinite and floor > INFINITE_MODE_THRESHOLD)) else 0,
        "feat_genio_elementale": 1 if player.run_tracker.get("max_fused_weapon_lvl", 0) >= 5 else 0,
        "feat_sopravvissuto": 1 if floor > 10 and not player.run_tracker.get("rested") else 0,
        "feat_epuratore": PROFILE_MANAGER.stats["total_bosses"],
        "feat_mani_bucate": player.run_tracker.get("gold_spent", 0),
        "feat_equilibrista": 1 if player.weapon.element != player.armor.element and player.weapon.element != "Normale" and player.armor.element != "Normale" and (player.escaped or (not infinite and floor > INFINITE_MODE_THRESHOLD)) else 0,
        "feat_lama_cristallo": 1 if floor >= 15 and not player.run_tracker.get("weapon_changed") else 0,
        "feat_furia_cieca": 1 if player.run_tracker.get("blind_fury_done") else 0,
        "feat_tiratore_scelto": player.run_tracker.get("super_effective_hits", 0),
        "feat_assaggiatore": 1 if player.run_tracker.get("1_hp_survive") else 0
    }

    for f_id, f_data in GAME_DATA["meta"]["feats"].items():
        if f_id in PROFILE_MANAGER.completed_feats: continue
        if feats_check.get(f_id, 0) >= f_data["target"]:
            display_msg(f"{Colors.GREEN}Impresa Completata: {f_data['name']}!{Colors.RESET}"); PROFILE_MANAGER.completed_feats.append(f_id)
            if f_data["reward_type"] in ["unlock", "class"] and f_data["reward_id"] not in PROFILE_MANAGER.unlocked_ids: PROFILE_MANAGER.unlocked_ids.append(f_data["reward_id"])
            elif f_data["reward_type"] == "perk": PROFILE_MANAGER.set_perk(f_data["reward_id"], True)
            elif f_data["reward_type"] == "trait": display_msg(f"Nuovo Tratto Sbloccato: {f_data['name']}")

def evaluate_run(player: Player, floor: int, infinite: bool):
    display_msg("\n" + ("="*50))
    if player.hp <= 0:
        delay_print(f"{Colors.RED}S E I   M O R T O.{Colors.RESET}")
        player.essence_gathered += int(player.gold * RATIO_GOLD_TO_ESSENCE_ON_DEATH); PROFILE_MANAGER.stats["total_deaths"] += 1
    elif player.escaped:
        delay_print(f"{Colors.GREEN}S E I   F U G G I T O.{Colors.RESET}"); player.essence_gathered += player.gold
    elif player.won:
        # La vittoria deve rendere almeno quanto la fuga: tutto l'oro diventa Essenza, più il bonus
        player.essence_gathered += player.gold
        
    player.essence_gathered += (player.bosses_killed * BOSS_ESSENCE_BONUS)
    
    pact_multi = 1.0 + sum([GAME_DATA["meta"]["pacts"][p]["bonus"] for p in player.active_pacts])
    final_essence = int(player.essence_gathered * pact_multi)
    if infinite and floor > INFINITE_MODE_THRESHOLD: final_essence = int(final_essence * INFINITE_MODE_ESSENCE_MULTIPLIER)
    
    PROFILE_MANAGER.essence += final_essence
    PROFILE_MANAGER.stats["total_gold"] += player.gold

    display_msg(f"Piano raggiunto: {floor} | Boss: {player.bosses_killed}")
    display_msg(f"Moltiplicatore Maledizioni: {pact_multi}x")
    display_msg(f"Essenza Astrale ottenuta: {Colors.CYAN}✨ {final_essence}{Colors.RESET}")
    
    _update_class_mastery(player, floor)
    _check_feats(player, floor, infinite)

    display_msg("="*50); PROFILE_MANAGER.save()
    wait_enter(f"\n{Colors.CYAN}Premi INVIO per tornare al Menu Principale...{Colors.RESET}")

# --- HUB E LOOP DI GIOCO ---
# Potenziamenti del Fuoco dell'Anima: (chiave, nome, descrizione, livello massimo, costo per livello, sì/no)
PERK_DEFS = [
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
    ("speranza_luce_lvl", "Speranza di Luce", f"+{int(SPERANZA_LUCE_PCT_PER_LVL*100)}% HP Max recuperati a ogni piano", 3, lambda l: 500 + (l*400), False)
]

def base_camp_fire():
    while True:
        clear_screen()
        perk_defs = PERK_DEFS
        
        options = []
        for i, (p_key, p_name, p_desc, p_max, p_cost_func, p_bool) in enumerate(perk_defs):
            lvl = PROFILE_MANAGER.get_perk(p_key, 0)
            if p_bool:
                status = "SBLOCCATO" if lvl else "BLOCCATO"
                cost = "MAX" if lvl else f"✨{p_cost_func(0)}"
                options.append(f"{p_name}[{status}] ({p_desc}) - Costo: {cost}")
            else:
                cost = "MAX" if lvl >= p_max else f"✨{p_cost_func(lvl)}"
                options.append(f"{p_name}[Lv.{lvl}/{p_max}] ({p_desc}) - Costo: {cost}")
                
        prompt = f"{Colors.CYAN}--- IL FUOCO DELL'ANIMA --- Essenza: ✨{PROFILE_MANAGER.essence}{Colors.RESET}"
        idx = interactive_menu(options, prompt, cancellable=True)
        
        if idx == -1: break
        
        p_key, p_name, p_desc, p_max, p_cost_func, p_bool = perk_defs[idx]
        lvl = PROFILE_MANAGER.get_perk(p_key, 0)
        cost = p_cost_func(0) if p_bool else p_cost_func(lvl)
        
        can_buy = (p_bool and not lvl) or (not p_bool and lvl < p_max)
        if not can_buy:
            display_msg(f"\n{Colors.YELLOW}{p_name} è già al livello massimo.{Colors.RESET}"); time.sleep(1.5)
        elif PROFILE_MANAGER.essence >= cost:
            PROFILE_MANAGER.essence -= cost
            if p_bool: PROFILE_MANAGER.set_perk(p_key, True)
            else: PROFILE_MANAGER.set_perk(p_key, lvl + 1)
            PROFILE_MANAGER.save()
        else:
            display_msg(f"\n{Colors.RED}Essenza insufficiente.{Colors.RESET}"); time.sleep(1.5)

def base_camp_forge():
    while True:
        clear_screen()
        has_speziale = PROFILE_MANAGER.get_npc_unlocked("speziale")
        has_borek = PROFILE_MANAGER.get_npc_unlocked("borek")
        has_elara = PROFILE_MANAGER.get_npc_unlocked("elara")
        has_valerius = PROFILE_MANAGER.get_npc_unlocked("valerius")
        
        options = ["Reliquie"]
        valid_cats = ["relics"]
        
        if has_borek:
            options.append("Armi")
            valid_cats.append("weapons")
        if has_elara:
            options.append("Armature")
            valid_cats.append("armors")
        if has_speziale:
            options.append("Consumabili")
            valid_cats.append("consumables")
        if has_valerius:
            options.append("Monili")
            valid_cats.append("accessories")
            
        prompt = f"{Colors.CYAN}--- FORGIA DIMENSIONALE --- Essenza: ✨{PROFILE_MANAGER.essence}{Colors.RESET}\nCosa desideri forgiare?"
        idx = interactive_menu(options, prompt, cancellable=True)
        
        if idx == -1: break
        
        cat = valid_cats[idx]
        cat_name = options[idx]
        base_camp_forge_category(cat, cat_name)

def locked_forge_items(cat) -> list:
    """Oggetti ancora da sbloccare: "unlock_id": null indica un oggetto disponibile fin dall'inizio."""
    return [i for i in RAW_DATA[cat] if i.get("unlock_id") and i["unlock_id"] not in PROFILE_MANAGER.unlocked_ids]

def base_camp_forge_category(cat, cat_name):
    while True:
        clear_screen()
        lkd = locked_forge_items(cat)
        options = []
        if not lkd: options.append("Tutto sbloccato in questa categoria!")
        else:
            for it in lkd:
                cost = it.get("unlock_cost", 0)
                cost_str = f"✨{cost}" if cost > 0 else "Sbloccabile tramite Imprese"
                desc_str = f" ({it.get('desc', '')})" if it.get('desc') else ""
                options.append(f"{it['name']}{desc_str} - Costo: {cost_str}")
        prompt = f"{Colors.CYAN}--- FORGIA DIMENSIONALE ({cat_name.upper()}) --- Essenza: ✨{PROFILE_MANAGER.essence}{Colors.RESET}"
        idx = interactive_menu(options, prompt, cancellable=True)
        
        if idx == -1: break
        
        if lkd and 0 <= idx < len(lkd):
            cost = lkd[idx].get("unlock_cost", 0)
            if PROFILE_MANAGER.essence >= cost and cost > 0:
                PROFILE_MANAGER.essence -= cost
                PROFILE_MANAGER.unlocked_ids.append(lkd[idx]["unlock_id"])
                PROFILE_MANAGER.save()
                display_msg(f"\n{Colors.GREEN}Sbloccato: {lkd[idx]['name']}!{Colors.RESET}")
                update_game_data()
                time.sleep(1)
            elif cost == 0:
                display_msg(f"\n{Colors.RED}Questo oggetto può essere sbloccato solo completando un'Impresa specifica!{Colors.RESET}")
                time.sleep(2)
            else:
                display_msg(f"\n{Colors.RED}Essenza insufficiente.{Colors.RESET}")
                time.sleep(1.5)

def base_camp_tavern():
    while True:
        clear_screen()
        lkc =[(c_id, c) for c_id, c in RAW_DATA["classes"].items() if not c.get("unlocked_by_default") and c_id not in PROFILE_MANAGER.unlocked_ids and c.get("unlock_id") not in PROFILE_MANAGER.unlocked_ids]
        options = []
        if not lkc: options.append("Tutti reclutati!")
        else:
            for c_id, c in lkc:
                cost = c.get('unlock_cost', 0)
                cost_str = f"✨{cost}" if cost > 0 else "Sbloccabile tramite Maestria o Imprese"
                options.append(f"{c['role']} ({c['desc']}) - Costo: {cost_str}")
        prompt = f"{Colors.CYAN}--- LA TAVERNA --- Essenza: ✨{PROFILE_MANAGER.essence}{Colors.RESET}"
        idx = interactive_menu(options, prompt, cancellable=True)
        
        if idx == -1: break
        
        if lkc and 0 <= idx < len(lkc) and PROFILE_MANAGER.essence>=lkc[idx][1].get("unlock_cost", 0) and lkc[idx][1].get("unlock_cost", 0)>0:
            PROFILE_MANAGER.essence-=lkc[idx][1]["unlock_cost"]; PROFILE_MANAGER.unlocked_ids.append(lkc[idx][1]["unlock_id"]); PROFILE_MANAGER.save()
            display_msg(f"{Colors.GREEN}Reclutato: {lkc[idx][1]['role']}!{Colors.RESET}"); time.sleep(1)

def base_camp_grimoire():
    clear_screen()
    display_msg(f"{Colors.CYAN}--- GRIMORIO ---{Colors.RESET}")
    for f_id, f in GAME_DATA["meta"]["feats"].items():
        st = f"{Colors.GREEN}[V]{Colors.RESET}" if f_id in PROFILE_MANAGER.completed_feats else f"{Colors.RED}[X]{Colors.RESET}"
        display_msg(f"{st} {f['name']}: {f['desc']}")
    display_msg(f"\n{Colors.CYAN}--- MAESTRIA CLASSI ---{Colors.RESET}")
    for c_id, c in RAW_DATA["classes"].items():
        if c.get("unlocked_by_default") or c_id in PROFILE_MANAGER.unlocked_ids or c.get("unlock_id") in PROFILE_MANAGER.unlocked_ids:
            display_msg(f"{c['role']}: Lv.{PROFILE_MANAGER.get_class_lvl(c_id, 1)} (XP: {PROFILE_MANAGER.get_class_xp(c_id, 0)})")
    wait_enter("\nPremi INVIO per tornare indietro...")


# Bottega di ogni artigiano: categoria, oggetti sempre in vendita (nome, costo) e chiave del profilo
NPC_SHOPS = {
    "speziale": ("consumables", [("Pozione Curativa", 20), ("Antidoto Universale", 30)], "starting_consumables"),
    "borek": ("weapons", [("Spada Corta", 30), ("Ascia da Battaglia", 30)], "starting_weapons"),
    "elara": ("armors", [("Tunica del Viaggiatore", 30), ("Corazza di Cuoio", 40)], "starting_armors"),
    "valerius": ("accessories", [("Occhio del Cacciatore", 50), ("Anello del Berserker", 50)], "starting_accessories"),
}

def npc_shop_items(item_cat, default_items) -> list:
    """Oggetti in vendita: quelli di base più ogni oggetto della categoria già sbloccato alla Forgia."""
    shop_items = list(default_items)
    for i in RAW_DATA[item_cat]:
        if i.get("unlock_id") and i["unlock_id"] in PROFILE_MANAGER.unlocked_ids:
            cost = max(20, i.get("unlock_cost", 300) // 10)
            shop_items.append((i["name"], cost))
    return shop_items

def generate_npc_shop(npc_name, title, desc, item_cat, default_items, essence_key):
    while True:
        clear_screen()
        shop_items = npc_shop_items(item_cat, default_items)

        options = []
        for it in shop_items:
            options.append(f"Compra {it[0]} (✨{it[1]})")
        prompt = f"{Colors.GREEN}--- {title} ---{Colors.RESET}\nEssenza: ✨{PROFILE_MANAGER.essence}\n\n{desc}"
        
        idx = interactive_menu(options, prompt, cancellable=True)
        if idx == -1: break
        
        it_name = shop_items[idx][0]
        cost = shop_items[idx][1]
        
        if PROFILE_MANAGER.essence >= cost:
            if essence_key not in PROFILE_MANAGER._data: PROFILE_MANAGER._data[essence_key] = []
            if len(PROFILE_MANAGER._data[essence_key]) >= 1:
                display_msg(f"\n{Colors.YELLOW}'Hai già un oggetto preparato per questa spedizione. Non esagerare!'{Colors.RESET}")
                time.sleep(2.5)
                continue
            PROFILE_MANAGER._data[essence_key].append(it_name)
            PROFILE_MANAGER.essence -= cost
            PROFILE_MANAGER.save()
            display_msg(f"\n{Colors.CYAN}'Ottima scelta.' {Colors.RESET}Hai aggiunto {it_name} all'inventario iniziale.")
            time.sleep(1.5)
        else:
            display_msg(f"\n{Colors.RED}Essenza insufficiente.{Colors.RESET}")
            time.sleep(1.5)

def base_camp_apothecary():
    generate_npc_shop("speziale", "LA TENDA DELLO SPEZIALE", "L'anziano che hai salvato mescola intrugli gorgoglianti.\n'Un piccolo aiuto per la tua prossima discesa? Per te, un prezzo di favore!'", *NPC_SHOPS["speziale"])

def base_camp_borek():
    generate_npc_shop("borek", "L'ARMERIA DI BOREK", "Il vecchio nano sta lucidando un'ascia. 'Vuoi partire ben equipaggiato? Posso farti un prezzo speciale.'", *NPC_SHOPS["borek"])

def base_camp_elara():
    generate_npc_shop("elara", "LA FUCINA DI ELARA", "Elara sta martellando una lastra di metallo rovente. 'Senza una buona armatura sei morto. Che pezzo ti serve?'", *NPC_SHOPS["elara"])

def base_camp_valerius():
    generate_npc_shop("valerius", "IL LABORATORIO DI VALERIUS", "Valerius lucida una gemma opalescente. 'La magia nei gioielli può fare la differenza tra la vita e la morte...'", *NPC_SHOPS["valerius"])
def base_camp():
    while True:
        clear_screen()
        has_speziale = PROFILE_MANAGER.get_npc_unlocked("speziale")
        has_borek = PROFILE_MANAGER.get_npc_unlocked("borek")
        has_elara = PROFILE_MANAGER.get_npc_unlocked("elara")
        has_valerius = PROFILE_MANAGER.get_npc_unlocked("valerius")
        
        options = [
            "Il Fuoco dell'Anima (Potenziamenti Base)",
            "La Forgia Dimensionale (Sblocca Oggetti)",
            "La Taverna delle Imprese (Sfide ed Eroi)",
            "Grimorio e Imprese",
            "L'Archivio di Aethelgard (Lore)",
            "Il Codice del Labirinto (Bestiario, Personaggi, Eventi, Lettere, Reliquie)"
        ]
        
        if has_speziale:
            options.append(f"La Tenda dello Speziale {Colors.GREEN}[SBLOCCATO]{Colors.RESET}")
        if has_borek:
            options.append(f"L'Armeria di Borek {Colors.GREEN}[SBLOCCATO]{Colors.RESET}")
        if has_elara:
            options.append(f"La Fucina di Elara {Colors.GREEN}[SBLOCCATO]{Colors.RESET}")
        if has_valerius:
            options.append(f"Il Laboratorio di Valerius {Colors.GREEN}[SBLOCCATO]{Colors.RESET}")
            
        options.append("Ritorna al Menu Principale")
        
        prompt = f"{Colors.MAGENTA}{Colors.BOLD}=== 🏕️ IL CAMPO BASE ==={Colors.RESET}\nEssenza: {Colors.CYAN}✨ {PROFILE_MANAGER.essence}{Colors.RESET}\n\nDove vuoi andare?"
        idx = interactive_menu(options, prompt)
        
        if options[idx] == "Ritorna al Menu Principale":
            break
        elif idx == 0:
            base_camp_fire()
        elif idx == 1:
            base_camp_forge()
        elif idx == 2:
            base_camp_tavern()
        elif idx == 3:
            base_camp_grimoire()
        elif idx == 4:
            show_archive(PROFILE_MANAGER._data)
        elif idx == 5:
            show_codex()
        else:
            opt = options[idx]
            if "Tenda dello Speziale" in opt: base_camp_apothecary()
            elif "Armeria di Borek" in opt: base_camp_borek()
            elif "Fucina di Elara" in opt: base_camp_elara()
            elif "Laboratorio di Valerius" in opt: base_camp_valerius()

def _hero_selection() -> tuple[str, str, list[str]]:
    avail_c = {c_id: c for c_id, c in GAME_DATA["classes"].items() if c.get("unlocked_by_default", False) or c_id in PROFILE_MANAGER.unlocked_ids}
    avail_c_list = list(avail_c.items())
    options = [f"{Colors.BOLD}{c['role'].upper()}{Colors.RESET} (Lv. Maestria: {PROFILE_MANAGER.get_class_lvl(c_id, 1)})" for c_id, c in avail_c_list]
    
    idx = interactive_menu(options, f"\n{Colors.CYAN}Scegli il tuo Eroe:{Colors.RESET}")
    c_choice = avail_c_list[idx][0]
    
    avail_t_list =[]
    for t_id, t in GAME_DATA["meta"]["traits"].items():
        ul = True
        if t["unlock_req"] == "deaths_10" and PROFILE_MANAGER.stats["total_deaths"] < 10: ul = False
        elif t["unlock_req"] == "gold_5000" and PROFILE_MANAGER.stats["total_gold"] < 5000: ul = False
        elif t["unlock_req"] not in ["none", "deaths_10", "gold_5000"] and t["unlock_req"] not in PROFILE_MANAGER.completed_feats and t["unlock_req"] not in PROFILE_MANAGER.unlocked_ids: ul = False
        if ul: avail_t_list.append((t_id, t))
        
    if len(avail_t_list) == 1:
        t_choice = avail_t_list[0][0]
    else:
        options = [f"{Colors.BOLD}{t['name']}{Colors.RESET} ({t['desc']})" for t_id, t in avail_t_list]
        idx = interactive_menu(options, f"\n{Colors.CYAN}Scegli un Tratto di partenza:{Colors.RESET}")
        t_choice = avail_t_list[idx][0]

    active_pacts = []
    if PROFILE_MANAGER.won_normal:
        avail_p = GAME_DATA["meta"]["pacts"]
        for p_id, p in avail_p.items():
            prompt = f"\n{Colors.RED}I PATTI DEL CAOS{Colors.RESET}\nAttiva le maledizioni per aumentare il moltiplicatore di Essenza.\n\nAttivare '{p['name']}'? ({p['desc']})"
            ans_idx = interactive_menu(["No", "Sì"], prompt)
            if ans_idx == 1: active_pacts.append(p_id)

    return c_choice, t_choice, active_pacts

def _apply_floor_regen(player: Player) -> int:
    sp_lvl = PROFILE_MANAGER.get_perk("speranza_luce_lvl", 0)
    if sp_lvl <= 0 or player.hp >= player.max_hp: return 0
    healed = player.heal(max(1, int(player.max_hp * SPERANZA_LUCE_PCT_PER_LVL * sp_lvl)))
    if healed > 0: display_msg(f"{Colors.GREEN}La Speranza di Luce ti rigenera {healed} HP. ({player.hp}/{player.max_hp}){Colors.RESET}")
    return healed

def play_game(infinite_mode=False):
    c_choice, t_choice, active_pacts = _hero_selection()

    player = Player(c_choice, t_choice, active_pacts)
    delay_print(f"\nLe porte si chiudono alle tue spalle, {player.role}.", 0.03); time.sleep(1)
    
    base_weights = GAME_DATA["meta"]["rooms"]["weights"]
    cooldowns_def = GAME_DATA["meta"]["rooms"]["cooldowns"]
    room_cooldowns = {k: 0 for k in base_weights.keys()}
    
    floor = 1
    while player.hp > 0 and not player.escaped:
        if not infinite_mode and floor > INFINITE_MODE_THRESHOLD:
            clear_screen()
            display_msg(f"{Colors.YELLOW}{Colors.BOLD}" + "="*50); delay_print("H A I   V I N T O ! ! !"); display_msg("="*50 + Colors.RESET)
            PROFILE_MANAGER.won_normal = True; player.won = True; player.essence_gathered += 1000
            _grant_victory_rewards()
            break

        clear_screen()
        delay_print(f"\n{Colors.MAGENTA}{Colors.BOLD}==== PIANO {floor} ===={Colors.RESET}", 0.05)
        biome = get_biome(floor)
        biome_title = f" · {biome['icon']} {biome['name']}" if biome else ""
        # L'atmosfera del bioma resta sopra la mappa per tutto il piano; entrando in un bioma nuovo se ne legge il pericolo
        biome_intro = f"{Colors.CYAN}{random.choice(biome['intro'])}{Colors.RESET}\n" if biome else ""
        if biome and floor == biome["floors"][0]:
            delay_print(f"\n{Colors.MAGENTA}{Colors.BOLD}{biome['icon']}  {biome['name'].upper()}{Colors.RESET}", 0.03)
            delay_print(biome_intro, 0.03)
            if biome.get("hazard"): display_msg(f"{Colors.RED}Pericolo: {biome['hazard']['name']}.{Colors.RESET} {biome['hazard']['desc']}")
            wait_enter("\nPremi INVIO per entrare...")
        
        _apply_floor_regen(player)
            
        player.run_tracker["floor_attacks"] = player.run_tracker["floor_hits"] = 0
        
        # La mappa del piano si genera all'arrivo: le reliquie possedute in quel momento ne cambiano i pesi
        weights_def = base_weights.copy()
        for r in player.relic_effects: r.modify_room_weights(weights_def)
        floor_map = generate_floor_map(floor, weights_def, cooldowns_def, room_cooldowns, active_pacts, player)
        path, current = [], None

        for step in range(1, ROWS + 2):
            if player.hp <= 0 or player.escaped: break
            choices = reachable(floor_map, step, current)

            while True:
                clear_screen()
                prompt = "\n".join([
                    f"\n{Colors.CYAN}--- Piano {floor}{biome_title} | Esplorazione {step}/{ROWS + 1} ---{Colors.RESET}",
                    f"❤️  HP: {Colors.GREEN}{player.hp}/{player.max_hp}{Colors.RESET} | 💰 Oro: {Colors.YELLOW}{player.gold}{Colors.RESET}", biome_intro,
                    *render_map(floor_map, step, path, biome, tall=shutil.get_terminal_size().lines >= TALL_MAP_ROWS), "", "Scegli dove proseguire:"])
                sixth = PROFILE_MANAGER.get_perk("sesto_senso", False)
                options = [f"Entra: {room_label(floor_map[step - 1][i], sixth, biome)}" + (f" ({SIDES[floor_map[step - 1][i]['slot']]})" if step <= ROWS else "")
                           for i in choices]
                options.append("Apri Inventario")
                options.append("Statistiche Eroe")
                options.append("Fuga dal Labirinto")
                
                idx = interactive_menu(options, prompt)
                if idx == len(options) - 3:
                    show_inventory_menu(player)
                elif idx == len(options) - 2:
                    show_player_stats(player)
                elif idx == len(options) - 1:
                    clear_screen(); display_msg(f"{Colors.YELLOW}Fuggi portando in salvo le ricchezze.{Colors.RESET}")
                    player.escaped = True; break
                else:
                    path.append(choices[idx]); current = floor_map[step - 1][choices[idx]]
                    chosen_door = current; clear_screen(); break
            
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
            attacks, hits = player.run_tracker["floor_attacks"], player.run_tracker["floor_hits"]
            if attacks >= BLIND_FURY_MIN_ATTACKS and hits * 2 < attacks: player.run_tracker["blind_fury_done"] = True
            heal = 20 + (floor * 5)
            player.heal(heal)
            display_msg(f"Ti riposi prima delle scale. (HP: {player.hp}/{player.max_hp})")
            floor += 1
            if floor > PROFILE_MANAGER.max_floor: PROFILE_MANAGER.max_floor = floor
            wait_enter("\nPremi INVIO per scendere...")

    evaluate_run(player, floor, infinite_mode)

def settings_menu():
    labels = {"lenta": "Lenta", "normale": "Normale", "veloce": "Veloce", "istantanea": "Istantanea"}
    speeds = list(TEXT_SPEEDS)
    while True:
        clear_screen()
        options = [f"{labels.get(s, s)}{' [ATTUALE]' if s == PROFILE_MANAGER.text_speed else ''}" for s in speeds]
        prompt = f"{Colors.CYAN}--- IMPOSTAZIONI ---{Colors.RESET}\nVelocità del testo narrativo:"
        idx = interactive_menu(options, prompt, cancellable=True, initial=speeds.index(PROFILE_MANAGER.text_speed))
        if idx == -1: break
        PROFILE_MANAGER.text_speed = speeds[idx]
        PROFILE_MANAGER.save()

# Sblocchi che si ottengono solo vincendo la discesa standard
VICTORY_UNLOCKS = ["lama_creatore"]

def _grant_victory_rewards():
    for unlock_id in VICTORY_UNLOCKS:
        if unlock_id not in PROFILE_MANAGER.unlocked_ids:
            PROFILE_MANAGER.unlocked_ids.append(unlock_id)
            name = next((i["name"] for cat in ("weapons", "armors", "accessories", "consumables", "relics") for i in RAW_DATA[cat] if i.get("unlock_id") == unlock_id), unlock_id)
            display_msg(f"{Colors.MAGENTA}{Colors.BOLD}Ricompensa leggendaria sbloccata: {name}!{Colors.RESET}")
    update_game_data()

def _grant_retroactive_mastery_unlocks():
    """Concede gli sblocchi di Maestria già raggiunti (es. classi aggiunte dopo che il livello era stato ottenuto)."""
    changed = False
    for c_id, c in GAME_DATA["classes"].items():
        lvl = PROFILE_MANAGER.get_class_lvl(c_id, 1)
        for m_lvl, reward in c.get("mastery", {}).items():
            r_id = reward.get("id")
            if int(m_lvl) <= lvl and reward.get("type") in ["unlock", "class"] and r_id not in (None, "null") and r_id not in PROFILE_MANAGER.unlocked_ids:
                PROFILE_MANAGER.unlocked_ids.append(r_id); changed = True
    if changed:
        update_game_data()
        PROFILE_MANAGER.save()

def main():
    _grant_retroactive_mastery_unlocks()
    if PROFILE_MANAGER.won_normal and any(u not in PROFILE_MANAGER.unlocked_ids for u in VICTORY_UNLOCKS):
        _grant_victory_rewards(); PROFILE_MANAGER.save()
    try:
        while True:
            clear_screen()
            delay_print(f"{Colors.MAGENTA}{Colors.BOLD}=== IL LABIRINTO DEGLI ELEMENTI E DEL CAOS ==={Colors.RESET}", 0.01)
            actions = [(f"Inizia Run (Standard - {INFINITE_MODE_THRESHOLD} Piani)", lambda: play_game(infinite_mode=False)),
                       ("Campo Base (Potenziamenti, Forgia, Taverna)", base_camp)]
            if PROFILE_MANAGER.won_normal:
                actions.append((f"{Colors.RED}Inizia Run Infinita (Oltre i {INFINITE_MODE_THRESHOLD} Piani){Colors.RESET}", lambda: play_game(infinite_mode=True)))
            actions.append(("Impostazioni", settings_menu))
            actions.append(("Esci dal gioco", None))
            
            idx = interactive_menu([label for label, _ in actions], f"\n{Colors.CYAN}[ MENU PRINCIPALE ]{Colors.RESET}")
            action = actions[idx][1]
            if action is None: clear_screen(); display_msg("Arrivederci!"); break
            action()
    except KeyboardInterrupt:
        sys.stdout.write('\033[?25h')
        display_msg("\nArrivederci!")
    except Exception as e:
        display_msg(f"\n{Colors.RED}{Colors.BOLD}ERRORE IMPREVISTO! Il gioco è andato in crash:{Colors.RESET}")
        traceback.print_exc()
        wait_enter(f"\n{Colors.CYAN}Premi INVIO per uscire...{Colors.RESET}")

if __name__ == "__main__":
    main()