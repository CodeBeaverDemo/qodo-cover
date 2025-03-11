import os
import argparse
from unittest.mock import patch, MagicMock
import pytest
from cover_agent.main import parse_args, main


class TestMain:
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
    def test_main_source_file_not_found(
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
        parse_args = lambda: args  # Mocking parse_args function
        mock_isfile.return_value = False  # Simulate source file not found

        with patch("cover_agent.main.parse_args", parse_args):
            with pytest.raises(FileNotFoundError) as exc_info:
                main()

        assert (
            str(exc_info.value) == f"Source file not found at {args.source_file_path}"
        )
        mock_unit_cover_agent.assert_not_called()
        mock_report_generator.generate_report.assert_not_called()

    @patch("cover_agent.CoverAgent.os.path.exists")
    @patch("cover_agent.CoverAgent.os.path.isfile")
    @patch("cover_agent.CoverAgent.UnitTestGenerator")
    def test_main_test_file_not_found(
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
        parse_args = lambda: args  # Mocking parse_args function
        mock_isfile.side_effect = [True, False]
        mock_exists.return_value = True

        with patch("cover_agent.main.parse_args", parse_args):
            with pytest.raises(FileNotFoundError) as exc_info:
                main()

        assert str(exc_info.value) == f"Test file not found at {args.test_file_path}"

    @patch("cover_agent.main.CoverAgent")
    def test_main_success(self, MockCoverAgent):
        """Test main function normal execution by ensuring agent.run() is called."""
        args = argparse.Namespace(
            source_file_path="test_source.py",
            test_file_path="test_file.py",
            code_coverage_report_path="coverage_report.xml",
            test_command="pytest",
            test_command_dir=os.getcwd(),
            included_files=["file1.c", "file2.c"],
            coverage_type="cobertura",
            report_filepath="test_results.html",
            desired_coverage=90,
            max_iterations=10,
            additional_instructions="Run more tests",
            model="gpt-4o",
            api_base="http://localhost:11434",
            strict_coverage=False,
            run_tests_multiple_times=1,
            use_report_coverage_feature_flag=False,
            log_db_path="",
            mutation_testing=False,
            more_mutation_logging=False,
        )
        parse_args = lambda: args
        mock_agent = MagicMock()
        MockCoverAgent.return_value = mock_agent
        with patch("cover_agent.main.parse_args", new=parse_args):
            from cover_agent.main import main
            main()
        mock_agent.run.assert_called_once()
    def test_parse_args_defaults(self):
        """Test that parse_args returns the correct default values when only the required arguments are provided."""
        import sys
        test_args = [
            "program.py",
            "--source-file-path", "src.py",
            "--test-file-path", "test.py",
            "--code-coverage-report-path", "cov.xml",
            "--test-command", "pytest",
        ]
        with patch("sys.argv", test_args):
            args = parse_args()
        assert args.source_file_path == "src.py"
        assert args.test_file_path == "test.py"
        assert args.code_coverage_report_path == "cov.xml"
        assert args.test_command == "pytest"
        assert args.test_command_dir == os.getcwd()
        assert args.included_files is None
        assert args.coverage_type == "cobertura"
        assert args.report_filepath == "test_results.html"
        assert args.desired_coverage == 90
        assert args.max_iterations == 10
        assert args.additional_instructions == ""
        assert args.model == "gpt-4o"
        assert args.api_base == "http://localhost:11434"
        assert args.strict_coverage is False
        assert args.run_tests_multiple_times == 1
        assert args.use_report_coverage_feature_flag is False
        assert args.log_db_path == ""
        assert args.mutation_testing is False
        assert args.more_mutation_logging is False

    def test_main_agent_constructor_called_arguments(self):
        pass
    def test_main_run_exception(self):
        """Test that if agent.run() raises an exception, main propagates the exception."""
        args = argparse.Namespace(
            source_file_path="src.py",
            test_file_path="test.py",
            code_coverage_report_path="cov.xml",
            test_command="pytest",
            test_command_dir=os.getcwd(),
            included_files=None,
            coverage_type="cobertura",
            report_filepath="test_results.html",
            desired_coverage=90,
            max_iterations=10,
            additional_instructions="",
            model="gpt-4o",
            api_base="http://localhost:11434",
            strict_coverage=False,
            run_tests_multiple_times=1,
            use_report_coverage_feature_flag=False,
            log_db_path="",
            mutation_testing=False,
            more_mutation_logging=False,
        )
        with patch("cover_agent.main.parse_args", return_value=args):
            with patch("cover_agent.main.CoverAgent") as MockCoverAgent:
                mock_agent = MagicMock()
                mock_agent.run.side_effect = Exception("Test Exception")
                MockCoverAgent.return_value = mock_agent
                with pytest.raises(Exception, match="Test Exception"):
                    main()
        """Test that the main function constructs CoverAgent with the expected arguments and calls run()."""
        args = argparse.Namespace(
            source_file_path="src.py",
            test_file_path="test.py",
            code_coverage_report_path="cov.xml",
            test_command="pytest",
            test_command_dir=os.getcwd(),
            included_files=["a.c"],
            coverage_type="cobertura",
            report_filepath="report.html",
            desired_coverage=95,
            max_iterations=5,
            additional_instructions="Extra",
            model="gpt-4o",
            api_base="http://localhost:11434",
            strict_coverage=True,
            run_tests_multiple_times=2,
            use_report_coverage_feature_flag=True,
            log_db_path="log.db",
            mutation_testing=True,
            more_mutation_logging=True,
        )
        with patch("cover_agent.main.parse_args", return_value=args):
            with patch("cover_agent.main.CoverAgent") as MockCoverAgent:
                mock_agent = MagicMock()
                MockCoverAgent.return_value = mock_agent
                main()
                # Verify that CoverAgent was instantiated with our args
                MockCoverAgent.assert_called_once_with(args)
                # Verify that the run method was called on the CoverAgent instance
                mock_agent.run.assert_called_once()