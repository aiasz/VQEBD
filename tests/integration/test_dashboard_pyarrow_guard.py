"""Fázis 7 — őr a pyarrow szegmentációs hibája ellen (M9, ``requirements-dashboard.txt``).

A ``pyarrow 25.0.0`` összeomlik (szegmentációs hiba), ha egy script-futásban ``st.dataframe`` fut,
a következő futás (a Streamlit minden futást új szálban végez) pedig ``pyarrow.compute``-ot hív
(pl. a pandas ``Series.unique()``-ját az ``str`` oszloptípuson). Egy szegmentációs hiba a
tesztfolyamatot is megölné, ezért a próba **alfolyamatban** fut.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

pytest.importorskip("streamlit", reason="a dashboard-tesztek a streamlit csomagot igénylik")

pytestmark = pytest.mark.integration

_PROBE = textwrap.dedent(
    '''
    from streamlit.testing.v1 import AppTest

    APP = """
    import pandas as pd
    import streamlit as st

    df = pd.DataFrame({"s": ["b", "a", "b"], "v": [1, 2, 3]})
    if st.radio("nézet", ["tábla", "egyedi"], key="r") == "tábla":
        st.dataframe(df)
    else:
        st.write(sorted(df["s"].dropna().unique()))
    """

    at = AppTest.from_string(APP, default_timeout=60).run()
    assert not at.exception, list(at.exception)
    at.radio(key="r").set_value("egyedi").run()
    assert not at.exception, list(at.exception)
    print("KÉSZ")
    '''
)


def test_second_script_run_after_st_dataframe_does_not_crash() -> None:
    """A második futás ``pyarrow.compute``-hívása nem omolhat össze az ``st.dataframe`` után."""
    result = subprocess.run(
        [sys.executable, "-W", "ignore", "-c", _PROBE],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert result.returncode == 0, (
        f"a próba kilépési kódja {result.returncode} (139 = szegmentációs hiba): "
        "a pyarrow pinje feltehetően túl magas (requirements-dashboard.txt, M9)\n"
        f"{result.stderr[-800:]}"
    )
    assert "KÉSZ" in result.stdout
