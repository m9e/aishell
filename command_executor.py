import subprocess
import threading
import signal
import sys

class CommandExecutor:
    def __init__(self):
        self.limit = None
        self.execution_count = 0
        self.current_process = None

    def execute(self, command):
        if self.limit and self.execution_count >= self.limit:
            print("Execution limit reached. Use 'Ctrl-I l' to set a new limit.")
            return

        try:
            self.current_process = subprocess.Popen(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            def read_output(pipe, file):
                for line in iter(pipe.readline, ''):
                    file.write(line)
                    file.flush()

            stdout_thread = threading.Thread(target=read_output, args=(self.current_process.stdout, sys.stdout))
            stderr_thread = threading.Thread(target=read_output, args=(self.current_process.stderr, sys.stderr))

            stdout_thread.start()
            stderr_thread.start()

            self.current_process.wait()
            stdout_thread.join()
            stderr_thread.join()

            self.execution_count += 1
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e}", file=sys.stderr)
        finally:
            self.current_process = None

    def stop_current_command(self):
        if self.current_process:
            self.current_process.send_signal(signal.SIGINT)

    def set_limit(self, limit):
        self.limit = limit
        self.execution_count = 0