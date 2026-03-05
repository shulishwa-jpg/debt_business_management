import requests

CONSUMER_KEY = "uGRBrWWE2yz4TpYEjlV2vBZmrADDQnrMij2wv0pPNUuJJTDE"
CONSUMER_SECRET = "aKVenunzRfNpZuHIGW80xh7riAHqYMgBfAxs5TRGG2Q7TWZjrQ8unKZliIV9VyWC"

url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

response = requests.get(url, auth=(CONSUMER_KEY, CONSUMER_SECRET))

print("STATUS:", response.status_code)
print("BODY:", response.text)
