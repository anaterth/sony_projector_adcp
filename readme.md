# Sony Projector ADCP Integration for Home Assistant

Control Sony projectors over your local network using the ADCP (Advanced Device Control Protocol). Provides a media player entity with 30 services covering picture quality, display settings, lens control, and projector diagnostics.

## Supported Models

Developed for the VPL-XW5000ES but works with any Sony projector that supports ADCP on TCP port 53595:

- VPL-XW5000ES, VPL-XW5100ES
- VPL-XW6000ES, VPL-XW6100ES
- VPL-XW7000ES, VPL-XW8100ES
- VPL-VW series (VW285ES, VW385ES, VW585ES, VW5000, etc.)

The projector rejects unsupported commands with `err_val`, so model-specific features degrade gracefully.

## Installation

### HACS (Recommended)

1. Open HACS > Integrations
2. Three-dot menu > Custom repositories
3. Add this repository URL, category: Integration
4. Install and restart Home Assistant

### Manual

Copy `custom_components/sony_projector_adcp/` into your HA config's `custom_components/` directory and restart.

## Configuration

1. **Settings** > **Devices & Services** > **Add Integration** > search "Sony Projector ADCP"
2. Enter:
   - **IP Address** of the projector
   - **Port** (default: 53595)
   - **Name** (friendly name)
   - **Use Authentication** (default: on)
   - **Password** (default: `Projector`, case-sensitive)

### Projector Network Setup

On the projector: **Menu** > **Installation** > **Network Settings**:

- Set **Network Management** to **ON** (or **Standby Mode** to **Standard**)
- Note the IP address and authentication password

Without Network Management ON, the projector won't accept commands while in standby.

## Features

### Media Player Entity

The integration creates `media_player.sony_projector` with standard controls:

- **Power on/off** via `media_player.turn_on` / `turn_off`
- **Input selection** via `media_player.select_source` (HDMI 1, HDMI 2)
- **State**: On, Off (plus startup/cooling transitions)
- **Polling**: Every 30 seconds

### Entity Attributes

All current settings are exposed as state attributes for use in templates, automations, and dashboards:

#### Picture Settings
| Attribute | Description |
|-----------|-------------|
| `picture_mode` | Current picture preset |
| `brightness` | Brightness level |
| `contrast` | Contrast level |
| `sharpness` | Sharpness level |
| `color` | Color (saturation) level |
| `hue` | Hue level |
| `light_output` | Laser/lamp output level |
| `reality_creation` | Reality Creation on/off |
| `video_muted` | Blank screen status |

#### Display / Processing Settings
| Attribute | Description |
|-----------|-------------|
| `aspect_ratio` | Current aspect ratio |
| `hdr_mode` | HDR processing mode |
| `motionflow` | Motion interpolation mode |
| `color_temp` | Color temperature preset |
| `gamma` | Gamma correction curve |
| `color_space` | Color space |
| `noise_reduction` | Noise reduction level |
| `film_mode` | Film cadence detection |
| `iris_mode` | Auto iris / dynamic contrast |
| `lamp_control` | Lamp/laser output mode |
| `light_output_mode` | Light source dynamic control |

#### Diagnostics (polled every ~5 minutes)
| Attribute | Description |
|-----------|-------------|
| `model_name` | Projector model (auto-detected) |
| `serial_number` | Serial number |
| `firmware_version` | Firmware version info |
| `light_source_hours` | Laser/lamp hours |
| `operation_hours` | Total operation hours |
| `temperature` | Internal temperature |
| `signal_info` | Current input signal |
| `error_status` | Error conditions |
| `warning_status` | Warning conditions |

### Services (30 total)

#### Picture Mode
```yaml
service: sony_projector_adcp.set_picture_mode
target:
  entity_id: media_player.sony_projector
data:
  mode: cinema_film1
```
Options: `cinema_film1`, `cinema_film2`, `reference`, `tv`, `photo`, `game`, `brt_cinema`, `brt_tv`, `imax`, `user`, `user1`, `user2`, `user3`, `cinema_digital`

