import requests
import json

def test_register():
    url = "https://vercel-i3ciim1ws-shining-johcis-projects.vercel.app/auth/register"
    data = {
        "username": "testuser1",
        "password": "testpass123"
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("Sending registration request...")
        response = requests.post(url, json=data, headers=headers)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_register() 