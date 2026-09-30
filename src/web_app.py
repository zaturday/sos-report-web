"""
Simple Flask web app for SOS Report upload and analysis.
Run: python src/web_app.py
"""
import os
import sys
import io
import tempfile
import tarfile
import re
from flask import Flask, request, render_template_string, send_file
from datetime import datetime

app = Flask(__name__)

# HTML templates
UPLOAD_HTML = '''
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SOS Report Web Analyzer</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            max-width: 500px;
            width: 100%;
        }
        h1 {
            color: #1a56db;
            margin-bottom: 10px;
            font-size: 24px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .upload-area {
            border: 2px dashed #ccc;
            border-radius: 8px;
            padding: 30px;
            text-align: center;
            transition: border-color 0.3s;
        }
        .upload-area:hover {
            border-color: #1a56db;
        }
        .upload-icon {
            font-size: 48px;
            margin-bottom: 15px;
        }
        .upload-text {
            color: #666;
            margin-bottom: 20px;
        }
        input[type="file"] {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            background: #1a56db;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 20px;
            width: 100%;
        }
        button:hover {
            background: #0d3b8f;
        }
        .info {
            margin-top: 20px;
            font-size: 12px;
            color: #999;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 SOS Report Web Analyzer</h1>
        <p class="subtitle">อัปโหลดไฟล์ sosreport เพื่อวิเคราะห์ระบบ RHEL 9</p>
        
        <form method="post" enctype="multipart/form-data">
            <div class="upload-area">
                <div class="upload-icon">📁</div>
                <p class="upload-text">เลือกไฟล์ sosreport (tar.xz หรือ tar.gz)</p>
                <input type="file" name="sosreport" accept=".tar.xz,.txz,.tar.gz,.tgz" required>
            </div>
            <button type="submit">วิเคราะห์ Report</button>
        </form>
        
        <p class="info">รองรับไฟล์ sosreport จาก RHEL 9</p>
    </div>
</body>
</html>
'''

ERROR_HTML = '''
<!DOCTYPE html>
<html>
<head><title>Error</title></head>
<body style="font-family: system-ui; padding: 40px; text-align: center;">
    <h1>❌ เกิดข้อผิดพลาด</h1>
    <p style="color: #b00020; margin: 20px 0;">{{ error }}</p>
    <a href="/" style="color: #1a56db;">← กลับหน้าหลัก</a>
</body>
</html>
'''