#### Picture Adjustments (0-100)
```yaml
service: sony_projector_adcp.set_brightness
target:
  entity_id: media_player.sony_projector
data:
  value: 75
```
Available: `set_brightness`, `set_contrast`, `set_sharpness`, `set_light_output`, `set_color`, `set_hue`

Each also has `increase_*` and `decrease_*` services that use the ADCP native `--rel` command for atomic +/- 1 adjustments (no race conditions):

```yaml
service: sony_projector_adcp.increase_brightness
target:
  entity_id: media_player.sony_projector
```

#### Aspect Ratio
```yaml
service: sony_projector_adcp.set_aspect_ratio
target:
  entity_id: media_player.sony_projector
data:
  mode: normal
```
Options: `normal`, `v_stretch`, `squeeze`, `1.85_1_zoom`, `2.35_1_zoom`, `stretch`

#### HDR Mode
```yaml
service: sony_projector_adcp.set_hdr_mode
target:
  entity_id: media_player.sony_projector
data:
  mode: auto
```
Options: `auto`, `on`, `hdr10`, `hdr_reference`, `hlg`, `off`

#### Motionflow
```yaml
service: sony_projector_adcp.set_motionflow
target:
  entity_id: media_player.sony_projector
data:
  mode: true_cinema
```
Options: `smooth_high`, `smooth_low`, `impulse`, `combination`, `true_cinema`, `off`

#### Color Temperature
```yaml
service: sony_projector_adcp.set_color_temp
target:
  entity_id: media_player.sony_projector
data:
  mode: d65
```
Options: `d93`, `d75`, `d65`, `d55`, `dci`, `custom1` - `custom5`

#### Gamma Correction
```yaml
service: sony_projector_adcp.set_gamma
target:
  entity_id: media_player.sony_projector
data:
  mode: "2.2"
```
Options: `1.8`, `2.0`, `2.1`, `2.2`, `2.4`, `2.6`, `gamma7` - `gamma10`, `off`

#### Color Space
```yaml
service: sony_projector_adcp.set_color_space
target:
  entity_id: media_player.sony_projector
data:
  mode: bt709
```
Options: `bt709`, `bt2020`, `adobe_rgb`, `dci`, `color_space1` - `color_space3`, `custom`, `custom1`, `custom2`

#### Noise Reduction
```yaml
service: sony_projector_adcp.set_noise_reduction
target:
  entity_id: media_player.sony_projector
data:
  mode: low
```
Options: `auto`, `high`, `mid`, `low`, `off`

#### Film Mode
```yaml
service: sony_projector_adcp.set_film_mode
target:
  entity_id: media_player.sony_projector
data:
  mode: auto
```
Options: `auto`, `off`

#### Iris Mode (Dynamic Contrast)
```yaml
service: sony_projector_adcp.set_iris_mode
target:
  entity_id: media_player.sony_projector
data:
  mode: full
```
Options: `full`, `limited`, `off`

#### Lamp/Laser Control
```yaml
service: sony_projector_adcp.set_lamp_control
target:
  entity_id: media_player.sony_projector
data:
  mode: high
```
Options: `high`, `low`

#### Light Source Dynamic Control
```yaml
service: sony_projector_adcp.set_light_output_mode
target:
  entity_id: media_player.sony_projector
data:
  mode: full
```
Options: `full`, `limited`, `off`

#### Reality Creation
```yaml
service: sony_projector_adcp.set_reality_creation
target:
  entity_id: media_player.sony_projector
data:
  state: "on"

# Or toggle:
service: sony_projector_adcp.toggle_reality_creation
target:
  entity_id: media_player.sony_projector
```

#### Remote Key Commands (60+ keys)
```yaml
service: sony_projector_adcp.send_key
target:
  entity_id: media_player.sony_projector
data:
  key: lens_shift_up
```

