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

class AIShell:
    def __init__(self):
        self.llm_interface = LLMInterface()
        self.command_executor = CommandExecutor()
        self.context_manager = ContextManager()
        self.user_interface = UserInterface()
        self.running = True
        self.ctrl_i_active = False
        
        self.kb = KeyBindings()
        self.setup_key_bindings()
        
        self.session = PromptSession(
            history=FileHistory(os.path.expanduser('~/.aishell_history')),
            auto_suggest=AutoSuggestFromHistory(),
            lexer=PygmentsLexer(BashLexer),
            key_bindings=self.kb
        )

    def setup_key_bindings(self):
        @self.kb.add('c-i')
        def _(event):
            self.ctrl_i_active = True
            event.app.exit()

    def display_aishell_status(self):
        print_formatted_text(HTML('\n<bold>AIShell</bold> '), end='', flush=True)

    def process_ctrl_i_command(self, command):
        if command == 'n':
            self.handle_ctrl_i_n()
        elif command == 's':
            self.handle_ctrl_i_s()
        elif command == 'a':
            self.handle_ctrl_i_a()
        elif command == 'l':
            self.handle_ctrl_i_l()
        elif command == 'i':
            self.handle_ctrl_i_i()
        elif command in ['h', '?']:
            self.print_ctrl_i_help()
        elif command in ['q', 'exit']:
            self.ctrl_i_active = False
            print("Exiting Ctrl-I mode")
        else:
            print("Invalid command - Ctrl-I ? for help")

    def run(self):
        while self.running:
            try:
                if self.ctrl_i_active:
                    self.display_aishell_status()
                    command = self.session.prompt("Ctrl-I> ")
                    self.process_ctrl_i_command(command.strip())
                else:
                    command = self.session.prompt(f"{os.getcwd()}$ ")
                    if command is not None:
                        self.execute_command(command)
            except KeyboardInterrupt:
                print("\nOperation aborted")
                self.ctrl_i_active = False
                continue
            except EOFError:
                print("\nExiting AIShell...")
                self.running = False
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                self.ctrl_i_active = False

    def execute_command(self, command):
        if command.strip() == "exit":
            print("Exiting AIShell...")
            self.running = False
            return

        if command.strip().startswith("llm"):
            instruction = command.strip()[4:]
            llm_response = self.llm_interface.generate_command(instruction)
            try:
                command_dict = json.loads(llm_response)
                bash_command = command_dict["bash"]
                print(f"Generated command: {bash_command}")
                if self.session.prompt("Execute command? (y/n): ").lower() == 'y':
                    self.command_executor.execute(bash_command)
            except json.JSONDecodeError:
                print("Error: Invalid response from LLM")
        else:
            self.command_executor.execute(command)

    def handle_ctrl_i_n(self):
        instruction = self.session.prompt("Enter instruction: ")
        llm_response = self.llm_interface.generate_command(instruction)
        try:
            command_dict = json.loads(llm_response)
            bash_command = command_dict["bash"]
            print(f"Generated command: {bash_command}")
            if self.session.prompt("Execute command? (y/n): ").lower() == 'y':
                self.command_executor.execute(bash_command)
        except json.JSONDecodeError:
            print("Error: Invalid response from LLM")

    def handle_ctrl_i_s(self):
        self.command_executor.stop_current_command()
        print("Execution stopped.")

    def handle_ctrl_i_a(self):
        question = self.session.prompt("Enter question: ")
        context = self.context_manager.get_context()
        answer = self.llm_interface.answer_question(question, context)
        print(f"Answer: {answer}")

    def handle_ctrl_i_l(self):
        try:
            new_limit = int(self.session.prompt("Enter new execution limit: "))
            self.command_executor.set_limit(new_limit)
            print(f"Execution limit set to {new_limit}")
        except ValueError:
            print("Invalid input. Please enter a number.")

    def handle_ctrl_i_i(self):
        self.user_interface.toggle_interactive_mode()

    def print_ctrl_i_help(self):
        help_text = """
        Ctrl-I Commands:
        n: Provide a new instruction
        s: Stop executing (LLM goes passive)
        a: Ask a question (using terminal buffer as context)
        l: Set a limit (max number of actions without confirmation)
        i: Toggle interactive mode
        h or ?: Display this help message
        q or exit: Exit Ctrl-I mode
        """
        print(help_text)

def main():
    aishell = AIShell()
    aishell.run()

if __name__ == "__main__":
    main()