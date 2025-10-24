from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Penyimpanan data sementara (nanti bisa diganti ke file/json/db)
players = {}

@app.route("/")
def home():
    return jsonify({"msg": "Adventure Text World Online Server aktif!"})

@app.route("/register", methods=["POST"])
def register():
    name = request.json.get("name")
    if not name:
        return jsonify({"error": "Nama diperlukan!"}), 400
    if name in players:
        return jsonify({"msg": f"{name} sudah terdaftar!"})
    players[name] = {"exp": 0, "gold": 0, "level": 1}
    return jsonify({"msg": f"Pemain {name} berhasil didaftarkan!"})

@app.route("/update", methods=["POST"])
def update():
    name = request.json.get("name")
    exp = request.json.get("exp", 0)
    gold = request.json.get("gold", 0)
    if name not in players:
        return jsonify({"error": "Pemain belum terdaftar!"}), 404

    players[name]["exp"] += exp
    players[name]["gold"] += gold

    # Auto level up sederhana
    while players[name]["exp"] >= players[name]["level"] * 100:
        players[name]["exp"] -= players[name]["level"] * 100
        players[name]["level"] += 1

    return jsonify({
        "msg": f"Data {name} diperbarui!",
        "data": players[name]
    })

@app.route("/leaderboard")
def leaderboard():
    lb = sorted(players.items(), key=lambda x: (x[1]["level"], x[1]["exp"]), reverse=True)
    return jsonify([
        {"name": p[0], "level": p[1]["level"], "exp": p[1]["exp"], "gold": p[1]["gold"]}
        for p in lb
    ])

if __name__ == "__main__":
    # host=0.0.0.0 biar bisa diakses lewat jaringan
    app.run(host="0.0.0.0", port=5000)
