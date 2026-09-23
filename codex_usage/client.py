from __future__ import annotations

import json
import os
import selectors
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from .usage import LimitSnapshot, parse_limits


class CodexClientError(RuntimeError):
    pass


def find_codex() -> Path:
    override = os.environ.get("CODEX_USAGE_CODEX_PATH")
    if override:
        candidate = Path(override).expanduser()
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
        raise CodexClientError(f"Configured Codex executable is not usable: {candidate}")

    executable = shutil.which("codex")
    if executable:
        return Path(executable)
    raise CodexClientError("Codex CLI not found in PATH")


def read_usage(timeout: float = 20.0) -> list[LimitSnapshot]:
    executable = find_codex()
    process = subprocess.Popen(
        [str(executable), "app-server", "--listen", "stdio://"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    try:
        if process.stdin is None or process.stdout is None:
            raise CodexClientError("Could not open Codex app-server pipes")

        _send(
            process,
            {
                "method": "initialize",
                "id": 0,
                "params": {
                    "clientInfo": {
                        "name": "codex_usage_linux",
                        "title": "Codex Usage for Linux",
                        "version": "0.1.0",
                    }
                },
            },
        )
        deadline = time.monotonic() + timeout
        initialized = _wait_for_response(process, 0, deadline)
        if "error" in initialized:
            raise CodexClientError(_error_message(initialized))

        _send(process, {"method": "initialized", "params": {}})
        _send(process, {"method": "account/rateLimits/read", "id": 1, "params": {}})
        response = _wait_for_response(process, 1, deadline)
        if "error" in response and _is_auth_error(_error_message(response)):
            _send(process, {"method": "account/read", "id": 2,
                            "params": {"refreshToken": True}})
            refreshed = _wait_for_response(process, 2, deadline)
            if "error" in refreshed:
                raise CodexClientError(_friendly_error(refreshed))
            _send(process, {"method": "account/rateLimits/read", "id": 3, "params": {}})
            response = _wait_for_response(process, 3, deadline)
        if "error" in response:
            raise CodexClientError(_friendly_error(response))
        result = response.get("result")
        if not isinstance(result, dict):
            raise CodexClientError("Codex returned an invalid usage response")
        return parse_limits(result)
    finally:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)


def _send(process: subprocess.Popen[str], message: dict[str, Any]) -> None:
    if process.stdin is None:
        raise CodexClientError("Codex app-server input is closed")
    process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
    process.stdin.flush()


def _wait_for_response(
    process: subprocess.Popen[str], request_id: int, deadline: float
) -> dict[str, Any]:
    if process.stdout is None:
        raise CodexClientError("Codex app-server output is closed")
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                detail = ""
                if process.stderr is not None:
                    detail = process.stderr.read().strip()
                raise CodexClientError(detail or "Codex app-server stopped unexpectedly")
            remaining = max(0.0, deadline - time.monotonic())
            if not selector.select(timeout=remaining):
                break
            line = process.stdout.readline()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(message, dict) and message.get("id") == request_id:
                return message
    finally:
        selector.close()
    raise CodexClientError("Timed out while waiting for Codex usage information")


def _error_message(response: dict[str, Any]) -> str:
    error = response.get("error")
    if isinstance(error, dict) and isinstance(error.get("message"), str):
        return error["message"]
    return "Codex usage information is unavailable"


def _is_auth_error(message: str) -> bool:
    return any(marker in message.lower() for marker in (
        "401", "token_revoked", "invalidated oauth token", "refresh_token",
        "refresh token", "not logged in", "sign in again",
    ))


def _friendly_error(response: dict[str, Any]) -> str:
    message = _error_message(response)
    if _is_auth_error(message):
        return ("Codex sign-in has expired or was revoked. "
                "Run `codex login` in a terminal, complete sign-in, then click Refresh.")
    return message