def parse_sosreport(archive_path: str) -> dict:
    """Parse sosreport archive and extract key information."""
    data = {
        'system': {},
        'hardware': {},
        'network': {},
        'services': {},
        'logs': {},
        'selinux': {}
    }
    
    try:
        with tarfile.open(archive_path, 'r:*') as tar:
            files = {}
            for member in tar.getmembers():
                if member.isfile():
                    try:
                        f = tar.extractfile(member)
                        if f:
                            content = f.read().decode('utf-8', errors='replace')
                            files[member.name] = content
                            f.close()
                    except:
                        pass
            
            # System info
            if 'hostname' in files or any('hostname' in k for k in files):
                for k, v in files.items():
                    if 'hostname' in k and 'sos_commands' not in k:
                        data['system']['hostname'] = v.strip().split('\n')[0]
                        break
                else:
                    for k, v in files.items():
                        if 'hostname' in k:
                            data['system']['hostname'] = v.strip().split('\n')[0]
                            break
            
            if 'uname' in files or any('uname' in k for k in files):
                for k, v in files.items():
                    if 'uname' in k and 'sos_commands' not in k:
                        data['system']['kernel'] = v.strip().split('\n')[0]
                        break
                else:
                    for k, v in files.items():
                        if 'uname' in k:
                            data['system']['kernel'] = v.strip().split('\n')[0]
                            break
            
            if 'etc_os-release' in files:
                for line in files['etc_os-release'].split('\n'):
                    if '=' in line:
                        key, val = line.split('=', 1)
                        data['system'][key.strip()] = val.strip().strip('"')
            
            # Hardware
            if 'cpuinfo' in files:
                for line in files['cpuinfo'].split('\n'):
                    if 'model name' in line:
                        data['hardware']['cpu'] = line.split(':', 1)[1].strip()
                    if 'cpu cores' in line:
                        match = re.search(r'(\d+)', line)
                        if match:
                            data['hardware']['cpu_cores'] = match.group(1)
            
            if 'meminfo' in files:
                for line in files['meminfo'].split('\n'):
                    if 'MemTotal' in line:
                        match = re.search(r'(\d+)', line)
                        if match:
                            kb = int(match.group(1))
                            data['hardware']['mem_total'] = f"{kb/1024/1024:.1f} GB"
            
            if 'dmidecode' in files:
                for line in files['dmidecode'].split('\n'):
                    if 'Manufacturer' in line:
                        data['hardware']['manufacturer'] = line.split(':', 1)[1].strip()
                    if 'Product Name' in line:
                        data['hardware']['product'] = line.split(':', 1)[1].strip()
            
            # Network
            if 'ip_addr' in files:
                interfaces = []
                current_iface = None
                for line in files['ip_addr'].split('\n'):
                    if line.strip().startswith('') and ':' in line:
                        current_iface = line.split(':')[1].strip()
                        interfaces.append({'name': current_iface})
                    elif current_iface and 'inet ' in line:
                        match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', line)
                        if match and interfaces:
                            interfaces[-1]['ip'] = match.group(1)
                    elif current_iface and 'link/' in line:
                        match = re.search(r'link/(\S+)', line)
                        if match and interfaces:
                            interfaces[-1]['mac'] = match.group(1)
                if interfaces:
                    data['network']['interfaces'] = interfaces
            
            if 'etc_resolv_conf' in files:
                data['network']['dns'] = []
                for line in files['etc_resolv_conf'].split('\n'):
                    if line.startswith('nameserver'):
                        parts = line.split()
                        if len(parts) > 1:
                            data['network']['dns'].append(parts[1])
            
            # Services
            if 'systemctl' in files:
                data['services']['enabled'] = []
                data['services']['failed'] = []
                in_enabled = False
                in_failed = False
                for line in files['systemctl'].split('\n'):
                    if 'enabled' in line.lower() and 'LOAD' in line:
                        in_enabled = True
                        in_failed = False
                        continue
                    if 'failed' in line.lower() and 'LOAD' in line:
                        in_failed = True
                        in_enabled = False
                        continue
                    if in_enabled and line.strip() and not line.startswith('---') and not line.startswith('LOAD') and not line.startswith('UNIT'):
                        name = line.split()[0] if line.split() else ''
                        if name and not name.startswith('['):
                            data['services']['enabled'].append(name)
                    if in_failed and line.strip() and not line.startswith('---') and not line.startswith('LOAD') and not line.startswith('UNIT'):
                        name = line.split()[0] if line.split() else ''
                        if name and not name.startswith('['):
                            data['services']['failed'].append(name)
            
            # Logs
            if 'journal' in files:
                errors = []
                for line in files['journal'].split('\n'):
                    if 'ERROR' in line or 'error' in line.lower() or 'FAILED' in line:
                        errors.append(line.strip()[:150])
                if errors:
                    data['logs']['errors'] = errors[:10]
            
            # SELinux
            if 'sos_commands/selinux' in files or 'selinux' in files:
                selinux_file = None
                for k in files:
                    if 'selinux' in k.lower():
                        selinux_file = k
                        break
                if selinux_file:
                    for line in files[selinux_file].split('\n'):
                        if 'SELinux status' in line:
                            match = re.search(r'(enabled|disabled)', line)
                            if match:
                                data['selinux']['status'] = match.group(1)
                        if 'Current mode' in line:
                            match = re.search(r'(enforcing|permissive|disabled)', line)
                            if match:
                                data['selinux']['mode'] = match.group(1)
        
        return data
    except Exception as e:
        raise Exception(f"ไม่สามารถอ่านไฟล์ได้: {str(e)}")


