#!/usr/bin/env python3
import json, os, random, time, copy

SAVE_FILE = "atw.json"

# === UTIL ===
def slow(txt, delay=0.02):
    for c in txt:
        print(c, end='', flush=True)
        time.sleep(delay)
    print()

def clear():
    os.system("clear" if os.name != "nt" else "cls")

# === DEFAULT PLAYER ===
def default_player():
    return {
        "name": "Hero",
        "lvl": 1,
        "exp": 0,
        "next_exp": 100,
        "gold": 50,
        "hp": 100,
        "mp": 30,
        "atk": 10,
        "def": 5,
        "spd": 7,
        "weapon": {"name": "Wooden Sword", "atk": 2, "value": 20},
        "armor": {"name": "Cloth Armor", "def": 1, "value": 15},
        "magic": {"name": "Tidak ada skill", "mp_cost": 0, "power": 0},
        "inventory": ["Potion"],
        # single quest active (None or dict)
        "quest": None
    }
# === ITEM LIST ===
items = {
    "Potion": {"type": "heal", "heal": 50},
    "Hi-Potion": {"type": "heal", "heal": 150},
    "Wooden Sword": {"type": "weapon", "atk": 1},
    "Iron Sword": {"type": "weapon", "atk": 5},
    "Steel Sword": {"type": "weapon", "atk": 10},
    "Silver Sword": {"type": "weapon", "atk": 15},
    "Cloth Armor": {"type": "armor", "def": 1},
    "Leather Armor": {"type": "armor", "def": 3},
    "Chain Armor": {"type": "armor", "def": 5},
    "Knight Armor": {"type": "armor", "def": 8}
}
player = default_player()

# === HITUNG ULANG STATUS ===
def recalc_stats():
    """Menghitung ulang total atk/def sesuai senjata & armor."""
    base_atk = player["atk"]
    base_def = player["def"]
    wpn = player.get("weapon", {"atk": 0})
    arm = player.get("armor", {"def": 0})
    player["total_atk"] = base_atk + wpn.get("atk", 0)
    player["total_def"] = base_def + arm.get("def", 0)

# === SAVE / LOAD (backwards-compatible) ===
def ensure_fields(data):
    base = default_player()
    changed = False
    for k, v in base.items():
        if k not in data:
            data[k] = v
            changed = True
    # nested checks
    if "weapon" not in data or "name" not in data["weapon"]:
        data["weapon"] = base["weapon"]; changed = True
    if "armor" not in data or "name" not in data["armor"]:
        data["armor"] = base["armor"]; changed = True
    return data, changed

def save_game():
    global player
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(player, f)
        slow("💾 Progress tersimpan.")
    except Exception as e:
        slow(f"❌ Gagal menyimpan: {e}")

def load_game():
    global player
    if not os.path.exists(SAVE_FILE):
        slow("⚠️ Tidak ada file save ditemukan.")
        return False
    try:
        with open(SAVE_FILE) as f:
            data = json.load(f)
        if not isinstance(data, dict) or "name" not in data:
            slow("❌ File save tidak valid.")
            return False
        data, changed = ensure_fields(data)
        player = data
        if changed:
            slow("⚠️ Save file dicocokkan dengan field terbaru.")
            save_game()
        slow("📂 Progress berhasil dimuat!")
        recalc_stats()  # pastikan senjata & armor diterapkan setelah load
        return True
    except Exception as e:
        slow(f"❌ Gagal memuat save: {e}")
        return False

def show_stats():
    recalc_stats()
    name = player["name"]
    lvl = player["lvl"]
    hp = player["hp"]
    mp = player["mp"]
    atk = player["total_atk"]
    base_atk = player["atk"]
    defense = player["total_def"]
    base_def = player["def"]
    gold = player["gold"]
    exp = player["exp"]
    next_exp = player["next_exp"]
    weapon = player["weapon"]["name"]
    armor = player["armor"]["name"]
    inv = ", ".join([f"{k} ({v})" for k, v in player["inventory"].items()]) if isinstance(player["inventory"], dict) else ", ".join(player["inventory"])

    print("\n╔════════════════════════════════════╗")
    print(f"║ {name}  Lv.{lvl:<3}                     ║")
    print("╠════════════════════════════════════╣")
    print(f"║ HP : {hp:<4} | MP : {mp:<4}              ║")
    print(f"║ ATK: {atk} (Base {base_atk})                 ║")
    print(f"║ DEF: {defense} (Base {base_def})                 ║")
    print("╠════════════════════════════════════╣")
    print(f"║ GOLD: {gold:<6} | EXP: {exp}/{next_exp:<4}       ║")
    print("╠════════════════════════════════════╣")
    print(f"║ Senjata: {weapon[:22]:<22}    ║")
    print(f"║ Armor  : {armor[:22]:<22}    ║")
    print("╠════════════════════════════════════╣")
    # 🔹 Tampilkan inventory dengan jumlah item (Potion (5), Elixir (2), dst)
    if player['inventory']:
        from collections import Counter
        inv_count = Counter(player['inventory'])
        formatted_inv = [f"{item} ({count})" for item, count in inv_count.items()]
        print("Inventory:", ', '.join(formatted_inv))
    else:
        print(f"║  (kosong)                          ║")
    print("╚════════════════════════════════════╝")

