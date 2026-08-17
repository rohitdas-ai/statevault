import subprocess
import os

def test_deploy_script_exists_and_executable():
    assert os.path.exists("scripts/deploy.sh")
    assert os.access("scripts/deploy.sh", os.X_OK)

def test_deploy_script_dry_run():
    env = os.environ.copy()
    env["DRY_RUN"] = "true"
    result = subprocess.run(["bash", "scripts/deploy.sh"], env=env, capture_output=True, text=True)
    assert result.returncode == 0
    assert "sam build" in result.stdout
