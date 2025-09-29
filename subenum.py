#!/usr/bin/env python3
"""
subenum.py - Subdomain enumeration + httpx live check + optional Discord webhook

Usage:
  python3 subenum.py -d example.com
  python3 subenum.py -d example.com --webhook-url "https://discord.com/api/webhooks/..."
Or set environment variable DISCORD_WEBHOOK and omit --webhook-url.

Notes:
 - Requires subfinder and httpx in PATH.
 - Uses requests for Discord if available; falls back to urllib.
"""

import argparse
import subprocess
import sys
import os
from datetime import datetime
import json
import textwrap

# Try to import requests for simpler HTTP POST; fallback to urllib if not installed
try:
    import requests
    _HAS_REQUESTS = True
except Exception:
    import urllib.request
    import urllib.error
    _HAS_REQUESTS = False

MAX_DISCORD_LINES = 15   # max number of live entries to send in one Discord message
DISCORD_CHAR_LIMIT = 1900  # keep below 2000 char limit for message content

def run_command(cmd, capture_output=False, text=True):
    """Run subprocess command. Raise on failure, returning CompletedProcess if capture_output True."""
    try:
        if capture_output:
            return subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=text)
        else:
            return subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Command failed: {' '.join(cmd)}")
        if hasattr(e, "stdout") and e.stdout:
            print("    stdout:", e.stdout.strip())
        if hasattr(e, "stderr") and e.stderr:
            print("    stderr:", e.stderr.strip())
        raise
    except FileNotFoundError:
        print(f"[!] Command not found: {cmd[0]}. Is it installed and in PATH?")
        raise

def send_discord_notification(webhook_url, domain, live_list):
    """
    Send a concise Discord webhook message listing the live subdomains.
    Uses requests if available; otherwise urllib.
    """
    if not webhook_url:
        print("[*] No webhook URL provided; skipping Discord notification.")
        return

    if not live_list:
        print("[*] No live hosts to notify about.")
        return

    # Build a short message: include domain, count, and up to MAX_DISCORD_LINES examples
    count = len(live_list)
    header = f"📡 Live hosts found for `{domain}`: **{count}**\n"
    examples = live_list[:MAX_DISCORD_LINES]
    # Prepare bullet list
    body_lines = [f"- {line}" for line in examples]
    body = "\n".join(body_lines)

    content = header + body

    # Ensure we don't exceed a safe message length
    if len(content) > DISCORD_CHAR_LIMIT:
        # trim lines until under limit
        while len(content) > DISCORD_CHAR_LIMIT and examples:
            examples = examples[:-1]
            body_lines = [f"- {line}" for line in examples]
            body = "\n".join(body_lines)
            content = header + body
        # append note about truncation
        content += f"\n\n*(truncated to {len(examples)} items)*"

    payload = {"content": content}

    print("[*] Sending Discord notification...")

    try:
        if _HAS_REQUESTS:
            resp = requests.post(webhook_url, json=payload, timeout=10)
            if resp.status_code in (200, 204):
                print("[+] Discord notification sent successfully.")
            else:
                print(f"[!] Discord webhook returned HTTP {resp.status_code}: {resp.text}")
        else:
            # urllib fallback
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(webhook_url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as r:
                # Discord usually returns 204 No Content on success
                code = r.getcode()
                if code in (200, 204):
                    print("[+] Discord notification sent successfully (urllib).")
                else:
                    print(f"[!] Discord webhook returned HTTP {code}")
    except Exception as e:
        print("[!] Failed to send Discord webhook:", str(e))

def main():
    parser = argparse.ArgumentParser(description="Subdomain Enumerator & Live Host Checker (with Discord webhook)")
    parser.add_argument("-d", "--domain", required=True, help="Target domain (e.g. example.com)")
    parser.add_argument("-o", "--outdir", default=".", help="Output directory (default: current directory)")
    parser.add_argument("--webhook-url", default=None, help="Discord webhook URL (optional). Can also set DISCORD_WEBHOOK env var.")
    args = parser.parse_args()

    domain = args.domain.strip()
    outdir = args.outdir
    webhook_url = args.webhook_url or os.environ.get("DISCORD_WEBHOOK")
    os.makedirs(outdir, exist_ok=True)

    subdomains_file = os.path.join(outdir, f"{domain}.txt")
    live_file = os.path.join(outdir, f"{domain}_live.txt")

    print(f"[+] Target domain: {domain}")
    print(f"[+] Outputs: {subdomains_file} and {live_file}")
    print(f"[+] Started at {datetime.now().isoformat(timespec='seconds')}")

    # 1) Run subfinder
    try:
        print("[*] Running subfinder to enumerate subdomains...")
        run_command(["subfinder", "-d", domain, "-silent", "-o", subdomains_file])
        print(f"[+] Subfinder finished. Results saved to {subdomains_file}")
    except Exception:
        print("[!] Subfinder step failed — aborting.")
        sys.exit(1)

    # Quick sanity check
    if not os.path.isfile(subdomains_file) or os.path.getsize(subdomains_file) == 0:
        print(f"[!] No subdomains found or {subdomains_file} is empty.")
        sys.exit(0)

    # 2) Run httpx
    try:
        print("[*] Running httpx to probe which subdomains are live (this may take a bit)...")
        try:
            run_command(["httpx", "-silent", "-l", subdomains_file, "-o", live_file])
            print(f"[+] httpx finished. Live hosts saved to {live_file}")
        except subprocess.CalledProcessError:
            cp = run_command(["httpx", "-silent", "-l", subdomains_file], capture_output=True)
            with open(live_file, "w") as f:
                f.write(cp.stdout)
            print(f"[+] httpx finished (captured). Live hosts saved to {live_file}")
    except FileNotFoundError:
        print("[!] httpx not found in PATH. Make sure httpx is installed.")
        sys.exit(1)
    except Exception:
        print("[!] httpx step failed.")
        sys.exit(1)

    # 3) Read results and summarize (loop + conditional)
    try:
        with open(live_file, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
        live_count = 0
        live_entries = []
        for line in lines:
            # httpx typically outputs full URL (https://...), but we'll accept hostnames too
            if line.startswith("http") or "." in line:
                live_count += 1
                live_entries.append(line)

        if live_count == 0:
            print("[!] No live hosts detected.")
        else:
            print(f"[+] Found {live_count} live hosts. Showing up to {MAX_DISCORD_LINES} entries:")
            for sample in live_entries[:5]:
                print("    -", sample)

        print(f"[+] Completed at {datetime.now().isoformat(timespec='seconds')}")
    except FileNotFoundError:
        print(f"[!] Expected live results file missing: {live_file}")
    except Exception as e:
        print("[!] Error while summarizing results:", str(e))

    # 4) Send Discord notification (if webhook provided)
    try:
        if webhook_url:
            send_discord_notification(webhook_url, domain, live_entries)
        else:
            print("[*] No Discord webhook configured (use --webhook-url or set DISCORD_WEBHOOK).")
    except Exception as e:
        print("[!] Error while sending Discord notification:", str(e))


if __name__ == "__main__":
    main()

