"""Export independent maintenance pages and Nginx configuration (stdlib only)."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import zipfile
from importlib import import_module
from pathlib import Path

BUNDLE_VERSION = "1.0.1"
ASSETS = Path(__file__).with_name("maintenance_assets")


def asset(name: str) -> str:
    if zipfile.is_zipfile(sys.argv[0]):
        with zipfile.ZipFile(sys.argv[0]) as archive:
            return archive.read("maintenance_assets/" + name).decode()
    path = Path(__file__).parent / "static/mf/availability.js" if name == "availability.js" else ASSETS / name
    return path.read_text(encoding="utf-8")


def quoted(path: Path) -> str:
    value = str(path.resolve())
    if any(c in value for c in '\n\r\x00$"\\;{}'):
        raise ValueError("Nginx paths cannot contain control characters or configuration syntax")
    return '"' + value + '"'


def export(
    destination: Path,
    upstream: str,
    listen: str = "127.0.0.1:8080",
    service: str = "서비스",
    retry_after: int | None = None,
    runtime_root: Path | None = None,
) -> None:
    """Create a new, relocatable-by-reexport deployment directory; never overwrite one."""
    if not re.fullmatch(r"http://[a-zA-Z0-9][a-zA-Z0-9.-]*(?::[0-9]{1,5})?", upstream):
        raise ValueError("upstream must be an internal http://hostname[:port] origin")
    if ":" in upstream[7:] and not 1 <= int(upstream.rsplit(":", 1)[1]) <= 65535:
        raise ValueError("upstream port must be 1..65535")
    if not re.fullmatch(r"(?:127\.0\.0\.1|0\.0\.0\.0):[0-9]{1,5}", listen):
        raise ValueError("listen must be 127.0.0.1:PORT or 0.0.0.0:PORT")
    if not 1 <= int(listen.rsplit(":", 1)[1]) <= 65535:
        raise ValueError("listen port must be 1..65535")
    if retry_after is not None and not 1 <= retry_after <= 86400:
        raise ValueError("retry-after must be 1..86400 seconds")
    if not service.strip() or len(service) > 120:
        raise ValueError("service must contain 1..120 characters")
    output = destination.resolve()
    destination = (runtime_root or output).resolve()
    quoted(destination)
    headers = (
        'add_header Cache-Control "no-store" always;\n'
        'add_header X-Content-Type-Options "nosniff" always;\n'
        "add_header Content-Security-Policy \"default-src 'none'; style-src 'unsafe-inline'; "
        "base-uri 'none'; form-action 'none'; frame-ancestors 'none'\" always;\n"
    )
    if retry_after is not None:
        headers += f'add_header Retry-After "{retry_after}" always;\n'
    # $request retains the ORIGINAL method when error_page internally redirects POST to GET.
    maps = """map $request $foundation_safe_read {
    default 0;
    ~^(GET|HEAD)\\x20 1;
}
map "$foundation_safe_read:$http_accept" $foundation_error_uri {
    default /__foundation_unavailable.json;
    ~*^1:.*text/html /__foundation_unavailable.html;
}
map $http_upgrade $foundation_connection { default upgrade; '' close; }
"""
    guard = f"if (-f {quoted(destination / 'maintenance.flag')}) {{ return 503; }}\n"
    proxy = f"""include {quoted(destination / "guard.conf")};
proxy_pass {upstream};
proxy_http_version 1.1;
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $remote_addr;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection $foundation_connection;
proxy_connect_timeout 3s;
proxy_read_timeout 60s;
proxy_intercept_errors off;
proxy_next_upstream off;
"""
    server = "error_page 502 503 504 =503 $foundation_error_uri;\n"
    for extension, content_type in [("html", "text/html"), ("json", "application/problem+json")]:
        server += f"""location = /__foundation_unavailable.{extension} {{
    internal;
    root {quoted(destination / "public")};
    types {{ }}
    default_type {content_type};
    charset utf-8;
    {headers}
    try_files /unavailable.{extension} =503;
}}
"""
    locations = f"""location ~ ^/(api|mcp|actuator|health|readyz|livez|race-rooms)(/|$) {{
    error_page 502 503 504 =503 /__foundation_unavailable.json;
    include {quoted(destination / "proxy.conf")};
}}
location / {{ include {quoted(destination / "proxy.conf")}; }}
"""
    config = f"""worker_processes 1;