# === SHOP (buy/sell) ===
def generate_shop_items(level=None):
    tier_pool = [
        {"name": "Iron Sword", "price": 50, "type": "weapon"},
        {"name": "Steel Sword", "price": 80, "type": "weapon"},
        {"name": "Leather Armor", "price": 60, "type": "armor"},
        {"name": "Chain Armor", "price": 100, "type": "armor"},
        {"name": "Potion", "price": 20, "type": "consumable"},
        {"name": "Hi-Potion", "price": 60, "type": "consumable"},

        # === Tambahan Skill Magic yang dijual di toko ===
        {"name": "Fireball", "price": 120, "type": "magic", "desc": "Serangan api membakar musuh."},
        {"name": "Ice Shard", "price": 150, "type": "magic", "desc": "Serangan es memperlambat musuh."},
        {"name": "Heal", "price": 180, "type": "magic", "desc": "Memulihkan HP sebanyak 30%."},
        {"name": "Thunder Strike", "price": 200, "type": "magic", "desc": "Serangan listrik yang kuat."}
    ]

    return random.sample(tier_pool, 4)

def shop_menu():
    global player
    clear()
    slow("=== TOKO PETUALANG ===")
    items = generate_shop_items(player["lvl"])
    while True:
        print("\nBarang Tersedia:")
        for i, it in enumerate(items, 1):
            print(f"{i}. {it['name']} - {it['price']} gold")
        print("B. Jual Barang")
        print("K. Keluar Toko")
        choice = input("> ").lower()
        if choice == "k":
            break
        elif choice == "b":
            sell_item()
        elif choice.isdigit():
            idx = int(choice)-1
            if 0 <= idx < len(items):
                buy_item(items[idx])
        else:
            slow("Pilihan tidak valid.")

def buy_item(item):
    global player
    if player["gold"] < item["price"]:
        slow("Uangmu tidak cukup!")
        return

    player["gold"] -= item["price"]

    # Jika item adalah magic skill
    if item["type"] == "magic":
        if "skills" not in player:
            player["skills"] = []
        if item["name"] in player["skills"]:
            slow("Kamu sudah memiliki skill ini.")
            return
        player["skills"].append(item["name"])
        slow(f"Kamu mempelajari skill baru: {item['name']}!")
    else:
        player["inventory"].append(item["name"])
        slow(f"Kamu membeli {item['name']}.")

    save_game()

def sell_item():
    global player
    if not player["inventory"]:
        slow("Inventori kosong.")
        return
    show_inventory(short=True)
    choice = input("\nPilih nomor item untuk dijual (atau enter untuk batal): ")
    if not choice.isdigit():
        return
    idx = int(choice)-1
    if idx < 0 or idx >= len(player["inventory"]):
        slow("Pilihan tidak valid.")
        return
    item = player["inventory"].pop(idx)
    # harga jual ~50% random range
    value = random.randint(10, 50)
    player["gold"] += value
    slow(f"Kamu menjual {item} dan mendapatkan {value} gold.")
    save_game()

# === INVENTORY & EQUIP ===
def show_inventory(short=False):
    clear()
    if not player["inventory"]:
        slow("Inventori kosong.")
        return

    if short:
        for i, it in enumerate(player["inventory"], 1):
            print(f"{i}. {it}")
        return

    slow("=== INVENTORY ===")
    for i, it in enumerate(player["inventory"], 1):
        print(f"{i}. {it}")

    choice = input("\nPilih nomor item untuk lihat detail (atau tekan Enter untuk kembali): ")
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(player["inventory"]):
            item = player["inventory"][idx]
            describe_item(item)

def describe_item(item):
    slow("\n=== DESKRIPSI ITEM ===")
    desc = ""

    # Item penyembuh
    if item in ["Potion", "Hi-Potion", "Mega Potion"]:
        heals = {"Potion": 50, "Hi-Potion": 100, "Mega Potion": 200}
        desc = f"Memulihkan {heals.get(item, 0)} HP."

    # Senjata
    elif "Sword" in item or "Dagger" in item or "Axe" in item or "Bow" in item:
        base = {"Sword": 5, "Dagger": 3, "Axe": 7, "Bow": 4}
        for key in base:
            if key in item:
                desc = f"Senjata jenis {key}. Menambah ATK sekitar {base[key]}–{base[key]*4}."
                break

        # Tambahan jika Legendary Sword
        if "Legendary Sword" in item:
            desc += " 🌟 Efek: +55 ATK, +100 HP, +50 MP."

    # Armor
    elif "Armor" in item or "Robe" in item or "Mail" in item or "Shield" in item:
        base = {"Armor": 3, "Robe": 2, "Mail": 4, "Shield": 3}
        for key in base:
            if key in item:
                desc = f"Pelindung jenis {key}. Menambah DEF sekitar {base[key]}–{base[key]*4}."
                break

        # Tambahan jika Legendary Armor
        if "Legendary Armor" in item:
            desc += " 🌟 Efek: +50 DEF, +150 HP, +50 MP."

    else:
        desc = "Item khusus tanpa efek yang diketahui."

    slow(f"🧾 {item}: {desc}")
    input("\nTekan Enter untuk kembali ke inventori...")

