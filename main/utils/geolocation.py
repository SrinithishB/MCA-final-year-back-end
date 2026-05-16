import requests

_PRIVATE_PREFIXES = ("127.", "192.168.", "10.", "172.", "::1")

def get_city_from_ip(ip: str) -> str | None:
    if not ip or any(ip.startswith(p) for p in _PRIVATE_PREFIXES):
        return "Chennai"
    try:
        res = requests.get(
            f"http://ip-api.com/json/{ip}?fields=status,city",
            timeout=3
        )
        data = res.json()
        if data.get("status") == "success":
            return data.get("city")
    except Exception:
        pass
    return None
