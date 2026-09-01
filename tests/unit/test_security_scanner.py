"""Unit tests for Security & Secret Scanner Analyzer."""

from pathlib import Path
from wia.analyzers.security.secret_scanner import SecretScanner, SecurityFinding


def test_security_finding_to_dict():
    finding = SecurityFinding(
        file_path="config.py",
        line_number=10,
        rule_id="SEC-001",
        severity="CRITICAL",
        description="AWS Key exposed",
        match_snippet="AKIA...1234",
        classification="REAL_SECRET",
        confidence="HIGH",
    )
    data = finding.to_dict()
    assert data["rule_id"] == "SEC-001"
    assert data["severity"] == "CRITICAL"
    assert data["file_path"] == "config.py"
    assert data["classification"] == "REAL_SECRET"


def test_mask_secret():
    assert SecretScanner.mask_secret("AKIAIOSFODNN7EXAMPLE") == "AKIA************MPLE"
    assert SecretScanner.mask_secret("short") == "*****"


def test_scan_aws_key():
    content = "aws_key = 'AKIAIOSFODNN7EXAMPLE'"
    findings = SecretScanner.scan_content(content, "aws.py")
    assert len(findings) >= 1
    aws_finding = next(f for f in findings if f.rule_id == "SEC-001")
    assert aws_finding.severity == "CRITICAL"
    assert "AKIAIOSFODNN7EXAMPLE" not in aws_finding.match_snippet
    assert aws_finding.classification == "REAL_SECRET"


def test_classify_synthetic_test_fixture():
    content = """
def test_scanner():
    (ignored_dir / "secret.py").write_text("AKIAIOSFODNN7EXAMPLE", encoding="utf-8")
    assert SecretScanner.mask_secret("AKIAIOSFODNN7EXAMPLE")
"""
    findings = SecretScanner.scan_content(content, "tests/unit/test_security_scanner.py")
    assert len(findings) >= 1
    for f in findings:
        assert f.classification == "SYNTHETIC_TEST_FIXTURE"


def test_classify_documentation_example():
    content = "Example token: `ghp_123456789012345678901234567890123456`"
    findings = SecretScanner.scan_content(content, "README.md")
    assert len(findings) >= 1
    assert findings[0].classification == "DOCUMENTATION_EXAMPLE"


def test_scan_private_key():
    content = "-----BEGIN RSA PRIVATE KEY-----\nMIIEogIBAAKCAQ..."
    findings = SecretScanner.scan_content(content, "id_rsa")
    assert len(findings) == 1
    assert findings[0].rule_id == "SEC-002"
    assert findings[0].severity == "CRITICAL"


def test_scan_github_pat():
    content = "token = 'ghp_123456789012345678901234567890123456'"
    findings = SecretScanner.scan_content(content, "auth.py")
    assert len(findings) >= 1
    pat_finding = next(f for f in findings if f.rule_id == "SEC-003")
    assert pat_finding.severity == "HIGH"


def test_scan_generic_api_key():
    content = "api_key = 'sk_live_123456789012345678'"
    findings = SecretScanner.scan_content(content, "settings.py")
    assert len(findings) >= 1
    key_finding = next(f for f in findings if f.rule_id == "SEC-004")
    assert key_finding.severity == "HIGH"


def test_scan_slack_webhook():

    content = (
        "WEBHOOK = 'https://hooks.slack.com/services/'"
        "'T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'"
    )

    findings = SecretScanner.scan_content(content, "notify.py")

    assert len(findings) >= 1

    webhook_finding = next(f for f in findings if f.rule_id == "SEC-005")

    assert webhook_finding.severity == "MEDIUM"

def test_scan_file_and_workspace(tmp_path: Path):
    clean_file = tmp_path / "clean.py"
    clean_file.write_text("print('Hello world')", encoding="utf-8")

    dirty_file = tmp_path / "dirty.py"
    dirty_file.write_text("api_key = 'secret_123456789012345678'", encoding="utf-8")

    ignored_dir = tmp_path / ".wia"
    ignored_dir.mkdir()
    (ignored_dir / "secret.py").write_text("AKIAIOSFODNN7EXAMPLE", encoding="utf-8")

    findings = SecretScanner.scan_workspace(tmp_path)
    assert len(findings) >= 1
    paths = {f.file_path for f in findings}
    assert any("dirty.py" in p for p in paths)
    assert not any(".wia" in p for p in paths)