from collections import Counter

def get_stacked_inventory():
    """Mengembalikan daftar inventory yang sudah dikelompokkan"""
    inv_count = Counter(player["inventory"])
    return list(inv_count.items())

def show_stacked_inventory():
    """Menampilkan inventory dengan format Item (jumlah)"""
    inv_list = get_stacked_inventory()
    if not inv_list:
        print("Inventori kosong.")
        return
    for i, (item, count) in enumerate(inv_list, 1):
        print(f"{i}. {item} ({count})")

def inventory_menu():
    while True:
        clear()
        print("=== MENU INVENTORY ===")
        print("1. Lihat Item")
        print("2. Equip Senjata/Armor")
        print("3. Gunakan Item")
        print("4. Crafting")
        print("5. kembali")
        ch = input("> ")
        if ch == "1":
            show_stacked_inventory()
            input("\nTekan ENTER untuk kembali.")
        elif ch == "2":
            equip_item()
        elif ch == "3":
            use_item_outside()
        elif ch == "4":
            craft_menu()
        elif ch == "5":
            break
        else:
            slow("Pilihan tidak valid.")

def equip_item():
    """
    Versi equip yang kompatibel dengan inventory stacked (Counter).
    Menampilkan daftar item ter-stack, memilih item berdasarkan nomor,
    mengurangi 1 dari stack (atau hapus jika tinggal 0), dan
    mengembalikan equipment lama ke inventory.
    """
    global player
    # jika inventory kosong
    if not player.get("inventory"):
        slow("Inventori kosong.")
        return

    # siapkan daftar stacked
    from collections import Counter
    inv_count = Counter(player["inventory"])
    stacked = list(inv_count.items())  # [(item_name, count), ...]

    # tampilkan
    clear()
    print("\n=== EQUIP ITEM ===")
    for i, (name, cnt) in enumerate(stacked, 1):
        print(f"{i}. {name} ({cnt})")
    print("0. Batal")

    # input pilihan
    choice = input("\nPilih item untuk equip (nomor): ").strip()
    if not choice.isdigit():
        slow("Pilihan tidak valid.")
        return
    idx = int(choice) - 1
    if choice == "0":
        return
    if idx < 0 or idx >= len(stacked):
        slow("Pilihan tidak valid.")
        return

    item_name, item_count = stacked[idx]

    # Pastikan kita mengurangi 1 item dari inventory (stack behavior)
    # Hapus satu instance dari player['inventory'] (yang berupa list of names)
    removed = False
    for i, it in enumerate(player["inventory"]):
        if it == item_name:
            player["inventory"].pop(i)
            removed = True
            break
    if not removed:
        slow("Gagal mengambil item dari inventori.")
        return

    # Jika item adalah senjata
    if "Sword" in item_name or "Dagger" in item_name or "Bow" in item_name:
        # simpan senjata lama ke inventory (jika ada dan bukan default)
        if player.get("weapon") and player["weapon"].get("name") not in (None, "", "Tangan Kosong"):
            player["inventory"].append(player["weapon"]["name"])

        # reset bonus senjata lama
        player["hp"] -= player.get("bonus_hp_weapon", 0)
        player["mp"] -= player.get("bonus_mp_weapon", 0)
        player["bonus_hp_weapon"] = 0
        player["bonus_mp_weapon"] = 0

        atk = random.randint(5, 10) + player["lvl"]
        if "Legendary Sword" in item_name:
            atk += 55
            player["bonus_hp_weapon"] = 100
            player["bonus_mp_weapon"] = 50
            player["hp"] += 100
            player["mp"] += 50
            slow("✨ Kekuatan legendaris mengalir ke tubuhmu!")

        player["weapon"] = {"name": item_name, "atk": atk}
        player["bonus_atk"] = atk
        slow(f"⚔️ Kamu melengkapi senjata: {item_name} (+{atk} ATK)")

    # Jika item adalah armor
    elif "Armor" in item_name or "Robe" in item_name or "Cloth" in item_name or "Mail" in item_name or "Shield" in item_name:
        # simpan armor lama ke inventory (jika ada dan bukan default)
        if player.get("armor") and player["armor"].get("name") not in (None, "", "Tanpa Armor"):
            player["inventory"].append(player["armor"]["name"])

        defense = random.randint(3, 7) + player["lvl"]
        if "Legendary Armor" in item_name:
            defense += 50
            slow("✨ Kamu merasakan perlindungan suci di sekitarmu!")

        player["armor"] = {"name": item_name, "def": defense}
        player["bonus_def"] = defense
        slow(f"🛡️ Kamu memakai armor: {item_name} (+{defense} DEF)")

    else:
        # bukan equipable -> kembalikan item ke inventory
        player["inventory"].append(item_name)
        slow("Item ini tidak bisa di-equip.")
        return

    # simpan otomatis dan perbarui stats
    save_game()
    recalc_stats()

