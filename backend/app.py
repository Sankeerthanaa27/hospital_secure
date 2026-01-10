from flask import Flask, request, render_template, send_file, redirect
from web3 import Web3
import hashlib
import os

app = Flask(__name__)

# ---------------- File Storage ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.abspath(os.path.join(BASE_DIR, "..", "uploads"))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- Blockchain Connection ----------------
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))
accounts = w3.eth.accounts
account_owner = accounts[0]   # Hospital A uploader

# ---------------- Hospital Mapping ----------------
HOSPITALS = {
    "Apollo Hospital": accounts[1],
    "AIIMS Hospital": accounts[2],
    "KIMS Hospital": accounts[3]
}

# ---------------- ABI ----------------
ABI = [
    {'anonymous': False, 'inputs': [{'indexed': False, 'internalType': 'string', 'name': 'patientId', 'type': 'string'}, {'indexed': False, 'internalType': 'address', 'name': 'hospital', 'type': 'address'}], 'name': 'AccessGranted', 'type': 'event'},
    {'anonymous': False, 'inputs': [{'indexed': False, 'internalType': 'string', 'name': 'patientId', 'type': 'string'}, {'indexed': False, 'internalType': 'string', 'name': 'fileHash', 'type': 'string'}], 'name': 'RecordStored', 'type': 'event'},
    {'inputs': [{'internalType': 'string', 'name': 'patientId', 'type': 'string'}, {'internalType': 'string', 'name': 'fileHash', 'type': 'string'}], 'name': 'addRecord', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'},
    {'inputs': [{'internalType': 'string', 'name': 'patientId', 'type': 'string'}, {'internalType': 'address', 'name': 'hospital', 'type': 'address'}], 'name': 'checkAccess', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'view', 'type': 'function'},
    {'inputs': [{'internalType': 'string', 'name': 'patientId', 'type': 'string'}], 'name': 'getFileHash', 'outputs': [{'internalType': 'string', 'name': '', 'type': 'string'}], 'stateMutability': 'view', 'type': 'function'},
    {'inputs': [{'internalType': 'string', 'name': 'patientId', 'type': 'string'}, {'internalType': 'address', 'name': 'hospital', 'type': 'address'}], 'name': 'grantAccess', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}
]

# ---------------- Contract Address ----------------
CONTRACT_ADDRESS = "0x75a499cd17dcC642E8a90eB4128421D181636882"   # <-- your deployed address

contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=ABI
)

# ---------------- ROUTES ----------------

# Main Page
@app.route("/")
def main():
    return render_template("main.html")

# Upload Page
@app.route("/upload_page")
def upload_page():
    return render_template("upload.html", hospitals=HOSPITALS.keys())

# Download Page
@app.route("/download_page")
def download_page():
    return render_template("download.html", hospitals=HOSPITALS.keys())

# ---------------- Upload + Auto Grant ----------------
@app.route("/upload", methods=["POST"])
def upload():
    patient_id = request.form["patient_id"].strip()
    hospital_name = request.form["hospital"]
    hospital_address = HOSPITALS[hospital_name]

    file = request.files["file"]
    filename = patient_id + "_" + file.filename.replace(" ", "_")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    with open(filepath, "rb") as f:
        data = f.read()

    file_hash = hashlib.sha256(data).hexdigest()

    # Store hash
    tx1 = contract.functions.addRecord(patient_id, file_hash).transact({
        "from": account_owner
    })
    w3.eth.wait_for_transaction_receipt(tx1)

    # Grant access automatically
    tx2 = contract.functions.grantAccess(patient_id, hospital_address).transact({
        "from": account_owner
    })
    w3.eth.wait_for_transaction_receipt(tx2)

    return redirect("/")

# ---------------- Download ----------------
@app.route("/download", methods=["POST"])
def download():
    patient_id = request.form["patient_id"].strip()
    hospital_name = request.form["hospital"]
    hospital_address = Web3.to_checksum_address(HOSPITALS[hospital_name])

    allowed = contract.functions.checkAccess(patient_id, hospital_address).call()

    if not allowed:
        return "❌ Access Denied by Blockchain"

    for file in os.listdir(UPLOAD_FOLDER):
        if file.startswith(patient_id + "_"):
            return send_file(os.path.join(UPLOAD_FOLDER, file), as_attachment=True)

    return "❌ File not found"

# ---------------- Run ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

