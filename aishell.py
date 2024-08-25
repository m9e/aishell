import os
import json
from prompt_toolkit import PromptSession, print_formatted_text, HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.input.defaults import create_input
from prompt_toolkit.output.defaults import create_output
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
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
        self.ctrl_d_pressed = False
        
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
            self.display_aishell_status()

        @self.kb.add('escape', filter=Condition(lambda: self.ctrl_i_active))
        def _(event):
            self.ctrl_i_active = False
            event.app.exit()

        @self.kb.add('c-d', filter=Condition(lambda: self.ctrl_i_active))
        def _(event):
            if self.ctrl_d_pressed:
                self.running = False
                event.app.exit()
            else:
                self.ctrl_d_pressed = True
                print_formatted_text(HTML('<i>Press Ctrl-D again to exit AIShell</i>'))

        @self.kb.add('n', filter=Condition(lambda: self.ctrl_i_active))
        @self.kb.add('s', filter=Condition(lambda: self.ctrl_i_active))
        @self.kb.add('a', filter=Condition(lambda: self.ctrl_i_active))
        @self.kb.add('l', filter=Condition(lambda: self.ctrl_i_active))
        @self.kb.add('i', filter=Condition(lambda: self.ctrl_i_active))
        @self.kb.add('h', filter=Condition(lambda: self.ctrl_i_active))
        @self.kb.add('?', filter=Condition(lambda: self.ctrl_i_active))
        def handle_ctrl_i_command(event):
            self.ctrl_i_active = False
            command = event.key_sequence[-1].key
            run_in_terminal(lambda: self.process_ctrl_i_command(command))

    def display_aishell_status(self):
        print_formatted_text(HTML('\n<bold>AIShell</bold>'))

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

    def run(self):
        while self.running:
            try:
                command = self.session.prompt(f"{os.getcwd()}$ ")
                self.execute_command(command)
            except KeyboardInterrupt:
                continue
            except EOFError:
                if self.ctrl_i_active:
                    self.ctrl_i_active = False
                    continue
                print("Exiting AIShell...")
                self.running = False

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
                if self.user_interface.confirm_execution():
                    self.command_executor.execute(bash_command)
            except json.JSONDecodeError:
                print("Error: Invalid response from LLM")
        else:
            self.command_executor.execute(command)

    def handle_ctrl_i_n(self):
        instruction = self.user_interface.get_instruction()
        llm_response = self.llm_interface.generate_command(instruction)
        try:
            command_dict = json.loads(llm_response)
            bash_command = command_dict["bash"]
            self.user_interface.display_command(bash_command)
            if self.user_interface.confirm_execution():
                self.command_executor.execute(bash_command)
        except json.JSONDecodeError:
            print("Error: Invalid response from LLM")

    def handle_ctrl_i_s(self):
        self.command_executor.stop_current_command()
        print("Execution stopped.")

    def handle_ctrl_i_a(self):
        question = self.user_interface.get_question()
        context = self.context_manager.get_context()
        answer = self.llm_interface.answer_question(question, context)
        self.user_interface.display_answer(answer)

    def handle_ctrl_i_l(self):
        new_limit = self.user_interface.get_limit()
        self.command_executor.set_limit(new_limit)
        print(f"Execution limit set to {new_limit}")

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
        """
        print(help_text)

def main():
    aishell = AIShell()
    aishell.run()

if __name__ == "__main__":
    main()