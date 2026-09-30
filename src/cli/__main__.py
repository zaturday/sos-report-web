"""
CLI entry point for sos-report-web.
Usage:
    python -m src.cli --input sosreport.tar.xz --output report.html
    python -m src.cli --serve --port 8080
"""
import argparse
import sys
from pathlib import Path
from src.parser.sos_parser import SosReportParser
from src.report.html_generator import HtmlReportGenerator


def parse_report(archive_path: str) -> dict:
    """Parse a sosreport archive and return structured data."""
    with SosReportParser(archive_path) as parser:
        return parser.parse_all()


def generate_html_report(data: dict, output_path: str, title: str = "SOS Report"):
    """Generate HTML report from parsed data."""
    generator = HtmlReportGenerator(data, title)
    generator.save(output_path)
    return output_path


def serve_mode(port: int = 8080):
    """Run Flask web server for interactive report generation."""
    try:
        from flask import Flask, request, send_file, render_template_string
        import io
        import tempfile
        
        app = Flask(__name__)
        
        UPLOAD_TEMPLATE = """
        <!DOCTYPE html>
        <html>
        <head><title>Upload SOS Report</title>
        <style>
            body { font-family: system-ui; max-width: 600px; margin: 40px auto; padding: 20px; }
            .upload-box { border: 2px dashed #ccc; padding: 40px; text-align: center; border-radius: 8px; }
            button { background: #1a56db; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
            button:hover { background: #0d3b8f; }
            .info { margin-top: 20px; color: #666; }
        </style>
        </head>
        <body>
            <h1>SOS Report Web Analyzer</h1>
            <div class="upload-box">
                <p>Select your sosreport archive (tar.xz or tar.gz)</p>
                <form method="post" enctype="multipart/form-data">
                    <input type="file" name="sosreport" accept=".tar.xz,.txz,.tar.gz,.tgz" required>
                    <br><br>
                    <button type="submit">Generate Report</button>
                </form>
            </div>
            <p class="info">Report will be generated and displayed in browser.</p>
        </body>
        </html>
        """
        
        REPORT_TEMPLATE = """
        <!DOCTYPE html>
        <html>
        <head><title>SOS Report - Analysis</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: system-ui; margin: 0; padding: 0; background: #f9fafb; }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            header { background: linear-gradient(135deg, #1a56db 0%, #0d3b8f 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .section { background: white; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden; }
            .section-header { background: #f3f4f6; padding: 12px 16px; border-bottom: 1px solid #e5e7eb; display: flex; align-items: center; gap: 8px; }
            .section-content { padding: 15px; }
            table { width: 100%; border-collapse: collapse; }
            td { padding: 8px 12px; border-bottom: 1px solid #e5e7eb; }
            .key { font-weight: 600; width: 180px; background: #f3f4f6; }
            .val { color: #4b5563; }
            ul { list-style: none; padding: 0; margin: 0; }
            li { padding: 6px 10px; margin: 3px 0; background: #f3f4f6; border-radius: 4px; border-left: 3px solid #1a56db; }
            .error { background: #fef2f2; border-left-color: #b00020; color: #991b1b; }
            .critical { background: #fff7ed; border-left-color: #b06000; color: #9a3412; }
            .empty { color: #6b7280; font-style: italic; text-align: center; padding: 15px; }
            h3 { font-size: 14px; margin: 15px 0 8px; padding-bottom: 5px; border-bottom: 1px solid #e5e7eb; }
            .actions { margin-top: 20px; display: flex; gap: 10px; }
            .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; font-size: 14px; }
            .btn-download { background: #1a56db; color: white; }
            .btn-print { background: #6b7280; color: white; }
        </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>{{ title }}</h1>
                    <div style="opacity: 0.9; font-size: 13px;">Generated: {{ timestamp }}</div>
                </header>
                {% for section in sections %}
                <div class="section">
                    <div class="section-header">
                        <span>{{ section.icon }}</span>
                        <h2>{{ section.title }}</h2>
                    </div>
                    <div class="section-content">
                        {{ section.content|safe }}
                    </div>
                </div>
                {% endfor %}
                <div class="actions">
                    <a href="/download" class="btn btn-download">📥 Download HTML</a>
                    <button onclick="window.print()" class="btn btn-print">🖨️ Print</button>
                </div>
            </div>
        </body>
        </html>
        """
        
        def build_sections(data):
            sections = []
            
            # System
            sys_rows = ""
            for k, v in data.get('system', {}).items():
                sys_rows += f'<tr><td class="key">{k}</td><td class="val">{v}</td></tr>'
            sections.append({
                'icon': '💻',
                'title': 'System Information',
                'content': f'<table>{sys_rows}</table>' if sys_rows else '<div class="empty">No system data</div>'
            })
            
            # Hardware
            hw = data.get('hardware', {})
            hw_rows = ""
            for k, v in hw.items():
                if k != 'disks' and v:
                    hw_rows += f'<tr><td class="key">{k}</td><td class="val">{v}</td></tr>'
            sections.append({
                'icon': '⚙️',
                'title': 'Hardware',
                'content': f'<table>{hw_rows}</table>' if hw_rows else '<div class="empty">No hardware data</div>'
            })
            
            # Network
            net = data.get('network', {})
            net_rows = ""
            if net.get('interfaces'):
                for iface in net['interfaces']:
                    net_rows += f'<tr><td class="key">{iface.get("name", "?")}</td><td class="val">IP: {iface.get("ip", "N/A")} / MAC: {iface.get("mac", "N/A")}</td></tr>'
            if net.get('dns_servers'):
                net_rows += f'<tr><td class="key">DNS</td><td class="val">{", ".join(net["dns_servers"])}</td></tr>'
            sections.append({
                'icon': '🌐',
                'title': 'Network',
                'content': f'<table>{net_rows}</table>' if net_rows else '<div class="empty">No network data</div>'
            })
            
            # Services
            svcs = data.get('services', {})
            svc_html = ""
            if svcs.get('failed'):
                svc_html += '<h3>⚠️ Failed Services</h3><ul>'
                for s in svcs['failed'][:10]:
                    svc_html += f'<li class="error">{s}</li>'
                svc_html += '</ul>'
            if svcs.get('enabled'):
                svc_html += '<h3>Enabled Services (sample)</h3><ul>'
                for s in svcs['enabled'][:15]:
                    svc_html += f'<li>{s}</li>'
                svc_html += '</ul>'
            sections.append({
                'icon': '🔧',
                'title': 'Systemd Services',
                'content': svc_html if svc_html else '<div class="empty">No service data</div>'
            })
            
            # Logs
            logs = data.get('logs', {})
            log_html = ""
            if logs.get('journal_errors'):
                log_html += '<h3>Errors (Journal)</h3><ul>'
                for e in logs['journal_errors'][:8]:
                    log_html += f'<li class="error">{e}</li>'
                log_html += '</ul>'
            if logs.get('critical_messages'):
                log_html += '<h3>Critical Messages</h3><ul>'
                for c in logs['critical_messages'][:8]:
                    log_html += f'<li class="critical">{c}</li>'
                log_html += '</ul>'
            sections.append({
                'icon': '📝',
                'title': 'Log Summary',
                'content': log_html if log_html else '<div class="empty">No log data</div>'
            })
            
            return sections
        
        @app.route('/', methods=['GET', 'POST'])
        def upload():
            if request.method == 'POST':
                if 'sosreport' not in request.files:
                    return "No file uploaded", 400
                file = request.files['sosreport']
                if file.filename == '':
                    return "No file selected", 400
                
                # Save to temp file
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.tar.xz', delete=False) as tmp:
                    file.save(tmp.name)
                    tmp_path = tmp.name
                
                try:
                    data = parse_report(tmp_path)
                    data['archive'] = {'name': file.filename}
                    
                    sections = build_sections(data)
                    timestamp = __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    return render_template_string(
                        REPORT_TEMPLATE,
                        title=f"SOS Report - {file.filename}",
                        timestamp=timestamp,
                        sections=sections
                    )
                finally:
                    import os
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
            
            return render_template_string(UPLOAD_TEMPLATE)
        
        @app.route('/download')
        def download():
            # This would need session state in production
            return "Download functionality requires state management. Use --output flag for CLI.", 404
        
        print(f"🚀 Starting web server at http://localhost:{port}")
        print("   Upload a sosreport file to generate analysis.")
        app.run(host='0.0.0.0', port=port, debug=False)
        
    except ImportError:
        print("❌ Flask not installed. Run: pip install flask")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="SOS Report Web Analyzer for RHEL 9",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate HTML report from archive
  python -m src.cli --input sosreport.tar.xz --output report.html
  
  # Start web server
  python -m src.cli --serve --port 8080
        """
    )
    
    parser.add_argument('--input', '-i', help='Path to sosreport archive (tar.xz or tar.gz)')
    parser.add_argument('--output', '-o', help='Output HTML file path')
    parser.add_argument('--title', '-t', default='SOS Report', help='Report title')
    parser.add_argument('--serve', action='store_true', help='Run as web server')
    parser.add_argument('--port', '-p', type=int, default=8080, help='Port for web server (default: 8080)')
    
    args = parser.parse_args()
    
    if args.serve:
        serve_mode(args.port)
        return
    
    if not args.input:
        parser.error("❌ --input is required (or use --serve for web mode)")
    
    if not args.output:
        parser.error("❌ --output is required for CLI mode")
    
    print(f"📦 Parsing: {args.input}")
    data = parse_report(args.input)
    
    print(f"📄 Generating: {args.output}")
    generate_html_report(data, args.output, args.title)
    
    print(f"✅ Report generated successfully!")
    print(f"   Open {args.output} in browser to view.")


if __name__ == '__main__':
    main()
