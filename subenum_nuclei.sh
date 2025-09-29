#!/usr/bin/env bash
#
# subenum_nuclei.sh
# Cron-friendly script:
#  - Enumerates subdomains with subfinder -> <domain>.txt
#  - Runs nuclei on the list -> nuclei_<domain>.txt
#  - Detects new subdomains since last run and re-scans them with nuclei
#  - Optional: send a short Discord notification if new vulnerable results are found
#
# Usage:
#   ./subenum_nuclei.sh -d example.com
#   ./subenum_nuclei.sh -d example.com -o /path/to/outdir --webhook-url "https://discord.com/api/webhooks/..."
#
# Requirements: subfinder, nuclei, sort, comm, curl (for optional Discord webhook)
#

set -euo pipefail

# --------------------------
# Defaults and helpers
# --------------------------
usage() {
  cat <<EOF
Usage: $0 -d domain [-o outdir] [--webhook-url URL]

  -d domain        Target domain (required)
  -o outdir        Output directory (default: current directory)
  --webhook-url    Optional: Discord webhook URL for notifications (or set DISCORD_WEBHOOK env)
EOF
  exit 1
}

# Parse args (simple)
DOMAIN=""
OUTDIR="."
WEBHOOK=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -d|--domain) DOMAIN="$2"; shift 2;;
    -o|--outdir) OUTDIR="$2"; shift 2;;
    --webhook-url) WEBHOOK="$2"; shift 2;;
    -h|--help) usage;;
    *) echo "[!] Unknown arg: $1"; usage;;
  esac
done

if [[ -z "$DOMAIN" ]]; then
  echo "[!] Domain is required."
  usage
fi

# Allow webhook as env var fallback
if [[ -z "$WEBHOOK" ]]; then
  WEBHOOK="${DISCORD_WEBHOOK:-}"
fi

mkdir -p "$OUTDIR"

# Filenames
SUBS_FILE="${OUTDIR}/${DOMAIN}.txt"
PREV_FILE="${OUTDIR}/${DOMAIN}.prev.txt"
NEW_FILE="${OUTDIR}/${DOMAIN}.new.txt"
NUCLEI_FILE="${OUTDIR}/nuclei_${DOMAIN}.txt"
NUCLEI_NEW_FILE="${OUTDIR}/nuclei_${DOMAIN}_new.txt"

# --------------------------
# Basic checks
# --------------------------
command -v subfinder >/dev/null 2>&1 || { echo "[!] subfinder not found in PATH. Install it and retry."; exit 1; }
command -v nuclei >/dev/null 2>&1 || { echo "[!] nuclei not found in PATH. Install it and retry."; exit 1; }

echo "[+] Target domain: $DOMAIN"
echo "[+] Output directory: $OUTDIR"
echo "[+] Timestamp: $(date -Iseconds)"

# --------------------------
# 1) Run subfinder and save to SUBS_FILE
# --------------------------
echo "[*] Running subfinder..."
# Use -silent for simpler output; change flags if your subfinder version differs
if subfinder -d "$DOMAIN" -silent -o "$SUBS_FILE" 2>/dev/null; then
  echo "[+] Subfinder finished. Results saved to $SUBS_FILE"
else
  echo "[!] subfinder encountered an error. Check CLI flags or network."
  exit 1
fi

# If file is empty, warn and exit (nothing to scan)
if [[ ! -s "$SUBS_FILE" ]]; then
  echo "[!] No subdomains discovered; $SUBS_FILE is empty. Exiting."
  exit 0
fi

# Ensure sorted unique copies (helpful for comm)
sort -u "$SUBS_FILE" -o "$SUBS_FILE"

# --------------------------
# 2) Run nuclei on all subdomains (full scan)
# --------------------------
echo "[*] Running nuclei on the full subdomain list (may take a while)..."
# nuclei reads -l <file>; output appended or overwritten depending on desired behavior
# We overwrite the full nuclei file for the full run
if nuclei -l "$SUBS_FILE" -o "$NUCLEI_FILE" 2>/dev/null; then
  echo "[+] Nuclei full scan finished. Results saved to $NUCLEI_FILE"
else
  echo "[!] nuclei encountered an error during full scan. Check templates & connectivity."
  # continue — we may still want to attempt monitoring step
fi

# --------------------------
# 3) Subdomain monitoring: detect new subdomains since last run
# --------------------------
# If PREV_FILE doesn't exist, treat all as "new" for first run
if [[ ! -f "$PREV_FILE" ]]; then
  echo "[*] No previous snapshot found. Treating all discovered subdomains as new."
  cp "$SUBS_FILE" "$PREV_FILE"
  # For first run, new list = empty (we already scanned everything)
  > "$NEW_FILE"
else
  # Use comm to find lines in SUBS_FILE that are not in PREV_FILE
  # Both must be sorted
  sort -u "$PREV_FILE" -o "$PREV_FILE"
  sort -u "$SUBS_FILE" -o "$SUBS_FILE"
  comm -23 "$SUBS_FILE" "$PREV_FILE" > "$NEW_FILE" || true
fi

# Count new entries
NEW_COUNT=0
if [[ -s "$NEW_FILE" ]]; then
  NEW_COUNT=$(wc -l < "$NEW_FILE" | tr -d ' ')
fi

if [[ "$NEW_COUNT" -eq 0 ]]; then
  echo "[*] No new subdomains found since last run."
else
  echo "[+] New subdomains found: $NEW_COUNT"
  echo "[*] New subdomains saved to $NEW_FILE"
  # --------------------------
  # 4) Run nuclei on new subdomains only
  # --------------------------
  echo "[*] Running nuclei on the new subdomains..."
  # Append results from new scan to the main nuclei file (so you maintain a historical file)
  if nuclei -l "$NEW_FILE" -o "$NUCLEI_NEW_FILE" 2>/dev/null; then
    # Append with a timestamp header for clarity
    {
      printf "\n# New scan on %s (for new subdomains):\n" "$(date -Iseconds)"
      cat "$NUCLEI_NEW_FILE"
    } >> "$NUCLEI_FILE"
    echo "[+] Nuclei scan for new subdomains finished and appended to $NUCLEI_FILE"
  else
    echo "[!] nuclei failed on new subdomains."
  fi

  # Optional: send a notification about new subdomains / new nuclei results
  if [[ -n "$WEBHOOK" ]]; then
    echo "[*] Sending Discord notification about new subdomains..."
    # build a short message: domain, count and up to 10 examples
    MAX_EX=10
    EXAMPLES=$(head -n $MAX_EX "$NEW_FILE" | sed ':a;N;$!ba;s/\n/\\n/g')
    CONTENT="{\"content\":\"📡 New subdomains discovered for \`$DOMAIN\`: **$NEW_COUNT**\\nExamples:\\n$EXAMPLES\"}"
    # send using curl
    if curl -s -X POST -H "Content-Type: application/json" -d "$CONTENT" "$WEBHOOK" >/dev/null 2>&1; then
      echo "[+] Discord notification sent."
    else
      echo "[!] Failed to send Discord notification (curl error)."
    fi
  fi
fi

# --------------------------
# 5) Rotate snapshot: save current list as prev for next run
# --------------------------
cp "$SUBS_FILE" "$PREV_FILE"
echo "[+] Snapshot updated: $PREV_FILE"

echo "[+] Completed at $(date -Iseconds)"

