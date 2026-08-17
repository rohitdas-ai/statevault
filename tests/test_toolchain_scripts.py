import subprocess
import os

def test_ccloud_check_script_executable():
    assert os.path.exists("scripts/ccloud_check.sh")
    assert os.access("scripts/ccloud_check.sh", os.X_OK)

def test_run_skills_audit_script_executable():
    assert os.path.exists("scripts/run_skills_audit.sh")
    assert os.access("scripts/run_skills_audit.sh", os.X_OK)

def test_ccloud_check_dry_run():
    env = os.environ.copy()
    env["DRY_RUN"] = "true"
    result = subprocess.run(["bash", "scripts/ccloud_check.sh"], env=env, capture_output=True, text=True)
    assert result.returncode == 0
    assert "statevault-db" in result.stdout

def test_run_skills_audit_dry_run():
    env = os.environ.copy()
    env["DRY_RUN"] = "true"
    result = subprocess.run(["bash", "scripts/run_skills_audit.sh"], env=env, capture_output=True, text=True)
    assert result.returncode == 0
    assert "detect-schema-anti-patterns" in result.stdout
