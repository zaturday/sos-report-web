#!/usr/bin/env python3
"""Patch app.py: 413 error handler + compact report styling"""
import re

with open('C:/Users/zatur/sos-report-web/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add 413 error handler right after app.config MAX_CONTENT_LENGTH
old_config = "app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload"
new_config = """app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload


@app.errorhandler(413)
def request_entity_too_large(e):
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>File Too Large</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: system-ui, sans-serif; background: #f5f5f5; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
        .error-container { background: white; padding: 30px 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); max-width: 480px; width: 100%; text-align: center; }
        .error-icon { font-size: 56px; margin-bottom: 15px; }
        h1 { color: #b00020; font-size: 22px; margin-bottom: 8px; font-weight: 600; }
        p { color: #666; font-size: 14px; line-height: 1.5; margin-bottom: 20px; }
        .info { background: #fff7ed; border-left: 3px solid #b06000; padding: 12px 15px; border-radius: 4px; margin-bottom: 20px; font-size: 13px; color: #9a3412; }
        button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 12px 28px; border-radius: 6px; font-size: 14px; cursor: pointer; font-weight: 500; text-decoration: none; display: inline-block; }
        .back-link { display: inline-block; }
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-icon">⚠️</div>
        <h1>File Too Large</h1>
        <p>The file you tried to upload exceeds the maximum allowed size.</p>
        <div class="info"><strong>Maximum:</strong> 500 MB per file<br>Please try a smaller sosreport file.</div>
        <a href="/" class="back-link"><button>Back to Upload</button></a>
    </div>
</body>
</html>''', 413

"""
content = content.replace(old_config, new_config)

# 2. Make report page more compact - replace the report CSS
old_report_css = """    <style>
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
    </style>"""

new_report_css = """    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 15px; color: #333; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 18px 25px; border-radius: 8px; margin-bottom: 12px; }}
        header h1 {{ font-size: 18px; margin-bottom: 3px; }}
        header .sub {{ opacity: 0.9; font-size: 12px; }}
        .card {{ background: white; border-radius: 8px; margin-bottom: 10px; box-shadow: 0 1px 6px rgba(0,0,0,0.06); overflow: hidden; }}
        .card-header {{ background: #f8f9fa; padding: 10px 18px; border-bottom: 1px solid #eee; display: flex; align-items: center; gap: 8px; }}
        .card-header .icon {{ font-size: 16px; }}
        .card-header h2 {{ font-size: 14px; font-weight: 600; color: #111; }}
        .card-body {{ padding: 10px 18px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        td {{ padding: 6px 10px; border-bottom: 1px solid #f0f0f0; }}
        li {{ list-style: none; padding: 4px 8px; margin: 2px 0; font-size: 12px; }}
        .actions {{ margin-top: 12px; display: flex; gap: 8px; }}
        .btn {{ padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; font-size: 12px; font-weight: 500; }}
        .btn-primary {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
        .btn-secondary {{ background: #666; color: white; }}
        .print-only {{ display: none; }}
        @media print {{
            .actions {{ display: none; }}
            header {{ background: #667eea !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            body {{ padding: 0; background: white; }}
            .container {{ max-width: 100%; }}
            .card {{ box-shadow: none; margin-bottom: 8px; }}
            .print-only {{ display: block; }}
        }}
    </style>"""

content = content.replace(old_report_css, new_report_css)

# 3. Add compact table styling to the row() function in build_report_html
old_row_fn = """    def row(k, v):
        return f'<tr><td style="padding:10px 15px;border-bottom:1px solid #eee;font-weight:600;width:220px;background:#f5f5f5">{k}</td><td style="padding:10px 15px;border-bottom:1px solid #eee">{v}</td></tr>'"""
new_row_fn = """    def row(k, v):
        return f'<tr><td style="padding:6px 10px;border-bottom:1px solid #eee;font-weight:600;width:200px;background:#f8f9fa;font-size:13px">{k}</td><td style="padding:6px 10px;border-bottom:1px solid #eee;font-size:13px">{v}</td></tr>'"""
content = content.replace(old_row_fn, new_row_fn)

# 4. Make service list items compact
old_svc_items = [
    ("Enabled Services</h3><ul>",
     "Enabled Services</h3><ul style='margin:0;padding:0'>"),
    ("Running Services</h3><ul>",
     "Running Services</h3><ul style='margin:0;padding:0'>"),
    ("Disabled Services</h3><ul>",
     "Disabled Services</h3><ul style='margin:0;padding:0'>"),
    ("Failed Services</h3><ul>",
     "Failed Services</h3><ul style='margin:0;padding:0'>"),
]
for old, new in old_svc_items:
    content = content.replace(old, new)

# 5. Compact the log items
old_log_style = "padding:8px 12px;margin:4px 0;background:#fff7ed;border-radius:4px;border-left:3px solid #b06000;color:#9a3412;font-family:monospace;font-size:12px"
new_log_style = "padding:4px 8px;margin:2px 0;background:#fff7ed;border-radius:3px;border-left:3px solid #b06000;color:#9a3412;font-family:monospace;font-size:11px"
content = content.replace(old_log_style, new_log_style)

# 6. Compact service items
old_svc_style = "padding:6px 12px;margin:4px 0;background:#f5f5f5;border-radius:4px;border-left:3px solid #1a56db;font-family:monospace;font-size:13px"
new_svc_style = "padding:4px 8px;margin:2px 0;background:#f5f5f5;border-radius:3px;border-left:3px solid #1a56db;font-family:monospace;font-size:12px"
content = content.replace(old_svc_style, new_svc_style)

# Fix running services style
old_run_style = "padding:6px 12px;margin:4px 0;background:#f0fff0;border-radius:4px;border-left:3px solid #0d6b3d;font-family:monospace;font-size:13px"
new_run_style = "padding:4px 8px;margin:2px 0;background:#f0fff0;border-radius:3px;border-left:3px solid #0d6b3d;font-family:monospace;font-size:12px"
content = content.replace(old_run_style, new_run_style)

# Fix disabled services style
old_dis_style = "padding:6px 12px;margin:4px 0;background:#f5f5f5;border-radius:4px;border-left:3px solid #999;font-family:monospace;font-size:13px"
new_dis_style = "padding:4px 8px;margin:2px 0;background:#f5f5f5;border-radius:3px;border-left:3px solid #999;font-family:monospace;font-size:12px"
content = content.replace(old_dis_style, new_dis_style)

# Fix failed services style
old_fail_style = "padding:6px 12px;margin:4px 0;background:#fef2f2;border-radius:4px;border-left:3px solid #b00020;color:#991b1b;font-family:monospace;font-size:13px"
new_fail_style = "padding:4px 8px;margin:2px 0;background:#fef2f2;border-radius:3px;border-left:3px solid #b00020;color:#991b1b;font-family:monospace;font-size:12px"
content = content.replace(old_fail_style, new_fail_style)

with open('C:/Users/zatur/sos-report-web/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ Patched app.py ({len(content)} chars)")
print("Changes:")
print("  1. Added @app.errorhandler(413) with styled error page (compact)")
print("  2. Made report CSS more compact (smaller fonts, tighter spacing)")
print("  3. Compacted table rows and service list items")
print("  4. Compacted log error items")
