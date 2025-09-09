# sorter_vpn.py
import requests
import concurrent.futures
import socket

# File berisi daftar sub URL
SUB_URL_FILE = "sub_urls.txt"
OUTPUT_FILE = "akun_aktif.txt"
TIMEOUT = 5  # detik untuk test koneksi

def fetch_accounts(url):
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        accounts = [line.strip() for line in resp.text.splitlines() if line.strip()]
        return [(account, url) for account in accounts]  # simpan asal URL
    except Exception as e:
        print(f"[!] Gagal fetch {url}: {e}")
        return []

def test_connect(account):
    """
    Cek koneksi sederhana.
    Kita coba parse host:port dari akun.
    """
    try:
        if account.startswith("vless://") or account.startswith("vmess://") or account.startswith("trojan://"):
            # Contoh parsing sederhana: ambil host:port setelah '@'
            body = account.split('@')[-1]
            host_port = body.split('?')[0]
            host, port = host_port.split(':')
            port = int(port)
        elif account.startswith("ss://"):
            body = account[5:]
            if '@' in body:
                host_port = body.split('@')[1]
            else:
                host_port = body.split('#')[0]
            host, port = host_port.split(':')
            port = int(port)
        else:
            return False

        # test koneksi
        with socket.create_connection((host, port), timeout=TIMEOUT):
            return True
    except Exception:
        return False

def main():
    # baca daftar sub URL
    with open(SUB_URL_FILE, "r") as f:
        sub_urls = [line.strip() for line in f if line.strip()]

    # ambil semua akun dari sub URL
    all_accounts = []
    for url in sub_urls:
        all_accounts.extend(fetch_accounts(url))

    print(f"[+] Total akun ditemukan: {len(all_accounts)}")

    # cek koneksi akun aktif
    aktif_accounts = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_account = {executor.submit(test_connect, acc): (acc, src) for acc, src in all_accounts}
        for future in concurrent.futures.as_completed(future_to_account):
            acc, src = future_to_account[future]
            try:
                if future.result():
                    aktif_accounts.append(acc)
                    print(f"[OK] {acc}")
            except Exception as e:
                print(f"[FAIL] {acc}: {e}")

# Simpan akun aktif
with open(OUTPUT_FILE, "w") as f:
    for acc in aktif_accounts:
        f.write(acc + "\n")
print(f"[+] Akun aktif tersimpan di {OUTPUT_FILE}: {len(aktif_accounts)} akun")

    print(f"[+] Akun aktif tersimpan di {OUTPUT_FILE}: {len(aktif_accounts)} akun")

if __name__ == "__main__":
    main()
