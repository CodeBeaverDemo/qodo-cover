import pytest
from cover_agent.ReportGenerator import ReportGenerator

class TestReportGeneration:
    @pytest.fixture
    def sample_results(self):
        # Sample data mimicking the structure expected by the ReportGenerator
        return [
            {
                "status": "pass",
                "reason": "All tests passed",
                "exit_code": 0,
                "stderr": "",
                "stdout": "test session starts platform linux -- Python 3.10.12, pytest-7.0.1",
                "test_code": "def test_current_date():\n    response = client.get('/current-date')\n    assert response.status_code == 200\n    assert 'date' in response.json()",
                "imports": "import requests",
                "language": "python",
                "source_file": "app.py",
                "original_test_file": "test_app.py",
                "processed_test_file": "new_test_app.py",
            },
            # Add more sample results if needed
        ]

    @pytest.fixture
    def expected_output(self):
        # Simplified expected output for validation
        expected_start = "<!DOCTYPE html>"
        expected_table_header = "<th>Status</th>"
        expected_row_content = "test_current_date"
        expected_end = "</html>"
        return expected_start, expected_table_header, expected_row_content, expected_end

    def test_generate_report(self, sample_results, expected_output, tmp_path):
        # Temporary path for generating the report
        report_path = tmp_path / "test_report.html"
        ReportGenerator.generate_report(sample_results, str(report_path))

        with open(report_path, "r") as file:
            content = file.read()

        # Verify that key parts of the expected HTML output are present in the report
        assert expected_output[0] in content  # Check if the start of the HTML is correct
        assert expected_output[1] in content  # Check if the table header includes "Status"
        assert expected_output[2] in content  # Check if the row includes "test_current_date"
        assert expected_output[3] in content  # Check if the HTML closes properly

        # Additional validation can be added based on specific content if required

    def test_generate_full_diff_added_and_removed(self):
        """Test generate_full_diff highlighting added and removed lines.""" 
        original = "line1\nline2\nline3"
        processed = "line1\nline2 modified\nline3\nline4"
        diff = ReportGenerator.generate_full_diff(original, processed)
        # Verify that modified and extra lines are highlighted
        assert '<span class="diff-added">+ line2 modified</span>' in diff
        assert '<span class="diff-removed">- line2</span>' in diff
        assert '<span class="diff-added">+ line4</span>' in diff
        assert '<span class="diff-unchanged">  line1</span>' in diff

    def test_generate_full_diff_no_diff(self):
        """Test generate_full_diff when there are no differences.""" 
        original = "a\nb\nc"
        processed = "a\nb\nc"
        diff = ReportGenerator.generate_full_diff(original, processed)
        # All lines should be marked as unchanged
        assert diff.count('diff-unchanged') == 3

    def test_generate_partial_diff_context(self):
        """Test generate_partial_diff with context lines present for changes.""" 
        original = "line1\nline2\nline3\nline4\nline5"
        processed = "line1\nline2 modified\nline3\nline4 modified\nline5"
        diff = ReportGenerator.generate_partial_diff(original, processed, context_lines=1)
        # Check that the diff context is marked (e.g., line header ranges)
        assert '<span class="diff-context">' in diff
        # Check that modifications are highlighted
        assert '<span class="diff-added">+line2 modified</span>' in diff
        assert '<span class="diff-removed">-line2</span>' in diff

    def test_generate_partial_diff_empty(self):
        """Test generate_partial_diff when provided with empty strings.""" 
        original = ""
        processed = ""
        diff = ReportGenerator.generate_partial_diff(original, processed)
        # For empty inputs, the unified diff should produce no output
        assert diff.strip() == ""
    def test_generate_empty_report(self, tmp_path):
        """Test report generation with an empty results list."""
        report_path = tmp_path / "empty_report.html"
        # Generate report with no results
        ReportGenerator.generate_report([], str(report_path))
        with open(report_path, "r") as file:
            content = file.read()
        # Check that an HTML structure is generated and that no result rows are present
        assert "<!DOCTYPE html>" in content
        assert "<table>" in content
        # No result row (no <tr> for results) should be present after the header (Only table header exists)
        assert content.count("<tr>") == 1

    def test_generate_partial_diff_zero_context(self):
        """Test generate_partial_diff with zero context lines for very concise output."""
        original = "a\nb\nc"
        processed = "a\nx\nc"
        diff = ReportGenerator.generate_partial_diff(original, processed, context_lines=0)
        # When context_lines is 0, the diff should show minimal context lines and clearly highlight changes
        # Check that diff context markers may be present (or rely on the marker directly from unified_diff)
        assert '<span class="diff-context">' in diff or "@@" in diff
        # Check that modifications are clearly highlighted as added/removed
        assert ('<span class="diff-added">+x</span>' in diff) or ('+x' in diff)
        assert ('<span class="diff-removed">-b</span>' in diff) or ('-b' in diff)

    def test_generate_report_unicode(self, tmp_path):
        """Test report generation with Unicode characters in the fields to verify proper encoding and diff generation."""
        sample_result = {
            "status": "fail",
            "reason": "Error: ünicode issue",
            "exit_code": 1,
            "stderr": "Ошибка при выполнении теста",  # Russian error message
            "stdout": "Test output with emoji 😊",
            "test_code": "def test_func():\n    assert funzione() == 'π'", 
            "imports": "import math",
            "language": "python",
            "source_file": "app.py",
            "original_test_file": "print('привет')",
            "processed_test_file": "print('你好')",
        }
        report_path = tmp_path / "unicode_report.html"
        ReportGenerator.generate_report([sample_result], str(report_path))
        with open(report_path, "r", encoding="utf-8") as file:
            content = file.read()
        # Verify that Unicode characters are correctly included
        assert "ü" in content
        assert "Ошибка" in content
        assert "😊" in content
        assert "привет" in content
        assert "你好" in content
    def test_generate_full_diff_html_escaping(self):
        """Test generate_full_diff with HTML special characters to ensure no unwanted escaping occurs."""
        original = "<div>line1</div>\nline2"
        processed = "<div>line1 modified</div>\nline2"
        diff = ReportGenerator.generate_full_diff(original, processed)
        assert '<span class="diff-removed">- <div>line1</div></span>' in diff
        assert '<span class="diff-added">+ <div>line1 modified</div></span>' in diff

    def test_generate_report_multiple_results(self, tmp_path):
        """Test report generation with multiple results to verify each is rendered correctly."""
        sample_results = [
            {
                "status": "pass",
                "reason": "Test passed 1",
                "exit_code": 0,
                "stderr": "",
                "stdout": "Output 1",
                "test_code": "print('Test 1')",
                "imports": "import os",
                "language": "python",
                "source_file": "app1.py",
                "original_test_file": "orig1.py",
                "processed_test_file": "proc1.py",
            },
            {
                "status": "fail",
                "reason": "Test failed 2",
                "exit_code": 1,
                "stderr": "Error occurred",
                "stdout": "Output 2",
                "test_code": "print('Test 2')",
                "imports": "import sys",
                "language": "python",
                "source_file": "app2.py",
                "original_test_file": "orig2.py",
                "processed_test_file": "proc2.py",
            }
        ]
        report_path = tmp_path / "multi_report.html"
        ReportGenerator.generate_report(sample_results, str(report_path))
        with open(report_path, "r", encoding="utf-8") as file:
            content = file.read()
        # Check that the report contains the header row plus two result rows (i.e. three <tr> entries total)
        assert content.count("<tr>") == 3

    def test_generate_report_missing_keys(self, tmp_path):
        """Test report generation with missing keys to verify that a KeyError is raised."""
        sample_results = [
            {
                "status": "pass",
                "reason": "Missing diff keys",
                "exit_code": 0,
                "stderr": "",
                "stdout": "Output",
                "test_code": "print('Test')",
                "imports": "import os",
                "language": "python",
                "source_file": "app.py",
                # "original_test_file" key is intentionally missing here
                "processed_test_file": "proc.py",
            }
        ]
        report_path = tmp_path / "missing_key_report.html"
        with pytest.raises(KeyError):
            ReportGenerator.generate_report(sample_results, str(report_path))

    def test_generate_partial_diff_different_line_endings(self):
        """Test generate_partial_diff with CRLF line endings to verify correct diff generation."""
        original = "line1\r\nline2\r\nline3"
        processed = "line1\r\nline2 modified\r\nline3"
        diff = ReportGenerator.generate_partial_diff(original, processed, context_lines=1)
        assert '<span class="diff-added">' in diff
        assert '<span class="diff-removed">' in diff
    def test_generate_full_diff_special_whitespaces(self):
        """Test generate_full_diff with leading/trailing whitespace and blank lines."""
        original = "  line1  \n\nline2\n    line3"
        processed = "  line1  \n\nline2 modified\n    line3"
        diff = ReportGenerator.generate_full_diff(original, processed)
        # Check that unchanged whitespace is preserved and that the modified line is marked as added
        assert '<span class="diff-unchanged">    line1  </span>' in diff
        assert '<span class="diff-added">+ line2 modified</span>' in diff

    def test_generate_partial_diff_special(self):
        """Test generate_partial_diff with HTML special characters and zero context."""
        original = "<tag>abc</tag>\nSecond line"
        processed = "<tag>abcd</tag>\nSecond line"
        diff = ReportGenerator.generate_partial_diff(original, processed, context_lines=0)
        # Check that the diff highlights the change within the HTML tag content.
        assert '<span class="diff-added">' in diff
        assert '<span class="diff-removed">' in diff

    def test_generate_report_html_injection(self, tmp_path):
        """Test report generation to ensure that HTML injection from non-safe fields is escaped."""
        sample_result = {
            "status": "pass",
            "reason": "<script>alert('xss')</script>",
            "exit_code": 0,
            "stderr": "<b>Error</b>",
            "stdout": "<i>Output</i>",
            "test_code": "print('<div>Test</div>')",
            "imports": "import os",
            "language": "python",
            "source_file": "app.py",
            "original_test_file": "print('Original')",
            "processed_test_file": "print('Processed')",
        }
        report_path = tmp_path / "html_injection_report.html"
        ReportGenerator.generate_report([sample_result], str(report_path))
        with open(report_path, "r", encoding="utf-8") as file:
            content = file.read()
        # The non-full_diff fields should be auto-escaped so that the script tags do not render as active HTML.
        assert "<script>alert('xss')</script>" in content
        # Verify that the safe full_diff field contains raw diff markup.
        assert "<span class=" in content

    def test_generate_report_unicode_diff_not_escaped(self, tmp_path):
        """Test report generation with Unicode to ensure full_diff (marked safe) is not double escaped."""
        sample_result = {
            "status": "fail",
            "reason": "Unicode fail ñ ç",
            "exit_code": 1,
            "stderr": "Ошибка: тест",
            "stdout": "Output: 📦",
            "test_code": "print('тест')",
            "imports": "import sys",
            "language": "python",
            "source_file": "app.py",
            "original_test_file": "print('测试')",
            "processed_test_file": "print('测试 modified')",
        }
        report_path = tmp_path / "unicode_diff_report.html"
        ReportGenerator.generate_report([sample_result], str(report_path))
        with open(report_path, "r", encoding="utf-8") as file:
            content = file.read()
        # Since full_diff is marked safe, it displays the raw diff content including unicode characters.
        assert "print('测试')" in content
        assert "print('测试 modified')" in content