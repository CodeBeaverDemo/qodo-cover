from cover_agent.CoverAgent import CoverAgent
from cover_agent.main import parse_args
from unittest.mock import patch, MagicMock
import argparse
import os
import pytest
import tempfile

import unittest
class TestCoverAgent:
    def test_parse_args(self):
        with patch(
            "sys.argv",
            [
                "program.py",
                "--source-file-path",
                "test_source.py",
                "--test-file-path",
                "test_file.py",
                "--code-coverage-report-path",
                "coverage_report.xml",
                "--test-command",
                "pytest",
                "--max-iterations",
                "10",
            ],
        ):
            args = parse_args()
            assert args.source_file_path == "test_source.py"
            assert args.test_file_path == "test_file.py"
            assert args.code_coverage_report_path == "coverage_report.xml"
            assert args.test_command == "pytest"
            assert args.test_command_dir == os.getcwd()
            assert args.included_files is None
            assert args.coverage_type == "cobertura"
            assert args.report_filepath == "test_results.html"
            assert args.desired_coverage == 90
            assert args.max_iterations == 10

    @patch("cover_agent.CoverAgent.UnitTestGenerator")
    @patch("cover_agent.CoverAgent.ReportGenerator")
    @patch("cover_agent.CoverAgent.os.path.isfile")
    def test_agent_source_file_not_found(
        self, mock_isfile, mock_report_generator, mock_unit_cover_agent
    ):
        args = argparse.Namespace(
            source_file_path="test_source.py",
            test_file_path="test_file.py",
            code_coverage_report_path="coverage_report.xml",
            test_command="pytest",
            test_command_dir=os.getcwd(),
            included_files=None,
            coverage_type="cobertura",
            report_filepath="test_results.html",
            desired_coverage=90,
            max_iterations=10,
        )
        parse_args = lambda: args
        mock_isfile.return_value = False

        with patch("cover_agent.main.parse_args", parse_args):
            with pytest.raises(FileNotFoundError) as exc_info:
                agent = CoverAgent(args)

        assert (
            str(exc_info.value) == f"Source file not found at {args.source_file_path}"
        )

        mock_unit_cover_agent.assert_not_called()
        mock_report_generator.generate_report.assert_not_called()

    @patch("cover_agent.CoverAgent.os.path.exists")
    @patch("cover_agent.CoverAgent.os.path.isfile")
    @patch("cover_agent.CoverAgent.UnitTestGenerator")
    def test_agent_test_file_not_found(
        self, mock_unit_cover_agent, mock_isfile, mock_exists
    ):
        args = argparse.Namespace(
            source_file_path="test_source.py",
            test_file_path="test_file.py",
            code_coverage_report_path="coverage_report.xml",
            test_command="pytest",
            test_command_dir=os.getcwd(),
            included_files=None,
            coverage_type="cobertura",
            report_filepath="test_results.html",
            desired_coverage=90,
            max_iterations=10,
            prompt_only=False,
        )
        parse_args = lambda: args
        mock_isfile.side_effect = [True, False]
        mock_exists.return_value = True

        with patch("cover_agent.main.parse_args", parse_args):
            with pytest.raises(FileNotFoundError) as exc_info:
                agent = CoverAgent(args)

        assert str(exc_info.value) == f"Test file not found at {args.test_file_path}"

    @patch("cover_agent.CoverAgent.shutil.copy")
    @patch("cover_agent.CoverAgent.os.path.isfile", return_value=True)
    def test_duplicate_test_file_with_output_path(self, mock_isfile, mock_copy):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_test_file:
                args = argparse.Namespace(
                    source_file_path=temp_source_file.name,
                    test_file_path=temp_test_file.name,
                    test_file_output_path="output_test_file.py",  # This will be the path where output is copied
                    code_coverage_report_path="coverage_report.xml",
                    test_command="echo hello",
                    test_command_dir=os.getcwd(),
                    included_files=None,
                    coverage_type="cobertura",
                    report_filepath="test_results.html",
                    desired_coverage=90,
                    max_iterations=10,
                    additional_instructions="",
                    model="openai/test-model",
                    api_base="openai/test-api",
                    use_report_coverage_feature_flag=False,
                    log_db_path="",
                    mutation_testing=False,
                    more_mutation_logging=False,
                )

                with pytest.raises(AssertionError) as exc_info:
                    agent = CoverAgent(args)
                    agent.test_gen.get_coverage_and_build_prompt()
                    agent._duplicate_test_file()

                assert "Fatal: Coverage report" in str(exc_info.value)
                mock_copy.assert_called_once_with(args.test_file_path, args.test_file_output_path)

        # Clean up the temp files
        os.remove(temp_source_file.name)
        os.remove(temp_test_file.name)

    @patch("cover_agent.CoverAgent.os.path.isfile", return_value=True)
    def test_duplicate_test_file_without_output_path(self, mock_isfile):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_test_file:
                args = argparse.Namespace(
                    source_file_path=temp_source_file.name,
                    test_file_path=temp_test_file.name,
                    test_file_output_path="",  # No output path provided
                    code_coverage_report_path="coverage_report.xml",
                    test_command="echo hello",
                    test_command_dir=os.getcwd(),
                    included_files=None,
                    coverage_type="cobertura",
                    report_filepath="test_results.html",
                    desired_coverage=90,
                    max_iterations=10,
                    additional_instructions="",
                    model="openai/test-model",
                    api_base="openai/test-api",
                    use_report_coverage_feature_flag=False,
                    log_db_path="",
                    mutation_testing=False,
                    more_mutation_logging=False,
                )

                with pytest.raises(AssertionError) as exc_info:
                    agent = CoverAgent(args)
                    agent.test_gen.get_coverage_and_build_prompt()
                    agent._duplicate_test_file()

                assert "Fatal: Coverage report" in str(exc_info.value)
                assert args.test_file_output_path == args.test_file_path

        # Clean up the temp files
        os.remove(temp_source_file.name)
        os.remove(temp_test_file.name)
    def test_run_successful(self):
        """Test that CoverAgent.run stops when desired coverage is reached."""
        import tempfile
        # Create temporary source and test files
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source, \
                tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_test:
            args = argparse.Namespace(
                source_file_path=temp_source.name,
                test_file_path=temp_test.name,
                test_file_output_path="",
                code_coverage_report_path="dummy.xml",
                test_command="echo",
                test_command_dir=os.getcwd(),
                included_files=None,
                coverage_type="cobertura",
                report_filepath="dummy_report.html",
                desired_coverage=90,
                max_iterations=2,
                additional_instructions="",
                model="dummy-model",
                api_base="dummy-api",
                use_report_coverage_feature_flag=False,
                log_db_path="dummy.db",
                mutation_testing=False,
                more_mutation_logging=False,
                strict_coverage=False,
                run_tests_multiple_times=False,
            )
            agent = CoverAgent(args)
        # Define a dummy test generator to simulate coverage increase after one iteration.
        class DummyTestGen:
            def __init__(self):
                self.current_coverage = 0.5
                self.desired_coverage = args.desired_coverage
                self.total_input_token_count = 10
                self.total_output_token_count = 20
                self.ai_caller = type("DummyCaller", (), {"model": "dummy-model"})()
                self.mutation_called = False

            def get_coverage_and_build_prompt(self):
                pass

            def initial_test_suite_analysis(self):
                pass

            def generate_tests(self, max_tokens):
                return {"new_tests": ["dummy_test"]}

            def validate_test(self, test, run_tests_multiple_times):
                return "dummy_result"

            def run_coverage(self):
                # Simulate increasing coverage to desired level.
                self.current_coverage = 0.9

            def run_mutations(self):
                self.mutation_called = True
        dummy_gen = DummyTestGen()
        agent.test_gen = dummy_gen
        # Override the test_db with a MagicMock
        dummy_db = MagicMock()
        agent.test_db = dummy_db

        # Call run() and then check that dump_to_report and insert_attempt were called.
        agent.run()

        # Assert that the loop ended with desired coverage reached.
        assert dummy_gen.current_coverage >= 0.9
        # insert_attempt should have been called for each generated test (one iteration only).
        dummy_db.insert_attempt.assert_called()
        dummy_db.dump_to_report.assert_called_once_with(args.report_filepath)

        # Clean up temporary files
        os.remove(args.source_file_path)
        os.remove(args.test_file_path)

    def test_run_max_iterations_strict(self):
        """Test that CoverAgent.run exits with sys.exit(2) when strict_coverage is true and max iterations reached."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source, \
                tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_test:
            args = argparse.Namespace(
                source_file_path=temp_source.name,
                test_file_path=temp_test.name,
                test_file_output_path="",
                code_coverage_report_path="dummy.xml",
                test_command="echo",
                test_command_dir=os.getcwd(),
                included_files=None,
                coverage_type="cobertura",
                report_filepath="dummy_report.html",
                desired_coverage=90,
                max_iterations=1,
                additional_instructions="",
                model="dummy-model",
                api_base="dummy-api",
                use_report_coverage_feature_flag=False,
                log_db_path="dummy.db",
                mutation_testing=False,
                more_mutation_logging=False,
                strict_coverage=True,
                run_tests_multiple_times=False,
            )
            agent = CoverAgent(args)
        # Dummy test generator that never increases coverage.
        class DummyTestGen:
            def __init__(self):
                self.current_coverage = 0.5
                self.desired_coverage = args.desired_coverage
                self.total_input_token_count = 0
                self.total_output_token_count = 0
                self.ai_caller = type("DummyCaller", (), {"model": "dummy-model"})()

            def get_coverage_and_build_prompt(self):
                pass

            def initial_test_suite_analysis(self):
                pass

            def generate_tests(self, max_tokens):
                return {"new_tests": []}

            def validate_test(self, test, run_tests_multiple_times):
                return "dummy_result"

            def run_coverage(self):
                # Do not change coverage.
                pass

            def run_mutations(self):
                pass
        dummy_gen = DummyTestGen()
        agent.test_gen = dummy_gen
        dummy_db = MagicMock()
        agent.test_db = dummy_db

        # Expect sys.exit with code 2 since strict_coverage is true.
        with pytest.raises(SystemExit) as exc_info:
            agent.run()
        assert exc_info.value.code == 2

        os.remove(args.source_file_path)
        os.remove(args.test_file_path)

    def test_run_max_iterations_non_strict(self):
        """Test that CoverAgent.run doesn't exit when strict_coverage is False even if max iterations are reached."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source, \
                tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_test:
            args = argparse.Namespace(
                source_file_path=temp_source.name,
                test_file_path=temp_test.name,
                test_file_output_path="",
                code_coverage_report_path="dummy.xml",
                test_command="echo",
                test_command_dir=os.getcwd(),
                included_files=None,
                coverage_type="cobertura",
                report_filepath="dummy_report.html",
                desired_coverage=90,
                max_iterations=1,
                additional_instructions="",
                model="dummy-model",
                api_base="dummy-api",
                use_report_coverage_feature_flag=False,
                log_db_path="dummy.db",
                mutation_testing=False,
                more_mutation_logging=False,
                strict_coverage=False,
                run_tests_multiple_times=False,
            )
            agent = CoverAgent(args)
        # Dummy test generator that never increases coverage.
        class DummyTestGen:
            def __init__(self):
                self.current_coverage = 0.5
                self.desired_coverage = args.desired_coverage
                self.total_input_token_count = 0
                self.total_output_token_count = 0
                self.ai_caller = type("DummyCaller", (), {"model": "dummy-model"})()

            def get_coverage_and_build_prompt(self):
                pass

            def initial_test_suite_analysis(self):
                pass

            def generate_tests(self, max_tokens):
                return {"new_tests": []}

            def validate_test(self, test, run_tests_multiple_times):
                return "dummy_result"

            def run_coverage(self):
                pass

            def run_mutations(self):
                pass
        dummy_gen = DummyTestGen()
        agent.test_gen = dummy_gen
        dummy_db = MagicMock()
        agent.test_db = dummy_db

        # With strict_coverage False, the run should complete without sys.exit.
        agent.run()
        dummy_db.dump_to_report.assert_called_once_with(args.report_filepath)

        os.remove(args.source_file_path)
        os.remove(args.test_file_path)

    def test_run_with_wandb(self):
        """Test that WANDB is initialized and finished when WANDB_API_KEY is set."""
        import tempfile
        from unittest.mock import patch
        # Set the environment variable for WANDB_API_KEY
        os.environ["WANDB_API_KEY"] = "dummy_key"

        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source, \
                tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_test:
            args = argparse.Namespace(
                source_file_path=temp_source.name,
                test_file_path=temp_test.name,
                test_file_output_path="",
                code_coverage_report_path="dummy.xml",
                test_command="echo",
                test_command_dir=os.getcwd(),
                included_files=None,
                coverage_type="cobertura",
                report_filepath="dummy_report.html",
                desired_coverage=90,
                max_iterations=2,
                additional_instructions="",
                model="dummy-model",
                api_base="dummy-api",
                use_report_coverage_feature_flag=False,
                log_db_path="dummy.db",
                mutation_testing=True,
                more_mutation_logging=False,
                strict_coverage=False,
                run_tests_multiple_times=False,
            )
            agent = CoverAgent(args)
        # Dummy test generator that increases coverage
        class DummyTestGen:
            def __init__(self):
                self.current_coverage = 0.5
                self.desired_coverage = args.desired_coverage
                self.total_input_token_count = 15
                self.total_output_token_count = 25
                self.ai_caller = type("DummyCaller", (), {"model": "dummy-model"})()
                self.mutation_called = False

            def get_coverage_and_build_prompt(self):
                pass

            def initial_test_suite_analysis(self):
                pass

            def generate_tests(self, max_tokens):
                return {"new_tests": ["dummy_test"]}

            def validate_test(self, test, run_tests_multiple_times):
                return "dummy_result"

            def run_coverage(self):
                self.current_coverage = 0.9

            def run_mutations(self):
                self.mutation_called = True
        dummy_gen = DummyTestGen()
        agent.test_gen = dummy_gen
        dummy_db = MagicMock()
        agent.test_db = dummy_db

        # Patch wandb functions in the CoverAgent module.
        with patch("cover_agent.CoverAgent.wandb") as mock_wandb:
            agent.run()
            mock_wandb.login.assert_called_once_with(key="dummy_key")
            mock_wandb.init.assert_called()  # We check that init is called with project "cover-agent"
            mock_wandb.finish.assert_called_once()

        # Check that run_mutations was called because mutation_testing is True.
        assert dummy_gen.mutation_called is True

        os.remove(args.source_file_path)
        os.remove(args.test_file_path)
        del os.environ["WANDB_API_KEY"]