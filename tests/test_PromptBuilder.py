import pytest
from unittest.mock import patch, mock_open
from cover_agent.PromptBuilder import PromptBuilder


class TestPromptBuilder:
    @pytest.fixture(autouse=True)
    def setup_method(self, monkeypatch):
        mock_open_obj = mock_open(read_data="dummy content")
        monkeypatch.setattr("builtins.open", mock_open_obj)
        self.mock_open_obj = mock_open_obj

    def test_initialization_reads_file_contents(self):
        builder = PromptBuilder(
            "source_path",
            "test_path",
            "dummy content",
        )
        assert builder.source_file == "dummy content"
        assert builder.test_file == "dummy content"
        assert builder.code_coverage_report == "dummy content"
        assert builder.included_files == ""  # Updated expected value

    def test_initialization_handles_file_read_errors(self, monkeypatch):
        def mock_open_raise(*args, **kwargs):
            raise IOError("File not found")

        monkeypatch.setattr("builtins.open", mock_open_raise)

        builder = PromptBuilder(
            "source_path",
            "test_path",
            "coverage_report",
        )
        assert "Error reading source_path" in builder.source_file
        assert "Error reading test_path" in builder.test_file

    def test_empty_included_files_section_not_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            included_files="Included Files Content",
        )
        # Directly read the real file content for the prompt template
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"
        builder.included_files = ""

        result = builder.build_prompt()
        assert "## Additional Includes" not in result["user"]

    def test_non_empty_included_files_section_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            included_files="Included Files Content",
        )

        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"

        result = builder.build_prompt()
        assert "## Additional Includes" in result["user"]
        assert "Included Files Content" in result["user"]

    def test_empty_additional_instructions_section_not_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            additional_instructions="",
        )
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"

        result = builder.build_prompt()
        assert "## Additional Instructions" not in result["user"]

    def test_empty_failed_test_runs_section_not_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            failed_test_runs="",
        )
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"

        result = builder.build_prompt()
        assert "## Previous Iterations Failed Tests" not in result["user"]

    def test_non_empty_additional_instructions_section_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            additional_instructions="Additional Instructions Content",
        )
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"

        result = builder.build_prompt()
        assert "## Additional Instructions" in result["user"]
        assert "Additional Instructions Content" in result["user"]

    # we currently disabled the logic to add failed test runs to the prompt
    def test_non_empty_failed_test_runs_section_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            failed_test_runs="Failed Test Runs Content",
        )
        # Directly read the real file content for the prompt template
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"

        result = builder.build_prompt()
        assert "## Previous Iterations Failed Tests" in result["user"]
        assert "Failed Test Runs Content" in result["user"]

    def test_build_prompt_custom_handles_rendering_exception(self, monkeypatch):
        def mock_render(*args, **kwargs):
            raise Exception("Rendering error")

        monkeypatch.setattr(
            "jinja2.Environment.from_string",
            lambda *args, **kwargs: type("", (), {"render": mock_render})(),
        )

        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
        )
        result = builder.build_prompt_custom("custom_file")
        assert result == {"system": "", "user": ""}

    def test_build_prompt_handles_rendering_exception(self, monkeypatch):
        def mock_render(*args, **kwargs):
            raise Exception("Rendering error")

        monkeypatch.setattr(
            "jinja2.Environment.from_string",
            lambda *args, **kwargs: type("", (), {"render": mock_render})(),
        )

        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
        )
        result = builder.build_prompt()
        assert result == {"system": "", "user": ""}

    def test_build_prompt_with_mutation_testing_success(self, monkeypatch):
        """Test build_prompt method when mutation_testing flag is True.
        Using fake settings with mutation_test_prompt templates to verify that
        the mutation testing branch renders correctly.
        """
        # Create a fake mutation_test_prompt attribute with dummy templates.
        fake_mutation = type("FakeMutation", (), {
            "system": "MT system prompt with {{ source_file }}",
            "user": "MT user prompt with {{ source_file }}"
        })
        fake_settings = type("FakeSettings", (), {
            "mutation_test_prompt": fake_mutation
        })()
        # Monkeypatch the get_settings function in the config_loader and in the module.
        monkeypatch.setattr("cover_agent.settings.config_loader.get_settings", lambda: fake_settings)
        monkeypatch.setattr("cover_agent.PromptBuilder.get_settings", lambda: fake_settings)
        
        builder = PromptBuilder("source_path", "test_path", "dummy coverage", mutation_testing=True)
        # Overwrite file contents used in the template
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        result = builder.build_prompt()
        assert "MT system prompt with Source Content" in result["system"]
        assert "MT user prompt with Source Content" in result["user"]

    def test_build_prompt_custom_success(self, monkeypatch):
        """Test build_prompt_custom method with a valid custom prompt configuration.
        Using fake settings where get('custom_key') returns a dummy prompt configuration.
        """
        fake_custom = type("FakeCustom", (), {
            "system": "Custom system prompt with {{ language }}",
            "user": "Custom user prompt with {{ language }}"
        })
        fake_settings = type("FakeSettings", (), {
            "get": lambda self, key: fake_custom
        })()
        # Monkeypatch the get_settings function similarly.
        monkeypatch.setattr("cover_agent.settings.config_loader.get_settings", lambda: fake_settings)
        monkeypatch.setattr("cover_agent.PromptBuilder.get_settings", lambda: fake_settings)
        
        builder = PromptBuilder("source_path", "test_path", "coverage content")
        builder.language = "python3"
        result = builder.build_prompt_custom("custom_key")
        assert "Custom system prompt with python3" in result["system"]
        assert "Custom user prompt with python3" in result["user"]
    def test_source_file_numbering(self, monkeypatch):
        """Test that the source_file_numbered and test_file_numbered attributes correctly number each line."""
        fake_file_content = "line1\nline2\nline3"
        from unittest.mock import mock_open
        monkeypatch.setattr("builtins.open", mock_open(read_data=fake_file_content))
        builder = PromptBuilder("dummy_source", "dummy_test", "coverage")
        expected_numbered = "1 line1\n2 line2\n3 line3"
        assert builder.source_file_numbered == expected_numbered
        assert builder.test_file_numbered == expected_numbered
    def test_build_prompt_includes_all_sections(self, monkeypatch):
        """Test that build_prompt correctly includes formatted additional sections when they are non-empty."""
        # Also monkeypatch the get_settings reference inside PromptBuilder to use fake_settings
        monkeypatch.setattr("cover_agent.PromptBuilder.get_settings", lambda: fake_settings)
        # Create fake prompt templates that display the additional sections in both system and user prompts.
        fake_prompt = type("FakePrompt", (), {
            "system": "System: {{ additional_includes_section }} | {{ additional_instructions_text }} | {{ failed_tests_section }}",
            "user": "User: {{ additional_includes_section }} | {{ additional_instructions_text }} | {{ failed_tests_section }}"
        })()
        fake_settings = type("FakeSettings", (), {
            "test_generation_prompt": fake_prompt,
        })()
        monkeypatch.setattr("cover_agent.settings.config_loader.get_settings", lambda: fake_settings)
        builder = PromptBuilder(
            "dummy_source",
            "dummy_test",
            "coverage",
            included_files="Included Files Content",
            additional_instructions="Additional Instructions Content",
            failed_test_runs="Failed Test Runs Content"
        )
        # Overwrite file content attributes to avoid dependence on file reading
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        result = builder.build_prompt()
        # Verify that the formatted sections (which include headers defined in the module-level constants)
        # are present in the output as both system and user prompts.
        assert "## Additional Includes" in result["user"]
        assert "Included Files Content" in result["user"]
        assert "## Additional Instructions" in result["user"]
        assert "Additional Instructions Content" in result["user"]
        assert "## Previous Iterations Failed Tests" in result["user"]
        assert "Failed Test Runs Content" in result["user"]
        # Also validate the system prompt
        assert "## Additional Includes" in result["system"]
        assert "Included Files Content" in result["system"]
        assert "## Additional Instructions" in result["system"]
        assert "Additional Instructions Content" in result["system"]
        assert "## Previous Iterations Failed Tests" in result["system"]
        assert "Failed Test Runs Content" in result["system"]
    def test_empty_source_file_numbering(self, monkeypatch):
        """Test that numbering works correctly when both the source and test files are empty."""
        from unittest.mock import mock_open
        empty_open = mock_open(read_data="")
        monkeypatch.setattr("builtins.open", empty_open)
        builder = PromptBuilder("dummy_source", "dummy_test", "coverage")
        # When reading an empty file, split("\n") returns [''] so numbering produces "1 " for that one empty string.
        expected_numbered = "1 "
        assert builder.source_file_numbered == expected_numbered
        assert builder.test_file_numbered == expected_numbered

    def test_file_read_error_numbering(self, monkeypatch):
        """Test that when file reading fails, the error message is included and correctly numbered."""
        # Create a function that always raises an error for file open.
        def mock_open_raise(*args, **kwargs):
            raise IOError("read error")

        monkeypatch.setattr("builtins.open", mock_open_raise)
        builder = PromptBuilder("error_source", "error_test", "coverage")
        # Check that the _read_file method returned the error message for both files.
        expected_source_error = f"Error reading error_source: read error"
        expected_test_error = f"Error reading error_test: read error"
        assert expected_source_error in builder.source_file
        assert expected_test_error in builder.test_file
        # The numbering should add a "1 " prefix to the error message (since it splits into one line)
        assert builder.source_file_numbered == f"1 {expected_source_error}"
        assert builder.test_file_numbered == f"1 {expected_test_error}"