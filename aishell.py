# aishell.py
import os
import getpass
import socket
import glob
import stat
import sys
import platform
import shutil
import signal
import termios
import json
import html
import tty
import traceback
from prompt_toolkit import PromptSession, print_formatted_text, HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.completion import Completer, Completion, PathCompleter, CompleteEvent
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style
from pygments.lexers.shell import BashLexer
from llm_interface import LLMInterface
from command_executor import CommandExecutor
from context_manager import ContextManager
from user_interface import UserInterface
from terminal_controller import TerminalController

class BashLikeCompleter(Completer):
    def __init__(self):
        self.path_completer = PathCompleter(expanduser=True)
    
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text.startswith('./'):
            # Complete only executable files
            path = text[2:]
            dirname = os.path.dirname(path) or '.'
            basename = os.path.basename(path)
            matches = glob.glob(os.path.join(dirname, basename) + '*')
            for match in matches:
                if os.path.isfile(match) and os.access(match, os.X_OK):
                    yield Completion(match[len(path):], start_position=0)
        else:
            # General path completion
            yield from self.path_completer.get_completions(document, complete_event)


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
        self.debug_mode = False
        self.interrupt_counter = 0
        self.version = 0.1
        self.last_dir = None

        self.last_dir = os.getcwd()
        self.kb = KeyBindings()
        self.setup_key_bindings()
        
        self.session = PromptSession(
            history=FileHistory(os.path.expanduser('~/.aishell_history')),
            auto_suggest=AutoSuggestFromHistory(),
            lexer=PygmentsLexer(BashLexer),
            key_bindings=self.kb,
            completer=BashLikeCompleter()
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

        @self.kb.add('tab')
        def _(event):
            buff = event.current_buffer
            completer = buff.completer
            document = buff.document

            completions = list(completer.get_completions(document, complete_event=CompleteEvent()))
            if len(completions) == 1:
                buff.insert_text(completions[0].text)
            elif len(completions) > 1:
                if event.is_repeat:
                    # Second Tab press, list all completions
                    print()
                    for c in completions:
                        print(c.text)
                    buff.start_completion(select_first=False)
                else:
                    buff.start_completion(select_first=False)
            else:
                buff.insert_text('\t')

        @self.kb.add('c-d')  # Custom handling for Ctrl-D
        def _(event):
            buffer = event.current_buffer
            if buffer.text:  # If there's text, clear the buffer
                buffer.text = ''
                buffer.cursor_position = 0
            else:  # If no text, treat as EOF
                self.interrupt_counter += 1
                if self.interrupt_counter >= 3:
                    print("\nExiting AIShell...")
                    self.running = False
                    event.app.exit()
                else:
                    print("\nInterrupt received. Press Ctrl-D {} more time(s) to exit.".format(3 - self.interrupt_counter))


    def display_aishell_status(self):
        print_formatted_text(HTML('\n<bold>AIShell</bold> '), end='', flush=True)

        
    def toggle_debug_mode(self):
        self.debug_mode = not self.debug_mode
        print(f"Debug mode {'enabled' if self.debug_mode else 'disabled'}.")
        # Re-instantiate LLMInterface with the new debug mode
        self.llm_interface = LLMInterface(debug_mode=self.debug_mode)

    def print_debug(self, message):
        if self.debug_mode:
            style = Style.from_dict({
                'debug': '#FFFF00 bold',
            })
            escaped_message = html.escape(str(message))
            print_formatted_text(HTML(f"<debug>{escaped_message}</debug>"), style=style)

    def get_prompt(self):
        user = getpass.getuser()
        host = socket.gethostname()
        cwd = os.getcwd()
        version_str = f"aishell-{self.version:.1f}"  # Format the version as a float with one decimal place
        return f"{version_str} {user}@{host}:{cwd}$ "

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
                    print("\nwe should be clearing this but we won't because we suck")
                    self.session.app.current_buffer.text = ''
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
        elif command == 'd':
            self.toggle_debug_mode()
        elif command in ['h', '?']:
            self.print_ctrl_e_help()
        else:
            print("Invalid command - Use 'h' or '?' for help")


    def execute_command(self, command, from_llm=False):
        if command.strip() == "exit":
            print("Exiting AIShell...")
            self.running = False
            return "", "", 0

        self.interrupt_counter = 0

        try:
            stdout, stderr = self.command_executor.execute(command)
            return_code = self.command_executor.last_return_code  # Assuming we add this attribute to CommandExecutor

            if stdout:
                print(stdout, end='')
            if stderr:
                print(stderr, file=sys.stderr, end='')

            self.context_manager.add_command(command, stdout, stderr, from_llm=from_llm)
            
            # Update the current working directory only for simple cd commands
            if command.strip().startswith("cd ") and " && " not in command and ";" not in command:
                new_dir = command.strip()[3:].strip()
                try:
                    if new_dir == "-":
                        new_dir = self.last_dir
                    self.last_dir = os.getcwd()
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
            "i: Toggle interactive mode (commands with sudo ALWAYS require confirmation)\n"
            "d: Toggle debug mode\n"
            "h or ?: Display this help message\n\n"
            "Press Enter or any other key to exit Ctrl-E mode\n"
        )
        print(help_text)

    def enter_raw_mode(self):
        tty.setraw(sys.stdin.fileno())


    def handle_ctrl_e_n(self):
        self.exit_raw_mode()
        print()  # Add a newline after exiting raw mode
        instruction = input("Enter instruction: ").strip()  # Strip any surrounding whitespace

        if not instruction:  # If the instruction is empty after trimming
            print("No instruction provided. Returning to interactive shell.")
            return  # Do nothing, just return to the interactive shell

        self.process_instruction(instruction)


    def get_system_info(self):
        system_info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
        }

        return system_info

    def process_instruction(self, instruction):
        system_info = self.get_system_info()
        system_info_str = "System Information:\n" + "\n".join([f"{k}: {v}" for k, v in system_info.items()])
        context = self.context_manager.get_context()

        continue_execution = True
        
        while continue_execution and self.running:
            try:
                self.print_debug(f"Sending instruction to LLM: {instruction}")
                self.print_debug(f"Context: {json.dumps(context, indent=2)}")

                bash_command, error = self.llm_interface.generate_command(
                    instruction=instruction, 
                    context=context, 
                    interactive_mode=self.interactive_mode, 
                    remaining_commands=self.execution_limit - self.execution_count if self.execution_limit else "unlimited",
                    limit=self.execution_limit or "unlimited",
                    system_info=system_info_str
                )
                
                if error:
                    print(f"Error generating command: {error}")
                    return

                if bash_command:
                    self.print_debug(f"Received response from LLM: {bash_command}")
                    try:
                        command_data = json.loads(bash_command)
                        if 'savecontext' in command_data:
                            print(f"AI Assistant note: {command_data['savecontext']}")
                            context.append({"role": "assistant", "content": command_data['savecontext']})
                            continue
                        bash_command = command_data.get('bash')
                        if not bash_command:
                            print("Error: 'bash' key not found in command data")
                            return
                        continue_execution = command_data.get('continue', False)
                    except json.JSONDecodeError:
                        print(f"Error parsing command JSON: {bash_command}")
                        return

                    if self.interactive_mode or bash_command.startswith('sudo') or 'sudo ' in bash_command:
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
                            
                            correction_instruction = f"Automated interpreter message: The previous command '{bash_command}' failed with return code {return_code}. stdout: {stdout}, stderr: {stderr}. Please provide a corrected command or explain why it failed and suggest an alternative approach (with an echo)"
                            context.append({"role": "user", "content": correction_instruction})
                            continue_execution = True
                            continue
                        
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
        # Check if there is a running command
        if self.current_process:
            # Stop the running command (call to stop_current_command from CommandExecutor)
            print("\nCommand interrupted")
            self.command_executor.stop_current_command()
            self.current_process = None
            self.interrupt_counter = 0  # Reset the counter after successfully interrupting a command
        else:
            # No active command, count the Ctrl-C presses
            self.interrupt_counter += 1
            if self.interrupt_counter >= 3:
                print("\nMultiple interrupts received, exiting AIShell...")
                self.running = False
                sys.exit(0)
            else:
                print("\nInterrupt received. Press Ctrl+C {} more time(s) to exit.".format(3 - self.interrupt_counter))


def main():
    aishell = AIShell()
    aishell.run()

if __name__ == "__main__":
    main()
