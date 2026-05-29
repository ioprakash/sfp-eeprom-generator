#!/usr/bin/env python3
"""SFP EEPROM Generator Web App — port 8091 — CLEAN REWRITE"""
import os, json, time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
MASTER_FILE = os.path.join(SCRIPT_DIR, "..", "input", "Y202512260220-LIVE.bin")
GEN_DIR     = os.path.join(SCRIPT_DIR, "..", "output")
os.makedirs(GEN_DIR, exist_ok=True)

def load_master():
    with open(MASTER_FILE, "rb") as f:
        return f.read()

def cc_base(data):
    return sum(data[0:63]) % 256

def cc_ext(data):
    return sum(data[64:95]) % 256

def gen(serial=None, base_serial=None, unit_digit='0',
        tx_wavelength=None, date_code=None,
        vendor_lot=None, vendor_id=None,
        vendor_pn=None, vendor_rev=None,
        identifier=None, connector=None,
        encoding=None, br_nominal=None,
        diag_type=None, enhanced_options=None):
    data = bytearray(load_master())
    
    # Serial (bytes 68-80)
    if serial and len(serial) == 13:
        for i, ch in enumerate(serial[:12]):
            data[68+i] = ord(ch)
        data[80] = ord(serial[12])
    elif base_serial and len(base_serial) == 12:
        for i, ch in enumerate(base_serial):
            data[68+i] = ord(ch)
        data[80] = ord(str(unit_digit))
    
    # TX Wavelength (bytes 60-61) — direct nm value
    if tx_wavelength is not None:
        wl = int(tx_wavelength)
        data[60] = (wl >> 8) & 0xFF
        data[61] = wl & 0xFF
    
    # Date Code (bytes 84-89)
    if date_code and len(date_code) == 6:
        for i, ch in enumerate(date_code):
            data[84+i] = ord(ch)
    
    # Vendor Lot (bytes 96-111)
    if vendor_lot and str(vendor_lot).strip():
        s = str(vendor_lot).strip()[:16].ljust(16)
        for i, ch in enumerate(s):
            data[96+i] = ord(ch)
    
    # Vendor ID (bytes 112-127)
    if vendor_id and str(vendor_id).strip():
        s = str(vendor_id).strip()[:16].ljust(16)
        for i, ch in enumerate(s):
            data[112+i] = ord(ch)
    
    # Vendor PN (bytes 40-55) - NEW
    if vendor_pn and str(vendor_pn).strip():
        s = str(vendor_pn).strip()[:16].ljust(16)
        for i, ch in enumerate(s):
            data[40+i] = ord(ch)
    
    # Vendor Rev (bytes 56-59) - NEW
    if vendor_rev and str(vendor_rev).strip():
        s = str(vendor_rev).strip()[:4].ljust(4)
        for i, ch in enumerate(s):
            data[56+i] = ord(ch)
    
    # Identifier (byte 0) - NEW
    if identifier is not None:
        data[0] = int(identifier) & 0xFF
    
    # Connector (byte 2) - NEW
    if connector is not None:
        data[2] = int(connector) & 0xFF
    
    # Encoding (byte 11) - NEW
    if encoding is not None:
        data[11] = int(encoding) & 0xFF
    
    # BR Nominal (byte 9) - NEW
    if br_nominal is not None:
        data[9] = int(br_nominal) // 100  # Convert to 100 MBd units
    
    # Diagnostic Type (byte 92) - NEW
    if diag_type is not None:
        data[92] = int(diag_type) & 0xFF
    
    # Enhanced Options (byte 93) - NEW
    if enhanced_options is not None:
        data[93] = int(enhanced_options) & 0xFF
    
    # Recalculate checksums
    data[63] = cc_base(data)
    data[95] = cc_ext(data)
    
    return bytes(data)

