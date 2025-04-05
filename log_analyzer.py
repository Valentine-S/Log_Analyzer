import threading
import sys
import queue
import time
from datetime import datetime
from collections import defaultdict, deque, Counter
import re

# Configuration
SLIDING_WINDOW_SIZE = 60  # seconds
DISPLAY_INTERVAL = 1  # seconds
BURST_THRESHOLD = 100  # logs per second

# Shared resources
log_queue = queue.Queue()
lock = threading.Lock()

# State
entries_processed = 0
current_rate = 0
peak_rate = 0
error_rate = 0
recent_timestamps = deque(maxlen=10000)
recent_logs = deque(maxlen=100000)

log_types = Counter()
error_patterns = Counter()

def read_logs():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        log_queue.put(line.strip())

def process_log_entry(log_entry):
    global entries_processed
    with lock:
        entries_processed += 1     

        time_match = re.search(r"\[(.*?)\]", log_entry)
        if time_match:
            timestamp = time_match.group(1)
            log_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
            recent_timestamps.append(log_time)
            recent_logs.append(log_entry)

        if "ERROR" in log_entry:
            log_types["ERROR"] += 1
            error_match = re.search(r"ERROR: (.+?)(?:\s|$)", log_entry)
            if error_match:
                error_pattern = error_match.group(1)
                error_patterns[error_pattern] += 1
            else:
                error_patterns["Unknown error"] += 1

        elif "INFO" in log_entry:
            log_types["INFO"] += 1
        elif "DEBUG" in log_entry:
            log_types["DEBUG"] += 1
        else:
            log_types["OTHER"] += 1


def process_logs():
    while True:
        try:
            log_entry = log_queue.get(timeout=0.1)
            process_log_entry(log_entry)
            log_queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            sys.stderr.write(f"Error processing log: {str(e)}\n")    


def parse_log(line):
    try:
        parts = line.split(" ", 4)
        timestamp = parts[0].strip("[]")
        level = parts[1] 
        ip = parts[3].split(":")[1]
        message = parts[4]
        return timestamp, level, ip, message
    except (IndexError, ValueError):
        return None, "UNKNOWN", line

def calculate_rate():
    global current_rate, peak_rate, error_rate
    if len(recent_timestamps) >= 2:
            time_diff = (recent_timestamps[-1] - recent_timestamps[0]).total_seconds()
            if time_diff > 0:
                current_rate = len(recent_timestamps) / time_diff
                
                peak_rate = max(peak_rate, current_rate)

                error_count = sum(1 for log in recent_logs if "ERROR" in log)
                error_rate = error_count / time_diff

def display_stats():
    while True:
        time.sleep(DISPLAY_INTERVAL)
        with lock:

            last_update = datetime.now()
            
            calculate_rate()

            total_logs = sum(log_types.values())
            error_percentage = f"{(log_types.get("ERROR", 0) / total_logs * 100):.0f}" if total_logs else 0
            info_percentage = f"{(log_types.get("INFO", 0) / total_logs * 100):.0f}" if total_logs else 0
            debug_percentage = f"{(log_types.get("DEBUG", 0) / total_logs * 100):.0f}" if total_logs else 0

            top_errors = error_patterns.most_common(3)

            header = f"Log Analysis Report (Last Updated: {last_update.strftime('%Y-%m-%d %H:%M:%S')} UTC)"
            divider = "━" * 70
            print(header)
            print(divider)

            print("Runtime Stats:")
            print(f"Entries processed: {total_logs}")
            print(f"Current rate: {current_rate:.0f} entries/sec (Peak: {peak_rate:.0f} entries/sec))")
            print(f"Adaptive Window: {SLIDING_WINDOW_SIZE} seconds (Adjusted from 60 seconds)")
            print()

            print("Pattern Analysis:")
            print(f"ERROR: {error_percentage}% ({log_types.get('ERROR', 0):,} entries)")
            print(f"INFO: {info_percentage}% ({log_types.get('INFO', 0):,} entries)")
            print(f"DEBUG: {debug_percentage}% ({log_types.get('DEBUG', 0):,} entries)")
            print()


def main():
    threads = [
        threading.Thread(target=read_logs, daemon=True),
        threading.Thread(target=process_logs, daemon=True),
        threading.Thread(target=display_stats, daemon=True),
    ]

    for thread in threads:
        thread.start()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down log analyzer...")


if __name__ == "__main__":
    main()