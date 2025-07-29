#!/bin/bash
# cleanup_script.sh
# A maintenance script to check disk usage, remove old logs, and clean temporary files.

# Define logfile
LOGFILE="/home/$USER/script_log.txt"

# Logging function
log() {
  local MESSAGE="$1"
  echo "$(date '+%Y-%m-%d %H:%M:%S') - $MESSAGE" | tee -a "$LOGFILE"
}

# Prompt user for confirmation
read -p "Do you want to continue with system maintenance and cleanup? (y/n) " ANSWER
if [[ "$ANSWER" != "y" && "$ANSWER" != "Y" ]]; then
  log "User aborted the script. Exiting."
  exit 0
fi

log "Script started."

# 1. Check disk usage
log "Checking disk usage..."
DF_OUTPUT=$(df -h)
echo "$DF_OUTPUT"
log "Disk usage checked."

echo
# 2. Delete logs older than 7 days
LOG_DIR="/var/log"
log "Removing log files older than 7 days in $LOG_DIR..."

# Find and delete .log files older than 7 days
find "$LOG_DIR" -type f -name "*.log" -mtime +7 | while read -r FILE; do
  rm -f "$FILE"
  log "Deleted old log: $FILE"
done
log "Old logs cleanup completed."

echo
# 3. Scheduled cleanup: Delete temporary files
TEMP_DIR="/tmp"
log "Cleaning temporary files in $TEMP_DIR..."

# Gather list of files
mapfile -t FILES < <(find "$TEMP_DIR" -mindepth 1)
TOTAL=${#FILES[@]}
COUNT=0

# Remove files with a simple progress bar
for FILE in "${FILES[@]}"; do
  rm -rf "$FILE"
  ((COUNT++))
  # Calculate and display progress
  PERCENT=$((COUNT * 100 / TOTAL))
  BAR=$(printf "%-50s" "" | tr ' ' '#')
  FILLED=$((PERCENT * 50 / 100))
  echo -ne "Progress: [${BAR:0:FILLED}${BAR:FILLED}] $PERCENT%%\r"
  log "Removed temp: $FILE"
done

echo -e "\n"
log "Temporary files cleanup completed."

log "Script finished successfully."