def list_gen():
    files = []
    for f in os.listdir(GEN_DIR):
        if f.endswith(".bin"):
            fp = os.path.join(GEN_DIR, f)
            files.append({"name": f, "size": os.path.getsize(fp), "mtime": os.path.getmtime(fp)})
    files.sort(key=lambda x: x["mtime"], reverse=True)
    return files

def mfields():
    m = load_master()
    return {
        "hex": m.hex(),
        "serial": bytes(m[68:80]).decode("ascii","replace") + chr(m[80]),
        "vendor": bytes(m[96:112]).decode("ascii","replace").strip(),
        "pn": bytes(m[40:56]).decode("ascii","replace").strip(),
        "date": bytes(m[84:90]).decode("ascii","replace").strip(),
        "tx_wl": (m[60]<<8)|m[61],
        "cc_b": m[63],
        "cc_e": m[95],
        "vendor_pn": bytes(m[40:56]).decode("ascii","replace").strip(),
        "vendor_rev": bytes(m[56:60]).decode("ascii","replace").strip(),
        "identifier": m[0],
        "connector": m[2],
        "encoding": m[11],
        "br_nominal": m[9] * 100,  # in MBd units
        "diag_type": m[92],
        "enhanced_options": m[93],
    }

def serve_html():
    mf = mfields()
    serial = mf["serial"]
    base_sn = serial[:12] if len(serial) >= 12 else "Y20251226022"
    unit_d = serial[12] if len(serial) >= 13 else "0"
    tx_wl = mf["tx_wl"]
    date_code = mf["date"]
    
    HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>SFP EEPROM Generator</title>
