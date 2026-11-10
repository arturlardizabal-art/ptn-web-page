#!/usr/bin/env python3
"""PTN local preview with rebuild/reload. Binds only to this computer."""
import argparse
import http.server
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import threading
import time
from urllib.parse import unquote, urlsplit

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'.local'
PID=STATE/'server.pid'
PORT=3200
VERSION=str(time.time_ns())
WATCH=[ROOT/'content/site.json',ROOT/'content/services.json',ROOT/'content/seo-plan.json',ROOT/'scripts/build.py',ROOT/'assets/site.css',ROOT/'assets/site.js',ROOT/'docs/analisis-seo-geo.html',ROOT/'favicon.svg',ROOT/'favicon.ico']

def build():
    subprocess.run([sys.executable,str(ROOT/'scripts/build.py')],cwd=ROOT,check=True)

def watch():
    global VERSION
    seen={p:p.stat().st_mtime_ns if p.exists() else 0 for p in WATCH}
    while True:
        time.sleep(.8)
        now={p:p.stat().st_mtime_ns if p.exists() else 0 for p in WATCH}
        if now!=seen:
            try:
                if any(now[p]!=seen[p] for p in WATCH[:4]+WATCH[-2:]):build()
                VERSION=str(time.time_ns());print('Updated preview',flush=True)
            except Exception as exc:print('Rebuild failed:',exc,flush=True)
            seen=now

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def end_headers(self):
        self.send_header('X-Robots-Tag','noindex, nofollow')
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        super().end_headers()
    def do_GET(self):
        clean=unquote(urlsplit(self.path).path)
        if clean=='/__dev/version':
            data=json.dumps({'version':VERSION}).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
        super().do_GET()
    def send_head(self):
        clean=unquote(urlsplit(self.path).path)
        if any(part.startswith('.') for part in Path(clean).parts if part not in ('/','')):
            self.send_error(404);return None
        target=Path(self.translate_path(self.path))
        if target.is_dir() and not (target/'index.html').exists():self.send_error(404);return None
        if target.suffix=='.html' or (target.is_dir() and (target/'index.html').exists() and clean.endswith('/')):
            if target.is_dir():target=target/'index.html'
            if target.is_file():
                import io
                original=target.read_bytes()
                reload=b'''<script>(()=>{let current;setInterval(async()=>{try{const r=await fetch('/__dev/version',{cache:'no-store'});const d=await r.json();if(current&&current!==d.version)location.reload();current=d.version;}catch{}},1500)})();</script>'''
                body=original.replace(b'</body>',reload+b'</body>')
                self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();return io.BytesIO(body)
        return super().send_head()
    def send_error(self,code,message=None,explain=None):
        if code==404 and (ROOT/'404.html').exists():
            body=(ROOT/'404.html').read_bytes();self.send_response(404);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers()
            if self.command!='HEAD':self.wfile.write(body)
        else:super().send_error(code,message,explain)

def running():
    if not PID.exists():return None
    try:
        pid=int(PID.read_text());cmd=subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True).strip()
        return pid if str(ROOT/'scripts/dev.py') in cmd and 'serve' in cmd else None
    except (ValueError,subprocess.CalledProcessError):return None

def start():
    if running():print(f'PTN is running: http://127.0.0.1:{PORT}');return
    with socket.socket() as s:
        if s.connect_ex(('127.0.0.1',PORT))==0:raise SystemExit(f'Port {PORT} is in use. No other process was stopped.')
    STATE.mkdir(exist_ok=True);build()
    with (STATE/'server.log').open('ab') as log:
        process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'serve'],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
    PID.write_text(str(process.pid))
    for _ in range(25):
        time.sleep(.2)
        with socket.socket() as s:
            if s.connect_ex(('127.0.0.1',PORT))==0:print(f'PTN local: http://127.0.0.1:{PORT} (PID {process.pid})');return
    raise SystemExit('Preview did not start. Check .local/server.log')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['start','stop','status','serve'],nargs='?',default='start');args=parser.parse_args()
    if args.action=='start':start()
    elif args.action=='status':print(f'Running: http://127.0.0.1:{PORT}' if running() else 'Stopped')
    elif args.action=='stop':
        pid=running()
        if pid:os.kill(pid,signal.SIGTERM);PID.unlink(missing_ok=True);print('PTN local stopped')
        else:print('No owned PTN server is running')
    else:
        threading.Thread(target=watch,daemon=True).start()
        http.server.ThreadingHTTPServer(('127.0.0.1',PORT),Handler).serve_forever()
if __name__=='__main__':main()
