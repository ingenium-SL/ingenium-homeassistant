# Ingenium Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![License](https://img.shields.io/github/license/ingenium-SL/ingenium-homeassistant)](LICENSE)
[![GitHub release](https://img.shields.io/github/release/ingenium-SL/ingenium-homeassistant)](https://github.com/ingenium-SL/ingenium-homeassistant/releases)

Custom Home Assistant integration for **Ingenium** home automation systems.  
Connects locally via the Ingenium ETH/IP gateway using the local network IP address.

---

## Supported Devices

| Platform | Description |
|----------|-------------|
| `switch` | On/off switches and relays |
| `light`  | Dimmable and binary lights |
| `cover`  | Blinds and shutters |
| `climate`| Thermostat and HVAC zones |
| `sensor` | Temperature, humidity and other sensors |

---

## Requirements

- Home Assistant 2023.1 or later
- An **Ingenium ETH/IP gateway** connected to your local network
- The gateway must be reachable from the Home Assistant host

---

## Installation via HACS

1. Open HACS → **Integrations** → ⋮ menu → **Custom repositories**
2. Add `https://github.com/ingenium-SL/ingenium-homeassistant` as an **Integration**
3. Search for **Ingenium** and install it
4. Restart Home Assistant

---

## Manual Installation

1. Download or clone this repository
2. Copy the `custom_components/ingenium/` folder into your HA `config/custom_components/` directory
3. Restart Home Assistant

---

## Configuration

After installation, add the integration from **Settings → Devices & Services → Add Integration → Ingenium**.

| Field | Description |
|-------|-------------|
| **IP Address / Hostname** | The local IP address (or hostname) of your Ingenium ETH/IP gateway (e.g. `192.168.1.100`) |

The integration connects directly to the gateway on your local network. No cloud account or internet access is required.

---

## Troubleshooting

- Make sure the Ingenium gateway is powered on and reachable from the Home Assistant host (`ping <gateway-ip>`).
- If entities do not appear after setup, check the HA logs for errors from the `ingenium` integration.
- After changing the gateway IP, remove and re-add the integration.

---

## License

[Apache 2.0](LICENSE) © Ingenium SL
