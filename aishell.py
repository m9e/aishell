import os
import sys
import subprocess
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.shell import BashLexer

from llm_interface import LLMInterface
from command_executor import CommandExecutor
from context_manager import ContextManager

class AIShell:
    def __init__(self):
        self.llm_interface = LLMInterface()
        self.command_executor = CommandExecutor()
        self.context_manager = ContextManager()
        self.running = True
        self.session = PromptSession(
            history=FileHistory(os.path.expanduser('~/.aishell_history')),
            auto_suggest=AutoSuggestFromHistory(),
            lexer=PygmentsLexer(BashLexer)
        )

    def run(self):
        while self.running:
            try:
                command = self.session.prompt(f"{os.getcwd()}$ ")
                self.execute_command(command)
            except KeyboardInterrupt:
                continue
            except EOFError:
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
            print(f"Generated command: {llm_response}")
            if input("Execute command? (y/n): ").lower() == 'y':
                self.run_shell_command(llm_response)
        else:
            self.run_shell_command(command)

    def run_shell_command(self, command):
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            
            for line in process.stderr:
                print(line.strip(), file=sys.stderr)

            return_code = process.poll()
            if return_code:
                print(f"Command exited with return code {return_code}", file=sys.stderr)
        except Exception as e:
            print(f"Error executing command: {e}", file=sys.stderr)

def main():
    aishell = AIShell()
    aishell.run()

if __name__ == "__main__":
    main()