from flask import Flask, request, jsonify
import requests
import csv
import time
import os

print("PORT:", os.environ.get("PORT")) # This will print the port Railway assigns

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to NSE API! Use /nse?date=DDMMYYYY"

def get_nse_data(date_str):
    url = f"https://archives.nseindia.com/content/nsccl/fao_participant_oi_{date_str}.csv"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.nseindia.com/",
        "Connection": "keep-alive"
    }

    try:
        session = requests.Session()
        # Initial request to get cookies
        init_resp = session.get("https://www.nseindia.com", headers=headers, timeout=10)
        init_resp.raise_for_status()
        time.sleep(1)

        response = session.get(url, headers=headers)
        response.raise_for_status()

        decoded = response.content.decode("utf-8").splitlines()
        reader = csv.reader(decoded)
        return list(reader)
    except Exception as e:
        print(f"Exception fetching NSE data: {e}")
        return None


@app.route('/nse', methods=['GET'])
def nse_data():
    date = request.args.get('date')  # format should be DDMMYYYY
    if not date:
        return jsonify({"error": "Date parameter is required (DDMMYYYY)"}), 400

    data = get_nse_data(date)
    if not data:
        return jsonify({"error": "Failed to fetch data"}), 500

    return jsonify(data)

# No need for app.run() here as Gunicorn will handle starting the app.
# If you keep it, ensure it's only run when the script is executed directly
# if __name__ == '__main__':
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host='0.0.0.0', port=port)