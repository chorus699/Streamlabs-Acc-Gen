import json
import tls_client
import time
import requests
from kopeechka import tempmail
from console import Console
from urllib.parse import unquote
import re
from bs4 import BeautifulSoup
import concurrent.futures
import random
import threading

api_host = "http://127.0.0.1:5000"


def twocaptchasolver():
    max_attempts = 50
    for attempt in range(max_attempts):
        try:
            if attempt > 0: console.info(f"Retrying in 1 minute... (Attempt {attempt}/{max_attempts})"); time.sleep(3)
            params = {"url": "https://streamlabs.com/slid/signup", "sitekey": "0x4AAAAAAACELUBpqiwktdQ9"}
            response = requests.get(f"{api_host}/turnstile", params=params, timeout=120)
            if response.status_code == 200:
                result = response.json()
                if result["status"] == "success": return result["result"]
                else: console.error(f"Turnstile-Solver failed: {result.get('error')}")
            else: console.error(f"Error from Turnstile-Solver: HTTP {response.status_code}")
        except requests.RequestException as e: console.error(f"Network error occurred: {str(e)}")
        except Exception as e: console.error(f"An unexpected error occurred: {str(e)}")
    console.error("Max attempts reached. Could not solve captcha.")
    return None

console = Console()
with open('config.json', 'r') as config_file:
    config = json.load(config_file)
    license_key = config.get("license")


def get_proxy():
    proxy = random.choice(proxies)
    if not proxy.startswith("http"):
        proxy = f"http://{proxy}"  # Use HTTP instead of HTTPS
    return proxy

def creator():
    proxy = get_proxy()
    ses = tls_client.Session(
            client_identifier="chrome_131", random_tls_extension_order=True
        )
    ses.proxies = {"http": proxy, "https": proxy}
    captcha_token = twocaptchasolver()
    email, email_id = tempmail.create_temp_email()

    headers = {
                "accept": "application/json, text/plain, */*",
                "accept-language": "en-US,en;q=0.9",
                "priority": "u=1, i",
                "referer": "https://streamlabs.com/slid/signup",
                "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            }
    ses.get('https://streamlabs.com/api/v5/available-features', headers=headers)
    xsrf = ses.cookies.get('XSRF-TOKEN')

    if not xsrf:
        return

    ses.headers.update({
        'accept': 'application/json, text/plain, */*',
        'cache-control': 'no-cache',
        'client-id': '419049641753968640',
        'content-type': 'application/json',
        'origin': 'https://streamlabs.com',
        'referer': 'https://streamlabs.com/',
        'x-xsrf-token': xsrf,
    })

    json_data = {
        'email': email,
        'username': '',
        'password': 'Jignewah382ry83#',
        'agree': True,
        'agreePromotional': False,
        'dob': '',
        'captcha_token': captcha_token,
        'locale': 'en-US',
    }

    response = ses.post('https://api-id.streamlabs.com/v1/auth/register', json=json_data)
    console.success(f"Created {email}")
    time.sleep(1)
    if response.status_code != 200:
        return

    otp_verified = False
    try:
        otp = tempmail.get_email_code(email_id)
        if otp:
            otp_verified = verifier(xsrf, otp, email, ses)
            if otp_verified:
                console.info(f"Verified -> {email}")
    except Exception:
        return

def verifier(xsrf, otp, email, ses):
    url = "https://api-id.streamlabs.com/v1/users/@me/email/verification/confirm"
    payload = {
        "code": otp,
        "email": email,
        "tfa_code": ""
    }
    ses.headers.update(
        {
            "x-xsrf-token": xsrf,
        }
    )

    response = ses.post(url, json=payload)
    if response.status_code == 204:
        with open("accs.txt",'a')as f:
            f.write(f"{email}:Jignewah382ry83#\n")
        return True
    else:
        console.error("Verification Failed:", response.text)
        return False


def loop_creator():
    while True:
        creator()

threads = []
thread_count = config.get("num_threads", 3)
for i in range(thread_count):  
    thread = threading.Thread(target=loop_creator, name=f"Thread-{i+1}", daemon=True)
    threads.append(thread)
    thread.start()

try:
    while True:
        time.sleep(1)  
except KeyboardInterrupt:
    print("Exiting program.")
