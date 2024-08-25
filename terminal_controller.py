import os
import sys
import termios
import tty
import select
import subprocess

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

    def handle_ctrl_e(self):
        sys.stdout.write("\nInstruction? (n/s/a/l/i): ")
        sys.stdout.flush()
        char = self.getch()
        sys.stdout.write(char.decode('utf-8') + '\n')
        sys.stdout.flush()
        return char.decode('utf-8')

    def get_input(self, prompt):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
        try:
            return input(prompt)
        finally:
            tty.setraw(sys.stdin.fileno())

    def execute_command(self, command):
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout_data = []
        stderr_data = []

        while True:
            reads = [process.stdout.fileno(), process.stderr.fileno()]
            ret = select.select(reads, [], [])

            for fd in ret[0]:
                if fd == process.stdout.fileno():
                    data = process.stdout.read(1)
                    if data:
                        sys.stdout.write(data)
                        sys.stdout.flush()
                        stdout_data.append(data)
                if fd == process.stderr.fileno():
                    data = process.stderr.read(1)
                    if data:
                        sys.stderr.write(data)
                        sys.stderr.flush()
                        stderr_data.append(data)

            if process.poll() is not None:
                break

        stdout = ''.join(stdout_data)
        stderr = ''.join(stderr_data)

        return stdout, stderr

    def capture_output(self, command):
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        return stdout, stderr