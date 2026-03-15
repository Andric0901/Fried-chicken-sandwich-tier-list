import http.server
import socketserver
import json
import os
import shutil
import subprocess
import sys

PORT = 8000

# Constants matching python tier list configurations
DEFAULT_WIDTH = 200
DEFAULT_GAP = 20
GAPS_BETWEEN_RESTAURANTS = 10

def get_num_rows_per_tier(num_rows: int, tier_dict: dict) -> dict:
    tier_num_rows = {}
    for k in tier_dict:
        if len(tier_dict[k]) % num_rows == 0:
            tier_num_rows[k] = len(tier_dict[k]) // num_rows
        else:
            tier_num_rows[k] = len(tier_dict[k]) // num_rows + 1
    return tier_num_rows

def evaluate_num_logos_per_row(tier_dict: dict, min_val: int = 17, threshold: int = 10) -> int:
    min_difference = 100
    num_logos_per_row = 0
    for i in range(min_val, min_val + threshold):
        tier_num_rows = get_num_rows_per_tier(i, tier_dict)
        total_width = DEFAULT_WIDTH * (i + 1) + GAPS_BETWEEN_RESTAURANTS * (i - 1) + DEFAULT_GAP * 3
        total_height = sum(tier_num_rows[tier] * DEFAULT_WIDTH + GAPS_BETWEEN_RESTAURANTS * (tier_num_rows[tier] - 1) for tier in tier_num_rows) + DEFAULT_GAP * (len(tier_num_rows) + 1)
        current_diff = abs(total_width / total_height - 1.618)
        if current_diff < min_difference:
            min_difference = current_diff
            num_logos_per_row = i
    return num_logos_per_row

class EditorHandler(http.server.SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def translate_path(self, path):
        if path in ['/', '/editor.html', '/editor.css', '/editor.js']:
            if path == '/':
                path = '/editor.html'
            path = '/src/editor' + path
        return super().translate_path(path)

    def send_json_response(self, data, status=200):
        try:
            body = json.dumps(data).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            print(f"Error sending JSON response: {e}")

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        
        # Disable cache for API, editor files to ensure data and logic stays fresh
        if (self.path.startswith('/api/') or 
            self.path.endswith('.html') or 
            self.path.endswith('.js') or 
            self.path.endswith('.css') or 
            self.path == '/'):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
        else:
            self.send_header('Cache-Control', 'public, max-age=3600')
            
        super().end_headers()

    def do_GET(self):
        if self.path == '/api/logos':
            try:
                logos = []
                if os.path.exists('logos'):
                    logos = [f for f in os.listdir('logos') if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                self.send_json_response({"logos": logos})
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return

        if self.path == '/api/data':
            try:
                with open('tier_dict.json', 'r', encoding='utf-8') as f:
                    tier_dict = json.load(f)
                
                num_logos_per_row = evaluate_num_logos_per_row(tier_dict)
                self.send_json_response({
                    "tier_dict": tier_dict,
                    "num_logos_per_row": num_logos_per_row
                })
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return
            
        return super().do_GET()

    def do_POST(self):
        if self.path == '/api/rename_logo':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                old_path = data.get('old_path')
                new_path = data.get('new_path')
                
                # Security Check: Prevent directory traversal
                if old_path and new_path:
                    # Resolve to absolute paths relative to current directory
                    base_dir = os.path.abspath('logos')
                    abs_old = os.path.abspath(old_path)
                    abs_new = os.path.abspath(new_path)
                    
                    # Ensure both paths strictly reside within the specific 'logos' directory boundary
                    if abs_old.startswith(base_dir) and abs_new.startswith(base_dir) and os.path.exists(abs_old):
                        os.rename(abs_old, abs_new)
                        self.send_json_response({"status": "success"})
                    else:
                        self.send_json_response({"error": "Security check failed: Invalid path or file does not exist. Path must remain inside logos directory."}, 400)
                else:
                    self.send_json_response({"error": "Invalid paths or file does not exist"}, 400)
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return

        if self.path == '/api/run_tierlist':
            try:
                # Run the tierlist.py file synchronously
                # Use current interpreter to ensure same environment
                result = subprocess.run(
                    [sys.executable, 'src/tierlist/tierlist.py'],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    self.send_json_response({"status": "success", "output": result.stdout})
                else:
                    self.send_json_response({"error": "Script failed", "details": result.stderr}, 500)
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return

        if self.path == '/api/update':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                new_dict = json.loads(post_data.decode('utf-8'))
                
                with open('tier_dict.json', 'w', encoding='utf-8') as f:
                    # dump with standard formatting to avoid big git diffs
                    json.dump(new_dict, f, indent=4)
                
                self.send_json_response({"status": "success"})
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return
            
        self.send_response(404)
        self.end_headers()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

if __name__ == '__main__':
    # Start server in same directory as tier_dict.json
    # Allow address reuse to prevent "Address already in use" errors during quick restarts
    socketserver.TCPServer.allow_reuse_address = True
    with ThreadedTCPServer(("", PORT), EditorHandler) as httpd:
        print(f"Server starting at http://localhost:{PORT}/editor.html")
        print("To stop, press Ctrl+C")
        httpd.serve_forever()
