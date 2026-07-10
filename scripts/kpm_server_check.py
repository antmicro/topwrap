import concurrent.futures
import logging
import threading
from pathlib import Path

from topwrap.cli.main import (
    DEFAULT_BACKEND_ADDR,
    DEFAULT_BACKEND_PORT,
    DEFAULT_FRONTEND_DIR,
    DEFAULT_SERVER_ADDR,
    DEFAULT_SERVER_PORT,
    KPM,
    kpm_build_server,
)
from topwrap.config import config

kpm_build_server()


with concurrent.futures.ThreadPoolExecutor() as executor:
    logging.info("Starting server")
    server_ready_event = threading.Event()
    server_init_failed = threading.Event()

    executor.submit(
        KPM.run_server,
        server_ready_event=server_ready_event,
        show_kpm_logs=True,
        server_init_failed=server_init_failed,
        shutdown_server=True,
        server_host=DEFAULT_SERVER_ADDR,
        server_port=DEFAULT_SERVER_PORT,
        backend_host=DEFAULT_BACKEND_ADDR,
        backend_port=DEFAULT_BACKEND_PORT,
        frontend_directory=Path(config.kpm_build_location) / DEFAULT_FRONTEND_DIR,
    )
    logging.info("Waiting for KPM server to initialize")
    server_ready_event.wait()
    logging.info("Server initialized")
    if server_init_failed.is_set():
        logging.error("KPM server failed to initialize. Aborting")
        raise RuntimeError()
    logging.info("Shutting down server")
