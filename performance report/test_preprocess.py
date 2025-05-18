# test_preprocess.py
import http.server
import socketserver
import webbrowser
import threading
import time

with open('Insurance_auto_data.csv', 'r') as file:
    csv_content = file.read()

from preprocess_csv import preprocess_csv

cleaned_data = preprocess_csv(csv_content)
print(f"Processed {len(cleaned_data)} rows")
for row in cleaned_data[:5]:  # Print first 5 rows
    print(row)

# Start local server and open browser
PORT = 8000
Handler = http.server.SimpleHTTPRequestHandler
httpd = socketserver.TCPServer(("", PORT), Handler)

def start_server():
    print(f"Serving at http://localhost:{PORT}")
    httpd.serve_forever()

# Run server in a separate thread
server_thread = threading.Thread(target=start_server)
server_thread.daemon = True
server_thread.start()

# Open browser
webbrowser.open(f"http://localhost:{PORT}/insurance_report.html")

# Keep the script running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Shutting down server...")
    httpd.shutdown()