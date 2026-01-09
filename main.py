import yaml
import os
import platform
import shutil
import subprocess
import sys


# ================= LOGO =================
def logo():
    print("==============================================")
    print("              AutoIsys Utility")
    print("==============================================")


# ================= PATHS =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.yaml")


# ================= DEFAULT CONFIG =================
DEFAULT_CONFIG = {
    "app": {
        "name": "AutoIsys",
        "version": "0.0.2",
    },
    "system": {
        "auto_update": True,
        "auto_install": True,
        "install_docker": True,

        "enable_services": [
            "docker"
        ]
    },
    "packages": [
        "git",
        "curl",
        "htop"
    ]
}


# ================= CONFIG MERGE =================
def merge_config(default, current):
    for key, value in default.items():
        if key not in current:
            current[key] = value
        elif isinstance(value, dict) and isinstance(current[key], dict):
            merge_config(value, current[key])


def load_config():
    if not os.path.exists(CONFIG_FILE):
        print("[CONFIG] Creating config.yaml")
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.dump(DEFAULT_CONFIG, f, allow_unicode=True)
        return DEFAULT_CONFIG.copy()

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        current = yaml.safe_load(f) or {}

    merge_config(DEFAULT_CONFIG, current)

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(current, f, allow_unicode=True)

    return current


config = load_config()


# ================= OS =================
def get_linux_distro():
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME"):
                    return line.split("=", 1)[1].strip().strip('"')
    except FileNotFoundError:
        return "Unknown Linux"


def check_os():
    system = platform.system()

    if system == "Linux":
        print("OS:", get_linux_distro())
    elif system == "Darwin":
        print("OS: macOS", platform.mac_ver()[0])
    else:
        print("Unsupported OS")
        sys.exit(1)


# ================= PACKAGE MANAGER =================
def detect_package_manager():
    system = platform.system()

    if system == "Linux":
        managers = {
            "pacman": "pacman",
            "apt": "apt",
            "dnf": "dnf",
            "yum": "yum",
            "zypper": "zypper",
            "apk": "apk",
            "emerge": "emerge",
            "xbps-install": "xbps",
            "nix-env": "nix"
        }

        for cmd, name in managers.items():
            if shutil.which(cmd):
                return name

        return "unknown-linux"

    elif system == "Darwin":
        if shutil.which("brew"):
            return "brew"
        if shutil.which("port"):
            return "macports"
        return "unknown-macos"

    return "unsupported-os"


# ================= AUTO UPDATE =================
def auto_update_system():
    if not config.get("system", {}).get("auto_update", False):
        print("[INFO] Auto update disabled")
        return

    pm = detect_package_manager()

    commands = {
        "pacman": ["sudo", "pacman", "-Syu"],
        "apt": ["sudo", "apt", "update"],
        "dnf": ["sudo", "dnf", "upgrade", "-y"],
        "yum": ["sudo", "yum", "update", "-y"],
        "apk": ["sudo", "apk", "upgrade"],
        "brew": ["brew", "update"],
    }

    if pm not in commands:
        print("[WARN] Auto update not supported for:", pm)
        return

    cmd = commands[pm]
    print("[RUN]", " ".join(cmd))
    subprocess.run(cmd)


# ================= DOCKER =================
def install_docker():
    if not config.get("system", {}).get("install_docker", False):
        print("[INFO] Docker install disabled")
        return

    pm = detect_package_manager()

    docker_packages = {
        "pacman": ["sudo", "pacman", "-S", "--noconfirm", "docker"],
        "apt": ["sudo", "apt", "install", "-y", "docker.io"],
        "dnf": ["sudo", "dnf", "install", "-y", "docker"],
        "yum": ["sudo", "yum", "install", "-y", "docker"],
        "apk": ["sudo", "apk", "add", "docker"],
        "brew": ["brew", "install", "--cask", "docker"],
    }

    if pm not in docker_packages:
        print("[WARN] Docker install not supported for:", pm)
        return

    print("[INFO] Installing Docker")
    subprocess.run(docker_packages[pm])


# ================= SERVICES =================
def enable_services():
    services = config.get("system", {}).get("enable_services", [])

    if not services:
        print("[INFO] No services to enable")
        return

    if not shutil.which("systemctl"):
        print("[WARN] systemd not detected")
        return

    for service in services:
        print(f"[SERVICE] Enabling {service}")
        subprocess.run(["sudo", "systemctl", "enable", "--now", service])


# ================= AUTO INSTALL PACKAGES =================
def is_installed(pkg):
    return shutil.which(pkg) is not None


def auto_install_packages():
    if not config.get("system", {}).get("auto_install", False):
        print("[INFO] Auto install disabled")
        return

    packages = config.get("packages", [])

    if not packages:
        print("[INFO] No packages to install")
        return

    pm = detect_package_manager()

    INSTALL_COMMANDS = {
        "pacman": lambda p: ["sudo", "pacman", "-S", "--noconfirm", p],
        "apt": lambda p: ["sudo", "apt", "install", "-y", p],
        "dnf": lambda p: ["sudo", "dnf", "install", "-y", p],
        "yum": lambda p: ["sudo", "yum", "install", "-y", p],
        "apk": lambda p: ["sudo", "apk", "add", p],
        "brew": lambda p: ["brew", "install", p],
    }

    if pm not in INSTALL_COMMANDS:
        print("[WARN] Package manager not supported:", pm)
        return

    print("[INFO] Installing packages using:", pm)

    for pkg in packages:
        if is_installed(pkg):
            print(f"[OK] {pkg} already installed")
            continue

        cmd = INSTALL_COMMANDS[pm](pkg)
        print("[INSTALL]", " ".join(cmd))
        subprocess.run(cmd)


# ================= MAIN =================
def main():
    logo()
    check_os()
    auto_update_system()
    install_docker()
    auto_install_packages()
    enable_services()


main()
