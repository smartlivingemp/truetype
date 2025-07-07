from flask import Blueprint, render_template
from db import db
from bson import ObjectId
from datetime import datetime

debtors_bp = Blueprint('debtors', __name__)

clients_col = db["clients"]
orders_col = db["orders"]
payments_col = db["payments"]

@debtors_bp.route('/debtors')
def view_debtors():
    clients = list(clients_col.find({"status": "active"}))
    client_data = []

    for client in clients:
        client_id = client["_id"]
        client_id_str = str(client_id)

        # ✅ Get approved orders (ordered by date DESC)
        approved_orders = list(orders_col.find({
            "client_id": client_id_str,
            "status": "approved"
        }).sort("date", -1))

        latest_order = approved_orders[0] if approved_orders else None

        if not latest_order:
            continue  # Skip clients without any approved order

        order_id = latest_order["_id"]
        total_debt = float(latest_order.get("total_debt", 0))

        # ✅ Get confirmed payments only for latest order
        payments = list(payments_col.find({
            "client_id": client_id,
            "order_id": order_id,
            "status": "confirmed"
        }).sort("date", 1))

        total_paid = 0
        payment_data = []

        for p in payments:
            try:
                amount = float(p.get("amount", 0))
                date_str = p.get("date")
                if isinstance(date_str, datetime):
                    date_str = date_str.strftime("%Y-%m-%d")
                elif not date_str:
                    date_str = "Unknown"
            except:
                amount = 0
                date_str = "Unknown"

            payment_data.append({
                "date": date_str,
                "amount": amount
            })
            total_paid += amount

        client_data.append({
            "name": client.get("name", "Unnamed"),
            "client_id": client.get("client_id", client_id_str),
            "total_paid": round(total_paid, 2),
            "total_debt": round(total_debt, 2),
            "payments": payment_data
        })

    return render_template("partials/debtors.html", client_data=client_data)
