from http.server import BaseHTTPRequestHandler
from datetime import datetime
import pytz


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # Set the timezone to San Francisco
        sf_timezone = pytz.timezone('America/Los_Angeles')

        # Get the current time in San Francisco
        sf_time = datetime.now(sf_timezone).strftime('%Y-%m-%d %H:%M:%S')

        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(f"Current time in San Francisco: {sf_time}".encode())
