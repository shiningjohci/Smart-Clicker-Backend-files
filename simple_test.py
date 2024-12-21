import requests

print("Starting simple test...")

url = "https://vercel-i3ciim1ws-shining-johcis-projects.vercel.app"
print(f"Testing URL: {url}")

try:
    response = requests.get(url)
    print(f"Status code: {response.status_code}")
    print(f"Response text: {response.text}")
except Exception as e:
    print(f"Error: {str(e)}") 