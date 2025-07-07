from flask import Blueprint, render_template, session, redirect, url_for
from bson import ObjectId
from datetime import datetime
from db import db

client_order_history_bp = Blueprint('client_order_history', __name__)
orders_col = db["orders"]
clients_col = db["clients"]
payments_col = db["payments"]

@client_order_history_bp.route("/order_history")
def client_order_history():
    client_id = session.get("client_id")

    # ✅ Validate session and ObjectId
    if not client_id or not ObjectId.is_valid(client_id):
        return redirect(url_for("login.client_login"))

    # ✅ Fetch client
    client = clients_col.find_one({"_id": ObjectId(client_id)})
    if not client:
        return redirect(url_for("login.client_login"))

    # ✅ Fetch orders (client_id stored as string in orders)
    orders = list(orders_col.find({"client_id": client_id}).sort("date", -1))

    # ✅ Get latest approved order
    latest_approved = next((o for o in orders if o.get("status") == "approved"), None)

    total_paid = 0
    amount_left = 0

    if latest_approved:
        # ✅ Get payments only for that order
        order_id = latest_approved["_id"]
        confirmed_payments = list(payments_col.find({
            "client_id": ObjectId(client_id),
            "order_id": order_id,
            "status": "confirmed"
        }))
        total_paid = sum(p.get("amount", 0) for p in confirmed_payments)
        total_debt = float(latest_approved.get("total_debt", 0))
        amount_left = max(total_debt - total_paid, 0)

    return render_template(
        "client/client_order_history.html",
        orders=orders,
        client=client,
        latest_approved=latest_approved,
        total_paid=round(total_paid, 2),
        amount_left=round(amount_left, 2)
    )
