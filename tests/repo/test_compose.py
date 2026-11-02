"""Fázis 8 — a Docker Compose-rendszer épsége (a repó-checkoutot tesztelik).

A Compose-fájlt szövegként vizsgáljuk (a PyYAML nincs a rögzített stackben); a tényleges
érvényességet a ``docker compose config`` és a konténeres indítás igazolja (TR-F08).

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def compose_text(repo_root: Path) -> str:
    return (repo_root / "docker" / "docker-compose.yml").read_text(encoding="utf-8")


def _service_block(text: str, name: str) -> str:
    """Egy szolgáltatás blokkja a ``services:`` alatt (a következőig, vagy a ``volumes:``-ig)."""
    pattern = rf"^  {name}:\n(.*?)(?=^  [a-z][a-z-]*:\n|^volumes:\n)"
    match = re.search(pattern, text, re.M | re.S)
    assert match, f"nincs `{name}` szolgáltatás a docker-compose.yml-ben"
    return match.group(1)


def test_every_service_uses_the_current_version_tag(compose_text: str, repo_root: Path) -> None:
    """Minden szolgáltatás az aktuális ``VERSION``-nek megfelelő image-címkét használja."""
    version = (repo_root / "VERSION").read_text(encoding="utf-8").strip()
    images = re.findall(r"^    image: (\S+)$", compose_text, re.M)
    assert len(images) >= 3, f"várt legalább 3 szolgáltatás (app, scheduler, dashboard): {images}"
    assert set(images) == {f"vqebd:{version}"}, images


def test_the_three_services_exist(compose_text: str) -> None:
    for name in ("app", "scheduler", "dashboard"):
        _service_block(compose_text, name)


def test_dashboard_is_reachable_only_from_the_host_loopback(compose_text: str) -> None:
    """A dashboardnak nincs hitelesítése: a port csak a 127.0.0.1-re van kötve."""
    block = _service_block(compose_text, "dashboard")
    ports = re.findall(r'^\s+- "([^"]+:[^"]+)"$', block, re.M)
    published = [p for p in ports if p.endswith(":8501")]
    assert published, f"a dashboard nem tesz közzé portot: {ports}"
    assert all(p.startswith("127.0.0.1:") for p in published), published
    assert "0.0.0.0:" not in block.replace('"0.0.0.0",', "")  # a szerver-cím nem a közzététel


def test_dashboard_runs_streamlit_with_the_thin_entry_point(compose_text: str) -> None:
    block = _service_block(compose_text, "dashboard")
    assert '"streamlit", "run", "dashboard/app.py"' in block
    assert '"--server.headless", "true"' in block
    assert '"--browser.gatherUsageStats", "false"' in block  # nincs kimenő telemetria


def test_dashboard_has_no_secrets_and_no_hardware_access(compose_text: str) -> None:
    """Nincs env_file, token, instance és QPU: a dashboard csak olvas."""
    block = _service_block(compose_text, "dashboard").lower()
    for forbidden in ("env_file", "ibm_quantum", "token", "allow_hardware", ".env"):
        assert forbidden not in block, forbidden


def test_dashboard_mounts_code_and_versioned_exports_read_only(compose_text: str) -> None:
    block = _service_block(compose_text, "dashboard")
    for mount in (
        "../src:/app/src:ro",
        "../dashboard:/app/dashboard:ro",
        "../docs/figures/data:/app/docs/figures/data:ro",
    ):
        assert mount in block, mount
    assert (
        "vqebd-data:/app/data" in block
    )  # az ütemező adatbázisa; a dashboard read_only=True-val nyitja
    assert "VQEBD_DASHBOARD_ROOT: /app" in block


def test_dashboard_has_a_healthcheck_on_the_streamlit_endpoint(compose_text: str) -> None:
    block = _service_block(compose_text, "dashboard")
    assert "healthcheck:" in block and "/_stcore/health" in block
    assert "start_period" in block


def test_makefile_offers_the_dashboard_commands(repo_root: Path) -> None:
    makefile = (repo_root / "Makefile").read_text(encoding="utf-8")
    for target in ("dashboard:", "dashboard-stop:", "dashboard-logs:"):
        assert re.search(rf"^{target}", makefile, re.M), target
    assert "up -d --build dashboard" in makefile


def test_dockerfile_ships_the_dashboard_directory(repo_root: Path) -> None:
    dockerfile = (repo_root / "docker" / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY --chown=vqebd:vqebd dashboard/ ./dashboard/" in dockerfile
