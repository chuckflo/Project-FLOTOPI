from flask import Flask
import subprocess

app = Flask(__name__)

def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True).strip()
    except Exception:
        return "Unavailable"

@app.route("/")
def dashboard():
    direwolf_status = run("systemctl is-active direwolf")
    on_air = "ON THE AIR" if direwolf_status == "active" else "OFFLINE"
    on_air_class = "ok" if direwolf_status == "active" else "bad"
    boot_status = run("systemctl is-enabled direwolf")
    uptime = run("uptime -p")
    temp = run("vcgencmd measure_temp | cut -d= -f2")
    disk = run("df -h / | awk 'NR==2 {print $5 \" used, \" $4 \" free\"}'")
    memory = run("free -h | awk 'NR==2 {print $3 \" / \" $2}'")
    beacons = run("journalctl -u direwolf.service --since '24 hours ago' --no-pager | grep -c APDW19")
    igate = run("journalctl -u direwolf.service --since '24 hours ago' --no-pager | grep -c '\\[ig'")
    digi = run("journalctl -u direwolf.service --since '24 hours ago' --no-pager | grep -c Digipeater")

    return f"""
    <html>
    <head>
        <title>Project FLOTOPI</title>
        <meta http-equiv="refresh" content="30">
        <style>
         body {{ font-family: Arial, sans-serif; background:#111; color:#eee; padding:30px; }}
         h1 {{ color:#7CFC00; }}
         .card {{ background:#222; padding:20px; margin:15px 0; border-radius:12px; border-left:8px solid #7CFC00; box-shadow:0 0 12px rgba(0,255,0,.15); }}
         .bad {{ color:#ff4d4d; font-weight:bold; }}
         .bigstatus {{ font-size:2em; font-weight:bold; }}        

    .ok {{ color:#7CFC00; font-weight:bold; }}
          .warn {{ color:#FFD700; font-weight:bold; }}
          .value {{ font-size:1.4em; }}
        </style>
    </head>
    <body>
        <h1>🚀 Project FLOTOPI</h1>
        <h2>AK6QN-10</h2>
 .      <h3>APRS iGate • Fill-In Digipeater • GP-3</h3>

        <div class="card">
            <h3>Station</h3>
            <p class="bigstatus"><span class="{on_air_class}">● {on_air}</span></p>
            <p>Status: <span class="{on_air_class}">{direwolf_status}</span></p>
            
            <p>Boot Start: <span class="ok">{boot_status}</span></p>
            <p>Antenna: <span class="value">Comet GP-3</span></p>
        </div>

        <div class="card">
            <h3>APRS Activity - Last 24 Hours</h3>
            <p>Station Beacons: <span class="value">{beacons}</span></p>
            <p>APRS-IS Events: <span class="value">{igate}</span></p>
            <p>Digipeater Lines: <span class="value">{digi}</span></p>
        </div>

        <div class="card">
            <h3>Raspberry Pi</h3>
            <p>Uptime: {uptime}</p>
            <p>CPU Temperature: {temp}</p>
            <p>Disk: {disk}</p>
            <p>Memory: {memory}</p>
        </div>
    </body>
    </html>
    """

app.run(host="0.0.0.0", port=8080)
