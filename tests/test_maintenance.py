import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from mobile_foundation.maintenance import bundle, export


def test_portable_bundle_is_deterministic_and_independent(tmp_path):
    one, two = tmp_path / "one.pyz", tmp_path / "two.pyz"
    bundle(one)
    bundle(two)
    assert one.read_bytes() == two.read_bytes()
    with zipfile.ZipFile(one) as archive:
        assert "maintenance_assets/unavailable.html" in archive.namelist()
    destination = tmp_path / "standalone"
    subprocess.run(
        [sys.executable, str(one), "export", str(destination), "--upstream", "http://localhost:8000"],
        check=True,
        cwd=tmp_path,
    )
    for state in ["on", "off"]:
        subprocess.run([sys.executable, str(one), "mode", str(destination), state], check=True, cwd=tmp_path)
        assert (destination / "maintenance.flag").exists() == (state == "on")


@pytest.mark.parametrize(
    "upstream",
    [
        "https://localhost:8000",
        "http://user:secret@host",
        "http://host/path",
        "http://host;return 200",
        "http://host:0",
    ],
)
def test_rejects_unsafe_configuration(tmp_path, upstream):
    with pytest.raises(ValueError):
        export(tmp_path / "edge", upstream)
    assert not (tmp_path / "edge").exists()


def test_service_name_is_escaped_and_export_preserves_existing_directory(tmp_path):
    destination = tmp_path / "edge"
    export(destination, "http://localhost:8000", service="<script>bad</script>")
    assert "&lt;script&gt;" in (destination / "public/unavailable.html").read_text()
    with pytest.raises(FileExistsError):
        export(destination, "http://localhost:8000")
    assert not (destination / "maintenance.flag").exists()


def test_container_paths_and_dependency_lock_reject_tampering(tmp_path):
    destination = tmp_path / "context"
    export(destination, "http://localhost:8000", runtime_root=Path("/opt/maintenance"))
    assert "/opt/maintenance/public" in (destination / "server.conf").read_text()
    assert str(tmp_path) not in (destination / "nginx.conf").read_text()
    tool = tmp_path / "tool.pyz"
    bundle(tool)
    lock = tmp_path / "lock.json"
    lock.write_text(json.dumps({"sha256": "0" * 64}))
    result = subprocess.run(
        [
            sys.executable,
            str(tool),
            "export",
            str(tmp_path / "bad"),
            "--upstream",
            "http://localhost:8000",
            "--lock",
            str(lock),
        ],
        check=False,
        capture_output=True,
    )
    assert result.returncode != 0 and b"SHA-256" in result.stderr
    assert not (tmp_path / "bad").exists()
