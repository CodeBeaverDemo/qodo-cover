import pytest
import os
from datetime import datetime, timedelta
from cover_agent.UnitTestDB import UnitTestDB, UnitTestGenerationAttempt

DB_NAME = "unit_test_runs.db"
DATABASE_URL = f"sqlite:///{DB_NAME}"
@pytest.fixture
def in_memory_unit_test_db():
    """Fixture providing a new in-memory database instance for isolation."""
    db = UnitTestDB("sqlite:///:memory:")
    yield db
    db.engine.dispose()
@pytest.fixture(scope="class")
def unit_test_db():
    # Create an empty DB file for testing
    with open(DB_NAME, "w"):
        pass

    db = UnitTestDB(DATABASE_URL)
    yield db

    # Cleanup after tests
    db.engine.dispose()

    # Delete the db file
    os.remove(DB_NAME)

@pytest.mark.usefixtures("unit_test_db")
class TestUnitTestDB:

    def test_insert_attempt(self, unit_test_db):
        test_result = {
            "status": "success",
            "reason": "",
            "exit_code": 0,
            "stderr": "",
            "stdout": "Test passed",
            "test": {
                "test_code": "def test_example(): pass",
                "new_imports_code": "import pytest"
            },
            "language": "python",
            "source_file": "sample source code",
            "original_test_file": "sample test code",
            "processed_test_file": "sample new test code",
        }

        attempt_id = unit_test_db.insert_attempt(test_result)
        with unit_test_db.Session() as session:
            attempt = session.query(UnitTestGenerationAttempt).filter_by(id=attempt_id).one()

        assert attempt.id == attempt_id
        assert attempt.status == "success"
        assert attempt.reason == ""
        assert attempt.exit_code == 0
        assert attempt.stderr == ""
        assert attempt.stdout == "Test passed"
        assert attempt.test_code == "def test_example(): pass"
        assert attempt.imports == "import pytest"
        assert attempt.language == "python"
        assert attempt.source_file == "sample source code"
        assert attempt.original_test_file == "sample test code"
        assert attempt.processed_test_file == "sample new test code"

    def test_dump_to_report(self, unit_test_db, tmp_path):
        test_result = {
            "status": "success",
            "reason": "Test passed successfully",
            "exit_code": 0,
            "stderr": "",
            "stdout": "Test passed",
            "test": {
                "test_code": "def test_example(): pass",
                "new_imports_code": "import pytest"
            },
            "language": "python",
            "source_file": "sample source code",
            "original_test_file": "sample test code",
            "processed_test_file": "sample new test code",
        }

        unit_test_db.insert_attempt(test_result)

        # Generate the report and save it to a temporary file
        report_filepath = tmp_path / "unit_test_report.html"
        unit_test_db.dump_to_report(str(report_filepath))

        # Check if the report was generated successfully
        assert os.path.exists(report_filepath)

        # Verify the report content
        with open(report_filepath, "r") as file:
            content = file.read()

        assert "sample test code" in content
        assert "sample new test code" in content
        assert "def test_example(): pass" in content
    def test_get_all_attempts_empty(self, in_memory_unit_test_db):
        """Test get_all_attempts returns an empty list when no attempts are inserted."""
        attempts = in_memory_unit_test_db.get_all_attempts()
        assert attempts == []

    def test_insert_attempt_with_missing_fields(self, in_memory_unit_test_db):
        """Test that insert_attempt handles missing nested keys and defaults to empty strings."""
        test_result = {}  # Empty dictionary, missing all expected keys
        attempt_id = in_memory_unit_test_db.insert_attempt(test_result)
        with in_memory_unit_test_db.Session() as session:
            attempt = session.query(UnitTestGenerationAttempt).filter_by(id=attempt_id).one()
        assert attempt.status is None
        assert attempt.reason is None
        assert attempt.exit_code is None
        assert attempt.stderr is None
        assert attempt.stdout is None
        assert attempt.test_code == ""
        assert attempt.imports == ""
        assert attempt.language is None
        assert attempt.prompt is None
        assert attempt.source_file is None
        assert attempt.original_test_file is None
        assert attempt.processed_test_file is None

    def test_get_all_attempts_multiple(self, in_memory_unit_test_db):
        """Test that get_all_attempts returns all inserted attempts."""
        test_result1 = {
            "status": "success",
            "reason": "First attempt",
        }
        test_result2 = {
            "status": "failure",
            "reason": "Second attempt",
        }
        in_memory_unit_test_db.insert_attempt(test_result1)
        in_memory_unit_test_db.insert_attempt(test_result2)
        attempts = in_memory_unit_test_db.get_all_attempts()
        statuses = {a["status"] for a in attempts}
        assert "success" in statuses
        assert "failure" in statuses
    
    def test_dump_to_report_with_monkeypatch(self, in_memory_unit_test_db, tmp_path, monkeypatch):
        """Test that dump_to_report calls ReportGenerator.generate_report with the correct parameters."""
        # Insert a test attempt so that there is data to report.
        test_result = {
            "status": "success",
            "reason": "Dump report test",
            "exit_code": 0,
            "stderr": "",
            "stdout": "All good",
            "test": {
                "test_code": "def test_sample(): pass",
                "new_imports_code": "import sys"
            },
            "language": "python",
            "source_file": "source.py",
            "original_test_file": "test_original.py",
            "processed_test_file": "test_processed.py",
        }
        in_memory_unit_test_db.insert_attempt(test_result)
        called = {}
        def fake_generate_report(attempts, report_filepath):
            called["attempts"] = attempts
            called["report_filepath"] = report_filepath
            with open(report_filepath, "w") as f:
                f.write("dummy report")
        from cover_agent.UnitTestDB import ReportGenerator
        monkeypatch.setattr(ReportGenerator, "generate_report", fake_generate_report)
        report_filepath = str(tmp_path / "monkey_report.html")
        in_memory_unit_test_db.dump_to_report(report_filepath)
        # Verify that fake_generate_report was called with the correct parameters.
        assert "attempts" in called
        assert "report_filepath" in called
        assert called["report_filepath"] == report_filepath
        # Check that the report file was created and contains the dummy content.
        with open(report_filepath, "r") as f:
            content = f.read()
        assert "dummy report" in content
    def test_insert_attempt_run_time(self, in_memory_unit_test_db):
        """Test that the run_time is correctly set to a recent time."""
        test_result = {"status": "time_test"}
        from datetime import datetime
        before_insert = datetime.now()
        attempt_id = in_memory_unit_test_db.insert_attempt(test_result)
        after_insert = datetime.now()
        with in_memory_unit_test_db.Session() as session:
            attempt = session.query(UnitTestGenerationAttempt).filter_by(id=attempt_id).one()
        # Check that run_time falls between before_insert and after_insert
        assert before_insert <= attempt.run_time <= after_insert

    def test_insert_attempt_with_prompt(self, in_memory_unit_test_db):
        """Test that the insert_attempt method correctly handles the 'prompt' field."""
        test_result = {
            "status": "prompt_test",
            "prompt": "Enter your test prompt"
        }
        attempt_id = in_memory_unit_test_db.insert_attempt(test_result)
        with in_memory_unit_test_db.Session() as session:
            attempt = session.query(UnitTestGenerationAttempt).filter_by(id=attempt_id).one()
        assert attempt.prompt == "Enter your test prompt"

    def test_dump_to_report_cli(self, monkeypatch, tmp_path):
        """Test the CLI wrapper dump_to_report_cli by simulating command-line arguments."""
        # Create a dummy ReportGenerator.generate_report function
        called = {}
        def fake_generate_report(attempts, report_filepath):
            called["attempts"] = attempts
            called["report_filepath"] = report_filepath
            with open(report_filepath, "w") as f:
                f.write("CLI dummy report")
        from cover_agent.UnitTestDB import ReportGenerator, dump_to_report_cli
        monkeypatch.setattr(ReportGenerator, "generate_report", fake_generate_report)

        # Setup fake command-line arguments; using an in-memory db for testing
        cli_db_path = ":memory:"
        cli_report_path = str(tmp_path / "cli_report.html")
        monkeypatch.setattr("sys.argv", ["dummy", "--path-to-db", cli_db_path, "--report-filepath", cli_report_path])

        dump_to_report_cli()

        # Verify that the report file was created with the dummy content
        assert os.path.exists(cli_report_path)
        with open(cli_report_path, "r") as f:
            content = f.read()
        assert "CLI dummy report" in content
        # Verify that ReportGenerator.generate_report was called with an empty list of attempts
        assert "attempts" in called
        assert len(called["attempts"]) == 0
        assert isinstance(called["attempts"], list)
    
    def test_sequential_ids(self, in_memory_unit_test_db):
        """Test that each inserted attempt gets a sequential ID, ensuring the auto-increment works."""
        first_id = in_memory_unit_test_db.insert_attempt({"status": "first"})
        second_id = in_memory_unit_test_db.insert_attempt({"status": "second"})
        assert isinstance(first_id, int)
        assert isinstance(second_id, int)
        # For SQLite in-memory, auto-incremented id should be increasing.
        assert second_id > first_id

    def test_dump_to_report_overwrite(self, in_memory_unit_test_db, tmp_path, monkeypatch):
        """Test that dump_to_report overwrites an existing report file."""
        # Insert a simple test attempt so that there is data for the report.
        in_memory_unit_test_db.insert_attempt({"status": "overwrite_test"})
        report_filepath = str(tmp_path / "overwrite_report.html")
        # Pre-create the report file with some initial content.
        with open(report_filepath, "w") as f:
            f.write("initial content")

        # Define a fake ReportGenerator.generate_report that always writes "overwritten content"
        def fake_generate_report(attempts, report_filepath):
            with open(report_filepath, "w") as f:
                f.write("overwritten content")
        from cover_agent.UnitTestDB import ReportGenerator
        monkeypatch.setattr(ReportGenerator, "generate_report", fake_generate_report)

        # Call dump_to_report; it should overwrite the file content.
        in_memory_unit_test_db.dump_to_report(report_filepath)

        with open(report_filepath, "r") as f:
            content = f.read()
        assert content == "overwritten content"
    def test_insert_attempt_with_extra_keys(self, in_memory_unit_test_db):
        """Test that extra keys in test_result are ignored and do not interfere with insertion."""
        test_result = {
            "status": "success",
            "reason": "has extra",
            "exit_code": 0,
            "stderr": "no error",
            "stdout": "output here",
            "test": {
                "test_code": "def extra_test(): pass",
                "new_imports_code": "import os"
            },
            "language": "python",
            "prompt": "extra prompt",
            "source_file": "extra_source",
            "original_test_file": "extra_original",
            "processed_test_file": "extra_processed",
            "extra_field": "should be ignored"
        }
        attempt_id = in_memory_unit_test_db.insert_attempt(test_result)
        with in_memory_unit_test_db.Session() as session:
            attempt = session.query(UnitTestGenerationAttempt).filter_by(id=attempt_id).one()
        # Verify expected fields; extra_field should not affect the record
        assert attempt.status == "success"
        assert attempt.reason == "has extra"
        assert attempt.exit_code == 0
        assert attempt.stderr == "no error"
        assert attempt.stdout == "output here"
        assert attempt.test_code == "def extra_test(): pass"
        assert attempt.imports == "import os"
        assert attempt.language == "python"
        assert attempt.prompt == "extra prompt"
        assert attempt.source_file == "extra_source"
        assert attempt.original_test_file == "extra_original"
        assert attempt.processed_test_file == "extra_processed"

    def test_insert_attempt_with_non_dict_test(self, in_memory_unit_test_db):
        """Test that providing a non-dict value for 'test' raises an error."""
        test_result = {"status": "error", "test": "not a dict"}
        import pytest
        with pytest.raises(AttributeError):
            in_memory_unit_test_db.insert_attempt(test_result)
    def test_dump_to_report_exception(self, in_memory_unit_test_db, tmp_path, monkeypatch):
        """Test that dump_to_report propagates an exception from ReportGenerator.generate_report."""
        from cover_agent.UnitTestDB import ReportGenerator
        # Monkey-patch generate_report to raise an exception when called
        monkeypatch.setattr(ReportGenerator, "generate_report", lambda attempts, report_filepath: (_ for _ in ()).throw(Exception("Test exception")))
        import pytest
        with pytest.raises(Exception) as excinfo:
            in_memory_unit_test_db.dump_to_report(str(tmp_path / "exception_report.html"))
        assert "Test exception" in str(excinfo.value)

    def test_dump_to_report_empty_db(self, in_memory_unit_test_db, tmp_path, monkeypatch):
        """Test that dump_to_report handles an empty database by calling ReportGenerator.generate_report with an empty list."""
        called = {}
        def fake_generate_report(attempts, report_filepath):
            called["attempts"] = attempts
            with open(report_filepath, "w") as f:
                f.write("empty report")
        from cover_agent.UnitTestDB import ReportGenerator
        monkeypatch.setattr(ReportGenerator, "generate_report", fake_generate_report)
        report_filepath = str(tmp_path / "empty_dump_report.html")
        in_memory_unit_test_db.dump_to_report(report_filepath)
        with open(report_filepath, "r") as f:
            content = f.read()
        assert content == "empty report"
        assert called["attempts"] == []