def equip_magic():
    if not player["inventory"]:
        slow("Inventory kosong.")
        return

    magic_items = [item for item in player["inventory"] if "Scroll" in item or "Tome" in item or "Rune" in item]
    if not magic_items:
        slow("Kamu tidak punya skill magic untuk di-equip.")
        return

    slow("\n=== PILIH SKILL MAGIC ===")
    for i, m in enumerate(magic_items, 1):
        slow(f"{i}. {m}")
    choice = input("> ")

    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(magic_items):
        slow("Pilihan tidak valid.")
        return

    chosen = magic_items[int(choice) - 1]

    # Kembalikan skill lama ke inventory (jika bukan default)
    if player["magic"]["name"] not in (None, "", "Tidak ada skill"):
        player["inventory"].append(player["magic"]["name"])

    # Tentukan atribut skill magic berdasarkan nama
    if "Fireball" in chosen:
        player["magic"] = {"name": "Fireball", "mp_cost": 10, "power": 25}
    elif "Ice Spike" in chosen:
        player["magic"] = {"name": "Ice Spike", "mp_cost": 8, "power": 18}
    elif "Thunder Rune" in chosen:
        player["magic"] = {"name": "Thunder", "mp_cost": 12, "power": 30}
    else:
        player["magic"] = {"name": chosen, "mp_cost": 10, "power": 20}

    player["inventory"].remove(chosen)
    slow(f"✨ Kamu mempelajari skill magic {player['magic']['name']}!")

def use_item_outside():
    if not player["inventory"]:
        slow("Inventori kosong.")
        return
    show_inventory()
    choice = input("\nGunakan item nomor (atau enter untuk batal): ")
    if not choice.isdigit():
        return
    idx = int(choice)-1
    if idx < 0 or idx >= len(player["inventory"]):
        slow("Pilihan tidak valid.")
        return
    item = player["inventory"].pop(idx)
    if item in ["Potion","Hi-Potion","Mega Potion","Elixir","Phoenix Potion"]:
        heals = {"Potion":50,"Hi-Potion":100,"Mega Potion":150,"Elixir":250,"Phoenix Potion":500}
        heal = heals.get(item,50)
        player["hp"] += heal
        maxhp = 100 + (player["lvl"]-1)*25
        if player["hp"] > maxhp: player["hp"] = maxhp
        slow(f"🧪 Kamu menggunakan {item} dan memulihkan {heal} HP.")
    else:
        slow("Item tidak bisa digunakan sekarang.")
    save_game()

# --- SISTEM CRAFTING ---
CRAFT_RECIPES = {
    "Battle Axe": {
        "requires": ["Iron Sword", "Orc Tooth"],
        "result": "Battle Axe"
    },
    "Dragon Scale Armor": {
        "requires": ["Leather Armor", "Lizard Scale"],
        "result": "Dragon Scale Armor"
    },
    "Dark Claw": {
        "requires": ["Bear Fur", "Shadow Essence"],
        "result": "Dark Claw"
    }
}

def craft_menu():
    print("\n🧰 === MEJA CRAFTING ===")
    for i, (k, v) in enumerate(CRAFT_RECIPES.items(), 1):
        reqs = ", ".join(v["requires"])
        print(f"{i}. {v['result']} (butuh: {reqs})")
    print("0. Batal")
    ch = input("> ")
    if ch == "0":
        return

    try:
        key = list(CRAFT_RECIPES.keys())[int(ch) - 1]
    except:
        slow("Pilihan tidak valid.")
        return

    recipe = CRAFT_RECIPES[key]
    if all(req in player["inventory"] for req in recipe["requires"]):
        # Hapus bahan dari inventory
        for req in recipe["requires"]:
            player["inventory"].remove(req)

        result_item = recipe["result"]

        # === Tambahkan bonus berdasarkan hasil crafting ===
        if result_item == "Battle Axe":
            atk = random.randint(25, 35)
            bonus_hp = random.randint(20, 35)
            player["inventory"].append({
                "name": result_item,
                "atk": atk,
                "bonus_hp_weapon": bonus_hp,
                "desc": f"Battle Axe (+{atk} ATK, +{bonus_hp} HP)"
            })
            slow(f"⚒️ Kamu berhasil membuat {result_item}! (+{atk} ATK, +{bonus_hp} HP)")

        elif result_item == "Dragon Scale Armor":
            defense = random.randint(25, 35)
            bonus_mp = random.randint(25, 40)
            player["inventory"].append({
                "name": result_item,
                "def": defense,
                "bonus_mp_armor": bonus_mp,
                "desc": f"Dragon Scale Armor (+{defense} DEF, +{bonus_mp} MP)"
            })
            slow(f"🛡️ Kamu berhasil membuat {result_item}! (+{defense} DEF, +{bonus_mp} MP)")

        elif result_item == "Dark Claw":
            atk = random.randint(20, 30)
            bonus_def = random.randint(20, 30)
            bonus_hp = random.randint(20, 35)
            player["inventory"].append({
                "name": result_item,
                "atk": atk,
                "bonus_def_weapon": bonus_def,
                "bonus_hp_weapon": bonus_hp,
                "desc": f"Dark Claw (+{atk} ATK, +{bonus_def} DEF, +{bonus_hp} HP)"
            })
            slow(f"🦴 Kamu berhasil membuat {result_item}! (+{atk} ATK, +{bonus_def} DEF, +{bonus_hp} HP)")

    else:
        slow("❌ Bahan tidak lengkap.")