Key categories:
- **Navigation**: `menu`, `up`, `down`, `left`, `right`, `enter`, `reset`
- **Power**: `power_on`, `power_off`
- **Lens**: `lens_focus_far`, `lens_focus_near`, `lens_zoom_up`, `lens_zoom_down`, `lens_shift_up`, `lens_shift_down`, `lens_shift_left`, `lens_shift_right`, `lens_position1` - `lens_position5`
- **Picture presets**: `picmode1` - `picmode9`
- **Aspect shortcuts**: `aspect_normal`, `aspect_v_stretch`, `aspect_1.85_1_zoom`, `aspect_2.35_1_zoom`, `aspect_stretch`, `aspect_squeeze`
- **Adjustments**: `bright +`, `bright -`, `sharpness +`, `sharpness -`, `color +`, `color -`, `laser_brightness +`, `laser_brightness -`
- **Toggles**: `reality_creation`, `motionflow`, `gamma_correction`, `iris_mode`, `color_temp`, `aspect`
- **Display**: `blank`, `status_on`, `status_off`
- **3D**: `3d`, `3d_format`, `3d_brightness`, `3d_glasses_brightness`

#### Raw ADCP Command
```yaml
service: sony_projector_adcp.send_raw_command
target:
  entity_id: media_player.sony_projector
data:
  command: 'blanking --top 10'
```
Send any ADCP command directly. Useful for commands not exposed as dedicated services (blanking, panel alignment, color matching, etc.).

## Automation Examples

### Movie Night
```yaml
automation:
  - alias: "Movie Night"
    trigger:
      - platform: state
        entity_id: media_player.shield_tv
        to: "playing"
    action:
      - service: media_player.turn_on
        target:
          entity_id: media_player.sony_projector
      - delay: 30
      - service: sony_projector_adcp.set_picture_mode
        target:
          entity_id: media_player.sony_projector
        data:
          mode: cinema_film1
      - service: sony_projector_adcp.set_aspect_ratio
        target:
          entity_id: media_player.sony_projector
        data:
          mode: normal
      - service: sony_projector_adcp.set_hdr_mode
        target:
          entity_id: media_player.sony_projector
        data:
          mode: auto
      - service: sony_projector_adcp.set_motionflow
        target:
          entity_id: media_player.sony_projector
        data:
          mode: true_cinema
```

### Gaming Mode
```yaml
script:
  projector_gaming_mode:
    alias: "Gaming Mode"
    sequence:
      - service: sony_projector_adcp.set_picture_mode
        target:
          entity_id: media_player.sony_projector
        data:
          mode: game
      - service: sony_projector_adcp.set_motionflow
        target:
          entity_id: media_player.sony_projector
        data:
          mode: "off"
      - service: media_player.select_source
        target:
          entity_id: media_player.sony_projector
        data:
          source: "HDMI 2"
```

### Scope Lens Recall
```yaml
script:
  projector_scope:
    alias: "2.35:1 Scope"
    sequence:
      - service: sony_projector_adcp.set_aspect_ratio
        target:
          entity_id: media_player.sony_projector
        data:
          mode: 2.35_1_zoom
      - service: sony_projector_adcp.send_key
        target:
          entity_id: media_player.sony_projector
        data:
          key: lens_position2
```

### Lamp Hours Warning
```yaml
automation:
  - alias: "Projector Lamp Hours Warning"
    trigger:
      - platform: numeric_state
        entity_id: media_player.sony_projector
        attribute: light_source_hours
        above: 10000
    action:
      - service: notify.mobile_app
        data:
          title: "Projector Maintenance"
          message: "Light source has {{ state_attr('media_player.sony_projector', 'light_source_hours') }} hours"
```

### Dashboard Card
```yaml
type: entities
title: Sony Projector
entities:
  - entity: media_player.sony_projector
  - type: attribute
    entity: media_player.sony_projector
    attribute: picture_mode
    name: Picture Mode
  - type: attribute
    entity: media_player.sony_projector
    attribute: hdr_mode
    name: HDR
  - type: attribute
    entity: media_player.sony_projector
    attribute: aspect_ratio
    name: Aspect Ratio
  - type: attribute
    entity: media_player.sony_projector
    attribute: light_source_hours
    name: Lamp Hours
  - type: attribute
    entity: media_player.sony_projector
    attribute: temperature
    name: Temperature
```

