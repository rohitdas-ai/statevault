import re

def test_landing_page_html_structure():
    with open("public/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    assert "<!DOCTYPE html>" in html
    assert "<title>StateVault | Memory-as-a-Service for AI Agents</title>" in html
    assert 'id="sync-curl-command"' in html
    assert 'id="copy-btn-sync"' in html
    assert 'id="interactive-simulator"' in html
    assert 'id="btn-run-simulation"' in html
    assert 'id="sim-output"' in html
    assert 'id="architecture-comparison"' in html
