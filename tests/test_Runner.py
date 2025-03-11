import pytest
from unittest.mock import patch
from cover_agent.Runner import Runner  # Adjust the import path as necessary
import sys
import time


class TestRunner:
    def test_run_command_success(self):
        """Test the run_command method with a command that succeeds."""
        command = 'echo "Hello, World!"'
        stdout, stderr, exit_code, _ = Runner.run_command(command)
        assert stdout.strip() == "Hello, World!"
        assert stderr == ""
        assert exit_code == 0

    def test_run_command_with_cwd(self):
        """Test the run_command method with a specified working directory."""
        command = 'echo "Working Directory"'
        stdout, stderr, exit_code, _ = Runner.run_command(command, cwd="/tmp")
        assert stdout.strip() == "Working Directory"
        assert stderr == ""
        assert exit_code == 0

    def test_run_command_failure(self):
        """Test the run_command method with a command that fails."""
        # Use a command that is guaranteed to fail
        command = "command_that_does_not_exist"
        stdout, stderr, exit_code, _ = Runner.run_command(command)
        assert stdout == ""
        assert (
            "command_that_does_not_exist: not found" in stderr
            or "command_that_does_not_exist: command not found" in stderr
        )
        assert exit_code != 0
    
    def test_run_command_empty(self):
        """Test running an empty command; expecting no output and a success exit code."""
        command = ""
        stdout, stderr, exit_code, command_start_time = Runner.run_command(command)
        # Expecting that an empty command returns no output and succeeds.
        assert stdout.strip() == ""
        assert stderr.strip() == ""
        assert exit_code == 0
        # Verify that command_start_time is a reasonable positive integer (timestamp in ms)
        assert isinstance(command_start_time, int) and command_start_time > 0

    def test_run_command_stdout_stderr(self):
        """Test a command that outputs to both stdout and stderr using a Python snippet."""
        # Build a Python command that writes to stdout and stderr.
        command = f'{sys.executable} -c "import sys; sys.stdout.write(\'STDOUT_CONTENT\'); sys.stderr.write(\'STDERR_CONTENT\')"'
        stdout, stderr, exit_code, _ = Runner.run_command(command)
        assert stdout.strip() == "STDOUT_CONTENT"
        assert stderr.strip() == "STDERR_CONTENT"
        assert exit_code == 0

    def test_run_command_invalid_cwd(self):
        """Test that running a command with an invalid working directory raises an error."""
        command = 'echo "This should fail due to cwd"'
        with pytest.raises(FileNotFoundError):
            Runner.run_command(command, cwd="/this/directory/does/not/exist")

    def test_run_command_timing(self):
        """Test that the command_start_time is set correctly before the command execution."""
        command = 'echo "Timing Test"'
        before_call = int(round(time.time() * 1000))
        _, _, exit_code, command_start_time = Runner.run_command(command)
        after_call = int(round(time.time() * 1000))
        # command_start_time should be between the time before and after the call.
        assert before_call <= command_start_time <= after_call
        assert exit_code == 0

    def test_run_command_non_string(self):
        """Test running a command that is not a string, expecting a TypeError."""
        with pytest.raises(TypeError):
            Runner.run_command(123)

    def test_run_command_unicode(self):
        """Test running a command with Unicode characters."""
        command = 'echo "こんにちは世界"'
        stdout, stderr, exit_code, _ = Runner.run_command(command)
        assert "こんにちは世界" in stdout
        assert stderr == ""
        assert exit_code == 0

    def test_run_command_large_output(self):
        """Test running a command that generates a large output."""
        command = f'{sys.executable} -c "print(\'A\' * 10000)"'
        stdout, stderr, exit_code, _ = Runner.run_command(command)
        assert stdout.strip() == 'A' * 10000
        assert stderr == ""
        assert exit_code == 0

    def test_run_command_custom_exit(self):
        """Test running a command that sets a custom exit code."""
        command = f'{sys.executable} -c "import sys; sys.exit(42)"'
        stdout, stderr, exit_code, _ = Runner.run_command(command)
        assert exit_code == 42

    def test_run_command_chained_commands(self):
        """Test running a chained command that outputs to both stdout and stderr in sequence."""
        command = 'echo "First Line" && echo "Second Line" >&2'
        stdout, stderr, exit_code, _ = Runner.run_command(command)
        assert "First Line" in stdout
        assert "Second Line" in stderr
        assert exit_code == 0
    def test_run_command_quotes(self):
        """Test running a command with embedded quotes to ensure proper handling of inner quotes."""
        # Using escaped quotes inside the command.
        command = 'echo "This is a test with quotes: \\"inner quote\\" and more text"'
        stdout, stderr, exit_code, _ = Runner.run_command(command)
        expected = 'This is a test with quotes: "inner quote" and more text'
        assert stdout.strip() == expected
        assert stderr == ""
        assert exit_code == 0

    def test_run_command_multiple_lines(self):
        """Test running a command that outputs multiple lines."""
        command = f'{sys.executable} -c "for i in range(3): print(f\'Line {{i}}\')"'
        stdout, stderr, exit_code, _ = Runner.run_command(command)
        expected_output = "Line 0\nLine 1\nLine 2"
        # Remove any trailing newline for comparison.
        assert stdout.strip() == expected_output
        assert stderr.strip() == ""
        assert exit_code == 0

    def test_run_command_stderr_only(self):
        """Test running a command that outputs only to stderr."""
        command = f'{sys.executable} -c "import sys; sys.stderr.write(\'Error only\\n\')"'
        stdout, stderr, exit_code, _ = Runner.run_command(command)
        assert stdout.strip() == ""
        assert stderr.strip() == "Error only"
        assert exit_code == 0

    def test_run_command_sleep_long(self):
        """Test running a command that sleeps before producing output to verify delay relative to command_start_time."""
        command = f'{sys.executable} -c "import time; time.sleep(1); print(\'Slept\')"'
        before_call = int(round(time.time() * 1000))
        stdout, stderr, exit_code, command_start_time = Runner.run_command(command)
        after_call = int(round(time.time() * 1000))
        # Check that the actual running time (from command_start_time) is at least around 900 ms.
        assert (after_call - command_start_time) >= 900  # Allow some margin for scheduling delays.
        assert stdout.strip() == "Slept"
        assert stderr.strip() == ""
        assert exit_code == 0