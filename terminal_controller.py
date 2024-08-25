import os
import sys
import termios
import tty

class TerminalController:
    def __init__(self):
        self.old_settings = termios.tcgetattr(sys.stdin)

    def __enter__(self):
        tty.setraw(sys.stdin.fileno())
        return self

    def __exit__(self, type, value, traceback):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)

    def getch(self):
        return os.read(sys.stdin.fileno(), 1)

    def handle_ctrl_i(self):
        sys.stdout.write("\nInstruction? (n/s/a/l/i): ")
        sys.stdout.flush()
        return self.getch().decode('utf-8')