<style>
body{font-family:monospace;background:#0d1117;color:#c9d1d9;margin:0;padding:20px}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;margin-bottom:16px}
h1,h2{color:#58a6ff;margin-top:0}
.fg{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.fg div{display:flex;flex-direction:column}
label{font-size:0.72rem;color:#8b949e;margin-bottom:4px}
input{padding:6px 8px;background:#0d1117;border:1px solid #30363d;color:#c9d1d9;border-radius:4px;font-size:0.85rem}
.btn{padding:8px 16px;background:#238636;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:0.85rem;margin-right:8px}
.btn:hover{background:#2ea043}
.bl{color:#8b949e;font-size:0.72rem}
.res{margin-top:12px;padding:12px;background:#0d1117;border:1px solid #30363d;border-radius:6px;display:none}
.res.show{display:block}
.ttl{color:#8b949e;font-size:0.72rem;margin-bottom:6px}
.hp{font-family:monospace;font-size:0.68rem;white-space:pre;max-height:140px;overflow:auto;background:#161b22;padding:8px;border-radius:4px}
.cmp{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px}
.cbox{flex:1;background:#161b22;padding:8px;border-radius:4px}
#gfList{max-height:200px;overflow:auto}
#gfList div{padding:4px 8px;border-bottom:1px solid #21262d;cursor:pointer}
#gfList div:hover{background:#21262d}
.adv-toggle{cursor:pointer;color:#58a6ff;font-size:0.78rem;margin-top:10px;display:inline-block}
.adv-toggle:hover{text-decoration:underline}
.adv-section{display:none;margin-top:12px;padding:12px;background:#1c2128;border:1px solid #30363d;border-radius:6px}
.adv-section.show{display:block}
</style>
</head>
<body>
<div class="card">
  <h1>SFP EEPROM Generator</h1>
  <div class="card" style="background:#1c2128">
    <h2>Master Golden Sample</h2>
    <div style="font-size:0.78rem;color:#8b949e">
      <div>Serial: <span style="color:#58a6ff">BASESN</span> + unit digit</div>
      <div>TX Wavelength: <span style="color:#58a6ff">TXWL nm</span></div>
      <div>Date Code: <span style="color:#58a6ff">YYMMDD</span></div>
      <div>File Size: 384 bytes</div>
    </div>
  </div>
  
  <div style="margin-top:14px">
    <div style="margin-bottom:10px">
      <label>Serial (13 chars) or Base (12 chars)</label>
      <input type="text" id="si" placeholder="BASESN" maxlength="13" style="font-size:1.05rem;letter-spacing:1px">
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px">
      <div>
        <label>Unit Digit (0-9)</label>
        <input type="text" id="ud" value="UD" maxlength="1" style="font-size:1.05rem;text-align:center">
      </div>
      <div>
        <label>TX Wavelength (nm)</label>
        <input type="number" id="txw" placeholder="TXWL" min="1200" max="1600">
      </div>
    </div>
    <div style="margin-bottom:10px">
      <label>Date Code (YYMMDD)</label>
      <input type="text" id="dc" placeholder="YYMMDD" maxlength="6">
    </div>
    
    <div class="adv-toggle" onclick="document.getElementById('adv').classList.toggle('show')">⚙️ Advanced Options (click to expand)</div>
    <div id="adv" class="adv-section">
      <div class="fg" style="margin-top:8px">
        <div>
          <label>Vendor PN (bytes 40-55)</label>
          <input type="text" id="vpn" placeholder="SFP-10G-B23L-20D" maxlength="16">
        </div>
        <div>
          <label>Vendor Rev (bytes 56-59)</label>
          <input type="text" id="vrev" placeholder="A" maxlength="4">
        </div>
      </div>
      <div class="fg" style="margin-top:10px">
        <div>
          <label>Identifier (byte 0, hex)</label>
          <input type="text" id="idf" placeholder="0x03" maxlength="4">
        </div>
        <div>
          <label>Connector (byte 2, hex)</label>
          <input type="text" id="con" placeholder="0x07" maxlength="4">
        </div>
      </div>
      <div class="fg" style="margin-top:10px">
        <div>
          <label>Encoding (byte 11, hex)</label>
          <input type="text" id="enc" placeholder="0x06" maxlength="4">
        </div>
        <div>
          <label>BR Nominal (byte 9, MBd)</label>
          <input type="number" id="brn" placeholder="10000" min="0" max="65535">
        </div>
      </div>
      <div class="fg" style="margin-top:10px">
        <div>
          <label>Diag Type (byte 92, hex)</label>
          <input type="text" id="dty" placeholder="0x68" maxlength="4">
        </div>
        <div>
          <label>Enhanced Opt (byte 93, hex)</label>
          <input type="text" id="eno" placeholder="0xF0" maxlength="4">
        </div>
      </div>
      <div class="fg" style="margin-top:10px">
        <div>
          <label>Vendor Lot (bytes 96-111)</label>
          <input type="text" id="vl" placeholder="ALCATEL 3HE04823" maxlength="16">
        </div>
        <div>
          <label>Vendor ID (bytes 112-127)</label>
          <input type="text" id="vi" placeholder="AA01 VAUIAS0AAA" maxlength="16">
        </div>
      </div>
      <div style="margin-top:8px;font-size:0.68rem;color:#8b949e">Leave fields empty to keep master defaults</div>
    </div>
    
    <div style="margin-top:12px">
      <button class="btn" onclick="generate()">Generate & Download</button>
      <button class="btn" onclick="preview()" style="background:#30363d">Preview</button>
    </div>
  </div>
  
  <div id="rs" class="res">
    <div id="rss" style="color:#58a6ff;font-size:0.85rem;margin-bottom:8px">—</div>
    <div id="rsc" style="font-size:0.72rem;margin-bottom:10px"></div>
    <div class="cmp">
      <div class="cbox"><div class="ttl">Original (Master)</div><div id="rso" style="font-size:0.68rem;font-family:monospace"></div></div>
      <div class="cbox"><div class="ttl">Generated (New)</div><div id="rsn" style="font-size:0.68rem;font-family:monospace"></div></div>
    </div>
    <div id="rsh" class="hp" style="margin-top:10px"></div>
    <div style="text-align:center;margin-top:12px"><a id="dl" class="btn" download>Download .bin</a></div>
  </div>
</div>

<div class="card">
  <h2>Generated Files</h2>
  <div id="gfList">Loading...</div>
</div>

<script>
const MASTER_HEX = "MFHEX";

function generate() {
  const si = document.getElementById('si').value.toUpperCase().trim();
  const body = {};
  
  if (si.length === 13) {
    body.serial = si;
  } else if (si.length === 12) {
    body.base_serial = si;
    body.unit_digit = document.getElementById('ud').value || '0';
  } else {
    body.base_serial = "BASESN";
    body.unit_digit = document.getElementById('ud').value || '0';
  }
  
  const txw = document.getElementById('txw').value;
  if (txw) body.tx_wavelength = parseInt(txw);
  
  const dc = document.getElementById('dc').value;
  if (dc) body.date_code = dc;
  
  // Advanced fields - only send if not empty
  const vpn = document.getElementById('vpn').value;
  if (vpn) body.vendor_pn = vpn;
  
  const vrev = document.getElementById('vrev').value;
  if (vrev) body.vendor_rev = vrev;
  
  const idf = document.getElementById('idf').value;
  if (idf) body.identifier = parseInt(idf);
  
  const con = document.getElementById('con').value;
  if (con) body.connector = parseInt(con);
  
  const enc = document.getElementById('enc').value;
  if (enc) body.encoding = parseInt(enc);
  
  const brn = document.getElementById('brn').value;
  if (brn) body.br_nominal = parseInt(brn);
  
  const dty = document.getElementById('dty').value;
  if (dty) body.diag_type = parseInt(dty);
  
  const eno = document.getElementById('eno').value;
  if (eno) body.enhanced_options = parseInt(eno);
  
  const vl = document.getElementById('vl').value;
  if (vl) body.vendor_lot = vl;
  
  const vi = document.getElementById('vi').value;
  if (vi) body.vendor_id = vi;
  
  fetch('/api/generate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  })
  .then(r => r.json())
  .then(res => {
    if (res.error) { alert(res.error); return; }
    showResult(res, true);
  })
  .catch(e => alert('Error: ' + e.message));
}

function preview() {
  const si = document.getElementById('si').value.toUpperCase().trim();
  const body = {};
  
  if (si.length === 13) {
    body.serial = si;
  } else if (si.length === 12) {
    body.base_serial = si;
    body.unit_digit = document.getElementById('ud').value || '0';
  } else {
    body.base_serial = "BASESN";
    body.unit_digit = document.getElementById('ud').value || '0';
  }
  
  const txw = document.getElementById('txw').value;
  if (txw) body.tx_wavelength = parseInt(txw);
  
  const dc = document.getElementById('dc').value;
  if (dc) body.date_code = dc;
  
  // Advanced fields - only send if not empty
  const vpn = document.getElementById('vpn').value;
  if (vpn) body.vendor_pn = vpn;
  
  const vrev = document.getElementById('vrev').value;
  if (vrev) body.vendor_rev = vrev;
  
  const idf = document.getElementById('idf').value;
  if (idf) body.identifier = parseInt(idf);
  
  const con = document.getElementById('con').value;
  if (con) body.connector = parseInt(con);
  
  const enc = document.getElementById('enc').value;
  if (enc) body.encoding = parseInt(enc);
  
  const brn = document.getElementById('brn').value;
  if (brn) body.br_nominal = parseInt(brn);
  
  const dty = document.getElementById('dty').value;
  if (dty) body.diag_type = parseInt(dty);
  
  const eno = document.getElementById('eno').value;
  if (eno) body.enhanced_options = parseInt(eno);
  
  const vl = document.getElementById('vl').value;
  if (vl) body.vendor_lot = vl;
  
  const vi = document.getElementById('vi').value;
  if (vi) body.vendor_id = vi;
  
  fetch('/api/generate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  })
  .then(r => r.json())
  .then(res => {
    if (res.error) { alert(res.error); return; }
    showResult(res, false);
  })
  .catch(e => alert('Error: ' + e.message));
}

function showResult(res, doDownload) {
  document.getElementById('rs').classList.add('show');
  document.getElementById('rss').textContent = '✅ Generated: ' + res.serial + ' (' + res.size + ' bytes)';
  
  // Show hex dump
  let hexOrig = MASTER_HEX;
  let hexNew = res.hex;
  
  let htmlOrig = '';
  let htmlNew = '';
  for (let i = 0; i < hexOrig.length; i += 32) {
    htmlOrig += hexOrig.substring(i, i+32) + '<br>';
    htmlNew += hexNew.substring(i, i+32) + '<br>';
  }
  document.getElementById('rso').innerHTML = htmlOrig;
  document.getElementById('rsn').innerHTML = htmlNew;
  
  // Download link
  const dl = document.getElementById('dl');
  const blob = new Blob([hexToBytes(res.hex)], {type: 'application/octet-stream'});
  dl.href = URL.createObjectURL(blob);
  dl.download = res.saved || ('SFP_' + res.serial + '.bin');
  
  if (doDownload) dl.click();
}

function hexToBytes(hex) {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2) {
    bytes[i/2] = parseInt(hex.substring(i, i+2), 16);
  }
  return bytes;
}

// Load generated files list
fetch('/api/list')
  .then(r => r.json())
  .then(files => {
    const div = document.getElementById('gfList');
    div.innerHTML = '';
    files.forEach(f => {
      const d = document.createElement('div');
      d.textContent = f.name + ' (' + f.size + ' bytes)';
      div.appendChild(d);
    });
  })
  .catch(e => console.error('Error loading files:', e));
</script>
</body>
</html>""".replace('BASESN', base_sn).replace('UD', unit_d).replace('TXWL', str(tx_wl)).replace('YYMMDD', date_code).replace('MFHEX', mf["hex"])
    
    return HTML

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress log output
    
    def do_GET(self):
        p = urlparse(self.path).path
        if p == '/' or p == '/index.html':
            html = serve_html()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', len(html.encode('utf-8')))
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        elif p == '/api/list':
            files = list_gen()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(files).encode())
        else:
            self.send_error(404)
    
    def do_POST(self):
        p = urlparse(self.path).path
        if p == '/api/generate':
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            
            try:
                data = gen(
                    serial=body.get('serial'),
                    base_serial=body.get('base_serial'),
                    unit_digit=body.get('unit_digit', '0'),
                    tx_wavelength=body.get('tx_wavelength'),
                    date_code=body.get('date_code'),
                    vendor_lot=body.get('vendor_lot'),
                    vendor_id=body.get('vendor_id'),
                    vendor_pn=body.get('vendor_pn'),
                    vendor_rev=body.get('vendor_rev'),
                    identifier=body.get('identifier'),
                    connector=body.get('connector'),
                    encoding=body.get('encoding'),
                    br_nominal=body.get('br_nominal'),
                    diag_type=body.get('diag_type'),
                    enhanced_options=body.get('enhanced_options'),
                )
                
                # Auto-save
                serial = body.get('serial') or (body.get('base_serial') + body.get('unit_digit', '0'))
                fname = f"{serial}_{time.strftime('%Y%m%d_%H%M%S')}.bin"
                fpath = os.path.join(GEN_DIR, fname)
                with open(fpath, 'wb') as f:
                    f.write(data)
                
                # Calculate diffs
                master = load_master()
                diffs = []
                for i in range(min(len(data), len(master))):
                    if data[i] != master[i]:
                        diffs.append(i)
                
                res = {
                    "ok": True,
                    "serial": serial,
                    "hex": data.hex(),
                    "size": len(data),
                    "cc_base_ok": data[63] == sum(data[0:63]) % 256,
                    "cc_ext_ok": data[95] == sum(data[64:95]) % 256,
                    "diffs": diffs[:20],
                    "saved": fname
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(res).encode())
                
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_error(404)

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8091), Handler)
    print(f'Serving on http://0.0.0.0:8091')
    server.serve_forever()
