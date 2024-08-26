# aishell.py
import os
import sys
import platform
import shutil
import signal
import termios
import json
import tty
import traceback
from prompt_toolkit import PromptSession, print_formatted_text, HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.shell import BashLexer
from llm_interface import LLMInterface
from command_executor import CommandExecutor
from context_manager import ContextManager
from user_interface import UserInterface
from terminal_controller import TerminalController

class AIShell:
    def __init__(self):
        self.llm_interface = LLMInterface()
        self.command_executor = CommandExecutor()
        self.context_manager = ContextManager()
        self.user_interface = UserInterface()
        self.terminal_controller = TerminalController()
        self.running = True
        self.ctrl_e_active = False
        self.interactive_mode = True
        self.execution_limit = None
        self.execution_count = 0
        
        self.kb = KeyBindings()
        self.setup_key_bindings()
        
        self.session = PromptSession(
            history=FileHistory(os.path.expanduser('~/.aishell_history')),
            auto_suggest=AutoSuggestFromHistory(),
            lexer=PygmentsLexer(BashLexer),
            key_bindings=self.kb
        )

        # Handle Ctrl-C globally to exit the app
        signal.signal(signal.SIGINT, self.handle_interrupt)

    def setup_key_bindings(self):
        @self.kb.add('c-e')
        def _(event):
            self.ctrl_e_active = True
            event.app.exit()

        @self.kb.add('c-c')
        def _(event):
            if self.ctrl_e_active:
                print("\nExiting Ctrl-E mode")
                self.exit_raw_mode()
                self.ctrl_e_active = False
                event.app.exit()

    def display_aishell_status(self):
        print_formatted_text(HTML('\n<bold>AIShell</bold> '), end='', flush=True)


    def run(self):
        while self.running:
            try:
                if self.ctrl_e_active:
                    self.enter_raw_mode()
                    command = self.terminal_controller.handle_ctrl_e()
                    self.exit_raw_mode()
                    print()  # Add a newline after exiting raw mode
                    self.process_ctrl_e_command(command)
                    self.ctrl_e_active = False
                else:
                    command = self.session.prompt(f"{os.getcwd()}$ ")
                    if command is not None:
                        self.execute_command(command)
            except KeyboardInterrupt:
                print("\nOperation aborted")
                self.exit_raw_mode()
                self.ctrl_e_active = False
                continue
            except EOFError:
                if self.ctrl_e_active:
                    print("\nExiting Ctrl-E mode")
                    self.exit_raw_mode()
                    self.ctrl_e_active = False
                elif not self.session.app.current_buffer.text:
                    print("\nExiting AIShell...")
                    self.running = False
                else:
                    print("\nUse Ctrl-D again to exit")
                continue
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                self.exit_raw_mode()
                self.ctrl_e_active = False

    def process_ctrl_e_command(self, command):
        if command == 'n':
            self.handle_ctrl_e_n()
        elif command == 's':
            self.handle_ctrl_e_s()
        elif command == 'a':
            self.handle_ctrl_e_a()
        elif command == 'l':
            self.handle_ctrl_e_l()
        elif command == 'i':
            self.handle_ctrl_e_i()
        elif command in ['h', '?']:
            self.print_ctrl_e_help()
        else:
            print("Invalid command - Use 'h' or '?' for help")


    def execute_command(self, command):
        if command.strip() == "exit":
            print("Exiting AIShell...")
            self.running = False
            return "", "", 0

        try:
            stdout, stderr = self.command_executor.execute(command)
            return_code = self.command_executor.last_return_code  # Assuming we add this attribute to CommandExecutor

            if stdout:
                print(stdout, end='')
            if stderr:
                print(stderr, file=sys.stderr, end='')

            self.context_manager.add_command(command, stdout, stderr)
            
            # Update the current working directory only for simple cd commands
            if command.strip().startswith("cd ") and " && " not in command and ";" not in command:
                new_dir = command.strip()[3:].strip()
                try:
                    os.chdir(os.path.expanduser(new_dir))
                except FileNotFoundError:
                    print(f"Directory not found: {new_dir}", file=sys.stderr)
                except NotADirectoryError:
                    print(f"Not a directory: {new_dir}", file=sys.stderr)

            # Update the prompt with the new current working directory
            self.update_prompt()

            return stdout, stderr, return_code
        except Exception as e:
            print(f"An error occurred while executing the command: {str(e)}", file=sys.stderr)
            return "", str(e), 1

    def update_prompt(self):
        self.session.message = lambda: f"{os.getcwd()}$ "

    def exit_raw_mode(self):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.terminal_controller.old_settings)
        sys.stdout.write('\r\n')  # Add carriage return and newline
        sys.stdout.flush()

    def handle_ctrl_e_s(self):
        self.command_executor.stop_current_command()
        self.interactive_mode = True
        self.execution_count = 0
        print("Execution stopped and switched to interactive mode.")

    def handle_ctrl_e_a(self):
        # Restore terminal settings for normal input
        self.exit_raw_mode()
        question = input("Enter question: ")
        context = self.context_manager.get_context(for_question=True)
        answer = self.llm_interface.answer_question(question, context)
        print(f"Answer: {answer}")

    def handle_ctrl_e_l(self):
        # Restore terminal settings for normal input
        self.exit_raw_mode()
        try:
            new_limit = int(input("Enter new execution limit (0 for unlimited): "))
            self.execution_limit = None if new_limit == 0 else new_limit
            self.execution_count = 0
            print(f"Execution limit set to {'unlimited' if self.execution_limit is None else self.execution_limit}")
        except ValueError:
            print("Invalid input. Please enter a number.")

    def handle_ctrl_e_i(self):
        self.interactive_mode = not self.interactive_mode
        self.execution_count = 0
        print(f"Interactive mode {'enabled' if self.interactive_mode else 'disabled'}.")

    def print_ctrl_e_help(self):
        help_text = (
            "Ctrl-E Commands:\n"
            "n: Provide a new instruction\n"
            "s: Stop executing (LLM goes passive)\n"
            "a: Ask a question (using terminal buffer as context)\n"
            "l: Set a limit (max number of actions without confirmation)\n"
            "i: Toggle interactive mode\n"
            "h or ?: Display this help message\n\n"
            "Press Enter or any other key to exit Ctrl-E mode\n"
        )
        print(help_text)

    def enter_raw_mode(self):
        tty.setraw(sys.stdin.fileno())


    def handle_ctrl_e_n(self):
        self.exit_raw_mode()
        print()  # Add a newline after exiting raw mode
        instruction = input("Enter instruction: ")
        self.process_instruction(instruction)


    def get_system_info(self):
        system_info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
        }

        # Check for common software
        for software in ["docker", "docker-compose", "brew"]:
            system_info[f"{software}_installed"] = shutil.which(software) is not None

        # If on macOS, check for Docker Desktop
        if system_info["os"] == "Darwin":
            try:
                result = subprocess.run(["pgrep", "-f", "Docker.app"], capture_output=True, text=True)
                system_info["docker_desktop_running"] = result.returncode == 0
            except:
                system_info["docker_desktop_running"] = False

        return system_info

    def process_instruction(self, instruction):
        # Get system information
        system_info = self.get_system_info()
        
        # Add system information to the context
        system_info_str = "System Information:\n" + "\n".join([f"{k}: {v}" for k, v in system_info.items()])
        context = self.context_manager.get_context()
        context.append({"role": "system", "content": system_info_str})

        continue_execution = True
        
        while continue_execution and self.running:
            try:
                bash_command, error = self.llm_interface.generate_command(
                    instruction, 
                    context, 
                    self.interactive_mode, 
                    self.execution_limit - self.execution_count if self.execution_limit else "unlimited",
                    self.execution_limit or "unlimited"
                )
                
                if error:
                    print(f"Error generating command: {error}")
                    return

                if bash_command:
                    try:
                        command_data = json.loads(bash_command)
                        bash_command = command_data.get('bash')
                        if not bash_command:
                            print("Error: 'bash' key not found in command data")
                            return
                        continue_execution = command_data.get('continue', False)
                    except json.JSONDecodeError:
                        print(f"Error parsing command JSON: {bash_command}")
                        return

                    if self.interactive_mode:
                        print(f"Generated command: {bash_command}")
                        if not self.user_interface.confirm_execution():
                            print("Command execution cancelled.")
                            return
                    else:
                        self.print_green(f"Executing: {bash_command}")

                    if self.execution_limit is None or self.execution_count < self.execution_limit:
                        stdout, stderr, return_code = self.execute_command(bash_command)
                        if not self.running:
                            return  # Exit if the 'exit' command was executed
                        self.execution_count += 1
                        
                        if return_code != 0:
                            print(f"Command failed with return code {return_code}")
                            print(f"stdout: {stdout}")
                            print(f"stderr: {stderr}")
                            
                            # Provide feedback to the LLM and ask for correction
                            correction_instruction = f"The previous command '{bash_command}' failed with return code {return_code}. stdout: {stdout}, stderr: {stderr}. Please provide a corrected command or explain why it failed and suggest an alternative approach."
                            context.append({"role": "user", "content": correction_instruction})
                            continue_execution = True
                            continue
                        
                        # Update context with the latest command and its output
                        context = self.context_manager.get_context()
                        
                        if bash_command.startswith("echo ") and "reason to stop" in bash_command:
                            print(f"\nAI Assistant stopped execution: {stdout.strip()}")
                            return
                    else:
                        print("Execution limit reached. Use 'Ctrl-E l' to set a new limit.")
                        return
                else:
                    print("Failed to generate a valid command.")
                    return

            except Exception as e:
                print(f"An error occurred: {str(e)}")
                print("Traceback:")
                traceback.print_exc()
                return

    def print_green(self, text):
        style = Style.from_dict({
            'green': '#00ff00 bold',
        })
        print_formatted_text(FormattedText([('class:green', text)]), style=style)


    def handle_interrupt(self, signum, frame):
        if self.ctrl_e_active:
            print("\nExiting Ctrl-E mode")
            self.exit_raw_mode()  # Restore terminal settings
            self.ctrl_e_active = False
        else:
            print("\nInterrupt received, exiting AIShell...")
            self.exit_raw_mode()  # Ensure raw mode is off
            self.running = False
            sys.exit(0)

def main():
    aishell = AIShell()
    aishell.run()

if __name__ == "__main__":
    main()
