import re
from typing import List, Dict, Any

class EndpointDetector:
    """Detects REST API endpoints and routes across FastAPI, Express, Flask, Django, Spring, and Go."""

    @staticmethod
    def detect_endpoints(file_path: str, code_content: str, language: str) -> List[Dict[str, Any]]:
        endpoints = []
        lines = code_content.splitlines()

        # FastAPI / Flask: @app.get("/path"), @router.post("/path")
        py_route_pattern = re.compile(r"""@(?:app|router|api_router)\.(get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]""")
        # Express / JS: app.get('/path', ...), router.post('/path', ...)
        js_route_pattern = re.compile(r"""(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]""")
        # Go Gin/Fiber: r.GET("/path", ...), app.Post("/path", ...)
        go_route_pattern = re.compile(r"""\.(GET|POST|PUT|DELETE|PATCH|Get|Post)\s*\(\s*['"]([^'"]+)['"]""")

        for idx, line in enumerate(lines, 1):
            if language == "Python":
                m = py_route_pattern.search(line)
                if m:
                    method, path = m.groups()
                    endpoints.append({
                        "method": method.upper(),
                        "path": path,
                        "file_path": file_path,
                        "line": idx,
                        "framework": "FastAPI/Flask"
                    })
            elif language in ("JavaScript", "TypeScript"):
                m = js_route_pattern.search(line)
                if m:
                    method, path = m.groups()
                    endpoints.append({
                        "method": method.upper(),
                        "path": path,
                        "file_path": file_path,
                        "line": idx,
                        "framework": "Express/Koa"
                    })
            elif language == "Go":
                m = go_route_pattern.search(line)
                if m:
                    method, path = m.groups()
                    endpoints.append({
                        "method": method.upper(),
                        "path": path,
                        "file_path": file_path,
                        "line": idx,
                        "framework": "Gin/Fiber"
                    })

        return endpoints

class TestDetector:
    """Discovers test suites, test files, and test-to-source linkages."""

    @staticmethod
    def is_test_file(file_path: str) -> bool:
        path_lower = file_path.lower()
        return (
            "test" in path_lower or "spec" in path_lower or
            path_lower.startswith("tests/") or path_lower.endswith("_test.go") or
            path_lower.endswith(".test.ts") or path_lower.endswith(".test.js") or
            path_lower.endswith(".spec.ts") or path_lower.endswith(".spec.js")
        )

    @staticmethod
    def extract_test_cases(file_path: str, code_content: str, language: str) -> List[Dict[str, Any]]:
        tests = []
        lines = code_content.splitlines()

        # Python pytest: def test_something(...)
        py_test_pattern = re.compile(r"""def\s+(test_\w+)\s*\(""")
        # JS/TS Jest/Mocha: test("name", ...), it("name", ...)
        js_test_pattern = re.compile(r"""(?:test|it)\s*\(\s*['"]([^'"]+)['"]""")
        # Go: func TestSomething(t *testing.T)
        go_test_pattern = re.compile(r"""func\s+(Test\w+)\s*\(""")

        for idx, line in enumerate(lines, 1):
            if language == "Python":
                m = py_test_pattern.search(line)
                if m:
                    tests.append({"name": m.group(1), "file_path": file_path, "line": idx})
            elif language in ("JavaScript", "TypeScript"):
                m = js_test_pattern.search(line)
                if m:
                    tests.append({"name": m.group(1), "file_path": file_path, "line": idx})
            elif language == "Go":
                m = go_test_pattern.search(line)
                if m:
                    tests.append({"name": m.group(1), "file_path": file_path, "line": idx})

        return tests
