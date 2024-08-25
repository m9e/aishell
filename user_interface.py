import os

class UserInterface:
    def __init__(self):
        self.interactive_mode = False

    def get_instruction(self):
        return input("Enter instruction: ")

    def get_question(self):
        return input("Enter question: ")

    def get_limit(self):
        return int(input("Enter new execution limit: "))

    def display_command(self, command):
        print(f"Generated command: {command}")

    def display_answer(self, answer):
        print(f"Answer: {answer}")

    def display_message(self, message):
        print(message)

    def toggle_interactive_mode(self):
        self.interactive_mode = not self.interactive_mode
        print(f"Interactive mode {'enabled' if self.interactive_mode else 'disabled'}.")

    def confirm_execution(self):
        return input("Execute command? (y/n): ").lower() == 'y'

    def display_prompt(self):
        print(f"{os.getcwd()}$ ", end='', flush=True)