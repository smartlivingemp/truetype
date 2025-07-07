from flask import Flask, redirect, url_for, session  # ✅ Required for logout

# === Auth/Login ===
from login import login_bp

# === Shared Features ===
from register_client import register_client_bp
from clientlist import clientlist_bp
from client_profile import client_profile_bp
from approved_orders import approved_orders_bp
from orders import orders_bp
from payments import payments_bp
from debtors import debtors_bp
from bdc import bdc_bp
from home import home_bp

# === Admin Features ===
from admin.admin_dashboard import admin_dashboard_bp
from admin.settings import admin_settings_bp

# === Assistant Features ===
from assistant.assistant_dashboard import assistant_dashboard_bp

# === Client Features ===
from client.client_dashboard import client_dashboard_bp
from client.client_order import client_order_bp
from client.client_order_history import client_order_history_bp
from client.client_payment import client_payment_bp


# === Initialize App ===
app = Flask(__name__)
app.secret_key = '4b1b26eee81fd7da3be8efd2649c3b07140b511118b11009f243adabd4d61559'  # 🔐 Use environment variable in production


# === Blueprint Registration ===

# Auth/Login
app.register_blueprint(login_bp)
app.register_blueprint(home_bp)

# Shared Features
app.register_blueprint(register_client_bp, url_prefix='/register')
app.register_blueprint(clientlist_bp)
app.register_blueprint(client_profile_bp)
app.register_blueprint(approved_orders_bp)
app.register_blueprint(orders_bp, url_prefix='/orders')
app.register_blueprint(payments_bp)
app.register_blueprint(debtors_bp)
app.register_blueprint(bdc_bp)

# Admin
app.register_blueprint(admin_dashboard_bp, url_prefix='/admin')
app.register_blueprint(admin_settings_bp)

# Assistant
app.register_blueprint(assistant_dashboard_bp, url_prefix='/assistant')

# Client
app.register_blueprint(client_dashboard_bp, url_prefix='/client')
app.register_blueprint(client_order_bp, url_prefix='/client')
app.register_blueprint(client_order_history_bp, url_prefix='/client')
app.register_blueprint(client_payment_bp, url_prefix='/client')


# === Logout Route ===
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login.login'))


# === Run App ===
if __name__ == '__main__':
    app.run(debug=True)
