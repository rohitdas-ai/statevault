import os
import pytest

def test_landing_page_html_structure():
    html_path = os.path.join(os.path.dirname(__file__), "..", "public", "index.html")
    assert os.path.exists(html_path), "index.html missing"
    
    with open(html_path, "r") as f:
        html = f.read()
        
    assert "<!DOCTYPE html>" in html
    assert "StateVault" in html
    assert "CockroachDB" in html
    assert "copy-btn" in html
    assert "pricing-card" in html
    assert "https://fonts.googleapis.com/css2?family=Inter" in html
