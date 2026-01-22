 from flask import Flask, request, render_template, send_file, redirect, url_for
from web3 import Web3
import hashlib
import os

app = Flask(__name__)

# ================= FILE STORAGE =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= BLOCKCHAIN CONFIG =================
INFURA_URL = os.environ.get("INFURA_URL")
PRIVATE_KEY = os.environ.get("PRIVATE_KEY")

if not INFURA_URL or not PRIVATE_KEY:
    raise Exception("❌ ENV variables INFURA_URL or PRIVATE_KEY not set")

w3 = Web3(Web3.HTTPProvider(INFURA_URL))

if not w3.is_connected():
    raise Exception("❌ Blockchain not connected")

account_owner = w3.eth.account.from_key(PRIVATE_KEY).address

# ================= HOSPITALS =================
# (You can replace with real Metamask addresses if needed)
HOSPITALS = {
    "Apollo Hospital": "0x1111111111111111111111111111111111111111",
    "AIIMS Hospital": "0x2222222222222222222222222222222222222222",
    "KIMS Hospital": "0x3333333333333333333333333333333333333333"
}

# ================= ABI =================
ABI = [
    {"inputs":[{"internalType":"string","name":"patientId","type":"string"},{"internalType":"string","name":"fileHash","type":"string"}],"name":"addRecord","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"string","name":"patientId","type":"string"},{"internalType":"address","name":"hospital","type":"address"}],"name":"grantAccess","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"string","name":"patientId","type":"string"},{"internalType":"address","name":"hospital","type":"address"}],"name":"checkAccess","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"string","name":"patientId","type":"string"}],"name":"getFileHash","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}
]

# ================= CONTRACT =================
CONTRACT_ADDRESS = "0x7cdc469F45e22d2B1e4C48AE17a1a95e5f626c18"

contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=ABI
)

# ================= ROUTES =================

@app.route("/")
def main():
    return render_template("main.html")


@app.route("/upload_page")
def upload_page():
    return render_template("upload.html", hospitals=HOSPITALS.keys())


@app.route("/download_page")
def download_page():
    return render_template("download.html", hospitals=HOSPITALS.keys())


# ================= UPLOAD =================
@app.route("/upload", methods=["POST"])
def upload():
    try:
        patient_id = request.form.get("patient_id", "").strip()
        hospital_name = request.form.get("hospital")
        file = request.files.get("file")

        if not patient_id or not hospital_name or not file:
            return "❌ Missing details"

        hospital_address = Web3.to_checksum_address(HOSPITALS[hospital_name])

        filename = patient_id + "_" + file.filename.replace(" ", "_")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        with open(filepath, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        nonce = w3.eth.get_transaction_count(account_owner)

        tx1 = contract.functions.addRecord(patient_id, file_hash).build_transaction({
            "from": account_owner,
            "nonce": nonce,
            "gas": 300000,
            "gasPrice": w3.to_wei("10", "gwei")
        })

        signed_tx1 = w3.eth.account.sign_transaction(tx1, PRIVATE_KEY)
        tx_hash1 = w3.eth.send_raw_transaction(signed_tx1.rawTransaction)
        w3.eth.wait_for_transaction_receipt(tx_hash1)

        tx2 = contract.functions.grantAccess(patient_id, hospital_address).build_transaction({
            "from": account_owner,
            "nonce": nonce + 1,
            "gas": 300000,
            "gasPrice": w3.to_wei("10", "gwei")
        })

        signed_tx2 = w3.eth.account.sign_transaction(tx2, PRIVATE_KEY)
        tx_hash2 = w3.eth.send_raw_transaction(signed_tx2.rawTransaction)
        w3.eth.wait_for_transaction_receipt(tx_hash2)

        return redirect(url_for("main"))

    except Exception as e:
        return f"❌ Upload Error: {str(e)}"


# ================= DOWNLOAD =================
@app.route("/download", methods=["GET", "POST"])
def download():
    if request.method == "GET":
        return redirect(url_for("download_page"))

    try:
        patient_id = request.form.get("patient_id", "").strip()
        hospital_name = request.form.get("hospital")

        if not patient_id or not hospital_name:
            return "❌ Missing details"

        hospital_address = Web3.to_checksum_address(HOSPITALS[hospital_name])

        allowed = contract.functions.checkAccess(
            patient_id, hospital_address
        ).call()

        if not allowed:
            return "❌ Access Denied by Blockchain"

        for file in os.listdir(UPLOAD_FOLDER):
            if file.startswith(patient_id + "_"):
                return send_file(os.path.join(UPLOAD_FOLDER, file), as_attachment=True)

        return "❌ File not found"

    except Exception as e:
        return f"❌ Download Error: {str(e)}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
