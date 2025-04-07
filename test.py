from API.convert_irt_to_usd import price


def create_json_config(username, expiration_in_day, traffic_in_byte, service_uuid, org_traffic, status="active"):
    config = {
        "username": username,
        "proxies": {
            "vless": {
                "id": service_uuid
            },
            "vmess": {
                "id": service_uuid
            },
            "trojan": {
                "password": service_uuid
            },
            "shadowsocks": {
                "password": service_uuid
            },
        },
        "inbounds": {
            "vless": [
                "VLESS TCP",
                "VLESS TCP REALITY",
                "VLESS GRPC REALITY"
            ],
            "vmess": [
                "VMess TCP",
                "VMess Websocket",
            ],
            "trojan": [
                "Trojan Websocket TLS",
            ],
            "shadowsocks": [
                "Shadowsocks TCP 2"
            ],
        },
        "expire": expiration_in_day,
        "data_limit": traffic_in_byte,
        "data_limit_reset_strategy": "no_reset",
        "status": status,
        "note": "",
        "on_hold_timeout": "2023-11-03T20:30:00",
        "on_hold_expire_duration": 0
    }
    if org_traffic >= 30 * 1024 ** 3:
        config["inbounds"]["shadowsocks"].append("Shadowsocks TCP")
    print(config)

create_json_config('', 1, 1, 1, 30 * 1024 ** 3)