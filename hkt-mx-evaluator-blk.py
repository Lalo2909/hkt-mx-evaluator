import argparse
import os
import re
import shutil
import json
import subprocess
import time
import socket
import platform
from http.client import HTTPConnection
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stdout.reconfigure(line_buffering=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Clean logs
log_dir = os.path.join(BASE_DIR, 'logs')
if os.path.exists(log_dir):
    shutil.rmtree(log_dir)
os.makedirs(log_dir, exist_ok=True)

# Paths And Files
TEST_CASES_PATH = os.path.join(BASE_DIR, 'test_cases')
SHELL_SCRIPTS_PATH = os.path.join(BASE_DIR, 'shell_scripts')
SHELL_DIR = "shell_scripts"

# Config
PORT = 5477
PROJECT_REGEX = r"blk-hacking-mx-([A-Za-z\-]+)"
TIME_OUT = 10  # seconds

# Weights for scoring
WEIGHTS = {"http": 0.3, "structure": 0.3, "value": 0.4}
END_POINT_WEIGHT = 20

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0

def extract_participant_name(name):
    match = re.match(PROJECT_REGEX, name)
    if match and match.group(1):
        return match.group(1).replace("-", " ")
    return name

def run_shell(script, args):
    if platform.system() == "Windows":
        shell_path = os.path.join(SHELL_DIR, script)
        subprocess.run(["cmd.exe", "/c", shell_path] + args, capture_output=True, text=True, encoding="utf-8")
    else:
        shell_path = "/bin/bash" if os.path.exists("/bin/bash") else "/bin/sh"
        subprocess.run([shell_path, os.path.join(SHELL_DIR, script)] + args, capture_output=True, text=True, encoding="utf-8")

def is_container_running(image_name, initial_interval=0.2, max_interval=1.0):
    """Waits up to `timeout` seconds for the container to be running, with exponential backoff."""
    start = time.time()
    interval = initial_interval
    while time.time() - start < TIME_OUT:
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={image_name}", "--format", "{{.Names}}"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
            )
            running = result.stdout.strip().splitlines()
            if image_name in running:
                return True
        except subprocess.CalledProcessError as e:
            print(f"Error checking container status: {e}")
            return False
        time.sleep(interval)
        interval = min(interval * 2, max_interval)
    return False

def stop_container(image_name):
    if platform.system() == "Windows":
        shell_path = os.path.join(SHELL_DIR, "clean_container.sh")
        subprocess.run(["cmd.exe", "/c", shell_path, image_name], capture_output=True)
    else:
        shell_path = "/bin/bash" if os.path.exists("/bin/bash") else "/bin/sh"
        subprocess.run([shell_path, os.path.join(SHELL_DIR, "clean_container.sh"), image_name], capture_output=True)

def load_test_cases():
    cases = []
    for filename in sorted(os.listdir(TEST_CASES_PATH)):
        file_path = os.path.join(TEST_CASES_PATH, filename)
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                cases.append(json.load(f))
    return cases

def call_endpoint(method, path, data=None):
    conn = HTTPConnection("localhost", PORT, timeout=10)
    headers = {"Content-Type": "application/json"}
    try:
        if method == "POST":
            conn.request("POST", path, body=json.dumps(data), headers=headers)
        else:
            conn.request("GET", path, headers=headers)
        resp = conn.getresponse()
        return resp.status, json.loads(resp.read().decode())
    except Exception as e:
        return 500, {"error": str(e)}
    finally:
        conn.close()