def build_report_html(data: dict, filename: str) -> str:
    """Build HTML report from parsed data."""
    
    # System section
    sys_rows = ""
    for k, v in data.get('system', {}).items():
        if v:
            sys_rows += f'<tr><td style="padding:10px;border-bottom:1px solid #eee;font-weight:600;width:200px;background:#f5f5f5;">{k}</td><td style="padding:10px;border-bottom:1px solid #eee;">{v}</td></tr>'
    
    # Hardware section
    hw_rows = ""
    for k, v in data.get('hardware', {}).items():
        if v:
            hw_rows += f'<tr><td style="padding:10px;border-bottom:1px solid #eee;font-weight:600;width:200px;background:#f5f5f5;">{k}</td><td style="padding:10px;border-bottom:1px solid #eee;">{v}</td></tr>'
    
    # Network section
    net_rows = ""
    for iface in data.get('network', {}).get('interfaces', []):
        net_rows += f'<tr><td style="padding:10px;border-bottom:1px solid #eee;font-weight:600;width:150px;background:#f5f5f5;">{iface.get("name", "?")}</td><td style="padding:10px;border-bottom:1px solid #eee;">IP: {iface.get("ip", "N/A")} / MAC: {iface.get("mac", "N/A")}</td></tr>'
    
    dns_list = ", ".join(data.get('network', {}).get('dns', []))
    if dns_list:
        net_rows += f'<tr><td style="padding:10px;border-bottom:1px solid #eee;font-weight:600;width:150px;background:#f5f5f5;">DNS Servers</td><td style="padding:10px;border-bottom:1px solid #eee;">{dns_list}</td></tr>'
    
    # Services section
    enabled_list = data.get('services', {}).get('enabled', [])
    failed_list = data.get('services', {}).get('failed', [])
    
    enabled_html = ""
    if enabled_list:
        enabled_html += '<h3 style="margin:15px 0 10px;padding-bottom:5px;border-bottom:1px solid #eee;font-size:14px;">Services ที่เปิดใช้งาน (ตัวอย่าง)</h3><ul>'
        for s in enabled_list[:15]:
            enabled_html += f'<li style="padding:6px 10px;margin:3px 0;background:#f5f5f5;border-radius:4px;border-left:3px solid #1a56db;">{s}</li>'
        enabled_html += '</ul>'
    
    failed_html = ""
    if failed_list:
        failed_html += '<h3 style="margin:15px 0 10px;padding-bottom:5px;border-bottom:1px solid #eee;font-size:14px;color:#b00020;">⚠️ Services ที่ล้มเหลว</h3><ul>'
        for s in failed_list[:10]:
            failed_html += f'<li style="padding:6px 10px;margin:3px 0;background:#fef2f2;border-radius:4px;border-left:3px solid #b00020;color:#991b1b;">{s}</li>'
        failed_html += '</ul>'
    
    # Logs section
    logs_html = ""
    for err in data.get('logs', {}).get('errors', [])[:8]:
        logs_html += f'<li style="padding:8px 12px;margin:3px 0;background:#fff7ed;border-radius:4px;border-left:3px solid #b06000;color:#9a3412;font-family:monospace;font-size:12px;">{err}</li>'
    
    # SELinux section
    selinux_html = ""
    for k, v in data.get('selinux', {}).items():
        if v:
            selinux_html += f'<tr><td style="padding:10px;border-bottom:1px solid #eee;font-weight:600;width:200px;background:#f5f5f5;">{k}</td><td style="padding:10px;border-bottom:1px solid #eee;">{v}</td></tr>'
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html = f'''
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SOS Report - {filename}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        header {{ background: linear-gradient(135deg, #1a56db 0%, #0d3b8f 100%); color: white; padding: 25px; border-radius: 8px; margin-bottom: 20px; }}
        header h1 {{ font-size: 24px; margin-bottom: 5px; }}
        header .sub {{ opacity: 0.9; font-size: 13px; }}
        .card {{ background: white; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); overflow: hidden; }}
        .card-header {{ background: #f5f5f5; padding: 15px 20px; border-bottom: 1px solid #eee; display: flex; align-items: center; gap: 10px; }}
        .card-header .icon {{ font-size: 20px; }}
        .card-header h2 {{ font-size: 16px; font-weight: 600; color: #111; }}
        .card-body {{ padding: 15px 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        li {{ list-style: none; }}
        .actions {{ margin-top: 20px; display: flex; gap: 10px; }}
        .btn {{ padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; font-size: 14px; }}
        .btn-primary {{ background: #1a56db; color: white; }}
        .btn-secondary {{ background: #666; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 รายงาน SOS Report</h1>
            <div class="sub">ไฟล์: {filename} | สร้างเมื่อ: {timestamp}</div>
        </header>
        
        <div class="card">
            <div class="card-header">
                <span class="icon">💻</span>
                <h2>ข้อมูลระบบ (System Information)</h2>
            </div>
            <div class="card-body">
                <table>{sys_rows if sys_rows else '<tr><td colspan="2" style="padding:20px;text-align:center;color:#999;">ไม่มีข้อมูล</td></tr>'}</table>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <span class="icon">⚙️</span>
                <h2>ฮาร์ดแวร์ (Hardware)</h2>
            </div>
            <div class="card-body">
                <table>{hw_rows if hw_rows else '<tr><td colspan="2" style="padding:20px;text-align:center;color:#999;">ไม่มีข้อมูล</td></tr>'}</table>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <span class="icon">🌐</span>
                <h2>เครือข่าย (Network)</h2>
            </div>
            <div class="card-body">
                <table>{net_rows if net_rows else '<tr><td colspan="2" style="padding:20px;text-align:center;color:#999;">ไม่มีข้อมูล</td></tr>'}</table>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <span class="icon">🔧</span>
                <h2>Services (Systemd)</h2>
            </div>
            <div class="card-body">
                {enabled_html}
                {failed_html}
                {'<div style="padding:20px;text-align:center;color:#999;">ไม่มีข้อมูล Services</div>' if not enabled_list and not failed_list else ''}
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <span class="icon">📝</span>
                <h2>บันทึกข้อผิดพลาด (Logs)</h2>
            </div>
            <div class="card-body">
                {f'<ul>{logs_html}</ul>' if logs_html else '<div style="padding:20px;text-align:center;color:#999;">ไม่พบข้อผิดพลาดใน log</div>'}
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <span class="icon">🔒</span>
                <h2>SELinux</h2>
            </div>
            <div class="card-body">
                <table>{selinux_html if selinux_html else '<tr><td colspan="2" style="padding:20px;text-align:center;color:#999;">ไม่มีข้อมูล</td></tr>'}</table>
            </div>
        </div>
        
        <div class="actions">
            <a href="/" class="btn btn-primary">⬅️ อัปโหลดไฟล์ใหม่</a>
            <button onclick="window.print()" class="btn btn-secondary">🖨️ พิมพ์รายงาน</button>
        </div>
    </div>
</body>
</html>
    '''
    return html


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'sosreport' not in request.files:
            return render_template_string(ERROR_HTML, error="ไม่พบไฟล์ที่อัปโหลด"), 400
        
        file = request.files['sosreport']
        if file.filename == '':
            return render_template_string(ERROR_HTML, error="ไม่ได้เลือกไฟลื่"), 400
        
        # Validate file extension
        allowed_ext = ['.tar.xz', '.txz', '.tar.gz', '.tgz']
        filename_lower = file.filename.lower()
        if not any(filename_lower.endswith(ext) for ext in allowed_ext):
            return render_template_string(ERROR_HTML, error="รูปแบบไฟล์ไม่ถูกต้อง กรุณาใช้ .tar.xz หรือ .tar.gz"), 400
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.tar.xz', delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            # Parse the report
            data = parse_sosreport(tmp_path)
            data['archive_name'] = file.filename
            
            # Generate HTML report
            report_html = build_report_html(data, file.filename)
            
            # Save report to temp file for download
            report_path = tmp_path.replace('.tar.xz', '_report.html')
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_html)
            
            return report_html
            
        except Exception as e:
            return render_template_string(ERROR_HTML, error=str(e)), 500
        finally:
            # Cleanup temp files
            import os as os_module
            for path in [tmp_path, tmp_path.replace('.tar.xz', '_report.html')]:
                if os_module.path.exists(path):
                    try:
                        os_module.unlink(path)
                    except:
                        pass
    
    return render_template_string(UPLOAD_HTML)


@app.route('/health')
def health():
    return {'status': 'ok', 'timestamp': datetime.now().isoformat()}


if __name__ == '__main__':
    print("=" * 50)
    print("🚀 เริ่มเซิร์ฟเวอร์ SOS Report Web Analyzer")
    print("=" * 50)
    print("📍 เปิดเบราว์เซอร์ที่: http://localhost:8080")
    print("📝 Upload หน้าแรกจะแสดงขึ้นมาให้อัปโหลดไฟล์ sosreport")
    print("=" * 50)
    app.run(host='0.0.0.0', port=8080, debug=False)