# === QUEST / NPC (single active quest) ===
def talk_to_npc():
    global player
    slow("\n👴 Penduduk Desa: 'Ah, kau petualang yang baru datang?'")
    if not player.get("quest"):
        slow("'Kau bisa bantu kami? Banyak monster muncul di dekat hutan.'")
        print("1. Bunuh 5 Slime (Reward: 80 EXP, 40 gold)")
        print("2. Bunuh 5 Goblin (Reward: 100 EXP, 50 gold)")
        print("3. Bunuh 3 Wolf (Reward: 150 EXP, 80 gold)")
        print("4. Bunuh 4 Kelelawar (Reward: 180 EXP, 90 gold)")
        print("5. Bunuh 2 Beruang (Reward: 220 EXP, 120 gold)")
        print("6. Bunuh 3 Orc (Reward: 250 EXP, 150 gold)")
        print("7. Bunuh 2 Lizardman (Reward: 300 EXP, 180 gold)")
        print("8. Tolak")
        ch = input("> ")
        if ch == "1":
           player["quest"] = {"title": "Bunuh 5 Slime", "target": "Slime", "count": 5, "progress": 0, "reward": {"exp": 80, "gold": 40}}
        elif ch == "2":
           player["quest"] = {"title": "Bunuh 5 Goblin", "target": "Goblin", "count": 5, "progress": 0, "reward": {"exp": 100, "gold": 50}}
        elif ch == "3":
           player["quest"] = {"title": "Bunuh 3 Wolf", "target": "Wolf", "count": 3, "progress": 0, "reward": {"exp": 150, "gold": 80}}
        elif ch == "4":
           player["quest"] = {"title": "Bunuh 4 Kelelawar", "target": "Kelelawar", "count": 4, "progress": 0, "reward": {"exp": 180, "gold": 90}}
        elif ch == "5":
           player["quest"] = {"title": "Bunuh 2 Beruang", "target": "Beruang", "count": 2, "progress": 0, "reward": {"exp": 220, "gold": 120}}
        elif ch == "6":
           player["quest"] = {"title": "Bunuh 3 Orc", "target": "Orc", "count": 3, "progress": 0, "reward": {"exp": 250, "gold": 150}}
        elif ch == "7":
           player["quest"] = {"title": "Bunuh 2 Lizardman", "target": "Lizardman", "count": 2, "progress": 0, "reward": {"exp": 300, "gold": 180}}
        else:
            slow("NPC: 'Baiklah, lain kali saja.'")
            return
        slow(f"Quest diterima: {player['quest']['title']}")
    else:
        q = player["quest"]
        icon = MONSTER_ICONS.get(q.get("target"), "❓")
        target_name = q.get("target", "???")
        progress = q.get("progress", 0)
        target = q.get("count", q.get("target", 0)) or q.get("target", 0)

        # Jika quest selesai
        if progress >= q.get("count", q.get("target", 0)):
            slow(f"NPC: 'Luar biasa! Kau berhasil membasmi semua {icon} {target_name}!'")
            rew = q.get("reward", {})
            player["exp"] += rew.get("exp", 0)
            player["gold"] += rew.get("gold", 0)
            slow(f"🎁 Kamu menerima {rew.get('exp', 0)} EXP dan {rew.get('gold', 0)} gold!")
            player["quest"] = None
            level_up_check()
            save_game()
        else:
            left = q.get("count", q.get("target", 0)) - progress
            total = q.get("count", q.get("target", 0))
            slow(f"Quest aktif: {icon} {target_name} — {progress}/{total} terbunuh.")
            slow(f"NPC: 'Masih ada {left} yang tersisa, lanjutkan perjuanganmu!'")

# === ENEMY SCALING ===
def scaled_enemy(enemy_base):
    scale = max(0.0, (player["lvl"] - 1) / 10.0)
    enemy = copy.deepcopy(enemy_base)
    enemy["hp"] = max(1, int(enemy_base["hp"] * (1 + scale)))
    enemy["atk"] = max(1, int(enemy_base["atk"] * (1 + scale)))
    enemy["def"] = max(0, int(enemy_base["def"] * (1 + scale)))
    enemy["exp"] = max(1, int(enemy_base["exp"] * (1 + scale)))
    enemy["gold"] = max(0, int(enemy_base["gold"] * (1 + scale)))
    return enemy