def validate_response(expected, actual, is_performance=False):

    score = 0
    messages = []

    if actual is None or not isinstance(actual, dict):
        return 0, "Invalid or no JSON response"

    # HTTP status assumed already checked
    score += WEIGHTS["http"]
    messages.append("✔ HTTP 200")

    # Check structure
    if set(expected.keys()).issubset(actual.keys()):
        score += WEIGHTS["structure"]
        messages.append("✔ JSON structure valid")
    else:
        messages.append("✘ JSON structure mismatch")

    # Check value match (only if not performance)
    if not is_performance:
        mismatch = False
        for k, v in expected.items():
            if actual.get(k) != v:
                mismatch = True
                break
        if not mismatch:
            score += WEIGHTS["value"]
            messages.append("✔ Values match")
        else:
            messages.append("✘ Values do not match")
    else:
        score += WEIGHTS["value"]
        messages.append("✔ Values match")

    return round(score * END_POINT_WEIGHT), "; ".join(messages)

def evaluate_submission(path):
    name = os.path.basename(path).replace(".tar", "")
    participant = extract_participant_name(name)
    image_name = name
    log_file = os.path.join(log_dir, f"{name}.log")
    result = {"participant": participant, "project": name}

    print(f"🚀 Evaluating submission: {participant} - {name}")

    with open(log_file, "w", encoding="utf-8") as log:
        if is_port_in_use(PORT):
            log.write(f"❌ Port [{PORT}] is in use.\n")
            print("❌ Port [{PORT}] is in use.")
            return

        if os.path.isdir(path):
            print(f"📦 Building and running project directory...\n")
            run_shell("build_and_run.sh", [path, image_name])
        elif path.endswith(".tar"):
            print(f"📦 Loading and running Docker image...")
            run_shell("load_and_run.sh", [path, image_name])
        else:
            log.write("❌ Invalid format\n")
            print("❌ Invalid format")
            return

        if not is_container_running(image_name):
            log.write(f"❌ Container [{image_name}] is not running.\n")
            print(f"❌ Container [{image_name}] is not running.")
            return

        total_score = 0
        test_cases = load_test_cases()

        try:
            for case in test_cases:
                try:
                    method = case.get("method")
                    path_ep = case.get("path")
                    input_data = case.get("input")
                    expected = case.get("expected_output")
                    is_performance = str(path_ep).endswith("performance")

                    print(f"📡 Sending {method}:{path_ep} request...")
                    status, response = call_endpoint(method, path_ep, input_data)
                    print(f"📬 Received  status code: {status}")

                    if status != 200:
                        log.write(f"[FAIL] {method}:{path_ep} - HTTP {status}\n")
                        print(f"❌ HTTP error at {method}:{path_ep} - {status}")
                        continue

                    points, message = validate_response(expected, response, is_performance)
                    total_score += points

                    log.write("----------------------------------------------------------------------\n")
                    log.write(f"Endpoint: {method}:{path_ep} - HTTP {status}\n")
                    log.write(f"[{points}/20] {path_ep} - {message}\n\n")
                    log.write(f"Expected JSON:\n{json.dumps(expected, ensure_ascii=False, indent=2)}\n")
                    log.write(f"Actual JSON:\n{json.dumps(response, ensure_ascii=False, indent=2)}\n")
                    log.write("----------------------------------------------------------------------\n")

                    print(f"📊 {method}:{path_ep} Score: {points}/20 - {message}")

                except Exception as e:
                    log.write(f"[ERROR] {case['path']} - {e}\n")
                    print(f"💥 Error on {case['path']}: {e}")

            result["score"] = total_score
            print(f"\n✅ Total score for {participant} - {name}: [{total_score}/100]")
            log.write(f"Total Score: {total_score}/100\n")

        finally:
            print(f"🚀 Stopping submission {participant} - {name} ...\n")
            stop_container(image_name)

    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="deliveries", help="Folder with Docker submissions")
    args = parser.parse_args()

    submissions = [os.path.join(args.dir, f) for f in os.listdir(args.dir)]
    results = [evaluate_submission(s) for s in submissions]
    with open(os.path.join(BASE_DIR, "hkt-mx-blk-results.csv"), "w", encoding="utf-8") as f:
        f.write("participant,project,score\n")
        for r in results:
            if r is not None:
                f.write(f"{r['participant']},{r['project']},{r['score']}\n")

if __name__ == "__main__":
    main()
