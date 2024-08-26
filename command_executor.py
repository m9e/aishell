import subprocess
import sys

class CommandExecutor:
    def __init__(self):
        self.current_process = None
        self.last_return_code = 0

    def execute(self, command):
        try:
            self.current_process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True
            )
            
            stdout, stderr = self.current_process.communicate()
            self.last_return_code = self.current_process.returncode

            return stdout, stderr
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e}", file=sys.stderr)
            self.last_return_code = e.returncode
            return "", str(e)
        finally:
            self.current_process = None

    def stop_current_command(self):
        if self.current_process:
            self.current_process.terminate()

    def set_limit(self, limit):
        self.limit = limit
        self.execution_count = 0