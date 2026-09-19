"""Unit tests for FileType classification detection across diverse file types."""

from wia.core.language import FileType, LanguageDetector


def test_file_type_classification():
    # 1. Notebooks
    assert LanguageDetector.detect_file_type("notebooks/analysis.ipynb") == FileType.NOTEBOOK

    # 2. CI/CD
    assert LanguageDetector.detect_file_type(".github/workflows/release.yml") == FileType.CI_CD
    assert LanguageDetector.detect_file_type(".gitlab-ci.yml") == FileType.CI_CD
    assert LanguageDetector.detect_file_type("Jenkinsfile") == FileType.CI_CD

    # 3. Dependency Lock
    assert LanguageDetector.detect_file_type("uv.lock") == FileType.DEPENDENCY_LOCK
    assert LanguageDetector.detect_file_type("poetry.lock") == FileType.DEPENDENCY_LOCK
    assert LanguageDetector.detect_file_type("package-lock.json") == FileType.DEPENDENCY_LOCK

    # 4. Tests
    assert LanguageDetector.detect_file_type("tests/test_api.py") == FileType.TEST
    assert LanguageDetector.detect_file_type("src/utils_test.py") == FileType.TEST
    assert LanguageDetector.detect_file_type("components/Button.test.tsx") == FileType.TEST

    # 5. Build
    assert LanguageDetector.detect_file_type("pyproject.toml") == FileType.BUILD
    assert LanguageDetector.detect_file_type("package.json") == FileType.BUILD
    assert LanguageDetector.detect_file_type("Dockerfile") == FileType.BUILD

    # 6. Documentation
    assert LanguageDetector.detect_file_type("README.md") == FileType.DOCUMENTATION
    assert LanguageDetector.detect_file_type("docs/architecture.rst") == FileType.DOCUMENTATION

    # 7. Configuration
    assert LanguageDetector.detect_file_type(".env.example") == FileType.CONFIGURATION
    assert LanguageDetector.detect_file_type("tsconfig.json") == FileType.CONFIGURATION
    assert LanguageDetector.detect_file_type("docker-compose.yml") == FileType.CONFIGURATION

    # 8. Source Code
    assert LanguageDetector.detect_file_type("src/main.py") == FileType.SOURCE_CODE
    assert LanguageDetector.detect_file_type("lib/app.ts") == FileType.SOURCE_CODE
    assert LanguageDetector.detect_file_type("server.go") == FileType.SOURCE_CODE
