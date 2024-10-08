#!/usr/bin/env python3
import logging
import signal
import threading
from http.server import HTTPServer

import config
import hardware
from main_web_server import MainWebHandler, add_programs
from programs.auto_drive import AutoDriveRobotProgram
from programs.beacon_follow import BeaconFollowRobotProgram
from programs.line_follow import LineFollowRobotProgram
from programs.scanner_calibration import CalibrateScannerRobotProgram

log = logging.getLogger(__name__)


def run():
    add_programs(LineFollowRobotProgram(), AutoDriveRobotProgram(),
                 BeaconFollowRobotProgram(), CalibrateScannerRobotProgram())
    server = HTTPServer(('', config.SERVER_PORT), MainWebHandler)

    def start_server():
        try:
            server.serve_forever()
        except (KeyboardInterrupt, Exception) as e:
            log.exception(e)
            if server:
                server.shutdown()
                server.server_close()
        finally:
            hardware.reset_hardware()

    threading.Thread(target=start_server).start()
    log.info("Started HTTP server on port %d" % config.SERVER_PORT)

    def handle_exit(signum, frame):
        server.shutdown()

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)


if __name__ == '__main__':
    run()
