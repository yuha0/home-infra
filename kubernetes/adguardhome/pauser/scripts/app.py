import argparse
import logging
import signal
import sys

from . import httpserver


fmt, datefmt = "[%(asctime)s.%(msecs)03d] - %(message)s", "%Y%m%d-%H:%M:%S"
handlers = [logging.StreamHandler()]


def graceful_exit(_signo, __stack_frame):
    logging.info("Received signal %s, exiting...", _signo)
    sys.exit(0)


def init_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--service", help="target headless service for instance discovery")
    parser.add_argument("-p", "--port", type=int, help="target service port")
    parser.add_argument("-l", "--listen", type=int, help="pauser's port to listen for requests")
    parser.add_argument("-v", "--verbose", default="INFO", help="logging level")
    return parser.parse_args()


def main():
    args = init_args()
    logging.basicConfig(
        level=args.verbose, format=fmt, datefmt=datefmt, handlers=handlers
    )
    signal.signal(signal.SIGTERM, graceful_exit)
    signal.signal(signal.SIGINT, graceful_exit)

    logging.info("Starting main server")
    httpserver.serve(args.service, args.port, "0.0.0.0", args.listen)


if __name__ == "__main__":
    main()