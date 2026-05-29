# SFP EEPROM Generator

Web-based tool for generating SFP/SFP+ EEPROM binary files for Nokia/Alcatel ONT SFP modules.

## Features

- **Web UI** — Generate SFP EEPROM .bin files via browser
- **Batch Generation** — Create multiple files with sequential serial numbers
- **Auto-checksum** — CC_BASE (byte 63) and CC_EXT (byte 95) auto-calculated
- **Master File Support** — Uses golden sample as template
- **Auto-save** — Generated files saved to `output/` folder

## File Structure

```
sfp-eeprom-generator/
├── input/           # Original/master .bin files (golden samples)
├── output/          # Generated .bin files
├── scripts/         # Patch scripts (future use)
├── web/             # Web application
│   └── sfp_web.py  # Main web server (port 8091)
└── README.md
```

## Supported Hardware

- **Nokia G-2524G-A** ONT SFP modules
- **SFP-10G-B23L-20D** (ALCATEL 3HE04823)
- TX Wavelength: 1270nm / 1330nm (configurable)

## Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/sfp-eeprom-generator.git
cd sfp-eeprom-generator

# Run the web server
cd web
python3 sfp_web.py
```

Server starts at: `http://0.0.0.0:8091`

## Usage

### Web UI

1. Open `http://localhost:8091` in browser
2. Enter **Serial Number** (13 chars) OR **Base Serial** (12 chars) + Unit Digit
3. Set **TX Wavelength** (default: 1330nm from master)
4. Click **"Generate & Download"**
5. .bin file downloads automatically

### API (curl)

```bash
# Generate single file
curl -X POST http://localhost:8091/api/generate \
  -H "Content-Type: application/json" \
  -d '{"serial": "Y202512260229", "tx_wavelength": 1270}'

# Batch generation (base serial + count)
curl -X POST http://localhost:8091/api/generate \
  -H "Content-Type: application/json" \
  -d '{"base_serial": "Y20251226022", "unit_digit": "9", "count": 10}'
```

## EEPROM Layout (SFF-8472)

| Offset | Field | Size | Description |
|--------|-------|------|-------------|
| 60-61 | TX Wavelength | 2 bytes | 16-bit value (direct nm) |
| 63 | CC_BASE | 1 byte | Checksum (bytes 0-62) |
| 68-80 | Serial Number | 13 bytes | ASCII, last byte = unit digit |
| 84-89 | Date Code | 6 bytes | YYMMDD |
| 94 | CC_EXT | 1 byte | Checksum (bytes 64-93) |
| 96-111 | Vendor Name | 16 bytes | ASCII (e.g., "ALCATEL 3HE04823") |
| 112-127 | Vendor Rev/ID | 16 bytes | ASCII |

## Master File

The tool uses `input/Y202512260220-LIVE.bin` (384 bytes) as the golden sample.

**Default values from master:**
- Serial: `Y202512260220`
- TX Wavelength: `1330 nm`
- Vendor: `ALCATEL 3HE04823`
- Vendor ID: `AA01 VAUIAS0AAA`

## Requirements

- Python 3.6+ (no external dependencies)
- Browser (Chrome/Firefox)

## License

MIT License

## Author

**Prakash Kushwaha**  
ONT+STB Repair Center, Nepal  
GitHub: [@ioprakash](https://github.com/ioprakash)
