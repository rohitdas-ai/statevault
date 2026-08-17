import os

def test_submission_doc_exists():
    assert os.path.exists("docs/SUBMISSION.md")
    with open("docs/SUBMISSION.md", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Must explicitly document all 4 CockroachDB tools
    assert "Managed MCP Server" in content
    assert "Distributed Vector Indexing" in content
    assert "ccloud CLI" in content
    assert "Agent Skills" in content

    # Must document AWS services
    assert "Amazon Bedrock" in content
    assert "AWS Lambda" in content
    assert "Amazon SQS" in content

    # Must have screencast video script
    assert "Video Screencast Script" in content
    assert "Testing Instructions" in content

def test_readme_references_submission():
    assert os.path.exists("README.md")
    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()
    assert "StateVault" in readme
    assert "CockroachDB" in readme
    assert "docs/SUBMISSION.md" in readme or "SUBMISSION.md" in readme