# === ENEMY BASE (semua musuh normal & baru) ===
ENEMIES_BASE = [
    # Musuh awal
    {"name":"Slime","hp":60,"atk":6,"def":1,"exp":25,"gold":10,"drop":"Potion"},
    {"name":"Goblin","hp":80,"atk":8,"def":2,"exp":30,"gold":20,"drop":"Iron Sword"},
    {"name":"Wolf","hp":100,"atk":10,"def":3,"exp":40,"gold":35,"drop":"Leather Armor"},

    # Musuh baru
    {"name":"Kelelawar","hp":55,"atk":10,"def":2,"exp":45,"gold":25,"drop":"Hi-Potion"},
    {"name":"Beruang","hp":160,"atk":20,"def":8,"exp":90,"gold":50,"drop":["Steel Armor","Bear Fur"]},
    {"name":"Lizardman","hp":180,"atk":28,"def":12,"exp":150,"gold":85,"drop":["Mega Potion","alizard Scale"]},
]

# === MINI BOSS DATA ===
MINI_BOSSES = [
    {"name":"Orc Warlord 🪓","hp":300,"atk":35,"def":10,"exp":350,"gold":200,"drop":["Battle Axe","Orch Tooth"]},
    {"name":"Lizard King 🦎👑","hp":400,"atk":42,"def":14,"exp":450,"gold":280,"drop":"Dragon Scale Armor"},
    {"name":"Shadow Bear 🐻‍⬛","hp":500,"atk":50,"def":18,"exp":600,"gold":350,"drop":["Dark Claw","Shadow Essence"]},

]

# === HUNT / RANDOM ENCOUNTER ===
def random_hunt():
    slow("\n🌲 Kamu memulai perburuan di hutan...")
    base = random.choice(ENEMIES_BASE)  # Ambil musuh acak dari ENEMIES_BASE
    enemy = scaled_enemy(base)          # Sesuaikan level musuh dengan pemain
    battle(enemy)                       # Mulai pertarungan

# === CENTRALIZED DEFEAT HANDLER (QUEST FIX) ===
def handle_enemy_defeat(enemy):
    """Tangani reward, quest progress, drop, level up dan simpan saat musuh tewas."""
    global player

    slow(f"\n🏆 Kamu mengalahkan {enemy['name']}!")
    player["exp"] += enemy.get("exp", 0)
    player["gold"] += enemy.get("gold", 0)
    slow(f"Kamu mendapatkan {enemy.get('exp', 0)} EXP dan {enemy.get('gold', 0)} gold.")

    # === Update progress quest ===
    q = player.get("quest")
    if q:
        enemy_name = str(enemy.get("name", "")).strip().lower()
        target_name = str(q.get("target_name", q.get("target", ""))).strip().lower()
        if enemy_name == target_name:
            q["progress"] = q.get("progress", 0) + 1
            total = q.get("count", q.get("target", 0))
            icon = MONSTER_ICONS.get(enemy["name"], "❓")
            slow(f"📜 Quest Update: {icon} {enemy['name']} {q['progress']}/{total}")
            save_game()
            # === Jika quest selesai ===
            if q["progress"] >= total:
                slow("🎉 Kamu telah menyelesaikan quest! Kembali ke NPC untuk klaim hadiah!")

    # === Drop chance ===
    if random.random() < min(0.75, 0.3 + player["lvl"] / 200):
        drop = enemy.get("drop")
        if drop:
            player["inventory"].append(drop)
            slow(f"🎁 {enemy['name']} menjatuhkan {drop}!")

    # === Level up check ===
    level_up_check()
    save_game()

# === Ikon untuk monster ===
MONSTER_ICONS = {
    "Slime": "🟢",
    "Goblin": "👺",
    "Wolf": "🐺",
    "Kelelawar": "🦇",
    "Beruang": "🐻",
    "Orc": "💀",
    "Lizardman": "🦎",
}

