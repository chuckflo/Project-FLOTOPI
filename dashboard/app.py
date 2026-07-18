from flask import Flask, render_template
import subprocess

app = Flask(__name__)

DASHBOARD_VERSION = "3.0.0"


def run(command):
    """Run a shell command and return its output."""
    try:
        return subprocess.check_output(
            command,
            shell=True,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=10
        ).strip()
    except Exception:
        return "Unavailable"


@app.route("/")
def dashboard():

    direwolf_status = run("systemctl is-active direwolf")
    boot_status = run("systemctl is-enabled direwolf")

    on_air = "ON THE AIR" if direwolf_status == "active" else "OFFLINE"
    status_class = "good" if direwolf_status == "active" else "bad"

    uptime = run("uptime -p")
    temperature = run("vcgencmd measure_temp | cut -d= -f2")
    disk = run("""df -h / | awk 'NR==2 {print $5 " used, " $4 " free"}'""")
    memory = run("""free -h | awk 'NR==2 {print $3 " used / " $2}'""")

    beacons = run(
        "journalctl -u direwolf.service --since '24 hours ago' "
        "--no-pager | grep -c APDW19"
    )

    igate_events = run(
        "journalctl -u direwolf.service --since '24 hours ago' "
        "--no-pager | grep -c '\\[ig'"
    )

    digipeater_events = run(
        "journalctl -u direwolf.service --since '24 hours ago' "
        "--no-pager | grep -c Digipeater"
    )

    return render_template(
        "index.html",
        version=DASHBOARD_VERSION,
        callsign="AK6QN-10",
        direwolf_status=direwolf_status,
        boot_status=boot_status,
        on_air=on_air,
        status_class=status_class,
        uptime=uptime,
        temperature=temperature,
        disk=disk,
        memory=memory,
        beacons=beacons,
        igate_events=igate_events,
        digipeater_events=digipeater_events,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081, debug=False)
