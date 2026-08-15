import json
import os
import subprocess
import time

import psutil

def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return r.stdout.strip() if r.returncode == 0 else None


def host_state(event_time=None):
    disk = psutil.disk_usage("/")
    mem = psutil.virtual_memory()

    if event_time is not None:
        start = int(event_time) - 120
        end = int(event_time) + 10
        kernel_cmd = ["journalctl", "-k", "-S", f"@{start}", "-U", f"@{end}"]
        window = {"start": start, "end": end}
    else:
        kernel_cmd = ["journalctl", "-k", "-S", "-2min"]
        window = None

    return {
        "disk": {
            "total_gb": round(disk.total / 1e9, 1),
            "free_gb": round(disk.free / 1e9, 1),
            "percent_used": disk.percent,
        },
        "memory": {
            "total_mb": round(mem.total / 1e6),
            "available_mb": round(mem.available / 1e6),
            "percent_used": mem.percent,
        },
        "load_avg": os.getloadavg(),
        "boot_time": psutil.boot_time(),
        "kernel_window": window,
        "kernel_messages": _run(kernel_cmd),
    }


def container_state(container):
    a = container.attrs
    state = a.get("State", {})
    config = a.get("Config", {})
    host_config = a.get("HostConfig", {})

    return {
        "name": a.get("Name", "").lstrip("/"),
        "id": a.get("Id", ""),
        "short_id": a.get("Id", "")[:12],
        "image": config.get("Image"),
        "exit_code": state.get("ExitCode"),
        "oom_killed": state.get("OOMKilled"),
        "error": state.get("Error"),
        "started_at": state.get("StartedAt"),
        "finished_at": state.get("FinishedAt"),
        "restart_count": a.get("RestartCount"),
        "restart_policy": host_config.get("RestartPolicy", {}).get("Name"),
        "memory_limit": host_config.get("Memory"),
        "env": config.get("Env"),
        "cmd": config.get("Cmd"),
        "entrypoint": config.get("Entrypoint"),
        "mounts": [
            {
                "source": m.get("Source"),
                "destination": m.get("Destination"),
                "mode": m.get("Mode"),
                "rw": m.get("RW"),
            }
            for m in a.get("Mounts", [])
        ],
    }


def container_logs(container, lines=100):
    raw = container.logs(tail=lines)
    return raw.decode("utf-8", errors="replace")


def collect(client, event, outdir="incidents"):
    container_id = event["Actor"]["ID"]
    name = event["Actor"]["Attributes"].get("name", "unknown")

    bundle = {
        "incident_id": f"{name}-{event['time']}",
        "event_time": event["time"],
        "collected_at": time.time(),
        "container": None,
        "logs": None,
        "host": host_state(event["time"])
    }

    container = client.containers.get(container_id)
    bundle["container"] = container_state(container)
    bundle["logs"] = container_logs(container)

    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"{bundle['incident_id']}.json")
    with open(path, "w") as f:
        json.dump(bundle, f, indent=2)

    return path