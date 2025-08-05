import os
import subprocess
import psutil
import datetime
import shutil
import socket


def write_output(line=""):
    """Echo output to console in real-time."""
    print(line)


def header():
    write_output(f"Security Scan Report - {datetime.datetime.now()} UTC")
    write_output("=" * 60)


def scan_clamav(path="~"):
    write_output(f"\n[1] ClamAV Virus Scan on {path}:")
    if shutil.which("clamscan"):
        cmd = ["clamscan", "-r", "--bell", os.path.expanduser(path)]
        write_output("Running clamscan recursively. This might take a while...")
        subprocess.run(cmd)
    else:
        write_output("ClamAV not installed. Install via 'sudo apt-get install clamav'.")


def scan_rootkit_tools():
    write_output("\n[2] Rootkit Scanner Checks:")
    if shutil.which("chkrootkit"):
        write_output("-- Running chkrootkit...")
        out = subprocess.getoutput("sudo chkrootkit")
        write_output(out)
    else:
        write_output("chkrootkit not installed. Install via 'sudo apt-get install chkrootkit'.")

    if shutil.which("rkhunter"):
        write_output("-- Running rkhunter...")
        out = subprocess.getoutput("sudo rkhunter --check --sk")
        write_output(out)
    else:
        write_output("rkhunter not installed. Install via 'sudo apt-get install rkhunter'.")


def list_running_processes():
    write_output("\n[3] Running Processes:")
    for p in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
        info = p.info
        write_output(f"PID:{info['pid']} User:{info['username']} CPU:{info['cpu_percent']}% MEM:{info['memory_percent']:.2f}% Name:{info['name']}")


def list_open_ports():
    write_output("\n[4] Open Network Ports:")
    for conn in psutil.net_connections(kind='inet'):
        laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else ""
        raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else ""
        proto = 'TCP' if conn.type == socket.SOCK_STREAM else 'UDP'
        write_output(f"Proto:{proto} LAddr:{laddr} RAddr:{raddr} Status:{conn.status} PID:{conn.pid}")


def list_startup_services():
    write_output("\n[5] Enabled Systemd Services:")
    out = subprocess.getoutput("systemctl list-unit-files --type=service --state=enabled")
    write_output(out)


def check_firewall():
    write_output("\n[6] UFW Firewall Status:")
    if shutil.which("ufw"):
        out = subprocess.getoutput("sudo ufw status verbose")
        write_output(out)
    else:
        write_output("UFW not installed. Install via 'sudo apt-get install ufw'.")


def analyze_auth_logs():
    write_output("\n[7] Recent Auth Logs (last 50 lines):")
    log = "/var/log/auth.log"
    if os.path.exists(log):
        out = subprocess.getoutput(f"tail -n 50 {log}")
        write_output(out)
    else:
        write_output("Auth log not found (/var/log/auth.log).")


def scan_other_partition():
    write_output("\n[8] Other OS Partition Scan:")
    p = subprocess.getoutput("lsblk -nr -o NAME,FSTYPE | grep ext4 | awk '{print $1}' | sed -n '2p'")
    if p:
        dev = f"/dev/{p}"
        mount_point = os.path.expanduser("~/mnt/other_os")
        try:
            os.makedirs(mount_point, exist_ok=True)
        except PermissionError:
            write_output(f"Permission denied: Cannot create {mount_point}. Run with sudo or use a path in your home directory.")
            return
        write_output(f"Mounting {dev} to {mount_point}...")
        subprocess.run(["sudo", "mount", dev, mount_point])
        scan_clamav(path=mount_point)
        write_output("-- Suspicious file permissions on other OS:")
        out = subprocess.getoutput(f"find {mount_point} -perm /6000 -o -perm /0002 -type f | head -n 50")
        write_output(out)
        subprocess.run(["sudo", "umount", mount_point])
    else:
        write_output("Secondary ext4 partition not detected.")


def footer():
    write_output("\nScan complete.")


def main():
    header()
    scan_clamav(path="~")
    scan_rootkit_tools()
    list_running_processes()
    list_open_ports()
    list_startup_services()
    check_firewall()
    analyze_auth_logs()
    scan_other_partition()
    footer()

if __name__ == '__main__':
    main()
