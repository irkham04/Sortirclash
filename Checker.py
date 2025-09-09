import subprocess
from pathlib import Path
import requests
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import socket
import time
import os

SERVERS_FILE = "servers.txt"
OUTPUT_FILE = Path("results/hasil.txt")
OUTPUT_FILE.parent.mkdir(exist_ok=True)
MAX_THREADS = 20
RETRY_CONN = 3
RETRY_PING = 3
RETRY_IP = 2
TIMEOUT_CONN = 20
CORE_PATH = "./cores/mihomo"  # gunakan MiHoYo Core

def fetch_servers_from_url(url):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        content = resp.text.strip()
        try:
            decoded = base64.b64decode(content).decode('utf-8')
            return [line.strip() for line in decoded.splitlines() if line.strip()]
        except:
            return [line.strip() for line in content.splitlines() if line.strip()]
    except Exception as e:
        print(f"❌ Gagal fetch {url}: {e}")
        return []

def get_host_port(server):
    pattern = r'^(?:vmess|vless|trojan|ss)://([^@:]+)'
    match = re.match(pattern, server)
    if match:
        return match.group(1)
    return None

def get_country(ip):
    for _ in range(RETRY_IP):
        try:
            r = requests.get(f"https://ipinfo.io/{ip}/json", timeout=5)
            data = r.json()
            return data.get("country", "Unknown")
        except:
            time.sleep(1)
    return "Unknown"

def average_ping(ip):
    delays = []
    for _ in range(RETRY_PING):
        try:
            ping_proc = subprocess.run(["ping", "-c", "1", ip], capture_output=True, text=True, timeout=5)
            match = re.search(r'time=(\d+\.\d+) ms', ping_proc.stdout)
            if match:
                delays.append(float(match.group(1)))
        except:
            continue
        time.sleep(0.2)
    return f"{sum(delays)/len(delays):.1f} ms" if delays else "N/A"

def test_server(server):
    for attempt in range(RETRY_CONN):
        try:
            cmd = [CORE_PATH, "-d", ".", "--try-test", server]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_CONN)

            if proc.returncode == 0:
                host = get_host_port(server)
                ping_ms = "N/A"
                country = "N/A"
                if host:
                    try:
                        ip = socket.gethostbyname(host)
                        ping_ms = average_ping(ip)
                        country = get_country(ip)
                    except:
                        pass
                return f"{server} | OK ✅ | {ping_ms} | {country}"
        except Exception:
            continue
    return None  # gagal semua percobaan

# Ambil semua server dari sub-url
servers = []
with open(SERVERS_FILE, "r") as f:
    urls = [line.strip() for line in f if line.strip()]
    for url in urls:
        servers.extend(fetch_servers_from_url(url))

print(f"Total server didapat: {len(servers)}")

results = []

with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
    future_to_server = {executor.submit(test_server, server): server for server in servers}
    for future in as_completed(future_to_server):
        res = future.result()
        if res:
            print(res)
            results.append(res)

with open(OUTPUT_FILE, "w") as f:
    f.write("\n".join(results))

print(f"✅ Testing selesai, {len(results)} server aktif, cek di results/hasil.txt")