# === BATTLE (dengan skill MP) ===
def battle(enemy):
    global player
    icon = MONSTER_ICONS.get(enemy["name"], "❓")
    slow(f"\nKamu menghadapi {icon} {enemy['name']}!")

    # Ambil bonus dari weapon & armor
    weapon_bonus = player.get("weapon", {}).get("atk", 0)
    armor_bonus = player.get("armor", {}).get("def", 0)

    while enemy["hp"] > 0 and player["hp"] > 0:
        print(f"\n{player['name']} HP:{player['hp']} MP:{player['mp']} | {enemy['name']} HP:{enemy['hp']}")
        print("1. Serang")
        print("2. Skill Slash (5 MP)")
        if player["magic"]["name"] != "Tidak ada skill":
            print(f"3. Gunakan Magic ({player['magic']['name']} - {player['magic']['mp_cost']} MP)")
        print("4. Gunakan Item (dari inventory)")
        print("5. Kabur")
        ch = input("> ")

        # === Serangan Normal ===
        if ch == "1":
            dmg = player["atk"] + weapon_bonus + player["lvl"] - enemy["def"]
            dmg = max(1, dmg)
            enemy["hp"] -= dmg
            slow(f"🗡️ Kamu menyerang dan memberi {dmg} damage!")

        # === Skill Slash ===
        elif ch == "2":
            if player["mp"] < 5:
                slow("❌ MP tidak cukup untuk Slash!")
                continue
            player["mp"] -= 5
            dmg = (player["atk"] + weapon_bonus) * 2 + player["lvl"] - enemy["def"]
            dmg = max(5, dmg)
            enemy["hp"] -= dmg
            slow(f"💥 Slash! Kamu memberi {dmg} damage! (MP -5)")

        # === Skill Magic ===
        elif ch == "3" and player["magic"]["name"] != "Tidak ada skill":
            skill = player["magic"]
            if player["mp"] < skill["mp_cost"]:
                slow(f"❌ MP tidak cukup untuk {skill['name']}!")
                continue

            player["mp"] -= skill["mp_cost"]
            dmg = (player["atk"] + player["lvl"]) + skill["power"]
            dmg = max(10, dmg - enemy["def"])
            enemy["hp"] -= dmg
            slow(f"🔥 Kamu melempar {skill['name']} dan memberi {dmg} damage! (-{skill['mp_cost']} MP)")

        # === Gunakan Item ===
        elif ch == "4":
            use_item_in_battle()

        # === Kabur ===
        elif ch == "5":
            if random.random() < 0.5:
                slow("🏃 Kamu berhasil kabur!")
                return
            else:
                slow("❌ Gagal kabur!")
                continue
        else:
            slow("Pilihan tidak valid.")
            continue

        # === Cek jika musuh mati ===
        if enemy["hp"] <= 0:
            slow(f"\n🏆 Kamu mengalahkan {enemy['name']}!")
            handle_enemy_defeat(enemy)
            return

        # === Giliran musuh ===
        enemy_dmg = enemy["atk"] - (player["def"] + armor_bonus)
        enemy_dmg = max(1, enemy_dmg)
        player["hp"] -= enemy_dmg
        slow(f"⚔️ {enemy['name']} menyerang dan memberi {enemy_dmg} damage! (HP kamu: {player['hp']})")

        # === Jika pemain kalah ===
        if player["hp"] <= 0:
            slow("💀 Kamu kalah... Respawn sebagian.")
            player["hp"] = 100 + (player["lvl"] - 1) * 25
            player["mp"] = 30 + (player["lvl"] - 1) * 10
            player["gold"] = max(0, player["gold"] - 10)
            save_game()
            return
def use_item_in_battle():
    if not player["inventory"]:
        slow("Tidak ada item.")
        return False
    consumables = [it for it in player["inventory"] if it in ["Potion","Hi-Potion","Mega Potion","Elixir","Phoenix Potion"]]
    if not consumables:
        slow("Tidak ada consumable yang bisa dipakai.")
        return False
    slow("Consumable:")
    for i, it in enumerate(consumables,1):
        print(f"{i}. {it}")
    ch = input("> ")
    if not ch.isdigit():
        return False
    idx = int(ch)-1
    if idx < 0 or idx >= len(consumables):
        return False
    item = consumables[idx]
    player["inventory"].remove(item)
    heals = {"Potion":50,"Hi-Potion":100,"Mega Potion":150,"Elixir":250,"Phoenix Potion":500}
    heal = heals.get(item,50)
    player["hp"] += heal
    maxhp = 100 + (player["lvl"]-1)*25
    if player["hp"] > maxhp: player["hp"] = maxhp
    slow(f"🧪 Kamu memakai {item} dan memulihkan {heal} HP.")
    return True

def enter_dungeon():
    slow("\n🏰 Kamu memasuki dungeon yang gelap...")
    time.sleep(1)

    # Daftar musuh per lantai
    dungeon_enemies = [
        ["Slime", "Goblin"],          # Lantai 1–3
        ["Kelelawar", "Serigala"],    # Lantai 4–6
        ["Orc", "Troll"],             # Lantai 7–9
    ]

    # Daftar mini boss (bisa dikembangkan)
    mini_bosses = [
        {"name": "Minotaur", "hp": 220, "atk": 25},
        {"name": "Lizard King", "hp": 260, "atk": 28},
        {"name": "Shadow Knight", "hp": 240, "atk": 30},
    ]

    for floor in range(1, 11):
        slow(f"\n⚔️ == Dungeon Lantai {floor} ==")
        time.sleep(1)

        # Tentukan musuh acak berdasarkan lantai
        if floor < 10:
            # Peluang 25% untuk mini boss muncul
            if random.random() < 0.25:
                boss = random.choice(mini_bosses)
                slow(f"\n⚡ Aura kekuatan terasa di udara...")
                slow(f"🔥 MINI BOSS muncul! {boss['name']} menghadangmu!")
                enemy = scaled_enemy(boss)
            else:
                if floor <= 3:
                    base = random.choice([{"name": e, "hp": 80, "atk": 10} for e in dungeon_enemies[0]])
                elif floor <= 6:
                    base = random.choice([{"name": e, "hp": 120, "atk": 15} for e in dungeon_enemies[1]])
                else:
                    base = random.choice([{"name": e, "hp": 160, "atk": 20} for e in dungeon_enemies[2]])
                enemy = scaled_enemy(base)

            battle(enemy)

        else:
            # Boss terakhir dungeon
            base = {"name": "Dark Lord", "hp": 300, "atk": 30}
            enemy = scaled_enemy(base)
            slow("\n💀 Bos besar muncul! Aura kegelapan menyelimuti ruangan!")
            battle(enemy)

            if player["hp"] > 0:
                slow("\n🏆 Kamu mengalahkan Dark Lord dan menaklukkan dungeon!")
                player["exp"] += 500
                player["gold"] += 300
                player["inventory"].append("Legendary Sword")
                save_game()
                level_up_check()
            break

        # Jika gugur di tengah dungeon
        if player["hp"] <= 0:
            slow("\n☠️ Kamu gugur di tengah dungeon...")
            break

