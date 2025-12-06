import json
import logging
import random
import requests
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)

load_dotenv()

MSG91_AUTH_KEY = os.getenv("MSG91_AUTH_KEY")
INTEGRATED_NUMBER = os.getenv("INTEGRATED_NUMBER")
TEMPLATE_NAMESPACE = os.getenv("TEMPLATE_NAMESPACE")
TEMPLATE_NAME = os.getenv("TEMPLATE_NAME")

def generate_otp():
    return str(random.randint(100000, 999999))

def send_whatsapp_otp(phone: str, otp: str):
    url = "https://api.msg91.com/api/v5/whatsapp/whatsapp-outbound-message/bulk/"

    headers = {
        "Content-Type": "application/json",
        "authkey": MSG91_AUTH_KEY
    }

    payload = {
        "integrated_number": INTEGRATED_NUMBER,
        "content_type": "template",
        "payload": {
            "messaging_product": "whatsapp",
            "type": "template",
            "template": {
                "name": TEMPLATE_NAME,
                "language": {
                    "code": "en_US",
                    "policy": "deterministic"
                },
                "namespace": TEMPLATE_NAMESPACE,
                "to_and_components": [
                    {
                        "to": [f"91{phone}"],
                        "components": {
                            "body_1": { "type": "text", "value": "" },
                            "body_2": { "type": "text", "value": otp }
                        }
                    }
                ]
            }
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        logger.info(f"MSG91 OTP Response: {data}")
        return data
    except Exception as e:
        logger.error(f"MSG91 OTP Error: {e}")
        return None

def json_response(status: bool, message: str, status_code: int = 200, **extra):
    payload = {"status": status, "message": message}
    if extra:
        payload.update(extra)
    return JsonResponse(payload, status=status_code)

def get_json(request, allow_empty: bool = False):
    if not request.body:
        return ({} if allow_empty else None, None if allow_empty else "Empty JSON body")

    try:
        body = request.body.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        logger.warning("Failed to decode request body: %s", exc)
        return None, "Invalid request encoding"

    if not body:
        return ({} if allow_empty else None, None if allow_empty else "Empty JSON body")

    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        logger.warning("Invalid JSON payload: %s", exc)
        return None, "Invalid JSON payload"

    if not isinstance(data, dict):
        return None, "JSON payload must be an object"

    if not data and not allow_empty:
        return None, "Empty JSON body"

    return data, None

def require_fields(data, fields):
    return [field for field in fields if not data.get(field)]

def tester(request):
    try:
        return json_response(True, "IoT Backend is running")
    except Exception:
        logger.exception("Tester endpoint failed")
        return json_response(False, "Tester endpoint encountered an unexpected error", status_code=500)

from datetime import datetime, timedelta

OTP_EXPIRY_MINUTES = 15

# ---------------- Signup ----------------
@csrf_exempt
def signup(request):
    if request.method != "POST":
        logger.warning("Signup attempt with non-POST method: %s", request.method)
        return json_response(False, "POST required", status_code=405)

    data, error = get_json(request)
    if error:
        logger.warning("Signup JSON parse error: %s", error)
        return json_response(False, error, status_code=400)

    missing = require_fields(data, ["phone", "password"])
    if missing:
        logger.warning("Signup missing fields: %s", missing)
        return json_response(False, f"Missing required fields: {', '.join(missing)}", status_code=400)

    phone = data["phone"]
    password = data["password"]
    name = data.get("name", "")

    logger.info("Starting signup for phone: %s", phone)

    try:
        with connection.cursor() as cursor:
            # Check if user already exists in main users
            cursor.execute("SELECT id FROM iot_users WHERE phone=%s", [phone])
            if cursor.fetchone():
                logger.info("Signup failed: user already exists: %s", phone)
                return json_response(False, "User already exists", status_code=400)

            # Remove old pending entries for same phone (if any)
            deleted = cursor.execute("DELETE FROM iot_pending_users WHERE phone=%s", [phone])
            logger.info("Deleted %d old pending users for phone %s", deleted, phone)

            # Insert into pending users
            hashed_password = password  # Replace with proper hash if needed
            cursor.execute(
                "INSERT INTO iot_pending_users (phone, password, name, created_at) VALUES (%s, %s, %s, %s)",
                [phone, hashed_password, name, datetime.now()]
            )
            pending_user_id = cursor.lastrowid
            logger.info("Pending user created with ID %s", pending_user_id)

            # Generate OTP
            otp = generate_otp()
            expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
            cursor.execute(
                "INSERT INTO iot_otps (phone, otp, purpose, expires_at) VALUES (%s, %s, 'signup', %s)",
                [phone, otp, expires_at]
            )
            logger.info("OTP %s inserted for phone %s, expires at %s", otp, phone, expires_at)

        # Send OTP via WhatsApp
        otp_response = send_whatsapp_otp(phone, otp)
        if otp_response:
            logger.info("OTP sent via WhatsApp successfully: %s", otp_response)
        else:
            logger.error("Failed to send OTP via WhatsApp for phone %s", phone)
            return json_response(False, "Unable to send OTP via WhatsApp", status_code=500)

    except Exception as e:
        logger.exception("Signup OTP failure for phone %s: %s", phone, str(e))
        return json_response(False, f"Unable to process signup right now: {str(e)}", status_code=500)

    return json_response(True, "OTP sent", user_id=pending_user_id)

# ---------------- Verify OTP ----------------
@csrf_exempt
def verify_signup_otp(request):
    if request.method != "POST":
        return json_response(False, "POST required", status_code=405)

    data, error = get_json(request)
    if error:
        return json_response(False, error, status_code=400)

    missing = require_fields(data, ["user_id", "otp"])
    if missing:
        return json_response(False, f"Missing required fields: {', '.join(missing)}", status_code=400)

    pending_user_id = data["user_id"]
    otp = data["otp"]

    try:
        with connection.cursor() as cursor:
            # Fetch pending user
            cursor.execute(
                "SELECT phone, password, name FROM iot_pending_users WHERE id=%s",
                [pending_user_id]
            )
            row = cursor.fetchone()
            if not row:
                return json_response(False, "Pending user not found", status_code=404)
            phone, password_hash, name = row

            # Fetch latest OTP
            cursor.execute(
                "SELECT id, otp, expires_at FROM iot_otps WHERE phone=%s AND purpose='signup' ORDER BY created_at DESC LIMIT 1",
                [phone]
            )
            otp_row = cursor.fetchone()
            if not otp_row:
                return json_response(False, "OTP not found", status_code=400)
            otp_id, db_otp, expires_at = otp_row

            if datetime.now() > expires_at:
                return json_response(False, "OTP expired", status_code=400)
            if str(otp) != str(db_otp):
                return json_response(False, "Invalid OTP", status_code=400)

            # Insert into main users table
            cursor.execute(
                "INSERT INTO iot_users (phone, password_hash, name) VALUES (%s, %s, %s)",
                [phone, password_hash, name]
            )
            user_id = cursor.lastrowid

            # Delete pending user and OTP
            cursor.execute("DELETE FROM iot_pending_users WHERE id=%s", [pending_user_id])
            cursor.execute("DELETE FROM iot_otps WHERE id=%s", [otp_id])

    except Exception:
        logger.exception("Signup verification failed for pending user %s", pending_user_id)
        return json_response(False, "Unable to verify OTP right now", status_code=500)

    return json_response(True, "Signup verified", user_id=user_id)

@csrf_exempt
def delete_device(request):
    if request.method != 'POST':
        return json_response(False, 'Invalid request method')

    try:
        data = json.loads(request.body.decode('utf-8'))
        device_id = data.get('device_id')
        user_id = data.get('user_id')

        if not device_id or not user_id:
            return json_response(False, 'Missing device_id or user_id')

        with connection.cursor() as cursor:

            # Check if device exists
            cursor.execute("SELECT id FROM iot_devices WHERE id=%s", [device_id])
            if not cursor.fetchone():
                return json_response(False, 'Device not found')

            # Check user-device mapping
            cursor.execute("""
                SELECT role FROM iot_user_devices
                WHERE user_id=%s AND device_id=%s
            """, [user_id, device_id])
            row = cursor.fetchone()

            if not row:
                return json_response(False, 'Device not assigned to this user')

            role = row[0]

            # ========== CASE 1: USER IS ADMIN → DELETE DEVICE COMPLETELY ==========
            if role == 'admin':
                # Delete device and mappings and requests
                cursor.execute("DELETE FROM iot_user_devices WHERE device_id=%s", [device_id])
                cursor.execute("DELETE FROM iot_device_access_requests WHERE device_id=%s", [device_id])
                cursor.execute("DELETE FROM iot_devices WHERE id=%s", [device_id])

                return json_response(True, 'Device deleted completely (Admin removed device)')

            # ========== CASE 2: USER IS MEMBER → JUST REMOVE THEM ==========

            # Remove mapping
            cursor.execute("""
                DELETE FROM iot_user_devices
                WHERE user_id=%s AND device_id=%s
            """, [user_id, device_id])

            # Reduce user_count
            cursor.execute("""
                UPDATE iot_devices
                SET user_count = user_count - 1
                WHERE id = %s
            """, [device_id])

            # After decreasing count, check if device has any users left
            cursor.execute("""
                SELECT COUNT(*) FROM iot_user_devices
                WHERE device_id=%s
            """, [device_id])
            remaining = cursor.fetchone()[0]

            # If no users remain → delete device fully
            if remaining == 0:
                cursor.execute("DELETE FROM iot_devices WHERE id=%s", [device_id])
                cursor.execute("DELETE FROM iot_device_access_requests WHERE device_id=%s", [device_id])
                return json_response(True, 'Device deleted because no members left')

        return json_response(True, 'Device removed from user successfully')

    except Exception as e:
        logger.exception("Delete device failure: %s", str(e))
        return json_response(False, 'Unable to remove device right now', status_code=500)

@csrf_exempt
def login(request):
    if request.method != "POST":
        return json_response(False, "POST required", status_code=405)

    data, error = get_json(request)
    if error:
        return json_response(False, error, status_code=400)

    missing = require_fields(data, ["phone", "password"])
    if missing:
        return json_response(False, f"Missing required fields: {', '.join(missing)}", status_code=400)

    phone = data["phone"]
    password = data["password"]

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, password_hash,name FROM iot_users WHERE phone=%s", [phone])
            row = cursor.fetchone()
    except Exception:
        logger.exception("Login failure for phone %s", phone)
        return json_response(False, "Unable to process login right now", status_code=500)

    if not row:
        return json_response(False, "Invalid phone or password", status_code=401)

    user_id, stored_password,name = row
    if stored_password != password:
        return json_response(False, "Invalid phone or password", status_code=401)

    return json_response(True, "Login successful", user_id=user_id, name=name)

@csrf_exempt
def forgot_password_send_otp(request):
    if request.method != "POST":
        return json_response(False, "POST required", status_code=405)

    data, error = get_json(request)
    if error:
        return json_response(False, error, status_code=400)

    phone = data.get("phone")
    if not phone:
        return json_response(False, "phone required", status_code=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM iot_users WHERE phone=%s", [phone])
            row = cursor.fetchone()
    except Exception:
        logger.exception("Forgot password OTP failure for phone %s", phone)
        return json_response(False, "Unable to process OTP request right now", status_code=500)

    if not row:
        return json_response(False, "Phone not registered", status_code=404)

    user_id = row[0]

    # Generate OTP
    otp = generate_otp()
    expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    # Store OTP in DB
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO iot_otps (phone, otp, purpose, expires_at) VALUES (%s, %s, 'forgot', %s)",
                [phone, otp, expires_at]
            )
    except Exception:
        logger.exception("Failed to store forgot OTP for phone %s", phone)
        return json_response(False, "Unable to generate OTP", status_code=500)

    # Send OTP via WhatsApp
    send_whatsapp_otp(phone, otp)

    return json_response(True, "OTP sent", user_id=user_id)

@csrf_exempt
def verify_forgot_otp(request):
    if request.method != "POST":
        return json_response(False, "POST required", status_code=405)

    data, error = get_json(request)
    if error:
        return json_response(False, error, status_code=400)

    missing = require_fields(data, ["user_id", "otp", "new_password"])
    if missing:
        return json_response(False, f"Missing required fields: {', '.join(missing)}", status_code=400)

    user_id = data["user_id"]
    otp = data["otp"]
    new_password = data["new_password"]

    try:
        with connection.cursor() as cursor:
            # Get phone from user_id
            cursor.execute("SELECT phone FROM iot_users WHERE id=%s", [user_id])
            row = cursor.fetchone()

        if not row:
            return json_response(False, "User not found", status_code=404)

        phone = row[0]

        # Fetch latest OTP for forgot-password
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, otp, expires_at FROM iot_otps WHERE phone=%s AND purpose='forgot' ORDER BY created_at DESC LIMIT 1",
                [phone]
            )
            otp_row = cursor.fetchone()

        if not otp_row:
            return json_response(False, "OTP not found or expired", status_code=400)

        otp_id, db_otp, expires_at = otp_row
        if datetime.now() > expires_at:
            return json_response(False, "OTP expired", status_code=400)

        if str(otp) != str(db_otp):
            return json_response(False, "Invalid OTP", status_code=400)

        # Update password
        with connection.cursor() as cursor:
            cursor.execute("UPDATE iot_users SET password_hash=%s WHERE id=%s", [new_password, user_id])

            # Delete used OTP
            cursor.execute("DELETE FROM iot_otps WHERE id=%s", [otp_id])

    except Exception as e:
        logger.exception("Forgot OTP verify error for user %s", user_id)
        return json_response(False, f"Error: {str(e)}", status_code=500)

    return json_response(True, "Password updated successfully")

@csrf_exempt
def logout(request):
    return json_response(True, "Logged out")

# -----------------------------
# New helper: check if user already has access to device
def _has_device_access(user_id, device_id):
    """Check if user already has access to the device"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM iot_user_devices WHERE user_id=%s AND device_id=%s",
                [user_id, device_id]
            )
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error("Error checking device access for user %s device %s: %s", user_id, device_id, str(e))
        return False

# Replaced add_device with improved implementation (duplicate checks + request checks)
@csrf_exempt
def add_device(request):
    if request.method != "POST":
        logger.warning("Invalid request method: %s", request.method)
        return json_response(False, "POST required", status_code=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        logger.info("Received add_device request with data: %s", data)
    except Exception as e:
        logger.error("Error parsing JSON: %s", str(e))
        return json_response(False, "Invalid JSON data", status_code=400)

    missing = require_fields(data, ["user_id", "device_code"])
    if missing:
        logger.warning("Missing required fields: %s", missing)
        return json_response(False, f"Missing required fields: {', '.join(missing)}", status_code=400)

    user_id = data["user_id"]
    device_code = data["device_code"].strip().upper()  # Normalize device code
    logger.info("Processing add_device for user_id: %s, device_code: %s", user_id, device_code)

    try:
        with connection.cursor() as cursor:
            # Check if device exists
            cursor.execute("SELECT id, user_count FROM iot_devices WHERE device_code=%s", [device_code])
            device = cursor.fetchone()

            if device:
                device_id = device[0]
                logger.info("Device exists with ID: %s", device_id)
                
                # Check if user already has access
                cursor.execute(
                    "SELECT id FROM iot_user_devices WHERE user_id=%s AND device_id=%s",
                    [user_id, device_id]
                )
                if cursor.fetchone():
                    logger.warning("User %s already has access to device %s", user_id, device_id)
                    return json_response(False, "You already have access to this device", status_code=400)
                
                # Check if request already exists
                cursor.execute(
                    "SELECT id FROM iot_device_access_requests WHERE device_id=%s AND requested_by_user_id=%s",
                    [device_id, user_id]
                )
                if cursor.fetchone():
                    logger.warning("Duplicate request from user %s for device %s", user_id, device_id)
                    return json_response(False, "Request already pending", status_code=400)

                # Create access request
                try:
                    cursor.execute(
                        "INSERT INTO iot_device_access_requests (device_id, requested_by_user_id) VALUES (%s, %s)",
                        [device_id, user_id],
                    )
                    logger.info("Access request created for user %s to device %s", user_id, device_id)
                    return json_response(True, "Access request sent", device_id=device_id)
                except Exception as e:
                    logger.error("Error creating access request: %s", str(e))
                    return json_response(False, "Unable to create access request", status_code=500)

            # Device doesn't exist, create it
            try:
                cursor.execute(
                    "INSERT INTO iot_devices (device_code, name, user_count) VALUES (%s, %s, %s)",
                    [device_code, f"Device {device_code[-4:]}", 1],
                )
                device_id = cursor.lastrowid
                logger.info("Created new device with ID: %s", device_id)

                # Add user as admin
                cursor.execute(
                    "INSERT INTO iot_user_devices (user_id, device_id, role) VALUES (%s, %s, 'admin')",
                    [user_id, device_id],
                )
                logger.info("Added user %s as admin to device %s", user_id, device_id)
                return json_response(True, "Device created and you are now the admin", device_id=device_id)

            except Exception as e:
                logger.error("Error creating new device: %s", str(e))
                return json_response(False, "Unable to create new device", status_code=500)

    except Exception as e:
        logger.exception("Unexpected error in add_device: %s", str(e))
        return json_response(False, "Unable to process request", status_code=500)
    
def my_devices(request):
    if request.method not in ("GET", "POST"):
        return json_response(False, "GET or POST required", status_code=405)

    data, error = get_json(request, allow_empty=True)
    if error:
        return json_response(False, error, status_code=400)

    user_id = data.get("user_id") if data else None
    if not user_id:
        user_id = request.GET.get("user_id")

    if not user_id:
        return json_response(False, "user_id required", status_code=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT d.id, d.name, d.device_code, ud.role
                FROM iot_devices d
                JOIN iot_user_devices ud ON d.id = ud.device_id
                WHERE ud.user_id=%s
                """,
                [user_id],
            )
            rows = cursor.fetchall()
    except Exception:
        logger.exception("Fetch devices failure for user %s", user_id)
        return json_response(False, "Unable to fetch devices right now", status_code=500)

    devices = [
        {"device_id": row[0], "name": row[1], "device_code": row[2], "role": row[3]}
        for row in rows
    ]
    return json_response(True, "Devices fetched", devices=devices)

