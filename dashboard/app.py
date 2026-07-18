from datetime import datetime
import subprocess

from flask import Flask, render_template

app = Flask(__name__)

DASHBOARD_VERSION = "3.1.0"


def run(command):
    """Run a shell command and return its output."""
    try:
        return subprocess.check_output(
            command,
            shell=True,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=10,
        ).strip()
    except Exception:
        return "Unavailable"


def command_succeeded(command):
    """Return True when a shell command finds the expected condition."""
    try:
        subprocess.check_output(
            command,
            shell=True,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
        return True
    except Exception:
        return False


@app.route("/")
def dashboard():
    direwolf_status = run("systemctl is-active direwolf")
    boot_status = run("systemctl is-enabled direwolf")

    direwolf_healthy = direwolf_status == "active"
    autostart_healthy = boot_status == "enabled"
 
    aprsis_healthy = command_succeeded(
    "journalctl -u direwolf.service --since '24 hours ago' "
    "--no-pager | grep -q '\\[ig>tx\\]'"
)


    digipeater_healthy = command_succeeded(
    "journalctl -u direwolf.service --since '24 hours ago' "
    "--no-pager | grep -q 'Digipeater'"
)
    overall_healthy = all(
        [
            direwolf_healthy,
            aprsis_healthy,
            digipeater_healthy,
            autostart_healthy,
        ]
    )

    on_air = "OPERATIONAL" if overall_healthy else "ATTENTION NEEDED"
    status_class = "good" if overall_healthy else "bad"

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

    updated_at = datetime.now().strftime("%A, %B %-d, %Y · %-I:%M:%S %p")

    return render_template(
        "index.html",
        version=DASHBOARD_VERSION,
        callsign="AK6QN-10",
        direwolf_status=direwolf_status,
        boot_status=boot_status,
        direwolf_healthy=direwolf_healthy,
        aprsis_healthy=aprsis_healthy,
        digipeater_healthy=digipeater_healthy,
        autostart_healthy=autostart_healthy,
        on_air=on_air,
        status_class=status_class,
        uptime=uptime,
        temperature=temperature,
        disk=disk,
        memory=memory,
        beacons=beacons,
        igate_events=igate_events,
        digipeater_events=digipeater_events,
        updated_at=updated_at,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081, debug=False)
