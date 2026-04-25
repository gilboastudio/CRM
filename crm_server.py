#!/usr/bin/env python3
"""
CRM Server — הרל גלבוע
הרץ עם: python3 crm_server.py
"""

import http.server
import urllib.request
import urllib.parse
import json
import os
import sys
import webbrowser
import threading
import socketserver

import os
PORT = int(os.environ.get('PORT', 8765))
HTML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'harel_crm_app.html')


class CRMHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress logs

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type, Notion-Version')

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            # Try local file first, fallback to remote
            if os.path.exists(HTML_FILE):
                try:
                    with open(HTML_FILE, 'rb') as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self._cors_headers()
                    self.end_headers()
                    self.wfile.write(content)
                    return
                except Exception:
                    pass
            self.send_error(404, f'לא נמצא קובץ: {HTML_FILE}')
        elif self.path == '/reload':
            # Special endpoint - reload HTML from file
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(b'ok')
        else:
            self.send_error(404)

    def do_POST(self):
        self._proxy_notion()

    def do_PATCH(self):
        self._proxy_notion()

    def _proxy_notion(self):
        if not self.path.startswith('/notion/'):
            self.send_error(404)
            return

        notion_path = self.path[len('/notion'):]
        notion_url = 'https://api.notion.com/v1' + notion_path

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length else None

        headers = {}
        for key in ['Authorization', 'Content-Type', 'Notion-Version']:
            val = self.headers.get(key)
            if val:
                headers[key] = val

        try:
            req = urllib.request.Request(notion_url, data=body, headers=headers, method=self.command)
            with urllib.request.urlopen(req) as res:
                response_body = res.read()
                self.send_response(res.status)
                self.send_header('Content-Type', 'application/json')
                self._cors_headers()
                self.end_headers()
                self.wfile.write(response_body)
        except urllib.error.HTTPError as e:
            error_body = e.read()
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(error_body)
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())


def open_browser():
    import time
    time.sleep(0.8)
    webbrowser.open(f'http://localhost:{PORT}')


if __name__ == '__main__':
    if not os.path.exists(HTML_FILE):
        print(f'שגיאה: לא נמצא קובץ harel_crm_app.html באותה תיקייה')
        input('לחץ Enter לסיום...')
        sys.exit(1)

    print(f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    print(f'  CRM — הרל גלבוע')
    print(f'  http://localhost:{PORT}')
    print(f'  Ctrl+C לעצירה')
    print(f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

    threading.Thread(target=open_browser, daemon=True).start()

    with socketserver.TCPServer(('', PORT), CRMHandler) as httpd:
        httpd.allow_reuse_address = True
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\nהשרת נעצר.')
