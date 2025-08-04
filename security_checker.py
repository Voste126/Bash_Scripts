#!/usr/bin/env python3
"""
security_checker.py

A simple cybersecurity tool that:
1. Scans a given directory for world-writable files.
2. Scans a given log file for occurrences of FAILED, ERROR, or DENIED.
3. Logs its findings to a timestamped report file.
"""

import os
import stat
import re
import datetime

def check_world_writable(directory):
    """
    Walk through `directory`, find files with world-writable permissions (mode & 0o002).
    Returns a list of file paths that are world-writable.
    """
    world_writable = []
    for root, dirs, files in os.walk(directory):
        for fname in files:
            path = os.path.join(root, fname)
            try:
                mode = os.stat(path).st_mode
            except OSError:
                # Skip files we cannot stat
                continue
            # Check the “other” write bit (octal 0o002)
            if mode & stat.S_IWOTH:
                world_writable.append(path)
    return world_writable

def scan_log_file(log_path):
    """
    Read the file at `log_path` line by line,
    count how many times the words FAILED, ERROR, and DENIED appear (case-insensitive).
    Returns a dict with the counts.
    """
    counts = {'FAILED': 0, 'ERROR': 0, 'DENIED': 0}
    # Compile a regex that matches any of the three keywords
    pattern = re.compile(r'\b(FAILED|ERROR|DENIED)\b', re.IGNORECASE)
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                for match in pattern.findall(line):
                    counts[match.upper()] += 1
    except FileNotFoundError:
        print(f"[!] Log file not found: {log_path}")
    return counts

def write_report(report_path, directory, world_list, log_path, log_counts):
    """
    Append a timestamped section to `report_path` summarizing:
      - which files were world-writable in `directory`
      - counts of FAILED/ERROR/DENIED in `log_path`
    """
    now = datetime.datetime.now().isoformat(sep=' ', timespec='seconds')
    with open(report_path, 'a') as rpt:
        rpt.write(f"\n=== Security Report: {now} ===\n")
        rpt.write(f"Scanned directory: {directory}\n")
        if world_list:
            rpt.write(f"World-writable files ({len(world_list)}):\n")
            for fn in world_list:
                rpt.write(f"  - {fn}\n")
        else:
            rpt.write("No world-writable files found.\n")
        rpt.write(f"\nScanned log file: {log_path}\n")
        rpt.write(f"FAILED entries: {log_counts['FAILED']}\n")
        rpt.write(f"ERROR entries: {log_counts['ERROR']}\n")
        rpt.write(f"DENIED entries: {log_counts['DENIED']}\n")
        rpt.write("=" * 30 + "\n")

def main():
    print("=== Security Checker Started ===")
    start_time = datetime.datetime.now()
    print("Start time:", start_time)

    # 1) File Permission Checker
    directory = input("Enter directory to scan for world-writable files: ").strip()
    print(f"Checking permissions in {directory} …")
    world_files = check_world_writable(directory)
    if world_files:
        print(f"[!] Found {len(world_files)} world-writable file(s):")
        for wf in world_files:
            print("   -", wf)
    else:
        print("[+] No world-writable files found.")

    # 2) Simple Log Monitor
    log_path = input("Enter path to log file to scan: ").strip()
    print(f"Scanning log file {log_path} …")
    log_counts = scan_log_file(log_path)
    print(f"[+] FAILED: {log_counts['FAILED']}, ERROR: {log_counts['ERROR']}, DENIED: {log_counts['DENIED']}")

    # 3) Write Security Report
    report_file = "security_report.txt"
    write_report(report_file, directory, world_files, log_path, log_counts)
    print(f"Report appended to {report_file}")

    end_time = datetime.datetime.now()
    print("End time:", end_time)
    print("=== Security Checker Finished ===")

if __name__ == "__main__":
    main()