@csrf_exempt
def rename_device(request):
    if request.method != "POST":
        return json_response(False, "POST required", status_code=405)

    data, error = get_json(request)
    if error:
        return json_response(False, error, status_code=400)

    missing = require_fields(data, ["device_id", "new_name"])
    if missing:
        return json_response(False, f"Missing required fields: {', '.join(missing)}", status_code=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE iot_devices SET name=%s WHERE id=%s",
                [data["new_name"], data["device_id"]],
            )
            if cursor.rowcount == 0:
                return json_response(False, "Device not found", status_code=404)
    except Exception:
        logger.exception("Rename device failure: %s", data.get("device_id"))
        return json_response(False, "Unable to rename device right now", status_code=500)

    return json_response(True, "Device Renamed")

@csrf_exempt
def change_admin(request):
    if request.method != "POST":
        return json_response(False, "POST required", status_code=405)

    data, error = get_json(request)
    if error:
        return json_response(False, error, status_code=400)

    missing = require_fields(data, ["device_id", "current_admin_user_id", "new_admin_user_id"])
    if missing:
        return json_response(False, f"Missing required fields: {', '.join(missing)}", status_code=400)

    device_id = data["device_id"]
    current_admin_user_id = data["current_admin_user_id"]
    new_admin_user_id = data["new_admin_user_id"]

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM iot_user_devices WHERE user_id=%s AND device_id=%s AND role='admin'",
                [current_admin_user_id, device_id],
            )
            if not cursor.fetchone():
                return json_response(False, "Not authorized", status_code=403)

            cursor.execute("UPDATE iot_user_devices SET role='member' WHERE device_id=%s", [device_id])
            cursor.execute(
                "UPDATE iot_user_devices SET role='admin' WHERE device_id=%s AND user_id=%s",
                [device_id, new_admin_user_id],
            )
            if cursor.rowcount == 0:
                return json_response(False, "New admin user not linked to device", status_code=404)
    except Exception:
        logger.exception(
            "Change admin failure device %s from %s to %s",
            device_id, current_admin_user_id, new_admin_user_id,
        )
        return json_response(False, "Unable to change admin right now", status_code=500)

    return json_response(True, "Admin changed")

