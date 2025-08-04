import requests
import subprocess
import time
import concurrent.futures

# 显示标签
label_map = {
    "SG": "🇸🇬SG-新加坡",
    "HK": "🇭🇰HK-香港",
    "US": "🇺🇸US-美国"
}

# 下载并提取 IP
def fetch_ips():
    url = "https://zip.cm.edu.kg/all.txt"
    resp = requests.get(url)
    raw_lines = resp.text.strip().splitlines()
    regions = {"SG": [], "HK": [], "US": []}
    for line in raw_lines:
        for tag in regions:
            if f"#{tag}" in line:
                ip_port = line.split("#")[0]
                ip, port = ip_port.split(":")
                regions[tag].append((ip.strip(), port.strip()))
    return regions

# 测试 Ping 延迟
def ping_ip(ip):
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            capture_output=True,
            text=True,
            timeout=3
        )
        for line in result.stdout.splitlines():
            if "time=" in line:
                latency = float(line.split("time=")[-1].split(" ")[0])
                return latency
    except:
        pass
    return float("inf")

# 对每组 IP 进行延迟排序
def filter_by_latency(region_ips, top_n=20):
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ip = {executor.submit(ping_ip, ip): (ip, port) for ip, port in region_ips}
        for future in concurrent.futures.as_completed(future_to_ip):
            ip, port = future_to_ip[future]
            latency = future.result()
            if latency < float("inf"):
                results.append((ip, port, latency))

    results.sort(key=lambda x: x[2])
    return results[:top_n]

# 使用 curl 测速（每个测试 1 次）
def speed_test(ip, port):
    test_url = f"http://{ip}:{port}"
    try:
        result = subprocess.run(
            ["curl", "-m", "5", "-o", "/dev/null", "-s", "-w", "%{speed_download}", test_url],
            capture_output=True,
            text=True,
            timeout=7
        )
        speed = float(result.stdout.strip())
        return speed
    except:
        return 0.0

# 对每组低延迟 IP 进行测速
def filter_by_speed(region_ips, top_n=10):
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_ip = {executor.submit(speed_test, ip, port): (ip, port) for ip, port, _ in region_ips}
        for future in concurrent.futures.as_completed(future_to_ip):
            ip, port = future_to_ip[future]
            speed = future.result()
            if speed > 0:
                results.append((ip, port, speed))

    results.sort(key=lambda x: x[2], reverse=True)
    return results[:top_n]

# 主流程
def main():
    print("正在获取 IP 列表...")
    region_data = fetch_ips()

    final_results = []

    for region in ["SG", "HK", "US"]:
        print(f"开始处理 {region} ...")
        ip_list = region_data[region]
        top_latency = filter_by_latency(ip_list, top_n=20)
        top_speed = filter_by_speed(top_latency, top_n=10)

        for ip, port, _ in top_speed:
            label = label_map.get(region, region)
            final_results.append(f"{ip}:{port}#{label}")

    # 写入文件
    with open("top10.txt", "w") as f:
        for line in final_results:
            f.write(line + "\n")

    print("处理完成，已生成 top10.txt")

if __name__ == "__main__":
    main()
