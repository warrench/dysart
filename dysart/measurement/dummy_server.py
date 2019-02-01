"""
Interface between dummy lab and DySART. Processes requests from DySART and
returns results from dummy lab to DySART controller features.
"""

import dummy_lab as dl
import http.server
import socketserver

PORT = 8080
Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
