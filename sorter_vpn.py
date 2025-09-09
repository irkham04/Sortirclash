# sorter_vpn.py
import requests
import concurrent.futures
import socket
import base64
import json
import os

SUB_URL_FILE = "sub_urls.txt"
OUTPUT_FILE = os.path.join(os.getcwd(), "akun_aktif.txt")  # pastikan di root repo
TIMEOUT = 15
MAX_THREADS = 20

def fetch_accounts(url):
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        lines = [line.strip() for line in resp.text.splitlines() if line.strip()]
        accounts = []
        for line in lines:
            # Decode VMess base64 jika perlu
            if line.startswith("vmess://"):
                try:
                    decoded = base64.b64decode(line[8:]).decode()
                    accounts.append((decoded, url))
                except Exception:
                    accounts.append((line, url))
            else:
                accounts.append((line, url))
        return accounts
    except Exception as e:
        print(f"[!] Gagal fetch {url}: {e}")
        return []

def parse_host_port(account):
    try:
        if account.startswith("vless://") or account.startswith("trojan://"):
            body = account.split('@')[-1]
            host_port = body.split('?')[0]
            host, port = host_port.split(':')
            return host, int(port)
        elif account.startswith("vmess://") or account.startswith("{"):
            data = json.loads(account)
            return data.get("add"), int(data.get("port"))
        elif account.startswith("ss://"):
            body = account[5:]
            if '@' in body:
                host_port = body.split('@')[1].split('#')[0]
                host, port = host_port.split(':')
                return host, int(port)
        return None, None
    except Exception as e:
        print(f"[DEBUG] Parsing gagal: {account[:50]}..., error: {e}")
        return None, None

def test_connect(account):
    host, port = parse_host_port(account)
    if not host or not port:
        return False
    try:
        with socket.create_connection((host, port), timeout=TIMEOUT):
            return True
    except Exception:
        return False

def main():
    if not os.path.exists(SUB_URL_FILE):
        print(f"[!] File {SUB_URL_FILE} tidak ditemukan")
        return

    with open(SUB_URL_FILE, "r") as f:
        sub_urls = [line.strip() for line in f if line.strip()]

    all_accounts = []
    for url in sub_urls:
        accounts = fetch_accounts(url)
        print(f"[DEBUG] {len(accounts)} akun diambil dari {url}")
        all_accounts.extend(accounts)

    print(f"[+] Total akun ditemukan: {len(all_accounts)}")

    aktif_accounts = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_to_account = {executor.submit(test_connect, acc): (acc, src) for acc, src in all_accounts}
        for future in concurrent.futures.as_completed(future_to_account):
            acc, src = future_to_account[future]
            try:
                if future.result():
                    aktif_accounts.append(f"{acc} # dari {src}")
                    print(f"[OK] {acc[:50]}...")
                else:
                    print(f"[FAIL] {acc[:50]}...")
            except Exception as e:
                print(f"[EXCEPT] {acc[:50]}: {e}")

    # Simpan file selalu ada
    with open(OUTPUT_FILE, "w") as f:
        for acc in aktif_accounts:
            f.write(acc + "\n")

    print(f"[+] Akun aktif tersimpan di {OUTPUT_FILE}: {len(aktif_accounts)} akun")
    print(f"[DEBUG] File ada: {os.path.exists(OUTPUT_FILE)}")

if __name__ == "__main__":
    main()
