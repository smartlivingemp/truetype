from flask import Blueprint, render_template, request, redirect, flash, session, jsonify
from datetime import datetime
from db import db
import requests
from urllib.parse import quote

register_client_bp = Blueprint('register_client', __name__, template_folder='templates')
clients_collection = db.clients

ARKESEL_API_KEY = "c1JKV21keG1DdnJZQW1zc2JpVks"
DEFAULT_IMAGE_URL = "https://cdn-icons-png.flaticon.com/256/3135/3135715.png"

# Generate client ID
def generate_unique_client_id(phone):
    year = datetime.now().year % 100
    last3 = phone[-3:].zfill(3)
    return f"TT{year:02d}{last3}"

# Send SMS using GET (same style as working payment route)
def send_registration_sms(name, phone, client_id):
    try:
        phone_number = phone.strip().replace(" ", "").replace("-", "")
        if phone_number.startswith("0") and len(phone_number) == 10:
            phone_number = "233" + phone_number[1:]

        if not phone_number.startswith("233") or len(phone_number) != 12:
            print("❌ Invalid phone number for SMS:", phone)
            return False

        first_name = name.split()[0] if name else "Client"
        message = (
            f"Welcome to TrueType Services, {first_name}!\n\n"
            f"Your account has been successfully created.\n"
            f"Login Details:\n"
            f"Client ID: {client_id}\n"
            f"Password: {phone}\n\n"
            f"Use these to log in at https://truetypegh.com/login\n"
            f"Thank you!"
        )

        sms_url = (
            "https://sms.arkesel.com/sms/api?action=send-sms"
            f"&api_key={ARKESEL_API_KEY}"
            f"&to={phone_number}"
            f"&from=TrueType"
            f"&sms={quote(message)}"
        )

        response = requests.get(sms_url)
        print("Arkesel SMS response:", response.text)

        # ✅ Fixed condition to accept "code": "ok"
        return response.status_code == 200 and '"code":"ok"' in response.text
    except Exception as e:
        print("SMS error:", str(e))
        return False

@register_client_bp.route('/admin/register_client', methods=['GET', 'POST'])
@register_client_bp.route('/assistant/register_client', methods=['GET', 'POST'])
def register_client():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        location = request.form.get('location', '').strip()
        image_url = request.form.get('image_url') or DEFAULT_IMAGE_URL

        if not name or not phone:
            msg = "❗ Name and phone are required!"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return msg, 400
            flash(msg, 'danger')
            return redirect(request.path)

        client_id = generate_unique_client_id(phone)
        existing = clients_collection.find_one({"client_id": client_id})
        if existing:
            msg = f"❌ A client with ID {client_id} already exists."
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return msg, 400
            flash(msg, 'danger')
            return redirect(request.path)

        creator = session.get("username", "unknown")
        role = session.get("role", "unknown")

        client_data = {
            'name': name,
            'phone': phone,
            'email': email if email else None,
            'location': location if location else None,
            'image_url': image_url,
            'client_id': client_id,
            'status': 'active',
            'date_registered': datetime.utcnow(),
            'created_by': {
                'role': role,
                'username': creator
            }
        }

        try:
            clients_collection.insert_one(client_data)
            sms_sent = send_registration_sms(name, phone, client_id)
            if not sms_sent:
                print("⚠️ SMS failed or invalid number.")
        except Exception as e:
            print("Registration error:", str(e))
            error_msg = "❌ Client registration failed. Please try again."
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return error_msg, 500
            flash(error_msg, 'danger')
            return redirect(request.path)

        success_msg = f"✅ Client registered successfully with ID: {client_id}"
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({
                "message": success_msg,
                "client_id": client_id,
                "phone": phone
            }), 200

        flash(success_msg, 'success')
        return redirect(request.path)

    return render_template('partials/register_client.html', role=session.get('role'))
