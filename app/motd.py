import platform
import os
import shutil
import datetime
import multiprocessing
import getpass
import socket
import subprocess

# ── ANSI colour palette ────────────────────────────────────────────────────────
RESET    = "\033[0m"
BOLD     = "\033[1m"
BBLACK   = "\033[90m"
BRED     = "\033[91m"
BGREEN   = "\033[92m"
BYELLOW  = "\033[93m"
BBLUE    = "\033[94m"
BWHITE = "\033[95m"
BCYAN    = "\033[96m"
BWHITE   = "\033[97m"

# Enable ANSI on Windows
if platform.system() == "Windows":
    os.system("color")

# ── ASCII art banner ───────────────────────────────────────────────────────────
BANNER = f"""{BWHITE}{BOLD}
  ██████╗██╗   ██╗███████╗████████╗ ██████╗ ███╗   ███╗
 ██╔════╝██║   ██║██╔════╝╚══██╔══╝██╔═══██╗████╗ ████║
 ██║     ██║   ██║███████╗   ██║   ██║   ██║██╔████╔██║
 ██║     ██║   ██║╚════██║   ██║   ██║   ██║██║╚██╔╝██║
 ╚██████╗╚██████╔╝███████║   ██║   ╚██████╔╝██║ ╚═╝ ██║
  ╚═════╝ ╚═════╝ ╚══════╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝
{RESET}{BCYAN}{BOLD}              S H E L L  —  Built from Scratch in Python
{RESET}"""

# ── Helper: progress bar ──────────────────────────────────────────────────────
def make_bar(used, total, width=20, fill_color=BWHITE, empty_color=BBLACK):
    if total == 0:
        return f"{BBLACK}{'─' * width}{RESET}"
    filled = int((used / total) * width)
    bar  = f"{fill_color}{'█' * filled}{RESET}"
    bar += f"{empty_color}{'░' * (width - filled)}{RESET}"
    return f"[{bar}]"

# ── Platform helpers ──────────────────────────────────────────────────────────

def _get_uptime_seconds():
    system = platform.system()
    try:
        if system == "Linux":
            with open("/proc/uptime") as f:
                return float(f.read().split()[0])
        elif system == "Darwin":
            import re, time
            out = subprocess.check_output(["sysctl", "-n", "kern.boottime"],
                                          text=True, stderr=subprocess.DEVNULL)
            match = re.search(r"sec\s*=\s*(\d+)", out)
            if match:
                return time.time() - int(match.group(1))
        elif system == "Windows":
            import ctypes
            return ctypes.windll.kernel32.GetTickCount64() / 1000.0
    except Exception:
        pass
    return 0

