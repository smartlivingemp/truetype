from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from db import db

client_order_bp = Blueprint('client_order', __name__, template_folder='templates')

orders_collection = db["orders"]

@client_order_bp.route('/submit_order', methods=['GET', 'POST'])
def submit_order():
    if 'client_id' not in session:
        flash("Please log in to place an order", "danger")
        return redirect(url_for('client_login'))

    if request.method == 'POST':
        product = request.form.get('product')
        vehicle_number = request.form.get('vehicle_number')
        driver_name = request.form.get('driver_name')
        driver_phone = request.form.get('driver_phone')
        quantity = request.form.get('quantity')
        region = request.form.get('region')

        # ✅ Remove product_type from the required fields check
        if not all([product, vehicle_number, driver_name, driver_phone, quantity, region]):
            flash("All fields are required.", "danger")
            return redirect(url_for('client_order.submit_order'))

        order_data = {
            "client_id": session['client_id'],
            "product": product,
            "vehicle_number": vehicle_number,
            "driver_name": driver_name,
            "driver_phone": driver_phone,
            "quantity": int(quantity.replace(",", "")),
            "region": region,
            "status": "pending",
            "date": datetime.utcnow()
        }

        orders_collection.insert_one(order_data)
        flash("Order submitted successfully!", "success")
        return redirect(url_for('client_order.submit_order'))

    return render_template('client/client_order.html')
