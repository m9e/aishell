# AIShell

AIShell is an interactive AI-powered shell that allows users to execute commands, generate new commands based on natural language instructions, and query the context of their session.

## Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/yourusername/aishell.git
   cd aishell
   ```

2. Set up a virtual environment:

   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install dependencies:

   ```sh
   pip install -r requirements.txt
   ```

4. Set up your environment variables:
   - `AZURE_OPENAI_API_KEY`
   - `AZURE_OPENAI_ENDPOINT`
   - `AZURE_OPENAI_DEPLOYMENT_NAME`

   OR for standard OpenAI:

   - `OPENAI_API_KEY`
   - `OPENAI_API_BASE` (optional, if using a different base URL)

## Usage

Run AIShell:

### Key Commands

- `Ctrl-E n`: Enter a new instruction for the AI to generate and execute commands.
- `Ctrl-E a`: Ask a question about the current context or previous commands.
- `Ctrl-E i`: Toggle interactive mode.
- `Ctrl-E d`: Toggle debug mode.
- `Ctrl-E s`: Stop executing (AI goes passive).
- `Ctrl-E l`: Set execution limit.
- `Ctrl-E h` or `Ctrl-E ?`: Display help message.

## Features

1. AI-powered command generation based on natural language instructions.
2. Context-aware responses to user questions.
3. Interactive and non-interactive modes.
4. Debug mode for viewing AI-system communication.
5. Execution limits for safety.
6. Integration with Azure OpenAI for language model capabilities.

## Components

1. **AIShell Class** (aishell.py):
   - Initializes various components like LLMInterface, CommandExecutor, ContextManager, UserInterface, and TerminalController.
   - Manages the main loop where user commands are read and processed.
   - Handles special key bindings and executes commands.

2. **CommandExecutor Class** (command_executor.py):
   - Executes shell commands.
   - Tracks the currently running process.
   - Provides methods to stop the current command execution.

3. **ContextManager Class** (context_manager.py):
   - Manages the context of the shell session by maintaining a history of commands and their outputs.
   - Prunes older context to keep the context size within a specified limit.

4. **LLMInterface Class** (llm_interface.py):
   - Interacts with an AI language model (such as Azure OpenAI) to generate shell commands based on user instructions.
   - Can answer user questions using the context from the shell session.
   - Calls the language model service and handles retries and error conditions.

5. **TerminalController Class** (terminal_controller.py):
   - Provides methods for handling terminal inputs, especially in raw mode.
   - Manages terminal settings and handles keystrokes for Ctrl-E commands.

6. **UserInterface Class** (user_interface.py):
   - Defines methods for interacting with the user, such as getting instructions, displaying commands, and confirming execution.

7. **LLMPrompts Class** (llm_prompts.py):
   - Contains predefined prompts to guide the language model in generating appropriate commands and answering questions.

## Risks and Cautions

1. **Command Execution**: AIShell can execute system commands. Be extremely careful when running it with elevated privileges or on production systems. The AI may generate and execute commands that could potentially harm your system or data.

2. **Data Privacy**: The system sends context to the AI service. Ensure no sensitive information is inadvertently shared. Be aware of what information is in your shell history and current working directory.

3. **AI Limitations**: The AI may generate incorrect or harmful commands. Always review commands before execution, especially in non-interactive mode. The AI's understanding of context and system state is limited to what it has been provided.

4. **Resource Usage**: Continuous use may result in high API usage and associated costs. Monitor your usage of the Azure OpenAI service.

5. **Security**: Ensure proper access controls and do not expose AIShell to untrusted users or networks. The tool could be exploited to gain unauthorized access or execute malicious commands.

6. **Compliance**: Using AIShell may have implications for regulatory compliance in certain industries or jurisdictions. Ensure usage complies with relevant data protection and privacy regulations.

7. **Dependency Risks**: AIShell relies on external services and libraries. Ensure all dependencies are kept up-to-date and be aware of any security implications they may introduce.

8. **Unintended Consequences**: The AI may misinterpret instructions or generate commands with unintended side effects. Always double-check the generated commands and their potential impacts.

## Best Practices

1. Always use AIShell in a controlled environment, preferably isolated from critical systems.
2. Regularly review and clear the context to prevent sensitive information buildup.
3. Use the interactive mode and carefully review each command before execution.
4. Set appropriate execution limits to prevent runaway processes.
5. Regularly audit the commands executed through AIShell for security and compliance purposes.

## Contributing

I dare you!

## License

AIShell is distributed under the Apache License 2.0. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0. See the License for the specific language governing permissions and limitations under the License.

## Disclaimer

AIShell is a powerful tool that combines AI with system command execution. It is provided "as is" without warranty of any kind. The developers are not responsible for any damage or data loss that may occur from its use. Use at your own risk and always exercise caution.