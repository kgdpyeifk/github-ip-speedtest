import requests
import time
import subprocess
from statistics import mean

TARGET_URL = "https://zip.cm.edu.kg/all.txt"
KEYWORDS = ["SG", "HK", "US"]
OUTPUT_FILE = "top10.txt"

def fetch_ip_list():
    response = requests.get(TARGET_URL)
    response.raise_for_status()
    lines = response.text.strip().split('\n')
    return [line.strip() for line in lines if any(k in line for k in KEYWORDS)]

def extract_info(ip_line):
    ip_port, label = ip_line.split("#")
    ip, port = ip_port.split(":")
    return ip, port, label

def ping_delay(ip):
    try:
        output = subprocess.check_output(["ping", "-c", "3", "-q", ip], stderr=subprocess.DEVNULL)
        line = output.decode().split('\n')[-3]
        avg_time = float(line.split("/")[4])
        return avg_time
    except:
        return float('inf')

def speed_test(ip, port):
    try:
        start = time.time()
        s = subprocess.run(["curl", f"https://{ip}:{port}", "--max-time", "3", "--insecure", "-o", "/dev/null"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return time.time() - start if s.returncode == 0 else float('inf')
    except:
        return float('inf')

def main():
    ip_lines = fetch_ip_list()
    categorized = {k: [] for k in KEYWORDS}

    for line in ip_lines:
        for key in KEYWORDS:
            if key in line:
                categorized[key].append(line)
                break

    final_results = []

    for key in KEYWORDS:
        tested = [(line, ping_delay(extract_info(line)[0])) for line in categorized[key]]
        top20 = sorted(tested, key=lambda x: x[1])[:20]

        speed_tested = [(line, speed_test(*extract_info(line)[:2])) for line, _ in top20]
        top10 = sorted(speed_tested, key=lambda x: x[1])[:10]

        final_results.extend([line for line, _ in top10])

    with open(OUTPUT_FILE, "w") as f:
        for line in final_results:
            f.write(line + "\n")

if __name__ == "__main__":
    main()
