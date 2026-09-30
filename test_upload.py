#!/usr/bin/env python3
"""Test upload to localhost:8080"""
import urllib.request

url = 'http://localhost:8080/'
file_path = "C:/Users/zatur/AppData/Local/Temp/test_sos.tar.xz"

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
data = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="sosreport"; filename="test.tar.xz"\r\n'
    f'Content-Type: application/octet-stream\r\n\r\n'
).encode() + open(file_path, 'rb').read() + f'\r\n--{boundary}--\r\n'.encode()

req = urllib.request.Request(url, data=data)
req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        status = resp.status
        html = resp.read().decode('utf-8')
        print('Status:', status)
        print('Length:', len(html))
        with open('/tmp/report_test.html', 'w') as f:
            f.write(html)
        print('Saved to /tmp/report_test.html')
        print('Title:', html[html.find('<title>')+7:html.find('</title>')])
except Exception as e:
    print('Error:', e)
