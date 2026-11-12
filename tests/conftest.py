"""tests never run real shell commands."""
import os
import subprocess

import pytest


@pytest.fixture(autouse=True)
def no_shell(monkeypatch):
    calls = []
    monkeypatch.setattr(os, "system", lambda cmd: calls.append(cmd) or 0)
    monkeypatch.setattr(subprocess, "run", lambda args, *a, **k: calls.append(args) or subprocess.CompletedProcess(args, 0))
    return calls
