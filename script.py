import requests
import time
import subprocess
import concurrent.futures

TARGET_URL = "https://zip.cm.edu.kg/all.txt"
KEYWORDS = ["SG", "HK", "US"]
OUTPUT_FILE = "top10.txt"
PING_TIMEOUT = 1
CURL_TIMEOUT = 1
MAX_IP_PER_REGION = 50
THREADS = 20

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
        output = subprocess.check_output(["ping", "-c", "1", "-W", str(PING_TIMEOUT), ip], stderr=subprocess.DEVNULL)
        line = output.decode().split('\n')[-3]
        avg_time = float(line.split("/")[4])
        return avg_time
    except:
        return float('inf')

def speed_test(ip, port):
    try:
        start = time.time()
        s = subprocess.run(["curl", f"https://{ip}:{port}", "--max-time", str(CURL_TIMEOUT), "--insecure", "-o", "/dev/null"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return time.time() - start if s.returncode == 0 else float('inf')
    except:
        return float('inf')

def threaded_test(fn, inputs):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
        future_to_ip = {executor.submit(fn, *args): args[0] for args in inputs}
        for future in concurrent.futures.as_completed(future_to_ip):
            ip = future_to_ip[future]
            try:
                result = future.result()
                results.append((ip, result))
            except:
                results.append((ip, float('inf')))
    return results

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
        selected = categorized[key][:MAX_IP_PER_REGION]
        ip_infos = [extract_info(line) for line in selected]
        ping_results = threaded_test(lambda ip, *_: ping_delay(ip), [(ip, port) for ip, port, _ in ip_infos])
        ip_latency_map = {ip: latency for ip, latency in ping_results}

        top20_lines = sorted(
            selected,
            key=lambda line: ip_latency_map.get(extract_info(line)[0], float('inf'))
        )[:20]

        top20_infos = [extract_info(line) for line in top20_lines]
        speed_results = threaded_test(lambda ip, port: speed_test(ip, port), [(ip, port) for ip, port, _ in top20_infos])
        ip_speed_map = {ip: speed for ip, speed in speed_results}

        top10_lines = sorted(
            top20_lines,
            key=lambda line: ip_speed_map.get(extract_info(line)[0], float('inf'))
        )[:10]

        final_results.extend(top10_lines)

    with open(OUTPUT_FILE, "w") as f:
        for line in final_results:
            f.write(line + "\n")

if __name__ == "__main__":
    main()
