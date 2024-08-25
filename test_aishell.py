import sys
import pytest
from unittest.mock import Mock, patch
import os
from collections import deque

# Imports (keep them as they are in your current file)
from context_manager import ContextManager
from llm_interface import LLMInterface
from command_executor import CommandExecutor
from user_interface import UserInterface

# Fixtures
@pytest.fixture
def context_manager():
    return ContextManager(max_lines=5)

@pytest.fixture
def mock_azure_client():
    with patch('llm_interface.AzureOpenAI') as mock_azure:
        mock_client = Mock()
        mock_azure.return_value = mock_client
        yield mock_client

@pytest.fixture
def llm_interface(mock_azure_client):
    return LLMInterface()

@pytest.fixture
def command_executor():
    return CommandExecutor()

@pytest.fixture
def user_interface():
    return UserInterface()

# Tests for ContextManager
def test_context_manager_add_and_get(context_manager):
    context_manager.add_line("Line 1")
    context_manager.add_line("Line 2")
    assert context_manager.get_context() == "Line 1\nLine 2"

def test_context_manager_max_lines(context_manager):
    for i in range(10):
        context_manager.add_line(f"Line {i}")
    assert len(context_manager.context) == 5
    assert context_manager.get_context().startswith("Line 5")

# Tests for LLMInterface
def test_llm_interface_generate_command(llm_interface, mock_azure_client):
    # Create a mock response that mimics the structure of the actual API response
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="echo 'Hello, World!'"))]
    mock_azure_client.chat.completions.create.return_value = mock_response
    
    command = llm_interface.generate_command("Print Hello World")
    assert command == "echo 'Hello, World!'"

def test_llm_interface_answer_question(llm_interface, mock_azure_client):
    # Create a mock response that mimics the structure of the actual API response
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Sunny"))]
    mock_azure_client.chat.completions.create.return_value = mock_response
    
    answer = llm_interface.answer_question("What's the weather?", "Context: It's a clear day.")
    assert answer == "Sunny"

def test_llm_interface_error_handling(llm_interface, mock_azure_client):
    mock_azure_client.chat.completions.create.side_effect = Exception("API Error")
    command = llm_interface.generate_command("This will fail")
    assert command is None

# Tests for CommandExecutor
@patch('subprocess.run')
def test_command_executor_execute(mock_run, command_executor):
    mock_run.return_value.stdout = "Command output"
    command_executor.execute("echo 'test'")
    mock_run.assert_called_once_with("echo 'test'", shell=True, check=True, text=True, capture_output=True)

def test_command_executor_limit(command_executor):
    command_executor.set_limit(2)
    for _ in range(3):
        with patch('subprocess.run') as mock_run:
            command_executor.execute("test")
    assert command_executor.execution_count == 2

# Tests for UserInterface
@patch('builtins.input')
@patch('builtins.print')
def test_user_interface_get_instruction(mock_print, mock_input, user_interface):
    mock_input.return_value = "list files"
    instruction = user_interface.get_instruction()
    assert instruction == "list files"

@patch('builtins.print')
def test_user_interface_display_command(mock_print, user_interface):
    user_interface.display_command("ls -la")
    mock_print.assert_called_once_with("Generated command: ls -la")

def test_user_interface_toggle_interactive_mode(user_interface):
    assert not user_interface.interactive_mode
    user_interface.toggle_interactive_mode()
    assert user_interface.interactive_mode
    user_interface.toggle_interactive_mode()
    assert not user_interface.interactive_mode

# Integration test
def test_integration_generate_and_execute():
    llm_interface = LLMInterface()
    command_executor = CommandExecutor()
    user_interface = UserInterface()

    with patch.object(llm_interface, 'generate_command', return_value="echo 'Integration Test'"):
        with patch.object(command_executor, 'execute') as mock_execute:
            instruction = "Run an integration test"
            llm_response = llm_interface.generate_command(instruction)
            user_interface.display_command(llm_response)
            command_executor.execute(llm_response)

            mock_execute.assert_called_once_with("echo 'Integration Test'")

# Environmental variable test
def test_environment_variables():
    required_vars = ['AZURE_OPENAI_API_KEY', 'AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_DEPLOYMENT_NAME']
    for var in required_vars:
        assert os.getenv(var) is not None, f"Environment variable {var} is not set"

@pytest.mark.integration
def test_real_api_call():
    llm_interface = LLMInterface()
    
    # Test generate_command
    try:
        command = llm_interface.generate_command("List all files in the current directory")
        assert command is not None
        assert isinstance(command, str)
        print(f"\nGenerated command: {command}", file=sys.stderr)
        
    except Exception as e:
        pytest.fail(f"generate_command failed with error: {str(e)}")
    
    # Test answer_question
    try:
        answer = llm_interface.answer_question("What's the capital of France?", "")
        assert answer is not None
        assert isinstance(answer, str)
        print(f"\nAnswer to 'What's the capital of France?': {answer}", file=sys.stderr)
        
    except Exception as e:
        pytest.fail(f"answer_question failed with error: {str(e)}")




if __name__ == "__main__":
    pytest.main([__file__])