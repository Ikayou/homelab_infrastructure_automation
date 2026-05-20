def calculate_memory_percent(stats):
    memory_usage = stats["memory_stats"].get("usage", 0)
    memory_limit = stats["memory_stats"].get("limit", 0)

    if memory_limit > 0:
        return (memory_usage / memory_limit) * 100

    return 0


def calculate_cpu_percent(stats):
    cpu_delta = (
        stats["cpu_stats"]["cpu_usage"]["total_usage"]
        - stats["precpu_stats"]["cpu_usage"]["total_usage"]
    )

    system_delta = (
        stats["cpu_stats"]["system_cpu_usage"]
        - stats["precpu_stats"]["system_cpu_usage"]
    )

    cpu_count = len(stats["cpu_stats"]["cpu_usage"].get("percpu_usage", []))

    if system_delta > 0 and cpu_delta > 0 and cpu_count > 0:
        return (cpu_delta / system_delta) * cpu_count * 100

    return 0


def build_alerts(container, memory_percent):
    alerts = []

    if container.status != "running":
        alerts.append("container is not running")

    if memory_percent > 80:
        alerts.append("memory usage is high")

    return alerts