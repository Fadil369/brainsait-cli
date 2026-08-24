"""Entry point: run the Apple Bridge over stdio (local) or streamable HTTP (remote).

stdio  — for Claude Desktop / Claude Code on the same Mac.
http   — for claude.ai custom connectors: expose http://host:port/mcp through a
         tunnel (e.g. `cloudflared tunnel --url http://127.0.0.1:8848`) and add
         the public URL as a custom connector. Requests must carry the shared
         token (Authorization: Bearer <token> or ?token=<token>) when
         APPLE_BRIDGE_TOKEN is set.
"""

from __future__ import annotations

import argparse
import secrets
import sys

from . import config as config_module
from .server import mcp


def _build_http_app():
    from mcp.server.transport_security import TransportSecuritySettings
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import JSONResponse

    cfg = config_module.CONFIG
    if cfg.allowed_hosts:
        security = TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=cfg.allowed_hosts + ["127.0.0.1", "localhost", f"127.0.0.1:{cfg.port}", f"localhost:{cfg.port}"],
            allowed_origins=[f"https://{h}" for h in cfg.allowed_hosts],
        )
    else:
        # Behind a tunnel the Host header is the public hostname; without an
        # explicit allowlist we rely on token auth instead of host checks.
        security = TransportSecuritySettings(enable_dns_rebinding_protection=False)

    app = mcp.streamable_http_app(
        stateless_http=True,
        json_response=True,
        transport_security=security,
    )
    token = cfg.auth_token

    class TokenAuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            if not token:
                return await call_next(request)
            header = request.headers.get("authorization", "")
            presented = header.removeprefix("Bearer ").strip() if header else request.query_params.get("token", "")
            if presented and secrets.compare_digest(presented, token):
                return await call_next(request)
            return JSONResponse({"error": "unauthorized"}, status_code=401)

    app.add_middleware(TokenAuthMiddleware)
    return app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="brainsait-apple-bridge")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="stdio for Claude Desktop/Code; http for claude.ai custom connectors",
    )
    parser.add_argument("--host", default=None, help="HTTP bind host (default from APPLE_BRIDGE_HOST)")
    parser.add_argument("--port", type=int, default=None, help="HTTP port (default from APPLE_BRIDGE_PORT)")
    args = parser.parse_args(argv)

    cfg = config_module.CONFIG
    if args.transport == "stdio":
        mcp.run(transport="stdio")
        return 0

    host = args.host or cfg.host
    port = args.port or cfg.port
    if not cfg.auth_token:
        print(
            "WARNING: APPLE_BRIDGE_TOKEN is not set — the HTTP endpoint is unauthenticated. "
            "Only do this behind an authenticated tunnel.",
            file=sys.stderr,
        )
    import uvicorn

    print(f"BrainSAIT Apple Bridge listening on http://{host}:{port}/mcp", file=sys.stderr)
    uvicorn.run(_build_http_app(), host=host, port=port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
