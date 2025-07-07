from flask import Blueprint, render_template, request, jsonify, session
from db import db
from datetime import datetime
from bson import ObjectId

# 📦 Collections
bdc_col = db["bdc"]
bdc_txn_col = db["bdc_transactions"]

# 🔹 Blueprint Declaration
bdc_bp = Blueprint('bdc', __name__)

# 📄 View: All BDC Accounts
@bdc_bp.route('/bdc')
def bdc_list():
    """
    Displays a list of all BDCs sorted by name.
    """
    bdcs = list(bdc_col.find().sort("name", 1))
    return render_template("partials/bdc.html", bdcs=bdcs)

# ➕ Create New BDC with name, phone, location
@bdc_bp.route('/bdc/add', methods=['POST'])
def add_bdc():
    """
    Adds a new BDC entry with name, phone, location, and initial balance 0.
    """
    data = request.json
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    location = data.get('location', '').strip()

    if not name or not phone or not location:
        return jsonify({"status": "error", "message": "All fields are required (name, phone, location)"}), 400

    if bdc_col.find_one({"name": name}):
        return jsonify({"status": "error", "message": "BDC with this name already exists"}), 400

    bdc_col.insert_one({
        "name": name,
        "phone": phone,
        "location": location,
        "balance": 0,
        "date_created": datetime.utcnow()
    })

    return jsonify({"status": "success"})

# 💰 Add or Subtract Funds
@bdc_bp.route('/bdc/txn/<bdc_id>', methods=['POST'])
def add_transaction(bdc_id):
    """
    Handles deposit or withdrawal transaction for a BDC.
    Stores a transaction log with amount, note, type, and timestamp.
    """
    try:
        data = request.json
        amount = float(data.get('amount', 0))
        note = data.get('note', '').strip()
        txn_type = data.get('type')

        if amount <= 0 or txn_type not in ['add', 'subtract']:
            return jsonify({"status": "error", "message": "Invalid amount or transaction type"}), 400

        bdc = bdc_col.find_one({"_id": ObjectId(bdc_id)})
        if not bdc:
            return jsonify({"status": "error", "message": "BDC not found"}), 404

        if txn_type == 'add':
            new_balance = bdc['balance'] + amount
            txn_label = 'deposit'
        else:
            new_balance = bdc['balance'] - amount
            txn_label = 'withdrawal'

        bdc_col.update_one({"_id": ObjectId(bdc_id)}, {"$set": {"balance": new_balance}})

        bdc_txn_col.insert_one({
            "bdc_id": ObjectId(bdc_id),
            "amount": amount,
            "type": txn_label,
            "note": note,
            "timestamp": datetime.utcnow()
        })

        return jsonify({"status": "success", "new_balance": new_balance})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 👤 View: BDC Profile and History
@bdc_bp.route('/bdc/profile/<bdc_id>')
def bdc_profile(bdc_id):
    """
    Displays the BDC profile page with balance and transaction history.
    Supports optional date filtering (?start=yyyy-mm-dd&end=yyyy-mm-dd).
    """
    bdc = bdc_col.find_one({"_id": ObjectId(bdc_id)})
    if not bdc:
        return "BDC not found", 404

    # ✅ Use session to determine role for proper back button
    role = session.get("role", "assistant")
    dashboard_url = "/admin/dashboard" if role == "admin" else "/assistant/dashboard"

    start = request.args.get("start")
    end = request.args.get("end")
    query = {"bdc_id": ObjectId(bdc_id)}

    try:
        if start:
            query["timestamp"] = {"$gte": datetime.strptime(start, "%Y-%m-%d")}
        if end:
            if "timestamp" in query:
                query["timestamp"]["$lte"] = datetime.strptime(end, "%Y-%m-%d")
            else:
                query["timestamp"] = {"$lte": datetime.strptime(end, "%Y-%m-%d")}
    except ValueError:
        pass

    transactions = list(bdc_txn_col.find(query).sort("timestamp", -1))
    return render_template("partials/bdc_profile.html", bdc=bdc, transactions=transactions, dashboard_url=dashboard_url)
