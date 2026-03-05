import requests
import base64
from datetime import datetime
import os

# Load credentials from environment
CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
SHORTCODE = os.getenv("MPESA_SHORTCODE", "174379")
PASSKEY = os.getenv("MPESA_PASSKEY")
BASE_URL = "https://sandbox.safaricom.co.ke"


def get_access_token():
    url = f"{BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(CONSUMER_KEY.strip(), CONSUMER_SECRET.strip()))
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception(f"Failed to get access token: {response.text}")


def generate_password():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    data_to_encode = SHORTCODE + PASSKEY + timestamp
    password = base64.b64encode(data_to_encode.encode()).decode()
    return password, timestamp


def send_stk_push(phone: str, amount: int = 1, callback_url: str = ""):
    # Normalize phone to 254 format
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif phone.startswith("+254"):
        phone = phone[1:]

    access_token = get_access_token()
    password, timestamp = generate_password()

    url = f"{BASE_URL}/mpesa/stkpush/v1/processrequest"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "BusinessShortCode": SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": "Subscription",
        "TransactionDesc": "Subscription Payment"
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()