## Troubleshooting

### Cannot Connect
- Verify the projector's IP address and port (default 53595)
- Ensure the projector and HA are on the same network/VLAN
- Check that **Network Management** is ON in the projector's menu
- Verify no firewall is blocking TCP port 53595

### Authentication Fails
- Default password is `Projector` (capital P, case-sensitive)
- This is the same as the projector's web admin password
- Check that the authentication setting matches between the integration and projector

### Commands Return Errors
- Most commands only work when the projector is powered on
- `err_cmd` in standby usually means Network Management is set to OFF
- `err_val` means the command/value isn't supported by your model
- `err_inactive` means the command is temporarily unavailable (e.g., during input switching)

### Integration Not Recovering After Power Outage
- The integration raises `ConfigEntryNotReady` when the projector is unreachable, so HA will automatically retry with exponential backoff
- Ensure your projector's **Standby Mode** is set to **Standard** so it accepts network connections after power is restored

### Values Not Updating
- Polling interval is 30 seconds; diagnostics poll every ~5 minutes
- Picture/display settings only available when the projector is on
- Check HA logs for connection errors

## Debug Logging

```yaml
logger:
  default: info
  logs:
    custom_components.sony_projector_adcp: debug
```

## ADCP Protocol Reference

This integration communicates via Sony's ADCP protocol over TCP port 53595. Key protocol details:

- **Authentication**: SHA-256 hash of (random challenge + password)
- **Command format**: `command "value"\r\n` (strings) or `command 123\r\n` (numbers)
- **Responses**: `ok`, `"value"`, `123`, or `err_*`
- **Connection timeout**: Projector drops idle connections after 60 seconds
- **Documentation**: [Sony Protocol Manual](https://pro.sony/s3/2018/07/03140912/Sony_Protocol-Manual_1st-Edition-Revised-2.pdf)

## References

### Official Sony Documentation
- [Sony Protocol Manual (Common)](https://pro.sony/s3/2018/07/03140912/Sony_Protocol-Manual_1st-Edition-Revised-2.pdf) — Connection, authentication, command format, error codes
- [Sony Protocol Manual (Supported Command List)](https://pro.sony/s3/2018/07/19110602/Sony_Protocol-Manual_Supported-Command-List_1st-Edition-Revised-1.pdf) — Per-model command compatibility matrix
- [VPL-XW5000ES Help Guide — ADCP Setup](https://helpguide.sony.net/vpl/xw5000/v1/en/contents/TP1000558245.html) — Network and ADCP configuration on the projector
- [Sony Canada — VPL-XW5000ES Manuals](https://www.sony.ca/en/electronics/support/product/vpl-xw5000es/manuals) — Full technical manual download (includes XW5000-specific command list)

### Community Projects
- [kennymc-c/ucr-integration-sonyADCP](https://github.com/kennymc-c/ucr-integration-sonyADCP) — Unfolded Circle Remote integration for Sony ADCP; comprehensive command implementation including lens, iris, 3D, and sensor data
- [tokyotexture/homeassistant-custom-components](https://github.com/tokyotexture/homeassistant-custom-components) — Minimal HA switch entity for Sony ADCP power control

### Community Discussions
- [Sony Projector ADCP Control — HA Community](https://community.home-assistant.io/t/sony-projector-adcp-control/933745) — Home Assistant community thread for this integration
- [Sony ADCP Projector Switch — HA Community](https://community.home-assistant.io/t/sony-adcp-projector-switch/87625) — Earlier HA community discussion on ADCP control
- [VPL-XW5000ES/XW6000ES/XW7000ES Owner's Thread — AVS Forum](https://www.avsforum.com/threads/the-sony-vpl-xw5000es-vplxw6000es-and-vpl-xw7000es-owner%E2%80%99s-thread.3249511/) — Extensive owner discussion including calibration, settings, and network control tips

## Contributing

Contributions welcome. Please submit a Pull Request.

## License

MIT License.
