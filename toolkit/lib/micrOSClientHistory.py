import sys
import os

try:
    import readline  # Linux/macOS
except ImportError:
    import pyreadline3 as readline  # Windows (PowerShell, CMD)

try:
    from .TerminalColors import Colors as color
except:
    from TerminalColors import Colors as color


class CommandInterface:
    def __init__(self, prompt):
        self.prompt = prompt
        self.command_history = ["help"]
        self.history_file = os.path.expanduser("~/.micrOS_cmd_history")  # History file (Linux/macOS)

        # Configure readline
        self.load_history()
        readline.set_completer_delims("")  # Ensure entire command is considered
        readline.set_completer(self.autocomplete)
        # Check if we're running on macOS using libedit
        if "libedit" in readline.__doc__:
            readline.parse_and_bind("bind ^I rl_complete")  # macOS alternative
        else:
            readline.parse_and_bind("tab: complete")  # Linux/GNU readline
        readline.set_pre_input_hook(self.pre_input_hook)
        readline.set_completion_display_matches_hook(self.completion_display)

    def __auto_clear_history(self):
        cmd_history = []
        # Load file history in order - skip duplicates
        if os.path.exists(self.history_file):
            with open(self.history_file, "r") as f:
                for line in reversed(f.readlines()):
                    if line in cmd_history:
                        continue
                    cmd_history.append(line)
            # Save cleaned history to file
            with open(self.history_file, "w") as f:
                f.writelines(f"{item}\n" for item in reversed(cmd_history))

    def load_history(self):
        """Loads command history from a file if available."""
        print(f"Command history: {self.history_file}")
        try:
            self.__auto_clear_history()
        except Exception as e:
            print(f"Auto clean history error: {e}")
        if os.path.exists(self.history_file):
            with open(self.history_file, "r") as f:
                for line in f:
                    clean_line = line.strip()
                    if clean_line:  # Avoid empty lines
                        self.command_history.append(clean_line)
                        readline.add_history(clean_line)

    def save_history(self):
        """Saves command history to a file."""
        with open(self.history_file, "w") as f:
            for cmd in self.command_history:
                f.write(cmd + "\n")

    def add_history(self, cmd):
        """Updates readline history and command_history."""
        cmd = cmd.strip()
        if cmd and cmd != self.command_history[-1]:  # Avoid duplicate last command
            self.command_history.append(cmd)
            readline.add_history(cmd)

    def autocomplete(self, text, state):
        """Autocomplete function: suggests previous commands."""
        matches = list(dict.fromkeys(cmd for cmd in self.command_history if cmd.startswith(text)))
        return matches[state] if state < len(matches) else None

    def pre_input_hook(self):
        """Ensures prompt visibility when scrolling through history."""
        sys.stdout.write(f"\r{self.prompt}{readline.get_line_buffer()}")
        sys.stdout.flush()
        readline.redisplay()  # Ensures history navigation does not erase prompt

    def completion_display(self, substitutions, matches, longest_match_length):
        print("\nSuggestions:", ", ".join(matches))

    #####################################
    #       STANDALONE TEST METHODS     #
    #####################################

    def dummy_send_cmd(self, cmd, stream):
        """TEST FUNCTION - OUTPUT STRUCTURE SIMULATION (Must remain unchanged)."""
        dummy_reply = "Bye!" if cmd.strip() in ["exit", "reboot"] else f"Dummy reply for {cmd}"
        if stream:
            print(dummy_reply)  # micrOS protocol: return response data
            print(self.prompt, end="")  # micrOS protocol: return prompt -> indicating ready state
        else:
            dummy_reply = f"{dummy_reply}\n{self.prompt}"
        return dummy_reply

    def dummy_run(self):
        """TEST FUNCTION - Simulated interactive terminal."""
        print(f"{self.prompt}", end="", flush=True)
        while True:
            try:
                cmd = input()
                output = self.dummy_send_cmd(cmd, stream=True)
                self.add_history(cmd)
                if 'Bye!' in str(output):
                    break
            except KeyboardInterrupt:
                print("\nExiting...")
                break

        self.save_history()
        print("Session closed.")


if __name__ == "__main__":
    shell = CommandInterface(prompt="<prompt_placeholder>$ ")
    shell.dummy_run()
