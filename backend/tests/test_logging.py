
import json
import logging

from main import JSONFormatter


def test_request_logging_includes_request_id(client, caplog):
    logger = logging.getLogger("smartcampus")
    original_propagate = logger.propagate

    try:
        logger.propagate = True

        with caplog.at_level(logging.INFO, logger="smartcampus"):
            response = client.get("/api/health")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

        request_id = response.headers["X-Request-ID"]

        assert len(request_id) == 36

        request_logs = [
            record
            for record in caplog.records
            if getattr(record, "event", None) == "http_request"
        ]

        assert request_logs

        matching_log = next(
            record
            for record in request_logs
            if record.request_id == request_id
        )

        assert matching_log.method == "GET"
        assert matching_log.path == "/api/health"
        assert matching_log.status_code == 200
        assert matching_log.duration_ms >= 0

    finally:
        logger.propagate = original_propagate


def test_json_formatter_outputs_structured_fields():
    formatter = JSONFormatter()

    record = logging.LogRecord(
        name="smartcampus",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Request completed successfully",
        args=(),
        exc_info=None,
    )

    record.event = "http_request"
    record.request_id = "test-request-id"
    record.method = "GET"
    record.path = "/api/health"
    record.status_code = 200
    record.duration_ms = 12.5

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "smartcampus"
    assert parsed["message"] == "Request completed successfully"
    assert parsed["event"] == "http_request"
    assert parsed["request_id"] == "test-request-id"
    assert parsed["method"] == "GET"
    assert parsed["path"] == "/api/health"
    assert parsed["status_code"] == 200
    assert parsed["duration_ms"] == 12.5
    assert "timestamp" in parsed


def test_client_error_is_logged_as_warning(client, caplog):
    logger = logging.getLogger("smartcampus")
    original_propagate = logger.propagate

    try:
        logger.propagate = True

        with caplog.at_level(logging.WARNING, logger="smartcampus"):
            response = client.get("/api/complaints")

        assert response.status_code == 401

        error_logs = [
            record
            for record in caplog.records
            if getattr(record, "event", None) == "http_request"
        ]

        assert any(
            record.levelno == logging.WARNING
            and record.status_code == 401
            for record in error_logs
        )

    finally:
        logger.propagate = original_propagate
