import sys
import os

# Cross-platform readline support
if sys.platform == "win32":
    try:
        import pyreadline3 as readline  # Windows (PowerShell, CMD)
    except ImportError:
        print("Warning: pyreadline3 not found. Install it with 'pip install pyreadline3'")
        readline = None
else:
    import readline  # Linux/macOS


class CommandInterface:
    def __init__(self, prompt):
        self.prompt = prompt
        self.command_history = ["help"]
        self.history_file = os.path.expanduser("~/.micrOS_cmd_history")  # History file (Linux/macOS)
        self.load_history()

        if readline:
            readline.set_completer(self.autocomplete)
            readline.parse_and_bind("tab: complete")
            readline.set_pre_input_hook(self.pre_input_hook)  # Fixes prompt visibility when scrolling history

    def load_history(self):
        """Loads command history from a file if available."""
        if readline and os.path.exists(self.history_file):
            with open(self.history_file, "r") as f:
                for line in f:
                    self.command_history.append(line.strip())
                    readline.add_history(line.strip())

    def save_history(self):
        """Saves command history to a file."""
        if readline:
            with open(self.history_file, "w") as f:
                for cmd in self.command_history:
                    f.write(cmd + "\n")

    def add_history(self, cmd):
        cmd = cmd.strip()
        if readline and len(cmd) > 0 and cmd != self.command_history[-1]:
            self.command_history.append(cmd)
            readline.add_history(cmd)

    def autocomplete(self, text, state):
        """Autocomplete function: suggests previous commands."""
        matches = [cmd for cmd in self.command_history if cmd.startswith(text)]
        return matches[state] if state < len(matches) else None

    def pre_input_hook(self):
        """Ensures the prompt stays visible when scrolling through history."""
        sys.stdout.write(f"\r{self.prompt}{readline.get_line_buffer()}")
        sys.stdout.flush()

    #####################################
    #       STANDALONE TEST METHODS     #
    #####################################

    def dummy_send_cmd(self, cmd, stream):
        dummy_reply = "Bye!" if cmd.strip() in ["exit", "reboot"] else f"Dummy reply for {cmd}"
        if stream:
            print(dummy_reply)
            print(self.prompt, end="")  # Must remain unchanged
        return dummy_reply

    def dummy_run(self):
        """Main command loop."""
        while True:
            try:
                # Print the prompt manually before input, without duplication
                cmd = input(f"\r{self.prompt}")  # Read user input WITHOUT printing the prompt again
                output = self.dummy_send_cmd(cmd, stream=True)

                if 'Bye!' in str(output):
                    break

                if readline:
                    self.add_history(cmd)

            except KeyboardInterrupt:
                print("\nExiting...")
                break

        self.save_history()
        print("Session closed.")


if __name__ == "__main__":
    shell = CommandInterface(prompt="<prompt_placeholder $> ")
    shell.dummy_run()
