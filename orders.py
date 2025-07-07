from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from bson import ObjectId
from db import db
from datetime import datetime

orders_bp = Blueprint('orders', __name__, template_folder='templates')

orders_collection = db['orders']
clients_collection = db['clients']
bdc_collection = db['bdc']  # Assuming your BDCs are stored in this collection


@orders_bp.route('/', methods=['GET'])
def view_orders():
    if 'role' not in session or session['role'] not in ['admin', 'assistant']:
        flash("Access denied.", "danger")
        return redirect(url_for('login.login'))

    orders = list(orders_collection.find({'status': 'pending'}).sort('date', -1))
    bdcs = list(bdc_collection.find({}, {'name': 1}))  # Only fetch name field

    for order in orders:
        try:
            client = clients_collection.find_one({'_id': ObjectId(order.get('client_id'))})
        except:
            client = None

        if client:
            order['client_name'] = client.get('name', 'No Name')
            order['client_image_url'] = client.get('image_url', '')
            order['client_id'] = client.get('client_id', '')
            order['client_profile_url'] = None
        else:
            order['client_name'] = 'Unknown'
            order['client_image_url'] = ''
            order['client_profile_url'] = None

        try:
            margin = float(order.get('margin', 0))
            quantity = float(order.get('quantity', 0))
            order['returns'] = round(margin * quantity, 2)
        except (TypeError, ValueError):
            order['returns'] = 0.0

    return render_template('partials/orders.html', orders=orders, bdcs=bdcs)

# ✅ Update Order Fields + Approve
@orders_bp.route('/update/<order_id>', methods=['POST'])
def update_order(order_id):
    if 'role' not in session or session['role'] not in ['admin', 'assistant']:
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    form = request.form

    fields = {
        "omc": form.get("omc"),
        "bdc": form.get("bdc"),
        "depot": form.get("depot"),
        "p_bdc_omc": form.get("p_bdc_omc"),
        "s_bdc_omc": form.get("s_bdc_omc"),
        "margin": form.get("margin"),
        "tax": form.get("tax"),
        "total_debt": form.get("total_debt"),
        "due_date": form.get("due_date")
    }

    if not all([fields["omc"], fields["bdc"], fields["depot"]]):
        return jsonify({"success": False, "error": "OMC, BDC, and DEPOT are required."}), 400

    update_data = {
        "omc": fields["omc"],
        "bdc": fields["bdc"],
        "depot": fields["depot"]
    }

    complete_fields = True
    try:
        update_data["p_bdc_omc"] = float(fields["p_bdc_omc"]) if fields["p_bdc_omc"] else None
        update_data["s_bdc_omc"] = float(fields["s_bdc_omc"]) if fields["s_bdc_omc"] else None
        update_data["margin"] = float(fields["margin"]) if fields["margin"] else None
        update_data["tax"] = float(fields["tax"]) if fields["tax"] else None
        update_data["total_debt"] = float(fields["total_debt"]) if fields["total_debt"] else None
        update_data["due_date"] = datetime.strptime(fields["due_date"], "%Y-%m-%d") if fields["due_date"] else None

        for k in ["p_bdc_omc", "s_bdc_omc", "margin", "tax", "total_debt", "due_date"]:
            if update_data.get(k) is None:
                complete_fields = False

    except ValueError:
        return jsonify({"success": False, "error": "Invalid input format"}), 400

    update_data["status"] = "approved" if complete_fields else "pending"

    orders_collection.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": update_data}
    )

    return jsonify({
        "success": True,
        "message": "Order updated" + (" and approved" if complete_fields else " (still pending)")
    })
