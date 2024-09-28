import logging
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, urljoin
from urllib.request import Request, urlopen


def get_server(service_name, service_port, is_ready):
    class PauserServer(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/healthz/live":
                self.liveness_check()
            elif self.path == "/healthz/ready":
                self.readiness_check()
            else:
                self._reply(404, "Valid GET endpoints are /healthz/live and /healthz/ready")

        def do_POST(self):
            insts = self._get_instances()
            logging.info("Discovered instances: %s", insts)

            content_length = int(self.headers.get('content-length', 0))

            headers = self.headers
            data = self.rfile.read(content_length)

            threads = []
            for i in insts:
                url = urljoin(f'http://{i[0]}:{i[1]}', self.path)
                thread = threading.Thread(target=self._forward, args=(url, data, headers))
                threads.append(thread)
                thread.start()
            for thread in threads:
                thread.join()
            
            self._reply(200, "Sent")
        
        def _reply(self, code, msg):
            self.send_response(code)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(msg.encode())

        def _get_instances(self):
            result = socket.getaddrinfo(service_name, service_port)
            return [(addr[4][0], addr[4][1]) for addr in result]

        def _forward(self, url, data, headers):
            req = Request(url, data=data, headers=headers)
            resp = urlopen(req)
            if resp.code != 200:
                logging.error(resp.msg)

        def liveness_check(self):
            self._reply(200, "Ok")

        def readiness_check(self):
            if is_ready():
                self._reply(200, "Ready")
            else:
                self._reply(503, "NotReady")

        def log_message(self, fmt, *args):
            logging.debug("Server Request: %s", args)

    return PauserServer


def serve(service_name, service_port, listen, port, is_ready=lambda: True):
    server = HTTPServer((listen, port), get_server(service_name, service_port, is_ready))
    logging.info("Starting web server at '%s:%s'", listen, port)
    server.serve_forever()
