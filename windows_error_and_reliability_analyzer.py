import os
import re
import datetime

def get_windows_event_logs(log_types=None, output_dir="logs"):
    """
    Exports specified types of Windows logs using wevtutil.
    Returns a list of exported log file paths.
    """
    if os.name != "nt":
        print("Script must be run on Windows.")
        return []
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if log_types is None:
        log_types = ["System", "Application"]
    output_files = []
    for log_type in log_types:
        log_file = os.path.join(output_dir, f"{log_type}_event_logs.txt")
        log_cmd = f'wevtutil qe {log_type} /f:text > "{log_file}"'
        os.system(log_cmd)
        output_files.append(log_file)
    return output_files

def get_reliability_history(output_file="logs/reliability_monitor.txt"):
    """
    Exports reliability history using PowerShell.
    """
    ps_script = (
        'powershell.exe "Get-WinEvent -FilterHashtable @{LogName=\'System\'; Id=1001} |'
        ' Select-Object -Property TimeCreated,Message |'
        f' Format-Table -AutoSize | Out-File \'{output_file}\'"'
    )
    os.system(ps_script)
    return output_file

def parse_logs(log_files):
    """
    Parses log files for Error, Fatal, Critical events.
    """
    errors = []
    event_levels = ["Error", "Critical", "Fatal"]
    for log_file in log_files:
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        events = re.split(r"\n\n+", content)
        for event in events:
            if any(f"Level: {lvl}" in event for lvl in event_levels):
                error = {}
                for line in event.split("\n"):
                    if line.startswith("Date:"):
                        error["date"] = line.replace("Date: ", "").strip()
                    if line.startswith("Time:"):
                        error["time"] = line.replace("Time: ", "").strip()
                    if line.startswith("Source:"):
                        error["source"] = line.replace("Source: ", "").strip()
                    if line.startswith("Event ID:"):
                        error["event_id"] = line.replace("Event ID: ", "").strip()
                    if line.startswith("Description:"):
                        error["description"] = line.replace("Description: ", "").strip()
                error["level"] = next((lvl for lvl in event_levels if f"Level: {lvl}" in event), "Unknown")
                errors.append(error)
    return errors

def parse_reliability_log(log_file):
    """
    Parses reliability monitor log.
    """
    reliability_events = []
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    for line in lines:
        if "TimeCreated" in line or "Message" in line:
            continue
        reliability_events.append(line.strip())
    return reliability_events

def suggest_solution(error):
    """
    Provides solutions for common fatal/error event IDs.
    """
    solutions = {
        "41": "Kernel-Power: System rebooted unexpectedly. Check for hardware issues, power supply, and overheating.",
        "7000": "Service Control Manager: A service failed to start. Check service dependencies and try restarting the service.",
        "10016": "DistributedCOM: Permission issue. Use Component Services to set correct permissions for the CLSID/AppID.",
        "101": "Application Hang: Update/reinstall the app, check for conflicting software.",
        "55": "NTFS: File system corruption. Run CHKDSK and check disk health.",
        "2019": "SRV: Server unable to allocate memory. Increase system memory or check for leaks.",
        "1001": "Windows Error Reporting: Review application crash details, update/reinstall problematic software.",
    }
    solution = solutions.get(error.get("event_id", ""), "No direct solution found. Search Microsoft Docs or relevant forums with the Event ID.")
    return solution

def main():
    log_files = get_windows_event_logs(log_types=["System", "Application"])
    reliability_log = get_reliability_history()
    log_files.append(reliability_log)
    errors = parse_logs(log_files)
    reliability_events = parse_reliability_log(reliability_log)

    print(f"Found {len(errors)} error(s)/fatal/critical events.\n")
    for idx, error in enumerate(errors, 1):
        print(f"Event #{idx}:")
        print(f"Date: {error.get('date', '')} Time: {error.get('time', '')}")
        print(f"Source: {error.get('source', '')}")
        print(f"Event ID: {error.get('event_id', '')}")
        print(f"Level: {error.get('level', '')}")
        print(f"Description: {error.get('description', '')}")
        print(f"Suggested Solution: {suggest_solution(error)}\n{'-'*60}\n")

    print("Reliability Monitor Events:")
    for event in reliability_events[-10:]:  # Show last 10 reliability events
        print(event)

if __name__ == "__main__":
    main()
