"""
HTML Report Generator for sosreport data.
Creates styled, printable web reports with system information.
"""
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import html


class HtmlReportGenerator:
    """Generate HTML reports from parsed sosreport data."""
    
    def __init__(self, data: Dict[str, Any], title: str = "SOS Report"):
        self.data = data
        self.title = title
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def _escape(self, text: str) -> str:
        """HTML-escape text."""
        if text is None:
            return ""
        return html.escape(str(text))
    
    def _format_bytes(self, kb: int) -> str:
        """Format KB to human readable."""
        if kb >= 1024 * 1024:
            return f"{kb / (1024*1024):.2f} GB"
        elif kb >= 1024:
            return f"{kb / 1024:.2f} MB"
        return f"{kb} KB"
    
    def _section(self, title: str, icon: str = "📋", content: str = "") -> str:
        """Generate a section in the report."""
        return f"""
        <div class="section">
            <div class="section-header">
                <span class="section-icon">{icon}</span>
                <h2 class="section-title">{title}</h2>
            </div>
            <div class="section-content">
                {content}
            </div>
        </div>
        """
    
    def _info_table(self, rows: list, cols: int = 2) -> str:
        """Generate a key-value info table."""
        html_rows = ""
        for i in range(0, len(rows), cols):
            html_rows += "<tr>"
            for j in range(cols):
                if i + j < len(rows):
                    key, val = rows[i + j]
                    html_rows += f'<td class="info-key">{self._escape(key)}</td>'
                    if j + 1 < cols:
                        html_rows += f'<td class="info-val">{self._escape(val) if val else "-"}</td>'
                    else:
                        # Last column in a 3-col layout might be empty
                        next_idx = i + j + 1
                        if next_idx < len(rows):
                            html_rows += f'<td class="info-val">{self._escape(rows[next_idx][1]) if rows[next_idx][1] else "-"}</td>'
                            html_rows += f'<td class="info-val"></td>'
                        else:
                            html_rows += f'<td class="info-val">{self._escape(val) if val else "-"}</td>'
                            html_rows += f'<td class="info-val"></td>'
                else:
                    html_rows += '<td></td>'
                    html_rows += '<td></td>'
            html_rows += "</tr>"
        return f'<table class="info-table"><tbody>{html_rows}</tbody></table>'
    
    def _list_items(self, items: list, empty_msg: str = "Not available") -> str:
        """Generate a list of items."""
        if not items:
            return f'<p class="empty-msg">{empty_msg}</p>'
        items_html = "".join(f'<li>{self._escape(item)}</li>' for item in items)
        return f'<ul class="item-list">{items_html}</ul>'
    
    def generate(self) -> str:
        """Generate complete HTML report."""
        d = self.data
        
        # System info section
        sys_rows = [
            ("Hostname", d.get('system', {}).get('hostname', 'Unknown')),
            ("Kernel", d.get('system', {}).get('kernel', 'Unknown')),
            ("OS Version", d.get('system', {}).get('VERSION', '') or d.get('system', {}).get('PRETTY_NAME', 'Unknown')),
            ("Arch", d.get('system', {}).get('BUILD_ID', '')),
            ("Generated", self.timestamp),
            ("Report Archive", d.get('archive', {}).get('name', 'Unknown')),
        ]
        system_html = self._info_table(sys_rows)
        system_section = self._section("System Information", "💻", system_html)
        
        # Hardware section
        hw = d.get('hardware', {})
        hw_rows = []
        if 'model name' in hw:
            hw_rows.append(("CPU", hw['model name']))
        if 'cpu_cores' in hw:
            hw_rows.append(("CPU Cores", str(hw['cpu_cores'])))
        if 'mem_total_gb' in hw:
            hw_rows.append(("Memory", f"{hw['mem_total_gb']} GB"))
        if 'Manufacturer' in hw:
            hw_rows.append(("Manufacturer", hw['Manufacturer']))
        if 'Product Name' in hw:
            hw_rows.append(("Product Name", hw['Product Name']))
        if 'Serial Number' in hw:
            hw_rows.append(("Serial Number", hw['Serial Number']))
            
        # Disks
        disks_html = ""
        if 'disks' in hw and hw['disks']:
            disk_rows = "".join(
                f'<tr><td>{self._escape(d.get("DEVNAME", "-"))}</td><td>{self._escape(d.get("LABEL", "-"))}</td><td>{self._escape(d.get("UUID", "-"))}</td><td>{self._escape(d.get("TYPE", "-"))}</td></tr>'
                for d in hw['disks']
            )
            disks_html = f'<table class="data-table"><thead><tr><th>Device</th><th>Label</th><th>UUID</th><th>Type</th></tr></thead><tbody>{disk_rows}</tbody></table>'
            hw_rows.append(("Storage Devices", f"{len(hw['disks'])} found"))
        
        hardware_html = self._info_table(hw_rows) + (f'<div class="subsection"><h3>Disk Devices</h3>{disks_html}</div>' if disks_html else "")
        hardware_section = self._section("Hardware", "⚙️", hardware_html)
        
        # Network section
        net = d.get('network', {})
        net_rows = []
        if 'interfaces' in net and net['interfaces']:
            for iface in net['interfaces']:
                net_rows.append((f"Interface: {iface.get('name', 'unknown')}", 
                                f"IP: {iface.get('ip', 'N/A')} / MAC: {iface.get('mac', 'N/A')}"))
        
        if 'dns_servers' in net and net['dns_servers']:
            net_rows.append(("DNS Servers", ", ".join(net['dns_servers'])))
        if 'iptables_rules' in net:
            net_rows.append(("Firewall Rules", str(net['iptables_rules'])))
            
        if 'routes' in net and net['routes']:
            routes_list = "".join(f'<li>{self._escape(r)}</li>' for r in net['routes'][:10])
            net_html_extra = f'<div class="subsection"><h3>Sample Routes (first 10)</h3><ul class="item-list">{routes_list}</ul></div>'
        else:
            net_html_extra = ""
            
        network_html = self._info_table(net_rows) + net_html_extra
        network_section = self._section("Network", "🌐", network_html)
        
        # Services section
        svcs = d.get('services', {})
        services_html = ""
        sections = []
        
        if svcs.get('enabled'):
            sections.append(("Enabled Services", svcs['enabled'][:20], f"... and {len(svcs['enabled'])-20} more" if len(svcs['enabled']) > 20 else ""))
        if svcs.get('disabled'):
            sections.append(("Disabled Services", svcs['disabled'][:10], ""))
        if svcs.get('failed'):
            sections.append(("Failed Services", svcs['failed'], "Critical - requires attention"))
            
        for title, items, note in sections:
            list_html = self._list_items(items, note or "None")
            if note:
                list_html += f'<p class="note">{note}</p>'
            services_html += f'<div class="subsection"><h3>{title}</h3>{list_html}</div>'
            
        services_section = self._section("Systemd Services", "🔧", services_html) if services_html else self._section("Systemd Services", "🔧", '<p class="empty-msg">No service data available</p>')
        
        # Logs section
        logs = d.get('logs', {})
        logs_html = ""
        
        if logs.get('journal_errors'):
            errors = logs['journal_errors'][:10]
            errors_html = "".join(f'<li class="log-error">{self._escape(e)}</li>' for e in errors)
            logs_html += f'<div class="subsection"><h3>Recent Errors (Journal)</h3><ul class="log-list">{errors_html}</ul></div>'
            if len(logs['journal_errors']) > 10:
                logs_html += f'<p class="note">... and {len(logs["journal_errors"]) - 10} more errors</p>'
                
        if logs.get('critical_messages'):
            critical = logs['critical_messages'][:10]
            crit_html = "".join(f'<li class="log-critical">{self._escape(c)}</li>' for c in critical)
            logs_html += f'<div class="subsection"><h3>Critical Messages</h3><ul class="log-list">{crit_html}</ul></div>'
            
        logs_section = self._section("Log Summary", "📝", logs_html if logs_html else '<p class="empty-msg">No log data extracted</p>')
        
        # SELinux section
        selinux = d.get('selinux', {})
        selinux_rows = [
            ("Status", selinux.get('status', 'Unknown')),
            ("Configured Mode", selinux.get('configured_mode', 'Unknown')),
        ]
        selinux_section = self._section("SELinux", "🔒", self._info_table(selinux_rows))
        
        # Build complete HTML
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self._escape(self.title)} - SOS Report</title>
    <style>
        :root {{
            --primary: #1a56db;
            --primary-light: #e8f0fe;
            --success: #0d6b3d;
            --warning: #b06000;
            --danger: #b00020;
            --gray: #6b7280;
            --gray-light: #f3f4f6;
            --border: #e5e7eb;
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background: #f9fafb;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        header {{
            background: linear-gradient(135deg, #1a56db 0%, #0d3b8f 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        
        header .subtitle {{
            opacity: 0.9;
            font-size: 14px;
        }}
        
        .section {{
            background: white;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .section-header {{
            background: var(--gray-light);
            padding: 15px 20px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .section-icon {{
            font-size: 20px;
        }}
        
        .section-title {{
            font-size: 18px;
            font-weight: 600;
            color: #111827;
        }}
        
        .section-content {{
            padding: 20px;
        }}
        
        .info-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
        }}
        
        .info-table td {{
            padding: 10px 15px;
            border-bottom: 1px solid var(--border);
            vertical-align: top;
        }}
        
        .info-table .info-key {{
            font-weight: 600;
            color: #374151;
            width: 200px;
            background: var(--gray-light);
        }}
        
        .info-table .info-val {{
            color: #4b5563;
        }}
        
        .info-table tr:last-child td {{
            border-bottom: none;
        }}
        
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        
        .data-table th, .data-table td {{
            padding: 10px 15px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        
        .data-table th {{
            background: var(--gray-light);
            font-weight: 600;
            color: #374151;
        }}
        
        .data-table tr:hover {{
            background: var(--primary-light);
        }}
        
        .item-list {{
            list-style: none;
            margin: 0;
            padding: 0;
        }}
        
        .item-list li {{
            padding: 8px 15px;
            margin-bottom: 5px;
            background: var(--gray-light);
            border-radius: 4px;
            border-left: 3px solid var(--primary);
        }}
        
        .item-list li:hover {{
            background: #fff;
        }}
        
        .log-list {{
            list-style: none;
            margin: 0;
            padding: 0;
        }}
        
        .log-list li {{
            padding: 10px 15px;
            margin-bottom: 5px;
            border-radius: 4px;
            font-family: 'Consolas', monospace;
            font-size: 13px;
        }}
        
        .log-error {{
            background: #fef2f2;
            border-left: 3px solid var(--danger);
            color: #991b1b;
        }}
        
        .log-critical {{
            background: #fff7ed;
            border-left: 3px solid var(--warning);
            color: #9a3412;
        }}
        
        .empty-msg {{
            color: var(--gray);
            font-style: italic;
            padding: 15px;
            text-align: center;
        }}
        
        .note {{
            color: var(--gray);
            font-size: 13px;
            margin-top: 10px;
            padding: 8px;
            background: var(--gray-light);
            border-radius: 4px;
        }}
        
        .subsection {{
            margin-top: 20px;
        }}
        
        .subsection h3 {{
            font-size: 15px;
            margin-bottom: 10px;
            color: #111827;
            border-bottom: 1px solid var(--border);
            padding-bottom: 5px;
        }}
        
        footer {{
            text-align: center;
            padding: 30px;
            color: var(--gray);
            font-size: 13px;
        }}
        
        @media print {{
            body {{ background: white; }}
            .section {{ box-shadow: none; break-inside: avoid; page-break-inside: avoid; }}
            header {{ background: #1a56db !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
        }}
        
        @media (max-width: 768px) {{
            .info-table .info-key {{ width: 120px; font-size: 14px; }}
            .container {{ padding: 10px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{self._escape(self.title)}</h1>
            <div class="subtitle">
                SOS Report Analysis for RHEL 9 | Generated: {self._escape(self.timestamp)}
            </div>
        </header>
        
        {system_section}
        {hardware_section}
        {network_section}
        {services_section}
        {selinux_section}
        {logs_section}
        
        <footer>
            <p>This report was automatically generated from a sosreport archive.</p>
            <p>For RHEL 9 system diagnostics - <a href="https://github.com/sosreport/sosreport" style="color: var(--primary)">sosreport project</a></p>
        </footer>
    </div>
</body>
</html>
"""
        
        return html_content
    
    def save(self, output_path: str):
        """Save report to file."""
        html_content = self.generate()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return output_path
