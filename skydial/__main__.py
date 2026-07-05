"""Entry point: ``python -m skydial`` or the ``skydial-api`` console script.

Loads config, then serves the app on the configured host/port.
"""

from __future__ import annotations

import uvicorn

from .config import load_config


def main() -> None:
    cfg = load_config()
    server = cfg.get("server", {})
    uvicorn.run(
        "skydial.app:app",
        host=server.get("host", "0.0.0.0"),
        port=int(server.get("port", 8090)),
        log_level="info",
    )


if __name__ == "__main__":
    main()