@csrf_exempt
def control_device(request):
    if request.method != "POST":
        return json_response(False, "POST required", status_code=405)

    data, error = get_json(request)
    if error:
        return json_response(False, error, status_code=400)

    missing = require_fields(data, ["device_id", "user_id", "command"])
    if missing:
        return json_response(False, f"Missing required fields: {', '.join(missing)}", status_code=400)

    return json_response(True, f"Command acknowledged: {data.get('command')}")

def _is_admin(user_id, device_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM iot_user_devices WHERE user_id=%s AND device_id=%s AND role='admin'",
                [user_id, device_id],
            )
            return cursor.fetchone() is not None
    except Exception:
        logger.exception("Admin check failed for user %s device %s", user_id, device_id)
        return False

def _get_request(request_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, device_id, requested_by_user_id FROM iot_device_access_requests WHERE id=%s",
                [request_id],
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {"request_id": row[0], "device_id": row[1], "user_id": row[2]}
    except Exception:
        logger.exception("Fetch request failed %s", request_id)
        return None

def _device_name(device_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM iot_devices WHERE id=%s", [device_id])
            row = cursor.fetchone()
            return row[0] if row else None
    except Exception:
        logger.exception("Failed to fetch device name %s", device_id)
        return None

def _link_user_to_device(user_id, device_id, role="member"):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM iot_user_devices WHERE user_id=%s AND device_id=%s",
                [user_id, device_id],
            )
            if cursor.fetchone():
                return True
            cursor.execute(
                "INSERT INTO iot_user_devices (user_id, device_id, role) VALUES (%s, %s, %s)",
                [user_id, device_id, role],
            )
            return True
    except Exception:
        logger.exception("Link user failed %s to device %s", user_id, device_id)
        return False

def _delete_request(request_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM iot_device_access_requests WHERE id=%s", [request_id])
            return cursor.rowcount > 0
    except Exception:
        logger.exception("Delete request failed %s", request_id)
        return False

# Updated pending requests fetch: include requester name & phone, avoid requests where user already has access, return unique results
def _pending_requests_for_admin(admin_user_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    r.id, 
                    r.device_id, 
                    COALESCE(d.name, '') as device_name, 
                    r.requested_by_user_id,
                    COALESCE(u.name, '') as user_name,
                    COALESCE(u.phone, '') as user_phone
                FROM iot_device_access_requests r
                JOIN iot_user_devices ud ON ud.device_id = r.device_id 
                    AND ud.role='admin' 
                    AND ud.user_id=%s
                JOIN iot_devices d ON d.id = r.device_id
                JOIN iot_users u ON u.id = r.requested_by_user_id
                WHERE NOT EXISTS (
                    SELECT 1 FROM iot_user_devices ud2 
                    WHERE ud2.device_id = r.device_id 
                    AND ud2.user_id = r.requested_by_user_id
                )
                ORDER BY r.id DESC
                """,
                [admin_user_id],
            )
            return [
                {
                    "request_id": row[0],
                    "device_id": row[1],
                    "device_name": row[2],
                    "user_id": row[3],
                    "name": row[4],  # User's name
                    "phone": row[5],  # User's phone number
                    "phone_number": row[5]  # Backwards compatibility
                }
                for row in cursor.fetchall()
            ]
    except Exception as e:
        logger.exception("Pending requests fetch failed for admin %s: %s", admin_user_id, str(e))
        return []

def device_members(request):
    if request.method != "GET":
        return json_response(False, "GET required", status_code=405)

    device_id = request.GET.get("device_id")
    if not device_id:
        return json_response(False, "device_id required", status_code=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT u.id, COALESCE(u.name, ''), COALESCE(u.phone, ''), ud.role
                FROM iot_users u
                JOIN iot_user_devices ud ON u.id = ud.user_id
                WHERE ud.device_id=%s
                ORDER BY ud.role='admin' DESC, u.id ASC
                """,
                [device_id],
            )
            rows = cursor.fetchall()
    except Exception:
        logger.exception("Failed to fetch members for device %s", device_id)
        return json_response(False, "Unable to fetch device members right now", status_code=500)

    members = [
        {
            "user_id": row[0],
            "name": row[1],
            "phone": row[2],
            "role": row[3],
        }
        for row in rows
    ]

    return json_response(True, "Members fetched", members=members)

def pending_access_requests(request):
    if request.method != "GET":
        return json_response(False, "GET required", status_code=405)

    admin_user_id = request.GET.get("admin_user_id")
    if not admin_user_id:
        return json_response(False, "admin_user_id required", status_code=400)

    try:
        requests_list = _pending_requests_for_admin(admin_user_id)
        return json_response(True, "Pending requests fetched", requests=requests_list)
    except Exception as e:
        logger.exception("Error in pending_access_requests: %s", str(e))
        return json_response(False, "Unable to fetch pending requests", status_code=500)

@csrf_exempt
def approve_access(request):
    if request.method != "POST":
        return json_response(False, "POST required", status_code=405)

    data, error = get_json(request)
    if error:
        return json_response(False, error, status_code=400)

    missing = require_fields(data, ["request_id", "admin_user_id"])
    if missing:
        return json_response(False, f"Missing required fields: {', '.join(missing)}", status_code=400)

    req = _get_request(data["request_id"])
    if not req:
        return json_response(False, "Request not found", status_code=404)

    if not _is_admin(data["admin_user_id"], req["device_id"]):
        return json_response(False, "Not authorized", status_code=403)

    # Prevent approving if user already has access (race condition safe-guard)
    if _has_device_access(req["user_id"], req["device_id"]):
        # Delete the request to clean up and inform admin
        _delete_request(req["request_id"])
        return json_response(False, "User already has access — request removed", status_code=400)

    if not _link_user_to_device(req["user_id"], req["device_id"], role="member"):
        return json_response(False, "Unable to approve access right now", status_code=500)

    _delete_request(req["request_id"])
    return json_response(True, "Access approved")

@csrf_exempt
def reject_access(request):
    if request.method != "POST":
        return json_response(False, "POST required", status_code=405)

    data, error = get_json(request)
    if error:
        return json_response(False, error, status_code=400)

    missing = require_fields(data, ["request_id", "admin_user_id"])
    if missing:
        return json_response(False, f"Missing required fields: {', '.join(missing)}", status_code=400)

    req = _get_request(data["request_id"])
    if not req:
        return json_response(False, "Request not found", status_code=404)

    if not _is_admin(data["admin_user_id"], req["device_id"]):
        return json_response(False, "Not authorized", status_code=403)

    if not _delete_request(req["request_id"]):
        return json_response(False, "Unable to reject request right now", status_code=500)

    return json_response(True, "Request rejected")

@csrf_exempt
def remove_access(request):
    if request.method != "POST":
        return json_response(False, "POST required", status_code=405)

    data, error = get_json(request)
    if error:
        return json_response(False, error, status_code=400)

    missing = require_fields(data, ["device_id", "user_id", "admin_user_id"])
    if missing:
        return json_response(False, f"Missing required fields: {', '.join(missing)}", status_code=400)

    device_id = data["device_id"]
    target_user_id = data["user_id"]
    admin_user_id = data["admin_user_id"]

    if not _is_admin(admin_user_id, device_id):
        return json_response(False, "Not authorized", status_code=403)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM iot_user_devices WHERE device_id=%s AND user_id=%s AND role!='admin'",
                [device_id, target_user_id],
            )
            if cursor.rowcount == 0:
                return json_response(False, "Access not found or cannot remove admin", status_code=404)
    except Exception:
        logger.exception("Remove access failure user %s device %s", target_user_id, device_id)
        return json_response(False, "Unable to remove access right now", status_code=500)

    return json_response(True, "Access removed")

@csrf_exempt
def get_popup(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT message, button_name, button_url
                FROM iot_popup
                WHERE is_active = 1
                ORDER BY id DESC
                LIMIT 1
            """)
            row = cursor.fetchone()

        if row:
            return JsonResponse({
                "show": True,
                "message": row[0],
                "button_name": row[1],
                "button_url": row[2],
            }, status=200)

        # No active popup
        return JsonResponse({"show": False}, status=200)

    except Exception as e:
        logger.exception("Get popup failed: %s", str(e))
        return JsonResponse({
            "show": False,
            "error": str(e)
        }, status=500)

# ================================================================
#                 RESEND OTP - SIGNUP
# ================================================================
@csrf_exempt
def resend_signup_otp(request):

    if request.method != "POST":
        return json_response(False, "POST required", status_code=405)

    data, error = get_json(request)
    if error:
        return json_response(False, error, status_code=400)

    user_id = data.get("user_id")

    if not user_id:
        return json_response(False, "user_id required", status_code=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT phone FROM iot_pending_users WHERE id=%s",
                [user_id]
            )
            row = cursor.fetchone()

            if not row:
                return json_response(False, "Pending user not found", status_code=404)

            phone = row[0]

            # Generate new OTP
            otp = generate_otp()
            expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

            cursor.execute(
                "INSERT INTO iot_otps (phone, otp, purpose, expires_at) VALUES (%s, %s, 'signup', %s)",
                [phone, otp, expires_at]
            )

        # Send OTP
        send_result = send_whatsapp_otp(phone, otp)
        return json_response(True, "OTP resent successfully")

    except Exception as e:
        logger.exception("Resend signup OTP failed: %s", str(e))
        return json_response(False, "Could not resend OTP", status_code=500)


# ================================================================
#                 RESEND OTP - FORGOT PASSWORD
# ================================================================
@csrf_exempt
def resend_forgot_otp(request):

    if request.method != "POST":
        return json_response(False, "POST required", status_code=405)

    data, error = get_json(request)
    if error:
        return json_response(False, error, status_code=400)

    user_id = data.get("user_id")

    if not user_id:
        return json_response(False, "user_id required", status_code=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT phone FROM iot_users WHERE id=%s", [user_id])
            row = cursor.fetchone()

            if not row:
                return json_response(False, "User not found", status_code=404)

            phone = row[0]

            # Generate new OTP
            otp = generate_otp()
            expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

            cursor.execute(
                "INSERT INTO iot_otps (phone, otp, purpose, expires_at) VALUES (%s, %s, 'forgot', %s)",
                [phone, otp, expires_at]
            )

        # Send OTP
        send_result = send_whatsapp_otp(phone, otp)

        return json_response(True, "OTP resent successfully")

    except Exception as e:
        logger.exception("Resend forgot OTP failed: %s", str(e))
        return json_response(False, "Some error occurred", status_code=500)