def _format_uptime(secs):
    days  = int(secs // 86400)
    hours = int((secs % 86400) // 3600)
    mins  = int((secs % 3600) // 60)
    parts = []
    if days:  parts.append(f"{days}d")
    if hours: parts.append(f"{hours}h")
    parts.append(f"{mins}m")
    return " ".join(parts)

def _get_cpu_name():
    system = platform.system()
    try:
        if system == "Linux":
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":", 1)[1].strip()
        elif system == "Darwin":
            out = subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                text=True, stderr=subprocess.DEVNULL).strip()
            if out:
                return out
            out = subprocess.check_output(
                ["sysctl", "-n", "hw.model"],
                text=True, stderr=subprocess.DEVNULL).strip()
            return out or platform.processor() or platform.machine()
        elif system == "Windows":
            out = subprocess.check_output(
                ["wmic", "cpu", "get", "Name", "/value"],
                text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                if "Name=" in line:
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or platform.machine() or "Unknown"

def _get_memory():
    system = platform.system()
    try:
        if system == "Linux":
            with open("/proc/meminfo") as f:
                lines = f.readlines()
            total = int(lines[0].split()[1]) // 1024
            avail = int(lines[2].split()[1]) // 1024
            return total - avail, total
        elif system == "Darwin":
            total_bytes = int(subprocess.check_output(
                ["sysctl", "-n", "hw.memsize"],
                text=True, stderr=subprocess.DEVNULL).strip())
            total = total_bytes // (1024 * 1024)
            vm = subprocess.check_output(
                ["vm_stat"], text=True, stderr=subprocess.DEVNULL)
            free_pages = 0
            for line in vm.splitlines():
                if "Pages free" in line or "Pages inactive" in line:
                    val = line.split(":")[1].strip().rstrip(".")
                    free_pages += int(val)
            avail = (free_pages * 4096) // (1024 * 1024)
            return total - avail, total
        elif system == "Windows":
            out = subprocess.check_output(
                ["wmic", "OS", "get",
                 "TotalVisibleMemorySize,FreePhysicalMemory", "/value"],
                text=True, stderr=subprocess.DEVNULL)
            vals = {}
            for line in out.splitlines():
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    vals[k.strip()] = v.strip()
            total = int(vals.get("TotalVisibleMemorySize", 0)) // 1024
            free  = int(vals.get("FreePhysicalMemory", 0))     // 1024
            return total - free, total
    except Exception:
        pass
    return 0, 0

def _get_gpu():
    system = platform.system()
    try:
        if system == "Darwin":
            out = subprocess.check_output(
                ["system_profiler", "SPDisplaysDataType"],
                text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                if "Chipset Model" in line or "Chip" in line:
                    return line.split(":", 1)[1].strip()
        elif system == "Linux":
            out = subprocess.check_output(
                ["lspci"], text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                if "VGA" in line or "3D" in line or "Display" in line:
                    return line.split(":", 2)[-1].strip()
        elif system == "Windows":
            out = subprocess.check_output(
                ["wmic", "path", "win32_VideoController",
                 "get", "Name", "/value"],
                text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                if "Name=" in line:
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return "N/A"

def _get_packages():
    system = platform.system()
    counts = []
    try:
        if system == "Darwin":
            out = subprocess.check_output(
                ["brew", "list", "--formula"],
                text=True, stderr=subprocess.DEVNULL)
            n = len([l for l in out.splitlines() if l.strip()])
            if n: counts.append(f"{n} (brew)")
        elif system == "Linux":
            for cmd, label in [
                (["dpkg", "--get-selections"], "dpkg"),
                (["rpm", "-qa"], "rpm"),
                (["pacman", "-Q"], "pacman"),
            ]:
                try:
                    out = subprocess.check_output(
                        cmd, text=True, stderr=subprocess.DEVNULL)
                    n = len([l for l in out.splitlines() if l.strip()])
                    if n:
                        counts.append(f"{n} ({label})")
                        break
                except Exception:
                    continue
        elif system == "Windows":
            out = subprocess.check_output(
                ["choco", "list", "--local-only"],
                text=True, stderr=subprocess.DEVNULL)
            lines = [l for l in out.splitlines() if l.strip()]
            if lines:
                counts.append(f"{len(lines)-1} (choco)")
    except Exception:
        pass
    return ", ".join(counts) if counts else "N/A"

def _get_resolution():
    system = platform.system()
    try:
        if system == "Darwin":
            out = subprocess.check_output(
                ["system_profiler", "SPDisplaysDataType"],
                text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                if "Resolution" in line:
                    return line.split(":", 1)[1].strip()
        elif system == "Linux":
            out = subprocess.check_output(
                ["xrandr"], text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                if "*" in line:
                    return line.strip().split()[0]
        elif system == "Windows":
            out = subprocess.check_output(
                ["wmic", "path", "Win32_VideoController",
                 "get", "CurrentHorizontalResolution,CurrentVerticalResolution",
                 "/value"],
                text=True, stderr=subprocess.DEVNULL)
            vals = {}
            for line in out.splitlines():
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    vals[k] = v
            h = vals.get("CurrentHorizontalResolution", "")
            v = vals.get("CurrentVerticalResolution", "")
            if h and v:
                return f"{h}x{v}"
    except Exception:
        pass
    return "N/A"

# ── Main info gatherer ────────────────────────────────────────────────────────
def get_system_info():
    info = {}
    system = platform.system()

    try:
        info["user"] = getpass.getuser()
    except Exception:
        info["user"] = os.environ.get("USER", os.environ.get("USERNAME", "user"))
    try:
        info["host"] = socket.gethostname()
    except Exception:
        info["host"] = "localhost"

    if system == "Linux":
        try:
            with open("/etc/os-release") as f:
                lines = dict(l.strip().split("=", 1) for l in f if "=" in l)
            info["os"] = lines.get("PRETTY_NAME", "Linux").strip('"')
        except Exception:
            info["os"] = f"Linux {platform.release()}"
    elif system == "Darwin":
        info["os"] = f"macOS {platform.mac_ver()[0]}"
    elif system == "Windows":
        info["os"] = f"Windows {platform.release()} {platform.version()}"
    else:
        info["os"] = system

    info["kernel"]     = platform.release()
    info["arch"]       = platform.machine()
    info["python"]     = f"Python {platform.python_version()}"
    info["shell"]      = "CustomShell v1.0"
    info["terminal"]   = os.environ.get("TERM_PROGRAM",
                          os.environ.get("TERM",
                          os.environ.get("WT_SESSION", "Unknown")))

    secs = _get_uptime_seconds()
    info["uptime"] = _format_uptime(secs) if secs else "N/A"

    cpu_name  = _get_cpu_name()
    cpu_cores = multiprocessing.cpu_count()
    info["cpu"] = f"{cpu_name} ({cpu_cores} cores)"

    info["gpu"]        = _get_gpu()
    info["packages"]   = _get_packages()
    info["resolution"] = _get_resolution()

    mem_used, mem_total = _get_memory()
    if mem_total > 0:
        if mem_total >= 1024:
            mt = f"{mem_total/1024:.1f} GiB"
            mu = f"{mem_used/1024:.1f} GiB"
        else:
            mt = f"{mem_total} MiB"
            mu = f"{mem_used} MiB"
        bar = make_bar(mem_used, mem_total)
        info["memory"] = f"{mu} / {mt}  {bar}"
    else:
        info["memory"] = "N/A"
    info["memory_used"]  = mem_used
    info["memory_total"] = mem_total

    try:
        total, used, free = shutil.disk_usage("/")
        dt  = total // 2**30
        du  = used  // 2**30
        bar = make_bar(du, dt)
        info["disk"] = f"{du} GiB / {dt} GiB  {bar}"
    except Exception:
        info["disk"] = "N/A"

    now = datetime.datetime.now()
    info["date"] = now.strftime("%A, %d %B %Y")
    info["time"] = now.strftime("%H:%M:%S")

    try:
        home  = os.path.expanduser("~")
        count = len(os.listdir(home))
        info["home_files"] = f"{count} items in ~"
    except Exception:
        info["home_files"] = "N/A"

    return info

# ── Render MOTD ───────────────────────────────────────────────────────────────
def print_motd():
    info = get_system_info()

    label = lambda s: f"{BCYAN}{BOLD}{s:<12}{RESET}"
    value = lambda s: f"{BWHITE}{s}{RESET}"
    kv    = lambda k, v: f"  {label(k)}  {value(v)}"

    user_host = (f"{BWHITE}{BOLD}{info['user']}{RESET}"
                 f"{BBLACK}@{RESET}"
                 f"{BCYAN}{BOLD}{info['host']}{RESET}")

    print(BANNER)
    print(f"  {user_host}")
    print(f"  {BBLACK}{'─' * (len(info['user']) + len(info['host']) + 1)}{RESET}")
    print()

    print(kv("OS",         info["os"]))
    print(kv("Kernel",     info["kernel"]))
    print(kv("Arch",       info["arch"]))
    print(kv("Uptime",     info["uptime"]))
    print(kv("Packages",   info["packages"]))
    print(kv("Resolution", info["resolution"]))
    print()

    print(kv("Shell",      info["shell"]))
    print(kv("Python",     info["python"]))
    print(kv("Terminal",   info["terminal"]))
    print()

    print(kv("CPU",        info["cpu"]))
    print(kv("GPU",        info["gpu"]))
    print(kv("Memory",     info["memory"]))
    print(kv("Disk",       info["disk"]))
    print()

    print(kv("Date",       info["date"]))
    print(kv("Time",       info["time"]))
    print(kv("Home",       info["home_files"]))
    print()

    colours = [
        "\033[40m  ", "\033[41m  ", "\033[42m  ", "\033[43m  ",
        "\033[44m  ", "\033[45m  ", "\033[46m  ", "\033[47m  ",
        "\033[100m  ", "\033[101m  ", "\033[102m  ", "\033[103m  ",
        "\033[104m  ", "\033[105m  ", "\033[106m  ", "\033[107m  ",
    ]
    print("  " + "".join(colours) + RESET)
    print()
    # print(f"  {BBLACK}Ready when you are...{RESET}")
    print(f"  {BWHITE}{BOLD}Ready when you are...{RESET}")
    print()

if __name__ == "__main__":
    print_motd()