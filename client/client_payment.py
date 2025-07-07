from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from db import db
from datetime import datetime
from bson import ObjectId

client_payment_bp = Blueprint("client_payment", __name__, template_folder="templates")

payments_col = db["payments"]
orders_col = db["orders"]

@client_payment_bp.route("/payment", methods=["GET", "POST"])
def client_payment():
    client_id = session.get("client_id")

    # ✅ Check if user is logged in
    if not client_id:
        flash("⚠ Session expired. Please log in again.", "warning")
        return redirect(url_for("login.login"))

    # ✅ Get latest approved order
    latest_order = orders_col.find_one(
        {"client_id": str(client_id), "status": "approved"},
        sort=[("date", -1)]
    )

    if not latest_order:
        flash("⚠ You don't have any approved order to make a payment.", "danger")
        return redirect(url_for("client_payment.client_payment"))

    latest_order_id = latest_order["_id"]

    if request.method == "POST":
        amount = request.form.get("amount", "").strip()
        bank_name = request.form.get("bank_name", "").strip()
        proof_url = request.form.get("proof_url", "").strip()

        # ✅ Field validation
        if not all([amount, bank_name, proof_url]):
            flash("⚠ All fields are required.", "danger")
            return redirect(url_for("client_payment.client_payment"))

        try:
            payment = {
                "client_id": ObjectId(client_id),
                "order_id": latest_order_id,  # ✅ Link payment to current approved order
                "amount": float(amount),
                "bank_name": bank_name,
                "proof_url": proof_url,
                "status": "pending",
                "date": datetime.utcnow()
            }
            payments_col.insert_one(payment)
            flash("✅ Payment submitted successfully!", "success")
        except Exception as e:
            flash(f"❌ Error saving payment: {str(e)}", "danger")

        return redirect(url_for("client_payment.client_payment"))

    # ✅ Get past payment history (all, not just for current order)
    payment_history = list(payments_col.find({"client_id": ObjectId(client_id)}).sort("date", -1))

    formatted_payments = []
    for p in payment_history:
        formatted_payments.append({
            "date": p["date"].strftime("%Y-%m-%d"),
            "amount": float(p.get("amount", 0)),
            "bank_name": p.get("bank_name", "-"),
            "proof_url": p.get("proof_url", "#"),
            "status": p.get("status", "pending"),
            "feedback": p.get("feedback", ""),
            "linked_order": str(p.get("order_id", ""))  # Optional: show on UI
        })

    return render_template(
        "client/client_payment.html",
        payments=formatted_payments,
        latest_order_total=latest_order.get("total_debt", 0)
    )
