# command_executor.py
import subprocess
import threading
import signal
import sys

class CommandExecutor:
    def __init__(self):
        self.current_process = None

    def execute(self, command):
        try:
            self.current_process = subprocess.Popen(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            stdout, stderr = self.current_process.communicate()

            return stdout, stderr
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e}", file=sys.stderr)
            return str(e), ""
        finally:
            self.current_process = None

    def stop_current_command(self):
        if self.current_process:
            self.current_process.send_signal(signal.SIGINT)

    def set_limit(self, limit):
        self.limit = limit
        self.execution_count = 0