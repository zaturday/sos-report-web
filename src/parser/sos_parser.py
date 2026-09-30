"""
Parser for RHEL 9 sosreport archives.
Extracts key system information from sosreport tarballs.
"""
import tarfile
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import xml.etree.ElementTree as ET


class SosReportParser:
    """Parse RHEL 9 sosreport and extract structured data."""
    
    def __init__(self, archive_path: str):
        self.archive_path = archive_path
        self.archive = None
        self.data: Dict[str, Any] = {}
        self.files: Dict[str, str] = {}  # path -> content mapping
        
    def open(self):
        """Open the archive."""
        self.archive = tarfile.open(self.archive_path, 'r:*')
        self._load_file_index()
        return self
        
    def close(self):
        """Close the archive."""
        if self.archive:
            self.archive.close()
            self.archive = None
            
    def _load_file_index(self):
        """Load all file contents into memory (for small-medium reports)."""
        for member in self.archive.getmembers():
            if member.isfile():
                try:
                    f = self.archive.extractfile(member)
                    if f:
                        content = f.read().decode('utf-8', errors='replace')
                        self.files[member.name] = content
                        f.close()
                except Exception:
                    pass
    
    def _find_file(self, patterns: List[str]) -> Optional[str]:
        """Find a file matching any of the patterns."""
        for pattern in patterns:
            for fname in self.files:
                if pattern in fname:
                    return self.files[fname]
        return None
    
    def _extract_line(self, content: str, pattern: str, group: int = 0) -> Optional[str]:
        """Extract a value from content using regex."""
        if not content:
            return None
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            return match.group(group).strip()
        return None
    
    def parse_system_info(self) -> Dict[str, Any]:
        """Extract basic system information."""
        info = {}
        
        # hostname
        content = self._find_file(['hostname', 'sos_commands/hostname'])
        if content:
            info['hostname'] = content.strip().split('\n')[0]
            
        # kernel
        content = self._find_file(['uname', 'sos_commands/uname'])
        if content:
            info['kernel'] = content.strip().split('\n')[0]
            
        # OS release
        content = self._find_file(['etc_os-release', 'sos_commands/os_release'])
        if content:
            for line in content.split('\n'):
                if '=' in line:
                    key, val = line.split('=', 1)
                    info[key.strip()] = val.strip().strip('"')
                    
        # date/time
        content = self._find_file(['date', 'sos_commands/date'])
        if content:
            info['date'] = content.strip().split('\n')[0]
            
        # sos report timestamp
        content = self._find_file(['sosreport'])
        if content:
            match = re.search(r'sosreport\s+([^\s]+)', content)
            if match:
                info['sos_timestamp'] = match.group(1)
                
        return info
    
    def parse_hardware(self) -> Dict[str, Any]:
        """Extract hardware information."""
        hw = {}
        
        # CPU info
        content = self._find_file(['cpuinfo', 'sos_commandsCPU_frequency'])
        if content:
            for line in content.split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    key = key.strip()
                    val = val.strip()
                    if key in ['model name', 'cpu cores', 'siblings', 'cpu MHz']:
                        hw[key] = val
            # Count CPUs
            cores = self._extract_line(content, r'cpu cores\s*:\s*(\d+)', group=1)
            if cores:
                hw['cpu_cores'] = int(cores)
                
        # Memory
        content = self._find_file(['meminfo', 'sos_commands/memory'])
        if content:
            total = self._extract_line(content, r'MemTotal\s*:\s*(\d+)', group=1)
            free = self._extract_line(content, r'MemFree\s*:\s*(\d+)', group=1)
            if total:
                hw['mem_total_kb'] = int(total)
                hw['mem_total_gb'] = round(int(total) / 1024 / 1024, 2)
            if free:
                hw['mem_free_kb'] = int(free)
                
        # DMI/System info
        content = self._find_file(['dmidecode', 'dmidecode'])
        if content:
            for line in content.split('\n'):
                if 'Product Name' in line or 'Manufacturer' in line or 'Serial Number' in line:
                    if ':' in line:
                        key, val = line.split(':', 1)
                        hw[key.strip()] = val.strip()
                        
        # Disk info from blkid
        content = self._find_file(['blkid', 'sos_commands/blk'])
        if content:
            hw['disks'] = []
            for line in content.split('\n'):
                if line.strip() and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 2:
                        disk_info = {}
                        for part in parts:
                            if '=' in part:
                                k, v = part.split('=', 1)
                                disk_info[k] = v.strip('"')
                        hw['disks'].append(disk_info)
                        
        return hw
    
    def parse_network(self) -> Dict[str, Any]:
        """Extract network information."""
        net = {}
        
        # IP addresses
        content = self._find_file(['ip_addr', 'sos_commands/ip'])
        if content:
            net['interfaces'] = []
            current_iface = None
            for line in content.split('\n'):
                if line.startswith('') and ':' in line:
                    current_iface = line.split(':')[1].strip()
                    net['interfaces'].append({'name': current_iface})
                elif current_iface and 'inet ' in line:
                    match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', line)
                    if match:
                        net['interfaces'][-1]['ip'] = match.group(1)
                elif current_iface and 'link/' in line:
                    match = re.search(r'link/(\d+)', line)
                    if match:
                        net['interfaces'][-1]['mac'] = match.group(1)
                        
        # Routes
        content = self._find_file(['route', 'sos_commands/route'])
        if content:
            net['routes'] = [line.strip() for line in content.split('\n') if line.strip()]
            
        # DNS
        content = self._find_file(['etc_resolv_conf', 'resolv_conf'])
        if content:
            net['dns_servers'] = []
            for line in content.split('\n'):
                if line.startswith('nameserver'):
                    ns = line.split()[1] if len(line.split()) > 1 else ''
                    net['dns_servers'].append(ns)
                    
        # Firewall
        content = self._find_file(['iptables', 'sos_commands/iptables'])
        if content:
            net['iptables_rules'] = len([l for l in content.split('\n') if l.strip()])
            
        return net
    
    def parse_services(self) -> Dict[str, Any]:
        """Extract systemd services status."""
        svcs = {}
        
        # Systemd units
        content = self._find_file(['systemctl', 'sos_commands/systemctl'])
        if content:
            svcs['enabled'] = []
            svcs['disabled'] = []
            svcs['static'] = []
            current_list = None
            for line in content.split('\n'):
                if 'enabled' in line.lower() and 'UNIT' in line:
                    current_list = 'enabled'
                    continue
                elif 'disabled' in line.lower() and 'UNIT' in line:
                    current_list = 'disabled'
                    continue
                elif line.strip().startswith('UNIT') or line.strip().startswith('LOAD'):
                    continue
                elif current_list and line.strip() and not line.startswith('---'):
                    unit_name = line.split()[0] if line.split() else ''
                    if unit_name and not unit_name.startswith('['):
                        svcs[current_list].append(unit_name)
                        
        # Failed units
        content = self._find_file(['failed', 'sos_commands/systemctl'])
        if content:
            svcs['failed'] = [line.strip() for line in content.split('\n') 
                             if line.strip() and not line.startswith('UNIT') 
                             and not line.startswith('LOAD') and not line.startswith('---')]
            
        return svcs
    
    def parse_logs_summary(self) -> Dict[str, Any]:
        """Extract key log entries."""
        logs = {}
        
        # Journal errors
        content = self._find_file(['journal', 'sos_commands/journal'])
        if content:
            errors = []
            for line in content.split('\n'):
                if 'ERROR' in line or 'error' in line.lower() or 'FAILED' in line:
                    errors.append(line.strip()[:200])
            logs['journal_errors'] = errors[:50]  # Limit to 50
            
        # Messages
        content = self._find_file(['messages', 'sos_commands/messages'])
        if content:
            critical = []
            for line in content.split('\n'):
                if 'crit' in line.lower() or 'alert' in line.lower() or 'emerg' in line.lower():
                    critical.append(line.strip()[:200])
            logs['critical_messages'] = critical[:50]
            
        return logs
    
    def parseSELinux(self) -> Dict[str, Any]:
        """Extract SELinux status."""
        selinux = {}
        
        content = self._find_file(['sos_commands/selinux', 'selinux'])
        if content:
            status = self._extract_line(content, r'SELinux status:\s*(\w+)')
            mode = self._extract_line(content, r'SELinux mode from config file:\s*(\w+)')
            if status:
                selinux['status'] = status
            if mode:
                selinux['configured_mode'] = mode
                
        return selinux
    
    def parse_all(self) -> Dict[str, Any]:
        """Parse all sections and return structured data."""
        self.data = {
            'system': self.parse_system_info(),
            'hardware': self.parse_hardware(),
            'network': self.parse_network(),
            'services': self.parse_services(),
            'logs': self.parse_logs_summary(),
            'selinux': self.parseSELinux(),
            'archive': {
                'path': self.archive_path,
                'name': os.path.basename(self.archive_path),
            }
        }
        return self.data
    
    def __enter__(self):
        return self.open()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
