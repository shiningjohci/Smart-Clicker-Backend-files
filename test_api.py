import requests
import json
import sys
from datetime import datetime

# Set up logging to file
log_file = "api_test_log.txt"
def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(message)  # Also print to console

log("Script starting...")

BASE_URL = "https://vercel-i3ciim1ws-shining-johcis-projects.vercel.app"

# Test basic connectivity first
log(f"\nTesting connection to {BASE_URL}")
try:
    response = requests.get(BASE_URL)
    log(f"Connection test response code: {response.status_code}")
    log(f"Connection test response: {response.text}")
except Exception as e:
    log(f"Connection test failed: {str(e)}")
    sys.exit(1)

def test_register():
    log("\nTesting Registration...")
    url = f"{BASE_URL}/auth/register"
    data = {
        "username": "testuser",
        "password": "testpass123"
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    log(f"Sending POST request to {url}")
    log(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, headers=headers)
        log(f"\nStatus Code: {response.status_code}")
        log(f"Response Headers: {dict(response.headers)}")
        log(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            log("\nRegistration successful!")
            return response_data.get('token')
        else:
            log(f"\nRegistration failed with status code: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        log(f"\nNetwork error during registration: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        log(f"\nError parsing response JSON: {str(e)}")
        log(f"Raw response: {response.text}")
        return None
    except Exception as e:
        log(f"\nUnexpected error during registration: {str(e)}")
        return None

def test_login():
    log("\nTesting Login...")
    url = f"{BASE_URL}/auth/login"
    data = {
        "username": "testuser",
        "password": "testpass123"
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    log(f"Sending POST request to {url}")
    log(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, headers=headers)
        log(f"\nStatus Code: {response.status_code}")
        log(f"Response Headers: {dict(response.headers)}")
        log(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            log("\nLogin successful!")
            return response_data.get('token')
        else:
            log(f"\nLogin failed with status code: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        log(f"\nNetwork error during login: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        log(f"\nError parsing response JSON: {str(e)}")
        log(f"Raw response: {response.text}")
        return None
    except Exception as e:
        log(f"\nUnexpected error during login: {str(e)}")
        return None

def test_check_vip(token):
    log("\nTesting VIP Status Check...")
    url = f"{BASE_URL}/auth/check-vip"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    log(f"Sending GET request to {url}")
    log(f"Headers: {json.dumps(headers, indent=2)}")
    
    try:
        response = requests.get(url, headers=headers)
        log(f"\nStatus Code: {response.status_code}")
        log(f"Response Headers: {dict(response.headers)}")
        log(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            log("\nVIP status check successful!")
        else:
            log(f"\nVIP status check failed with status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        log(f"\nNetwork error checking VIP status: {str(e)}")
    except json.JSONDecodeError as e:
        log(f"\nError parsing response JSON: {str(e)}")
        log(f"Raw response: {response.text}")
    except Exception as e:
        log(f"\nUnexpected error checking VIP status: {str(e)}")

def test_add_vip(username):
    log("\nTesting Add VIP Status...")
    url = f"{BASE_URL}/auth/add-vip/{username}"
    headers = {
        "Content-Type": "application/json"
    }
    
    log(f"Sending POST request to {url}")
    log(f"Headers: {json.dumps(headers, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers)
        log(f"\nStatus Code: {response.status_code}")
        log(f"Response Headers: {dict(response.headers)}")
        log(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            log("\nVIP status added successfully!")
        else:
            log(f"\nFailed to add VIP status with status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        log(f"\nNetwork error adding VIP status: {str(e)}")
    except json.JSONDecodeError as e:
        log(f"\nError parsing response JSON: {str(e)}")
        log(f"Raw response: {response.text}")
    except Exception as e:
        log(f"\nUnexpected error adding VIP status: {str(e)}")

if __name__ == "__main__":
    log("Starting API Tests...")
    log(f"Base URL: {BASE_URL}")
    
    try:
        # Test registration
        token = test_register()
        
        if token:
            # Test login
            login_token = test_login()
            
            # Test VIP check
            if login_token:
                test_check_vip(login_token)
                
                # Test adding VIP status
                test_add_vip("testuser")
                
                # Check VIP status again
                test_check_vip(login_token)
        
        log("\nAPI Tests completed.")
    except Exception as e:
        log(f"\nFatal error during testing: {str(e)}")
        sys.exit(1) 