#!/usr/bin/env python3
import os
import signal
import subprocess
import threading
import time
from flask import Flask, request, render_template_string, jsonify

app = Flask(__name__)

# ------------------ Global variable to track current attack process ------------------
current_process = None
current_attack_info = None
process_lock = threading.Lock()

# ------------------ HTML Template (Updated with Stop Button) ------------------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Notica · Stress Test</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Roboto, system-ui, sans-serif;
        }
        body {
            background: #0b0f17;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }
        .card {
            max-width: 1000px;
            width: 100%;
            background: #131a2c;
            border-radius: 28px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6), 0 0 0 1px #2a3a55 inset;
            color: #e0e5f0;
        }
        .warning {
            background: #1e2a3a;
            border-left: 6px solid #f0b400;
            border-radius: 18px;
            padding: 16px 22px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 30px;
        }
        .warning p {
            font-size: 1.1rem;
            font-weight: 500;
            color: #ffd966;
        }
        .ok-btn {
            background: #2d405b;
            border: none;
            color: white;
            font-weight: 600;
            font-size: 1rem;
            padding: 8px 28px;
            border-radius: 40px;
            cursor: pointer;
        }
        .ok-btn:hover {
            background: #3e5577;
        }
        .input-row {
            background: #101826;
            border-radius: 60px;
            padding: 20px 30px;
            margin-bottom: 25px;
            border: 1px solid #2b3f5c;
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            align-items: center;
            justify-content: space-between;
        }
        .input-group {
            display: flex;
            align-items: center;
            gap: 10px;
            background: #1b253c;
            padding: 8px 20px;
            border-radius: 40px;
        }
        .input-group label {
            font-weight: 600;
            color: #a5c1ff;
        }
        .input-group input {
            background: transparent;
            border: 1px solid #3f5a82;
            color: white;
            padding: 8px 15px;
            border-radius: 30px;
            width: 140px;
            font-size: 1rem;
        }
        .input-group input:focus {
            outline: none;
            border-color: #5f8aff;
        }
        .action-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #101826;
            border-radius: 60px;
            padding: 12px 25px 12px 30px;
            margin-bottom: 35px;
            border: 1px solid #2b3f5c;
            gap: 15px;
        }
        .concurrent-box {
            display: flex;
            align-items: center;
        }
        .concurrent-label {
            font-size: 1.4rem;
            font-weight: 600;
            color: #b7c9e2;
        }
        .concurrent-number {
            font-size: 2rem;
            font-weight: 800;
            background: linear-gradient(145deg, #a3c6ff, #5b8cff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-left: 12px;
        }
        .button-group {
            display: flex;
            gap: 15px;
        }
        .send-btn {
            background: linear-gradient(145deg, #2658b8, #103780);
            border: none;
            color: white;
            font-size: 1.5rem;
            font-weight: 700;
            padding: 14px 38px;
            border-radius: 60px;
            cursor: pointer;
            box-shadow: 0 10px 18px rgba(0, 30, 100, 0.6);
            border: 1px solid #3f7eff;
            transition: 0.2s;
            min-width: 220px;
        }
        .send-btn:hover:not(:disabled) {
            background: linear-gradient(145deg, #2f6be0, #154ab0);
            transform: scale(1.02);
        }
        .stop-btn {
            background: linear-gradient(145deg, #b82222, #780000);
            border: none;
            color: white;
            font-size: 1.5rem;
            font-weight: 700;
            padding: 14px 38px;
            border-radius: 60px;
            cursor: pointer;
            box-shadow: 0 10px 18px rgba(100, 0, 0, 0.6);
            border: 1px solid #ff4f4f;
            transition: 0.2s;
            min-width: 220px;
        }
        .stop-btn:hover:not(:disabled) {
            background: linear-gradient(145deg, #d83232, #a00000);
            transform: scale(1.02);
        }
        .send-btn:disabled, .stop-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        .history-title {
            font-size: 1.8rem;
            font-weight: 600;
            margin-bottom: 18px;
            color: #d0ddff;
            border-bottom: 2px solid #253449;
            padding-bottom: 8px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: #0f172b;
            border-radius: 24px;
            overflow: hidden;
            margin-bottom: 35px;
            border: 1px solid #2a3850;
        }
        th {
            text-align: left;
            padding: 16px 18px;
            background: #1d2a41;
            color: #a5c1ff;
            font-weight: 600;
        }
        td {
            padding: 16px 18px;
            border-top: 1px solid #25344a;
            color: #cdddfa;
        }
        .status-active {
            background: #1e3b2e;
            color: #7cf9b0;
            font-weight: 600;
            padding: 6px 14px;
            border-radius: 40px;
            display: inline-block;
        }
        .status-stopped {
            background: #3b2e2e;
            color: #f97c7c;
            font-weight: 600;
            padding: 6px 14px;
            border-radius: 40px;
            display: inline-block;
        }
        .upgrade-box {
            background: linear-gradient(145deg, #1e2640, #131b30);
            border-radius: 30px;
            padding: 24px 30px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 30px;
            border: 1px solid #4a6085;
        }
        .upgrade-text {
            font-size: 1.6rem;
            font-weight: 700;
            background: linear-gradient(145deg, #ffe791, #ccb055);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .upgrade-btn {
            background: #fedb5f;
            border: none;
            color: #0b0f17;
            font-weight: 800;
            font-size: 1.3rem;
            padding: 16px 40px;
            border-radius: 60px;
            cursor: pointer;
            border: 1px solid #ffed9e;
        }
        .slots-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #0e1629;
            border-radius: 80px;
            padding: 20px 30px;
            border: 1px solid #364b6e;
        }
        .slots-label {
            font-size: 1.4rem;
            font-weight: 600;
            color: #a3bbdc;
        }
        .slots-numbers {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(145deg, #bbd4ff, #7faaef);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .in-use {
            background: #1f334e;
            padding: 12px 30px;
            border-radius: 60px;
            font-size: 1.3rem;
            color: #b5d0ff;
            border: 1px solid #4f71a5;
        }
        .hidden {
            display: none;
        }
        .status-badge {
            font-size: 1rem;
            margin-left: 20px;
            background: #2a3f5a;
            padding: 8px 18px;
            border-radius: 40px;
        }
    </style>
</head>
<body>
    <div class="card">
        <!-- Warning banner -->
        <div class="warning" id="warningBanner">
            <p>⚠️ Match server response timed out. Please check your network.</p>
            <button class="ok-btn" id="dismissWarning">OK</button>
        </div>

        <!-- Input fields for IP, Port, Time -->
        <div class="input-row">
            <div class="input-group">
                <label>IP:</label>
                <input type="text" id="targetIp" placeholder="127.0.0.1" value="127.0.0.1">
            </div>
            <div class="input-group">
                <label>Port:</label>
                <input type="number" id="targetPort" placeholder="8080" value="8080">
            </div>
            <div class="input-group">
                <label>Time (s):</label>
                <input type="number" id="attackTime" placeholder="60" value="60">
            </div>
            <span class="status-badge" id="attackStatus">⚪ Idle</span>
        </div>

        <!-- Action Row: Concurrents + Start/Stop buttons -->
        <div class="action-row">
            <div class="concurrent-box">
                <span class="concurrent-label">Concurrents</span>
                <span class="concurrent-number">1</span>
            </div>
            <div class="button-group">
                <button class="send-btn" id="sendAttackBtn">🚀 START ATTACK</button>
                <button class="stop-btn" id="stopAttackBtn">🛑 STOP ATTACK</button>
            </div>
        </div>

        <!-- History table -->
        <div class="history-title">⚡ History</div>
        <table id="historyTable">
            <thead>
                <tr>
                    <th>Target</th>
                    <th>Method</th>
                    <th>Time</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody id="historyBody">
                <!-- Sample static row -->
                <tr>
                    <td>20.198.82.124:26635</td>
                    <td>UDP-FREE</td>
                    <td>120s</td>
                    <td><span class="status-active">1:49</span></td>
                </tr>
            </tbody>
        </table>

        <!-- Upgrade section -->
        <div class="upgrade-box">
            <span class="upgrade-text">🚀 Upgrade for 10x Power</span>
            <button class="upgrade-btn" id="upgradeBtn">UPGRADE NOW</button>
        </div>

        <!-- Network slots -->
        <div class="slots-container">
            <span class="slots-label">Free Network</span>
            <span class="slots-numbers">9 / 10</span>
            <span class="in-use">1 in use</span>
        </div>
    </div>

    <script>
        // DOM elements
        const warningBanner = document.getElementById('warningBanner');
        const dismissBtn = document.getElementById('dismissWarning');
        const sendBtn = document.getElementById('sendAttackBtn');
        const stopBtn = document.getElementById('stopAttackBtn');
        const attackStatus = document.getElementById('attackStatus');
        const historyBody = document.getElementById('historyBody');
        
        // State
        let attackActive = false;

        // Dismiss warning
        dismissBtn.addEventListener('click', () => {
            warningBanner.classList.add('hidden');
        });

        // Upgrade button demo
        document.getElementById('upgradeBtn').addEventListener('click', () => {
            alert('✨ Upgrade feature – demo only.');
        });

        // Helper to add history entry
        function addHistoryEntry(ip, port, time, statusText, statusClass) {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${ip}:${port}</td>
                <td>UDP-FREE</td>
                <td>${time}s</td>
                <td><span class="${statusClass}">${statusText}</span></td>
            `;
            historyBody.prepend(row);
        }

        // Update UI based on attack state
        function setAttackState(active) {
            attackActive = active;
            if (active) {
                attackStatus.innerHTML = '🟢 Attack Running';
                attackStatus.style.background = '#1e3b2e';
                sendBtn.disabled = true;
                stopBtn.disabled = false;
            } else {
                attackStatus.innerHTML = '⚪ Idle';
                attackStatus.style.background = '#2a3f5a';
                sendBtn.disabled = false;
                stopBtn.disabled = true;
            }
        }

        // Initial state
        setAttackState(false);

        // Start attack
        sendBtn.addEventListener('click', () => {
            const ip = document.getElementById('targetIp').value.trim();
            const port = document.getElementById('targetPort').value.trim();
            const time = document.getElementById('attackTime').value.trim();

            if (!ip || !port || !time) {
                alert('Please fill IP, Port and Time');
                return;
            }

            // Disable button
            sendBtn.disabled = true;
            sendBtn.innerText = '⏳ STARTING...';

            fetch('/attack', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ip, port, time })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'started') {
                    setAttackState(true);
                    addHistoryEntry(ip, port, time, 'started', 'status-active');
                } else {
                    alert('Error: ' + data.message);
                    setAttackState(false);
                }
            })
            .catch(err => {
                alert('Network error: ' + err);
                setAttackState(false);
            })
            .finally(() => {
                sendBtn.innerText = '🚀 START ATTACK';
                // If attack didn't start, re-enable
                if (!attackActive) sendBtn.disabled = false;
            });
        });

        // Stop attack
        stopBtn.addEventListener('click', () => {
            if (!attackActive) {
                setAttackState(false);
                return;
            }

            stopBtn.disabled = true;
            stopBtn.innerText = '⏳ STOPPING...';

            fetch('/stop', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'stopped') {
                    setAttackState(false);
                    // Add a stopped entry if we have last attack info
                    if (data.last_attack) {
                        addHistoryEntry(
                            data.last_attack.ip, 
                            data.last_attack.port, 
                            data.last_attack.time, 
                            'stopped (manual)', 
                            'status-stopped'
                        );
                    }
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(err => {
                alert('Network error: ' + err);
            })
            .finally(() => {
                stopBtn.innerText = '🛑 STOP ATTACK';
                stopBtn.disabled = !attackActive; // Re-disable if still active (unlikely)
            });
        });

        // Optional: Periodically check attack status (simple polling)
        setInterval(() => {
            fetch('/status')
                .then(res => res.json())
                .then(data => {
                    setAttackState(data.active);
                })
                .catch(() => {});
        }, 2000);
    </script>
</body>
</html>
"""

# ------------------ Flask routes ------------------
BINARY_PATH = os.path.join(os.path.dirname(__file__), "ultra")

# Ensure binary exists
if not os.path.isfile(BINARY_PATH):
    print(f"❌ Error: binary '{BINARY_PATH}' not found.")
    print("Please place the 'ultra' binary in the same folder as this script.")
    exit(1)

if not os.access(BINARY_PATH, os.X_OK):
    print("🔧 Making 'ultra' executable...")
    os.chmod(BINARY_PATH, 0o755)

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/attack', methods=['POST'])
def attack():
    global current_process, current_attack_info
    data = request.get_json()
    ip = data.get('ip')
    port = data.get('port')
    time_sec = data.get('time')
    threads = 800

    if not ip or not port or not time_sec:
        return jsonify({'status': 'error', 'message': 'Missing parameters'}), 400

    with process_lock:
        # If there's already an attack running, don't start another
        if current_process and current_process.poll() is None:
            return jsonify({'status': 'error', 'message': 'Attack already running. Stop it first.'}), 409

        # Build command: assuming binary takes <IP> <PORT> <TIME> <THREADS>
        cmd = [BINARY_PATH, ip, str(port), str(time_sec), str(threads)]

        def run_attack():
            global current_process, current_attack_info
            try:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                with process_lock:
                    current_process = process
                    current_attack_info = {'ip': ip, 'port': port, 'time': time_sec}
                # Wait for completion (binary will run for 'time_sec' seconds)
                stdout, stderr = process.communicate()
                print(f"Attack finished: {ip}:{port} for {time_sec}s")
            except Exception as e:
                print(f"Error in attack thread: {e}")
            finally:
                with process_lock:
                    current_process = None
                    current_attack_info = None

        thread = threading.Thread(target=run_attack)
        thread.daemon = True
        thread.start()

    return jsonify({'status': 'started', 'message': 'Attack launched in background'})

@app.route('/stop', methods=['POST'])
def stop_attack():
    global current_process, current_attack_info
    with process_lock:
        if current_process and current_process.poll() is None:
            # Terminate the process
            current_process.terminate()
            # Give it a moment to terminate, then kill if needed
            time.sleep(1)
            if current_process.poll() is None:
                current_process.kill()
            
            # Store last attack info before clearing
            last_attack = current_attack_info.copy() if current_attack_info else None
            
            current_process = None
            current_attack_info = None
            
            return jsonify({
                'status': 'stopped', 
                'message': 'Attack stopped',
                'last_attack': last_attack
            })
        else:
            return jsonify({'status': 'error', 'message': 'No active attack to stop'}), 404

@app.route('/status', methods=['GET'])
def status():
    with process_lock:
        active = current_process is not None and current_process.poll() is None
        return jsonify({'active': active})

if __name__ == '__main__':
    print("=" * 60)
    print("🔥 Starting Notica Web Interface with STOP button")
    print(f"📁 Binary path: {BINARY_PATH}")
    print("🌐 Open http://127.0.0.1:5000 in your browser")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
