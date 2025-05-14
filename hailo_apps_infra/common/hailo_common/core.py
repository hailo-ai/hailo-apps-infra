"""  
Core helpers: arch detection, parser, buffer utils.  
"""  
import platform  
import subprocess  
import argparse  
from gi.repository import Gst  
from .defines import EPSILON  
  
def detect_host_arch() -> str:  
    """Detect host: rpi, arm, x86, or unknown."""  
    m = platform.machine().lower()  
    s = platform.system().lower()  
    if 'arm' in m or 'aarch64' in m:  
        if s == 'linux' and ('raspberrypi' in platform.uname().node or 'pi' in platform.uname().node):  
            return 'rpi'  
        return 'arm'  
    if 'x86' in m or 'amd64' in m:  
        return 'x86'  
    return 'unknown'  
  
def detect_hailo_arch() -> str | None:  
    """Use hailortcli to identify Hailo architecture."""  
    try:  
        res = subprocess.run(['hailortcli', 'fw-control', 'identify'], capture_output=True, text=True)  
        if res.returncode != 0:  
            return None  
        for line in res.stdout.splitlines():  
            if 'HAILO8L' in line: return 'hailo8l'  
            if 'HAILO8' in line:  return 'hailo8'  
    except Exception:  
        return None  
    return None  
  
def get_caps_from_pad(pad: Gst.Pad):  
    caps = pad.get_current_caps()  
    if caps:  
        s = caps.get_structure(0)  
        return s.get_value('format'), s.get_value('width'), s.get_value('height')  
    return None, None, None  
  
def get_default_parser() -> argparse.ArgumentParser:  
    """Shared CLI parser for all Hailo apps."""  
    p = argparse.ArgumentParser(description='Hailo App Help')  
    p.add_argument('-i', '--input', type=str, help='Input source: file, usb, rpi, ximage')  
    p.add_argument('-u', '--use-frame', action='store_true')  
    p.add_argument('-f', '--show-fps', action='store_true')  
    p.add_argument('--arch', choices=['hailo8','hailo8l'], default=None)  
    p.add_argument('--hef-path', help='Override HEF file path')  
    p.add_argument('--disable-sync', action='store_true')  
    p.add_argument('--dump-dot', action='store_true', help='Dump pipeline graph to dot file')  
    return p  
