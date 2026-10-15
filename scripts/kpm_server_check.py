import concurrent.futures
import logging
import threading

from topwrap.cli.main import (
    DEFAULT_BACKEND_ADDR,
    DEFAULT_SERVER_ADDR,
    KPM,
)

logging.basicConfig(level=logging.INFO)

with concurrent.futures.ThreadPoolExecutor() as executor:
    logging.info("Starting server")
    server_ready_event = threading.Event()

    server_future = executor.submit(
        KPM.run_server,
        preserve_parent_state=False,
        server_ready_event=server_ready_event,
        show_kpm_logs=True,
        shutdown_server=True,
        tcp_server_host=DEFAULT_SERVER_ADDR,
        tcp_server_port=0,
        backend_host=DEFAULT_BACKEND_ADDR,
        backend_port=0,
    )
    logging.info("Waiting for KPM server to initialize")
    while not server_ready_event.wait(timeout=0.1):
        if server_future.done():
            server_future.result()

    logging.info("Server initialized, waiting for shutdown")
    server_future.result()
    logging.info("Server shut down")