pid {quoted(destination / "nginx.pid")};
error_log {quoted(destination / "error.log")} warn;
events {{ worker_connections 256; }}
http {{
    access_log off;
    server_tokens off;
    client_body_temp_path {quoted(destination / "client_temp")};
    proxy_temp_path {quoted(destination / "proxy_temp")};
    fastcgi_temp_path {quoted(destination / "fastcgi_temp")};
    uwsgi_temp_path {quoted(destination / "uwsgi_temp")};
    scgi_temp_path {quoted(destination / "scgi_temp")};
    include {quoted(destination / "http.conf")};
    server {{
        listen {listen};
        include {quoted(destination / "server.conf")};
        include {quoted(destination / "locations.conf")};
    }}
}}
"""
    outputs = {
        "public/unavailable.html": asset("unavailable.html").replace("{{SERVICE}}", html.escape(service)),
        "public/unavailable.json": json.dumps(
            {
                "type": "about:blank",
                "title": "Service unavailable",
                "status": 503,
                "code": "SERVICE_UNAVAILABLE",
                "detail": "Please try again later.",
            }
        )
        + "\n",
        "public/availability.js": asset("availability.js"),
        "http.conf": maps,
        "server.conf": server,
        "locations.conf": locations,
        "proxy.conf": proxy,
        "guard.conf": guard,
        "nginx.conf": config,
        "README.md": asset("README.md"),
        "LICENSE.txt": asset("LICENSE.txt"),
        "manifest.json": json.dumps({"bundle_version": BUNDLE_VERSION, "upstream": upstream}, indent=2),
    }
    output.mkdir(parents=True, exist_ok=False)
    for relative, content in outputs.items():
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def bundle(destination: Path) -> None:
    """Build a deterministic, inspectable Python zipapp for non-Python consumers."""
    files = {
        "__main__.py": "from maintenance import main\nmain()\n",
        "maintenance.py": Path(__file__).read_text(encoding="utf-8"),
        "maintenance_probe.py": Path(__file__).with_name("maintenance_probe.py").read_text(encoding="utf-8"),
    }
    files.update({"maintenance_assets/" + p.name: p.read_text(encoding="utf-8") for p in ASSETS.iterdir()})
    files["maintenance_assets/availability.js"] = asset("availability.js")
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 11, 27, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, content.encode())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    exporting = commands.add_parser("export")
    exporting.add_argument("destination", type=Path)
    exporting.add_argument("--upstream", required=True)
    exporting.add_argument("--listen", default="127.0.0.1:8080")
    exporting.add_argument("--service", default="서비스")
    exporting.add_argument("--retry-after", type=int)
    exporting.add_argument("--lock", type=Path)
    exporting.add_argument("--runtime-root", type=Path)
    packing = commands.add_parser("bundle")
    packing.add_argument("destination", type=Path)
    mode = commands.add_parser("mode")
    mode.add_argument("destination", type=Path)
    mode.add_argument("state", choices=["on", "off"])
    checking = commands.add_parser("verify")
    checking.add_argument("--nginx", default="nginx")
    checking.add_argument("--lock", type=Path)
    args = parser.parse_args()
    try:
        lock = getattr(args, "lock", None)
        if lock is not None:
            expected = json.loads(lock.read_text(encoding="utf-8"))["sha256"]
            if hashlib.sha256(Path(sys.argv[0]).read_bytes()).hexdigest() != expected:
                raise ValueError("maintenance bundle SHA-256 does not match the dependency lock")
        if args.command == "export":
            export(
                args.destination,
                args.upstream,
                args.listen,
                args.service,
                args.retry_after,
                args.runtime_root,
            )
        elif args.command == "bundle":
            bundle(args.destination)
        elif args.command == "mode":
            if not (args.destination / "manifest.json").is_file():
                raise ValueError("not an exported deployment directory")
            flag = args.destination / "maintenance.flag"
            if args.state == "on":
                flag.touch()
            else:
                flag.unlink(missing_ok=True)
        elif args.command == "verify":
            probe = import_module(f"{__package__}.maintenance_probe" if __package__ else "maintenance_probe")
            probe.verify(args.nginx, export)
    except (ValueError, FileExistsError) as failure:
        parser.error(str(failure))


if __name__ == "__main__":
    main()
