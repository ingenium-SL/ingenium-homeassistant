# Ingenium Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)

Integration for **Ingenium** home automation systems (BUSing & KNX) in Home Assistant.

This component connects to your local Ingenium IP gateway or remote Ingenium cloud account and automatically discovers and integrates all your configured installation devices into Home Assistant.

---

## Supported Platforms & Devices

| Platform | Domain | Description | Models / Codes |
| :--- | :--- | :--- | :--- |
| **Switches** | `switch` | Relays, on/off actuators, smart outlets with power consumption | COD2E2S, COD4E4S, COD6E6S, COD_KCTR, T_KNX_ONOFF |
| **Lights** | `light` | Dimmers and regulators with smooth brightness adjustment | COD2S300, CODRB1500, CODRF10A, COD_T_KNX_DIMMER |
| **Covers** | `cover` | Motorized blinds, shutters, and venetians with positioning | Actuator blinds (Icon 5), T_KNX_BLIND |
| **Climate** | `climate` | Thermostats with heating, cooling, setpoint & humidity | COD_TRMD, COD_MEC_BUS, COD_TEC_ING, COD_TEC_BUS, COD_INTERNAL_THERMOSTAT, COD_DANFOSS |
| **Sensors** | `sensor` | Energy monitors (MeterBus), Multi-sensors (SIF), Air Quality | MeterBus channels, SIF (Temp/Lux/Hum), CO2 & VOCs |

---

## Installation

### Method 1: Via HACS (Recommended)

1. Ensure [HACS (Home Assistant Community Store)](https://hacs.xyz/) is installed.
2. In Home Assistant, open **HACS** > **Integrations**.
3. Click the three dots in the top right corner and select **Custom repositories**.
4. Paste the URL of this repository:
   ```text
   https://github.com/ingeniumsl/homeassistant-ingenium
   ```
5. Select category: **Integration** and click **Add**.
6. Search for `Ingenium`, click **Download**, and restart Home Assistant.

### Method 2: Manual Installation

1. Download the latest release from the [Releases](https://github.com/ingeniumsl/homeassistant-ingenium/releases) page.
2. Copy the entire `custom_components/ingenium` directory into your Home Assistant `<config>/custom_components/` folder.
3. The directory structure should look like:
   ```text
   config/
   └── custom_components/
       └── ingenium/
           ├── __init__.py
           ├── manifest.json
           ├── config_flow.py
           ├── switch.py
           ├── light.py
           ├── cover.py
           ├── climate.py
           ├── sensor.py
           ├── strings.json
           └── ...
   ```
4. Restart Home Assistant.

---

## Configuration

The integration is configured exclusively via the Home Assistant user interface:

1. In Home Assistant, navigate to **Settings** > **Devices & Services**.
2. Click **Add Integration** in the bottom right corner.
3. Search for **Ingenium**.
4. Choose your connection mode:
   * **Local**: Provide the local IP address or hostname of your Ingenium ETH/IP gateway.
   * **Remote**: Enter your Ingenium cloud username and password.
5. Click **Submit**. Your devices and platforms will be automatically discovered and added to your dashboard.

---

## Troubleshooting & Debugging

To enable debug logging for this component, add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.ingenium: debug
    ingeniumpy: debug
```

Check the Home Assistant logs under **Settings** > **System** > **Logs**.

---

## Contributing & License

Contributions, bug reports, and feature requests are welcome! Please open an issue or pull request on GitHub.

Distributed under the Apache 2.0 License.

