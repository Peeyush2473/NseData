from flask import Flask, request, jsonify
import random
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
    # Multiple URL patterns to try
    urls = [
        f"https://archives.nseindia.com/content/nsccl/fao_participant_oi_{date_str}.csv",
        f"https://www1.nseindia.com/content/nsccl/fao_participant_oi_{date_str}.csv",
        f"https://www.nseindia.com/content/nsccl/fao_participant_oi_{date_str}.csv"
    ]
    
    # Rotate through different user agents
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
    ]
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0"
    }

    session = requests.Session()
    
    for attempt, url in enumerate(urls):
        try:
            print(f"Attempt {attempt + 1}: Trying URL: {url}")
            
            # First, visit the main NSE website to get cookies
            print("Getting initial cookies from NSE website...")
            init_resp = session.get("https://www.nseindia.com", headers=headers, timeout=15)
            print(f"Initial response status: {init_resp.status_code}")
            
            # Add some delay and additional headers
            time.sleep(random.uniform(2, 4))
            
            # Update headers with referer
            headers["Referer"] = "https://www.nseindia.com/"
            
            # Try to get the CSV data
            print(f"Fetching CSV data from: {url}")
            response = session.get(url, headers=headers, timeout=30)
            print(f"CSV response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                print(f"Content-Type: {content_type}")
                
                if 'text/csv' in content_type or 'application/csv' in content_type or len(response.content) > 100:
                    try:
                        decoded = response.content.decode("utf-8").splitlines()
                        reader = csv.reader(decoded)
                        data = list(reader)
                        print(f"Successfully parsed {len(data)} rows")
                        return data
                    except UnicodeDecodeError:
                        print("UTF-8 decode failed, trying latin-1...")
                        decoded = response.content.decode("latin-1").splitlines()
                        reader = csv.reader(decoded)
                        data = list(reader)
                        print(f"Successfully parsed {len(data)} rows with latin-1")
                        return data
                else:
                    print(f"Unexpected content type or size: {len(response.content)} bytes")
                    print(f"First 500 chars: {response.text[:500]}")
            else:
                print(f"HTTP Error {response.status_code}: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"Timeout error for URL: {url}")
        except requests.exceptions.ConnectionError:
            print(f"Connection error for URL: {url}")
        except requests.exceptions.RequestException as e:
            print(f"Request exception for URL {url}: {e}")
        except Exception as e:
            print(f"Unexpected error for URL {url}: {e}")
        
        # Wait before trying next URL
        if attempt < len(urls) - 1:
            time.sleep(random.uniform(1, 3))
    
    print("All attempts failed")
    return None

@app.route('/nse', methods=['GET'])
def nse_data():
    date = request.args.get('date')
    if not date:
        return jsonify({"error": "Date parameter is required (DDMMYYYY)"}), 400
    
    # Validate date format
    if len(date) != 8 or not date.isdigit():
        return jsonify({"error": "Date should be in DDMMYYYY format (8 digits)"}), 400

    print(f"Fetching NSE data for date: {date}")
    data = get_nse_data(date)
    
    if not data:
        return jsonify({
            "error": "Failed to fetch data",
            "details": "Check server logs for more information",
            "date": date,
            "suggestion": "Try a different date or check if the date exists in NSE archives"
        }), 500

    return jsonify({
        "date": date,
        "rows": len(data),
        "data": data
    })

@app.route('/test-connection')
def test_connection():
    """Test basic connectivity to NSE website"""
    try:
        response = requests.get("https://www.nseindia.com", timeout=10)
        return jsonify({
            "status": "success",
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content_length": len(response.content)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "service": "NSE API"})

# No need for app.run() here as Gunicorn will handle starting the app.
# If you keep it, ensure it's only run when the script is executed directly
# if __name__ == '__main__':
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host='0.0.0.0', port=port)