import requests
import sys
from datetime import datetime

# 设置输出到文件
output_file = "simple_test_output.txt"

def write_log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(message)

write_log("Starting simple test...")

url = "https://vercel-i3ciim1ws-shining-johcis-projects.vercel.app"
write_log(f"Testing URL: {url}")

try:
    response = requests.get(url)
    write_log(f"Status code: {response.status_code}")
    write_log(f"Response text: {response.text}")
except Exception as e:
    write_log(f"Error: {str(e)}")
    sys.exit(1) 