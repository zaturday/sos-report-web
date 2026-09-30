# sos-report-web
Web report generator for RHEL 9 sosreport data

## Features
- Upload sosreport (tar.xz, tar.gz) via web UI with drag and drop
- Multi-file upload support with file list management
- Analyze system info, hardware, network, services, logs, SELinux
- Print report via browser
- Max upload size: 2GB

## Installation
```bash
pip install -r requirements.txt
```

## Usage
Start Flask web server:
```bash
python app.py
```
Then open http://localhost:8080 in browser.

## Project Structure
```
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── patch_app.py           # Patch script for updates
├── test_upload.py         # Upload test script
└── sosreport-*.tar.xz    # Example sosreport file (not committed)
```

## License
MIT
