from flask import Flask, jsonify, render_template
import re
import time
from collections import defaultdict
import threading
import os

# Define the log file path
log_file_path = os.path.join(os.path.expanduser("~"), "AppData", "Local", "FortniteGame", "Saved", "Logs", "FortniteGame.log")


# Patterns for identifying game start, elimination, and reboot logs
game_start_pattern = r"(\[\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3}\])\s*\[\d+\]LogStats:.*Loot Item Defs determined!"
elimination_pattern = r"LogFortEliminationFeed: Verbose: <(?:Gold)?(?:Team)?(?:Local)?Killer>(.*?)</> (?!knocked out).* <(?:Team)?(?:Local)?Victim>(.*?)</>"
reboot_pattern = r"LogFortEliminationFeed: Verbose: <Victim>(.*?)</> was rebooted"

# Initialize Flask app
app = Flask(__name__)
leaderboard = defaultdict(lambda: {"score": 0, "status": "alive"})
last_position = 0

def update_leaderboard():
    """Continuously update the leaderboard from the log file."""
    global last_position
    while True:
        try:
            with open(log_file_path, "r", encoding="utf-8", errors="ignore") as log_file:
                log_file.seek(last_position)
                lines = log_file.readlines()
                if lines:
                    for line in lines:
                        parse_log_line(line)
                    last_position = log_file.tell()
                time.sleep(1)
        except FileNotFoundError:
            print("Log file not found. Ensure Fortnite is running and generating logs.")
            time.sleep(1)

def parse_log_line(line):
    """Parse the line for elimination, game start, or reboot events."""
    global leaderboard
    # Check for game start pattern to reset leaderboard
    if re.search(game_start_pattern, line):
        leaderboard.clear()
        return
    
    # Check for elimination log
    elimination_match = re.search(elimination_pattern, line)
    if elimination_match:
        killer = re.sub(r" \(\d+\)", "", elimination_match.group(1))
        victim = re.sub(r" \(\d+\)", "", elimination_match.group(2))
        leaderboard[killer]["score"] += 1
        leaderboard[victim]["status"] = f"Killed by {killer}"  # Set status to show killer's name
        leaderboard[killer]["status"] = "alive"
        return

    # Check for reboot log
    reboot_match = re.search(reboot_pattern, line)
    if reboot_match:
        victim = re.sub(r" \(\d+\)", "", reboot_match.group(1))
        leaderboard[victim]["status"] = "alive"  # Mark the player as alive again

@app.route('/')
def index():
    """Serve the main dashboard page."""
    return render_template("index.html")

@app.route('/leaderboard')
def get_leaderboard():
    """Serve sorted leaderboard data as a list of tuples in JSON."""
    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1]["score"], reverse=True)
    return jsonify(sorted_leaderboard)

if __name__ == '__main__':
    threading.Thread(target=update_leaderboard, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=True)