# === LEVEL UP ===
def level_up_check():
    global player
    leveled = False
    player["next_exp"] = player["lvl"] * 100
    # Naik level sebanyak mungkin jika EXP cukup (sampai cap 100)
    while player["lvl"] < 100 and player["exp"] >= player["lvl"] * 100:
        player["exp"] -= player["lvl"] * 100
        player["lvl"] += 1
        player["next_exp"] = player["lvl"] * 100
    # kenaikan stat per level (sesuai versi 3.4_fix)
        player["hp"] += 25
        player["mp"] += 10    # <- pastikan MP bertambah setiap level
        player["atk"] += 4
        player["def"] += 3
        leveled = True
        slow(f"✨ Level Up! Sekarang Lv.{player['lvl']}! Stat meningkat!")

    # Pastikan tidak melebihi cap level dan EXP
    if player["lvl"] >= 100:
        player["lvl"] = 100
        player["exp"] = min(player["exp"], player["lvl"] * 100)

    # Terapkan cap/limit maksimum current HP/MP agar tidak overflow
    max_hp = 100 + (player["lvl"] - 1) * 25
    max_mp = 30 + (player["lvl"] - 1) * 10
    if player["hp"] > max_hp:
        player["hp"] = max_hp
    if player["mp"] > max_mp:
        player["mp"] = max_mp

    # Jika ada kenaikan level, simpan perubahan
    if leveled:
        save_game()

# === INTRO STORY ===
def intro_story():
    clear()
    slow("🌌 Dunia yang dulunya damai kini diselimuti kegelapan...")
    slow("Monster menyerang, desa-desa terbakar. Seorang petualang bangkit...")
    slow("Dialah kamu — satu-satunya harapan.")
    input("\nTekan ENTER untuk memulai perjalananmu...")

# === NEW / START / MENU ===
def new_game():
    global player
    player = default_player()
    intro_story()
    player["name"] = input("Masukkan nama karaktermu: ") or player["name"]
    slow(f"Selamat datang, {player['name']}!")
    save_game()
    start_game()

def start_game():
    while True:
        print("\n=== MENU UTAMA ===")
        print("1. Status")
        print("2. Berburu")
        print("3. Inventory")
        print("4. Toko")
        print("5. Bicara dengan NPC (Quest)")
        print("6. Masuk Dungeon")
        print("7. Simpan")
        print("8. Keluar (Simpan otomatis)")
        ch = input("> ")
        if ch == "1":
            show_stats()
        elif ch == "2":
            random_hunt()
        elif ch == "3":
            inventory_menu()
        elif ch == "4":
            shop_menu()
        elif ch == "5":
            talk_to_npc()
        elif ch == "6":
            enter_dungeon()
        elif ch == "7":
            save_game()
        elif ch == "8":
            save_game()
            slow("Sampai jumpa, petualang!")
            break
        else:
            slow("Pilihan tidak valid.")

def main_menu():
    clear()
    slow("=== Adventure Text Worlds v3.8 ===")
    if os.path.exists(SAVE_FILE):
        print("1. Muat Game")
        print("2. Game Baru")
        print("3. Hapus Save")
        print("4. Keluar")
        choice = input("> ")
        if choice == "1":
            ok = load_game()
            if ok:
                slow(f"Selamat datang kembali, {player.get('name','Hero')}!")
                start_game()
            else:
                slow("Membuat game baru...")
                new_game()
        elif choice == "2":
            new_game()
        elif choice == "3":
            confirm = input("Yakin hapus save? (y/n): ")
            if confirm.lower() == "y":
                try:
                    os.remove(SAVE_FILE)
                    slow("Save dihapus.")
                except:
                    slow("Gagal menghapus save.")
            main_menu()
        else:
            slow("Keluar dari permainan.")
            return
    else:
        new_game()

if __name__ == "__main__":
    main_menu()
