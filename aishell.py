# aishell.py
import os
import sys
import json
from prompt_toolkit import PromptSession, print_formatted_text, HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition
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

    def setup_key_bindings(self):
        @self.kb.add('c-e')
        def _(event):
            self.ctrl_e_active = True
            event.app.exit()

    def display_aishell_status(self):
        print_formatted_text(HTML('\n<bold>AIShell</bold> '), end='', flush=True)

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
            print("Invalid command - Ctrl-E ? for help")

    def run(self):
        while self.running:
            try:
                if self.ctrl_e_active:
                    self.display_aishell_status()
                    command = self.terminal_controller.handle_ctrl_e()
                    self.process_ctrl_e_command(command.strip())
                    self.ctrl_e_active = False
                else:
                    command = self.session.prompt(f"{os.getcwd()}$ ")
                    if command is not None:
                        self.execute_command(command)
            except KeyboardInterrupt:
                print("\nOperation aborted")
                self.ctrl_e_active = False
                continue
            except EOFError:
                if self.ctrl_e_active:
                    print("\nExiting Ctrl-E mode")
                    self.ctrl_e_active = False
                elif not self.session.buffer.text:
                    print("\nExiting AIShell...")
                    self.running = False
                else:
                    print("\nUse Ctrl-D again to exit")
                continue
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                self.ctrl_e_active = False

    def execute_command(self, command):
        if command.strip() == "exit":
            print("Exiting AIShell...")
            self.running = False
            return

        stdout, stderr = self.command_executor.execute(command)
        if stdout:
            print(stdout, end='')
        if stderr:
            print(stderr, file=sys.stderr, end='')
        self.context_manager.add_command(command, stdout, stderr)

    def handle_ctrl_e_n(self):
        instruction = self.terminal_controller.get_input("Enter instruction: ")
        context = self.context_manager.get_context()
        bash_command = self.llm_interface.generate_command(
            instruction, 
            context, 
            self.interactive_mode, 
            self.execution_limit - self.execution_count if self.execution_limit else "unlimited",
            self.execution_limit or "unlimited"
        )
        
        if bash_command:
            print(f"Generated command: {bash_command}")
            if self.interactive_mode:
                if self.user_interface.confirm_execution():
                    stdout, stderr = self.command_executor.execute(bash_command)
                    self.context_manager.add_command(bash_command, stdout, stderr, from_llm=True)
            else:
                if self.execution_limit is None or self.execution_count < self.execution_limit:
                    stdout, stderr = self.command_executor.execute(bash_command)
                    self.context_manager.add_command(bash_command, stdout, stderr, from_llm=True)
                    self.execution_count += 1
                else:
                    print("Execution limit reached. Use 'Ctrl-E l' to set a new limit.")

    def handle_ctrl_e_s(self):
        self.command_executor.stop_current_command()
        self.interactive_mode = True
        self.execution_count = 0
        print("Execution stopped and switched to interactive mode.")

    def handle_ctrl_e_a(self):
        question = self.terminal_controller.get_input("Enter question: ")
        context = self.context_manager.get_context(for_question=True)
        answer = self.llm_interface.answer_question(question, context)
        print(f"Answer: {answer}")

    def handle_ctrl_e_l(self):
        try:
            new_limit = int(self.terminal_controller.get_input("Enter new execution limit (0 for unlimited): "))
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
        help_text = """
        Ctrl-E Commands:
        n: Provide a new instruction
        s: Stop executing (LLM goes passive)
        a: Ask a question (using terminal buffer as context)
        l: Set a limit (max number of actions without confirmation)
        i: Toggle interactive mode
        h or ?: Display this help message
        
        Press Enter or any other key to exit Ctrl-E mode
        """
        print(help_text)

def main():
    aishell = AIShell()
    aishell.run()

if __name__ == "__main__":
    main()