import logging
import threading

from infrastructure.mcp.ring_buffer_log_handler import RingBufferLogHandler


def _logger(handler, name="application.services.scan"):
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    log.propagate = False
    log.handlers = [handler]
    return log


def test_level_filter_and_prefix_filter():
    handler = RingBufferLogHandler(level=logging.DEBUG)
    scan_log = _logger(handler, "application.services.scan")
    scan_log.info("scan started")
    scan_log.debug("detail")
    _logger(handler, "infrastructure.mcp").warning("mcp warn")

    assert [r["message"] for r in handler.recent(level="INFO")] == ["scan started", "mcp warn"]
    assert [r["message"] for r in handler.recent(level="DEBUG", logger_prefix="application.")] == ["scan started", "detail"]
    assert [r["level"] for r in handler.recent(level="WARNING")] == ["WARNING"]


def test_default_handler_level_ignores_debug():
    handler = RingBufferLogHandler()
    _logger(handler).debug("noise")
    assert handler.recent(level="DEBUG") == []


def test_maxlen_and_limit_and_message_truncation():
    handler = RingBufferLogHandler(maxlen=5)
    log = _logger(handler)
    for i in range(20):
        log.info("line %s", i)
    log.info("x" * 5000)

    rows = handler.recent(limit=3)
    assert len(handler.recent(limit=100)) == 5
    assert len(rows) == 3
    assert len(rows[-1]["message"]) == 500


def test_concurrent_logging_and_reading():
    handler = RingBufferLogHandler(maxlen=100)
    log = _logger(handler, "concurrent")
    stop = threading.Event()
    errors = []

    def write():
        for i in range(2000):
            log.info("m %s", i)

    def read():
        while not stop.is_set():
            stop.wait(0.001)  # a reader spinning without pause would starve the writers
            try:
                handler.recent()
            except Exception as e:
                errors.append(e)

    reader = threading.Thread(target=read)
    writers = [threading.Thread(target=write) for _ in range(4)]
    reader.start()
    for w in writers:
        w.start()
    for w in writers:
        w.join()
    stop.set()
    reader.join()

    assert errors == []
    assert len(handler.recent(limit=1000)) == 100
