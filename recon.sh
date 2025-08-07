#!/usr/bin/env bash
#
# recon.sh – basic automated reconnaissance for Kali learners
# Usage: sudo ./recon.sh <target-ip-or-domain>
# Prerequisites: nmap, dirb, nikto installed on your Kali box

set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <target-domain-or-ip>"
  exit 1
fi

TARGET="$1"
OUTDIR="recon_${TARGET}_$(date +%Y%m%d_%H%M%S)"

echo "[*] Target is: $TARGET"
echo "[*] Creating output directory: $OUTDIR"
mkdir -p "$OUTDIR"

echo "[*] 1) Running fast Nmap scan on $TARGET..."
nmap -T4 -sV -oA "$OUTDIR"/nmap_fast "$TARGET"

HTTP_PORTS=$(
  # allow grep to return 1 (no matches) without aborting script
  grep -E 'open.*(http|ssl/http|https)' "$OUTDIR"/nmap_fast.nmap || true \
    | awk '{ print $1 }' \
    | cut -d'/' -f1
)
if [ -z "$HTTP_PORTS" ]; then
  echo "[!] No HTTP ports found. Skipping web enumeration."
else
  echo "[*] Found HTTP ports: $HTTP_PORTS"
  for P in $HTTP_PORTS; do
    echo "[*] 2) Running dirb on port $P..."
    dirb "http://${TARGET}:${P}" -o "$OUTDIR"/dirb_${P}.txt

    echo "[*] 3) Running nikto on port $P..."
    nikto -h "http://${TARGET}:${P}" -o "$OUTDIR"/nikto_${P}.txt
  done
fi

echo "[*] Recon completed. Results in $OUTDIR/"
