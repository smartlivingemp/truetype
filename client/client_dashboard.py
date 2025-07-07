from flask import Blueprint, render_template, session, redirect, url_for, flash
from bson import ObjectId
from db import clients_collection

client_dashboard_bp = Blueprint('client_dashboard', __name__, template_folder='templates')

@client_dashboard_bp.route('/dashboard')
def dashboard():
    if 'client_id' not in session or 'client_name' not in session:
        flash("Please log in first", "warning")
        return redirect(url_for('login.login'))

    client_id = session['client_id']

    # Validate and fetch the client document
    if not ObjectId.is_valid(client_id):
        flash("Invalid session. Please log in again.", "danger")
        return redirect(url_for('login.login'))

    client = clients_collection.find_one({"_id": ObjectId(client_id)})
    if not client:
        flash("Client not found. Please contact support.", "danger")
        return redirect(url_for('login.login'))

    return render_template(
        'client/client_dashboard.html',
        client=client
    )
