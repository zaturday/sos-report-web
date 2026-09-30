#!/usr/bin/env python3
"""Patch app.py: English UI + comprehensive network/services parser"""
import re

with open('C:/Users/zatur/sos-report-web/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace UPLOAD_PAGE
old_upload_start = content.find("UPLOAD_PAGE = '''")
old_upload_end = content.find("'''", old_upload_start + 20) + 3
new_upload = """UPLOAD_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SOS Report Web Analyzer</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: system-ui; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
        .container { background: white; padding: 40px; border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); max-width: 550px; width: 100%; }
        h1 { color: #333; margin-bottom: 10px; font-size: 26px; text-align: center; }
        .subtitle { color: #666; margin-bottom: 30px; font-size: 14px; text-align: center; }
        .upload-area { border: 2px dashed #ddd; border-radius: 12px; padding: 40px 20px; text-align: center; transition: all 0.3s; background: #fafafa; cursor: pointer; }
        .upload-area:hover, .upload-area.dragover { border-color: #667eea; background: #f0f0ff; }
        .upload-icon { font-size: 64px; margin-bottom: 20px; }
        .upload-text { color: #666; margin-bottom: 25px; font-size: 15px; }
        .upload-text.dragover { color: #667eea; font-weight: 500; }
        input[type="file"] { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; background: white; display: none; }
        button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 14px 30px; border-radius: 6px; font-size: 16px; cursor: pointer; margin-top: 25px; width: 100%; font-weight: 500; }
        .info { margin-top: 25px; font-size: 12px; color: #999; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>SOS Report Web Analyzer</h1>
        <p class="subtitle">Upload sosreport to analyze RHEL 9 system</p>
        <form method="post" enctype="multipart/form-data">
            <div class="upload-area" id="drop-zone">
                <div class="upload-icon">📁</div>
                <p class="upload-text" id="upload-text">Select sosreport file (tar.xz or tar.gz)<br>or drag and drop here</p>
                <input type="file" name="sosreport" id="file-input" accept=".tar.xz,.txz,.tar.gz,.tgz,.tar,.gz,.xz" required>
            </div>
            <button type="submit">Analyze Report</button>
        </form>
        <p class="info">Supports sosreport from RHEL 9 | Analyzes: System Info, Hardware, Network, Services, Logs, SELinux</p>
    </div>
    <script>
        const dz = document.getElementById('drop-zone');
        const fi = document.getElementById('file-input');
        const ut = document.getElementById('upload-text');
        dz.addEventListener('click', () => fi.click());
        dz.addEventListener('dragover', (e) => { e.preventDefault(); dz.classList.add('dragover'); ut.classList.add('dragover'); });
        dz.addEventListener('dragleave', (e) => { e.preventDefault(); dz.classList.remove('dragover'); ut.classList.remove('dragover'); });
        dz.addEventListener('drop', (e) => { e.preventDefault(); dz.classList.remove('dragover'); ut.classList.remove('dragover'); const files = e.dataTransfer.files; if (files.length > 0) { fi.files = files; document.querySelector('form').submit(); } });
    </script>
</body>
</html>
'''"""
content = content[:old_upload_start] + new_upload + content[old_upload_end:]

# 2. Replace ERROR_PAGE
old_err_start = content.find("ERROR_PAGE = '''")
old_err_end = content.find("'''", old_err_start + 20) + 3
new_err = """ERROR_PAGE = '''
<!DOCTYPE html>
<html>
<head><title>Error</title>
<style>body { font-family: system-ui; padding: 40px; text-align: center; background: #f5f5f5; } .error-box { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); max-width: 500px; margin: 50px auto; } h1 { color: #b00020; } p { color: #666; } a { color: #667eea; text-decoration: none; }</style></head>
<body><div class="error-box"><h1>Error</h1><p>{{ error }}</p><a href="/">Back to upload</a></div></body></html>
'''"""
content = content[:old_err_start] + new_err + content[old_err_end:]

# 3. Replace parse_sosreport function
old_parse_start = content.find('def parse_sosreport(')
old_parse_end = content.find('\ndef build_report_html(')
new_parse = '''def parse_sosreport(archive_path: str) -> dict:
    """Parse sosreport archive and extract comprehensive system information."""
    data = {
        'system': {},
        'hardware': {},
        'network': {'interfaces': [], 'routes': [], 'arp': [], 'dns': [], 'firewall_rules': [], 'bonding': []},
        'services': {'enabled': [], 'disabled': [], 'failed': [], 'running': []},
        'logs': {'errors': [], 'critical': []},
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
            
            # === SYSTEM INFO ===
            for name, content in files.items():
                if '/etc/hostname' in name and 'sos_commands' not in name:
                    data['system']['hostname'] = content.strip().split('\\n')[0]
                    break
                if 'sos_commands/host/hostname' in name:
                    data['system']['hostname'] = content.strip().split('\\n')[0]
                    break
            
            for name, content in files.items():
                if 'sos_commands/kernel/uname_-a' in name:
                    data['system']['kernel'] = content.strip().split('\\n')[0]
                    break
            
            for name, content in files.items():
                if '/etc/os-release' in name or '/usr/lib/os-release' in name:
                    for line in content.split('\\n'):
                        if '=' in line:
                            k, v = line.split('=', 1)
                            data['system'][k.strip()] = v.strip().strip('"')
                    break
            
            # === HARDWARE ===
            for name, content in files.items():
                if '/proc/cpuinfo' in name:
                    for line in content.split('\\n'):
                        if 'model name' in line:
                            data['hardware']['cpu'] = line.split(':', 1)[1].strip()
                        if 'cpu cores' in line:
                            m = re.search(r'(\\d+)', line)
                            if m: data['hardware']['cpu_cores'] = m.group(1)
                    break
            
            for name, content in files.items():
                if '/proc/meminfo' in name:
                    for line in content.split('\\n'):
                        if 'MemTotal' in line:
                            m = re.search(r'(\\d+)', line)
                            if m: data['hardware']['mem_total'] = f"{int(m.group(1))/1024/1024:.1f} GB"
                    break
            
            for name, content in files.items():
                if 'sos_commands/hardware/dmidecode' in name:
                    for line in content.split('\\n'):
                        if 'Manufacturer' in line:
                            data['hardware']['manufacturer'] = line.split(':', 1)[1].strip()
                        if 'Product Name' in line:
                            data['hardware']['product'] = line.split(':', 1)[1].strip()
                    break
            
            # === NETWORK - IP addresses ===
            for name, content in files.items():
                if 'sos_commands/networking/ip_-o_addr' in name or 'sos_commands/networking/ip_addr' in name:
                    interfaces = []
                    current_iface = None
                    for line in content.split('\\n'):
                        m = re.match(r'(\\d+):\\s+(\\S+)\\s+inet\\s+(\\S+)', line)
                        if m:
                            idx, iface_name, ip_cidr = m.groups()
                            current_iface = {'name': iface_name, 'ip': ip_cidr, 'mac': '', 'state': ''}
                            interfaces.append(current_iface)
                        elif current_iface and 'link/' in line:
                            m = re.search(r'link/(\\S+)', line)
                            if m:
                                current_iface['mac'] = m.group(1)
                        elif current_iface and 'state' in line:
                            m = re.search(r'state\\s+(\\S+)', line)
                            if m:
                                current_iface['state'] = m.group(1)
                    if interfaces:
                        data['network']['interfaces'] = interfaces
                    break
            
            # === NETWORK - Link info ===
            for name, content in files.items():
                if 'sos_commands/networking/ip_-s_-d_link' in name or 'sos_commands/networking/ip_link' in name:
                    for line in content.split('\\n'):
                        if 'link/' in line and ':' in line:
                            parts = line.split()
                            if len(parts) >= 2:
                                iface_name = parts[0].rstrip(':')
                                mac = ''
                                state = ''
                                for p in parts:
                                    if p.startswith('link/'):
                                        mac = p.split('/', 1)[1]
                                    if p == 'UP' or p == 'DOWN':
                                        state = p
                                found = False
                                for iface in data['network']['interfaces']:
                                    if iface['name'] == iface_name:
                                        if not iface['mac'] and mac:
                                            iface['mac'] = mac
                                        if not iface['state'] and state:
                                            iface['state'] = state
                                        found = True
                                        break
                                if not found:
                                    data['network']['interfaces'].append({'name': iface_name, 'ip': 'N/A', 'mac': mac, 'state': state})
                    break
            
            # === NETWORK - Bonding ===
            for name, content in files.items():
                if 'sos_commands/networking/ifenslave_-a' in name:
                    bond_info = []
                    current_bond = None
                    for line in content.split('\\n'):
                        if 'Bonding Mode:' in line or 'Currently Active Slave:' in line:
                            if current_bond:
                                bond_info.append(current_bond)
                            current_bond = {'mode': '', 'active_slave': '', 'slaves': []}
                        elif current_bond:
                            if 'Bonding Mode:' in line:
                                current_bond['mode'] = line.split(':', 1)[1].strip()
                            elif 'Currently Active Slave:' in line:
                                current_bond['active_slave'] = line.split(':', 1)[1].strip()
                            elif 'Slave Interface:' in line:
                                current_bond['slaves'].append(line.split(':', 1)[1].strip())
                    if current_bond:
                        bond_info.append(current_bond)
                    if bond_info:
                        data['network']['bonding'] = bond_info
                    break
            
            # === NETWORK - Routes ===
            for name, content in files.items():
                if 'sos_commands/networking/ip_route_show_table_all' in name or 'sos_commands/networking/ip_-6_route_show_table_all' in name:
                    routes = []
                    for line in content.split('\\n'):
                        line = line.strip()
                        if line and not line.startswith('broadcast') and not line.startswith('local'):
                            routes.append(line)
                    if routes:
                        data['network']['routes'] = routes[:20]
                    break
            
            # === NETWORK - ARP table ===
            for name, content in files.items():
                if 'sos_commands/networking/ip_neigh_show_nud_noarp' in name:
                    arp = []
                    for line in content.split('\\n'):
                        line = line.strip()
                        if line and not line.startswith('Address'):
                            arp.append(line)
                    if arp:
                        data['network']['arp'] = arp[:15]
                    break
            
            # === NETWORK - DNS ===
            for name, content in files.items():
                if '/etc/resolv.conf' in name:
                    dns = []
                    for line in content.split('\\n'):
                        if line.startswith('nameserver'):
                            parts = line.split()
                            if len(parts) > 1:
                                dns.append(parts[1])
                    if dns:
                        data['network']['dns'] = dns
                    break
            
            # === NETWORK - Firewall rules ===
            for name, content in files.items():
                if 'sos_commands/networking/ip_-4_rule_list' in name:
                    rules = []
                    for line in content.split('\\n'):
                        line = line.strip()
                        if line:
                            rules.append(line)
                    if rules:
                        data['network']['firewall_rules'] = rules[:15]
                    break
            
            # === SERVICES ===
            all_enabled = []
            all_disabled = []
            all_failed = []
            all_running = []
            for name, content in files.items():
                if 'sos_commands' in name and 'systemctl_status' in name:
                    lines = content.split('\\n')
                    for i, line in enumerate(lines):
                        if line.startswith('\\u25CF') or line.startswith('\\u25CB'):
                            parts = line.split()
                            if len(parts) >= 2:
                                svc_full = parts[1] if len(parts) > 1 else ''
                                svc_name = svc_full.replace('.service', '') if '.service' in svc_full else svc_full
                                if i + 1 < len(lines):
                                    nl = lines[i + 1]
                                    if 'enabled' in nl.lower() and 'disabled' not in nl.lower():
                                        all_enabled.append(svc_name)
                                    elif 'disabled' in nl.lower():
                                        all_disabled.append(svc_name)
                                if i + 2 < len(lines):
                                    al = lines[i + 2] if i + 2 < len(lines) else ''
                                    if 'failed' in al.lower():
                                        all_failed.append(svc_name)
                                    elif 'active (running)' in al.lower():
                                        all_running.append(svc_name)
            
            for name, content in files.items():
                if 'sos_commands/systemd/systemctl_list-units' in name:
                    for line in content.split('\\n'):
                        line = line.strip()
                        if line and not line.startswith('UNIT') and not line.startswith('LOAD') and not line.startswith('ACTIVE') and not line.startswith('SUB') and not line.startswith('DESCRIPTION'):
                            parts = line.split()
                            if len(parts) >= 4:
                                svc_name = parts[0]
                                load_state = parts[1]
                                active_state = parts[2]
                                if 'enabled' in load_state.lower():
                                    all_enabled.append(svc_name)
                                elif 'disabled' in load_state.lower():
                                    all_disabled.append(svc_name)
                                if 'failed' in active_state.lower():
                                    all_failed.append(svc_name)
                                elif 'active' in active_state.lower():
                                    all_running.append(svc_name)
            
            if all_enabled:
                data['services']['enabled'] = list(set(all_enabled))[:30]
            if all_disabled:
                data['services']['disabled'] = list(set(all_disabled))[:30]
            if all_failed:
                data['services']['failed'] = list(set(all_failed))
            if all_running:
                data['services']['running'] = list(set(all_running))[:30]
            
            # === LOGS ===
            for name, content in files.items():
                if 'journalctl' in name and 'sos_commands' in name:
                    errors = []
                    for line in content.split('\\n'):
                        if 'ERROR' in line or 'error' in line.lower() or 'FAILED' in line:
                            errors.append(line.strip()[:150])
                    if errors:
                        data['logs']['errors'].extend(errors[:10])
                    break
            
            for name, content in files.items():
                if 'var.log.messages' in name:
                    critical = []
                    for line in content.split('\\n'):
                        if any(x in line.lower() for x in ['crit', 'alert', 'emerg', 'error']):
                            critical.append(line.strip()[:150])
                    if critical:
                        data['logs']['critical'].extend(critical[:10])
                    break
            
            # === SELINUX ===
            for name, content in files.items():
                if '/etc/selinux/config' in name:
                    for line in content.split('\\n'):
                        if line.startswith('SELINUX='):
                            m = re.search(r'SELINUX=(enforcing|permissive|disabled)', line)
                            if m: data['selinux']['mode'] = m.group(1)
                    break
            
            # === SOSREPORT DATE ===
            for name, content in files.items():
                if 'version.txt' in name and 'sosreport' in name.lower():
                    m = re.search(r'\\d{4}-\\d{2}-\\d{2}', content)
                    if m: data['system']['sosdate'] = m.group(0)
                    break
        
        return data
    except Exception as e:
        raise Exception(f"Cannot read file: {str(e)}")

'''
content = content[:old_parse_start] + new_parse + content[old_parse_end:]

# 4. Replace build_report_html function
old_build_start = content.find('def build_report_html(')
old_build_end = content.find('\n\n@app.route')
new_build = '''def build_report_html(data: dict, filename: str) -> str:
    """Build comprehensive HTML report from parsed data."""
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def row(k, v):
        return f'<tr><td style="padding:10px 15px;border-bottom:1px solid #eee;font-weight:600;width:220px;background:#f5f5f5">{k}</td><td style="padding:10px 15px;border-bottom:1px solid #eee">{v}</td></tr>'
    
    def rows(items):
        r = ''
        for k, v in items:
            if v:
                r += row(k, v)
        if not r:
            r = '<tr><td colspan="2" style="padding:20px;text-align:center;color:#999">No data available</td></tr>'
        return r
    
    # System
    sys_rows = rows([(k, v) for k, v in data.get('system', {}).items() if v])
    
    # Hardware
    hw_rows = rows([(k, v) for k, v in data.get('hardware', {}).items() if v])
    
    # Network - Interfaces
    net_rows = ''
    for iface in data.get('network', {}).get('interfaces', []):
        name = iface.get('name', '?')
        ip = iface.get('ip', 'N/A')
        mac = iface.get('mac', 'N/A')
        state = iface.get('state', 'N/A')
        net_rows += f'<tr><td style="padding:10px 15px;border-bottom:1px solid #eee;font-weight:600;width:220px;background:#f5f5f5">{name}</td><td style="padding:10px 15px;border-bottom:1px solid #eee">IP: {ip} | MAC: {mac} | State: {state}</td></tr>'
    
    # Network - Bonding
    for bond in data.get('network', {}).get('bonding', []):
        mode = bond.get('mode', 'N/A')
        active = bond.get('active_slave', 'N/A')
        slaves = ', '.join(bond.get('slaves', []))
        net_rows += f'<tr><td style="padding:10px 15px;border-bottom:1px solid #eee;font-weight:600;width:220px;background:#f5f5f5">Bonding</td><td style="padding:10px 15px;border-bottom:1px solid #eee">Mode: {mode} | Active: {active} | Slaves: {slaves}</td></tr>'
    
    # Network - DNS
    dns = ', '.join(data.get('network', {}).get('dns', []))
    if dns:
        net_rows += row('DNS Servers', dns)
    
    # Network - Routes
    routes = data.get('network', {}).get('routes', [])
    if routes:
        net_rows += row('Routes', '<br>'.join(routes))
    
    # Network - ARP
    arp = data.get('network', {}).get('arp', [])
    if arp:
        net_rows += row('ARP Table', '<br>'.join(arp))
    
    # Network - Firewall
    fw = data.get('network', {}).get('firewall_rules', [])
    if fw:
        net_rows += row('Firewall Rules', '<br>'.join(fw))
    
    if not net_rows:
        net_rows = '<tr><td colspan="2" style="padding:20px;text-align:center;color:#999">No network data available</td></tr>'
    
    # Services
    enabled = data.get('services', {}).get('enabled', [])
    disabled = data.get('services', {}).get('disabled', [])
    failed = data.get('services', {}).get('failed', [])
    running = data.get('services', {}).get('running', [])
    
    svc_html = ''
    if enabled:
        svc_html += '<h3 style="margin:15px 0 10px;padding-bottom:5px;border-bottom:1px solid #eee;font-size:14px">Enabled Services</h3><ul>'
        for s in enabled[:15]:
            svc_html += f'<li style="padding:6px 12px;margin:4px 0;background:#f5f5f5;border-radius:4px;border-left:3px solid #1a56db;font-family:monospace;font-size:13px">{s}</li>'
        svc_html += '</ul>'
        if len(enabled) > 15:
            svc_html += f'<p style="color:#999;font-size:12px;margin-top:10px">And {len(enabled)-15} more</p>'
    
    if running:
        svc_html += '<h3 style="margin:15px 0 10px;padding-bottom:5px;border-bottom:1px solid #eee;font-size:14px">Running Services</h3><ul>'
        for s in running[:15]:
            svc_html += f'<li style="padding:6px 12px;margin:4px 0;background:#f0fff0;border-radius:4px;border-left:3px solid #0d6b3d;font-family:monospace;font-size:13px">{s}</li>'
        svc_html += '</ul>'
        if len(running) > 15:
            svc_html += f'<p style="color:#999;font-size:12px;margin-top:10px">And {len(running)-15} more</p>'
    
    if disabled:
        svc_html += '<h3 style="margin:15px 0 10px;padding-bottom:5px;border-bottom:1px solid #eee;font-size:14px">Disabled Services</h3><ul>'
        for s in disabled[:10]:
            svc_html += f'<li style="padding:6px 12px;margin:4px 0;background:#f5f5f5;border-radius:4px;border-left:3px solid #999;font-family:monospace;font-size:13px">{s}</li>'
        svc_html += '</ul>'
    
    if failed:
        svc_html += '<h3 style="margin:15px 0 10px;padding-bottom:5px;border-bottom:1px solid #eee;font-size:14px;color:#b00020">Failed Services</h3><ul>'
        for s in failed[:10]:
            svc_html += f'<li style="padding:6px 12px;margin:4px 0;background:#fef2f2;border-radius:4px;border-left:3px solid #b00020;color:#991b1b;font-family:monospace;font-size:13px">{s}</li>'
        svc_html += '</ul>'
    
    if not svc_html:
        svc_html = '<div style="padding:20px;text-align:center;color:#999">No service data available</div>'
    
    # Logs
    logs_html = ''
    for err in data.get('logs', {}).get('errors', [])[:8]:
        logs_html += f'<li style="padding:8px 12px;margin:4px 0;background:#fff7ed;border-radius:4px;border-left:3px solid #b06000;color:#9a3412;font-family:monospace;font-size:12px">{err}</li>'
    for crit in data.get('logs', {}).get('critical', [])[:5]:
        logs_html += f'<li style="padding:8px 12px;margin:4px 0;background:#fff7ed;border-radius:4px;border-left:3px solid #b06000;color:#9a3412;font-family:monospace;font-size:12px">{crit}</li>'
    if logs_html:
        logs_html = f'<ul>{logs_html}</ul>'
    else:
        logs_html = '<div style="padding:20px;text-align:center;color:#999">No errors found in logs</div>'
    
    # SELinux
    selinux_rows = rows([(k, v) for k, v in data.get('selinux', {}).items() if v])
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SOS Report - {filename}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 12px; margin-bottom: 20px; }}
        header h1 {{ font-size: 24px; margin-bottom: 5px; }}
        header .sub {{ opacity: 0.9; font-size: 13px; }}
        .card {{ background: white; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); overflow: hidden; }}
        .card-header {{ background: #f5f5f5; padding: 15px 20px; border-bottom: 1px solid #eee; display: flex; align-items: center; gap: 10px; }}
        .card-header .icon {{ font-size: 20px; }}
        .card-header h2 {{ font-size: 16px; font-weight: 600; color: #111; }}
        .card-body {{ padding: 15px 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        li {{ list-style: none; }}
        .actions {{ margin-top: 20px; display: flex; gap: 10px; }}
        .btn {{ padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; font-size: 14px; }}
        .btn-primary {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
        .btn-secondary {{ background: #666; color: white; }}
        @media print {{ .actions {{ display: none; }} header {{ background: #667eea !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }} }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>SOS Report</h1>
            <div class="sub">File: {filename} | Generated: {ts}</div>
        </header>
        
        <div class="card">
            <div class="card-header"><span class="icon">💻</span><h2>System Information</h2></div>
            <div class="card-body"><table>{sys_rows}</table></div>
        </div>
        
        <div class="card">
            <div class="card-header"><span class="icon">⚙️</span><h2>Hardware</h2></div>
            <div class="card-body"><table>{hw_rows}</table></div>
        </div>
        
        <div class="card">
            <div class="card-header"><span class="icon">🌐</span><h2>Network</h2></div>
            <div class="card-body"><table>{net_rows}</table></div>
        </div>
        
        <div class="card">
            <div class="card-header"><span class="icon">🔧</span><h2>Services (Systemd)</h2></div>
            <div class="card-body">{svc_html}</div>
        </div>
        
        <div class="card">
            <div class="card-header"><span class="icon">📝</span><h2>Log Errors</h2></div>
            <div class="card-body">{logs_html}</div>
        </div>
        
        <div class="card">
            <div class="card-header"><span class="icon">🔒</span><h2>SELinux</h2></div>
            <div class="card-body"><table>{selinux_rows}</table></div>
        </div>
        
        <div class="actions">
            <a href="/" class="btn btn-primary">Upload New File</a>
            <button onclick="window.print()" class="btn btn-secondary">Print Report</button>
        </div>
    </div>
</body>
</html>"""  '''
content = content[:old_build_start] + new_build + content[old_build_end:]

# 5. Replace main block
old_main_start = content.find("if __name__ == '__main__':")
new_main = """if __name__ == '__main__':
    print("=" * 60)
    print("SOS Report Web Analyzer")
    print("=" * 60)
    print("Open browser at: http://localhost:8080")
    print("Drag & drop file to upload")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8080, debug=False)
"""
content = content[:old_main_start] + new_main

with open('C:/Users/zatur/sos-report-web/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f'✅ Updated app.py ({len(content)} chars)')
print('Changes:')
print('  1. UPLOAD_PAGE → English')
print('  2. ERROR_PAGE → English')
print('  3. parse_sosreport → comprehensive (network: IP/MAC/bonding/routes/ARP/firewall; services: enabled/disabled/failed/running)')
print('  4. build_report_html → shows all network + service details')
print('  5. Main block → English messages')
