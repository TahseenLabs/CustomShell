import sys
import os
import subprocess
import shlex
import readline

def get_executables_from_path():
    """Return all executable names found in PATH directories."""
    executables = set()
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    for dir_path in path_dirs:
        if not os.path.isdir(dir_path):
            continue
        try:
            for name in os.listdir(dir_path):
                full_path = os.path.join(dir_path, name)
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    executables.add(name)
        except PermissionError:
            continue
    return executables

# All builtin command names
BUILTINS = ["echo", "exit", "type", "pwd", "cd", "history"]
HISTORY_FILE = os.path.expanduser("~/.shell_history")


def completer(text, state):     
    if state == 0:
        buffer = readline.get_line_buffer()

        # Command completion (no space typed yet)
        if ' ' not in buffer:
            all_commands = BUILTINS + sorted(get_executables_from_path())
            completer.matches = [c + " " for c in all_commands if c.startswith(text)]

        # Filename/directory argument completion
        else:
            # Split text into directory part and file prefix
            # e.g. "foo/bar/ba" -> dir="foo/bar/", prefix="ba"
            if "/" in text:
                dir_part = text[:text.rfind("/") + 1]
                prefix = text[text.rfind("/") + 1:]
            else:
                dir_part = ""
                prefix = text

            search_dir = dir_part if dir_part else "."

            try:
                entries = os.listdir(search_dir)
            except OSError:
                entries = []

            matches = []
            for entry in entries:
                if entry.startswith(prefix):
                    full = dir_part + entry
                    if os.path.isdir(os.path.join(search_dir, entry)):
                        matches.append(full + "/")  # no trailing space for dirs
                    else:
                        matches.append(full + " ")  # trailing space for files
            completer.matches = sorted(matches)

    if state < len(completer.matches):
        return completer.matches[state]
    return None

def display_matches(substitution, matches, longest_match_length):
    """
    Custom display hook for when there are multiple completions.
    Prints them on a new line, then reprints the prompt + current input.
    """
    print()  # move past current input line
    print("  ".join(m.strip() for m in matches))
    sys.stdout.write("$ " + readline.get_line_buffer())
    sys.stdout.flush()
 
 
def setup_readline():
    readline.set_completer(completer)
    readline.set_completion_display_matches_hook(display_matches)
    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(" \t\n")
    # History setup
    readline.parse_and_bind("set history-size 1000")
    readline.parse_and_bind('"\\e[A": history-search-backward')
    readline.parse_and_bind('"\\e[B": history-search-forward')
    readline.set_history_length(1000)

def main():
    builtins = BUILTINS
    setup_readline()
    
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
    
        command = input()
        raw_command = command

        parts = shlex.split(command)

        redirect_file = None
        redirect_mode = "w"
        stderr_file = None
        stderr_mode = "w"

        i = 0
        while i < len(parts):
            if parts[i] == "2>":
                stderr_file = parts[i + 1]
                stderr_mode = "w"
                del parts[i:i+2]
            elif parts[i] == "2>>":
                stderr_file = parts[i + 1]
                stderr_mode = "a"
                del parts[i:i+2]
            elif parts[i] == ">" or parts[i] == "1>":
                redirect_file = parts[i + 1]
                redirect_mode = "w"
                del parts[i:i+2]
            elif parts[i] == ">>" or parts[i] == "1>>":
                redirect_file = parts[i + 1]
                redirect_mode = "a"
                del parts[i:i+2]
            else:
                i += 1

        command = " ".join(parts)

        if not command:
            continue

        # Handle !N history execution before adding to history
        if command.startswith("!"):
            try:
                n = int(command[1:])
                hist_len = readline.get_current_history_length()
                if 1 <= n <= hist_len:
                    command = readline.get_history_item(n)
                    parts = shlex.split(command)
                else:
                    print(f"bash: !{n}: event not found")
                    continue
            except ValueError:
                print(f"bash: {command}: event not found")
                continue

        readline.write_history_file(HISTORY_FILE)

        if command == "exit":
            break

        # Pipeline check FIRST, before any builtin handling
        elif "|" in parts:
            raw_parts = shlex.split(raw_command)
            pipeline_segments = []
            current_segment = []
            for token in raw_parts:
                if token == "|":
                    if current_segment:
                        pipeline_segments.append(current_segment)
                        current_segment = []
                else:
                    current_segment.append(token)
            if current_segment:
                pipeline_segments.append(current_segment)

            prev_output = None  # initialize before the loop
            prev_proc = None

            for idx, seg in enumerate(pipeline_segments):
                is_last = (idx == len(pipeline_segments) - 1)

                # Built-in handling
                if seg[0] in BUILTINS:
                    # If a previous process was piping into this builtin, drain and discard its output
                    if prev_proc is not None:
                        prev_proc.stdout.read() 
                        prev_proc.stdout.close()
                        prev_proc.wait()
                        prev_proc = None
                    if seg[0] == "echo":
                        output = " ".join(seg[1:]) + "\n"
                    elif seg[0] == "pwd":
                        output = os.getcwd() + "\n"
                    elif seg[0] == "history":
                        hist_len = readline.get_current_history_length()
                        lines = []
                        for i in range(1, hist_len + 1):
                            lines.append(f"    {i}  {readline.get_history_item(i)}")
                        output = "\n".join(lines) + "\n"
                    elif seg[0] == "type":
                        cmd_name = seg[1] if len(seg) > 1 else ""
                        if cmd_name in BUILTINS:
                            output = f"{cmd_name} is a shell builtin\n"
                        else:
                            found_type = False
                            for dir_path in os.environ.get("PATH", "").split(os.pathsep):
                                if not os.path.isdir(dir_path):
                                    continue
                                full_path = os.path.join(dir_path, cmd_name)
                                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                                    output = f"{cmd_name} is {full_path}\n"
                                    found_type = True
                                    break
                            if not found_type:
                                output = f"{cmd_name}: not found\n"
                    else:
                        output = ""

                    prev_output = output.encode()

                else:
                    # For the last process: stdout goes to file or directly to terminal
                    if is_last and not redirect_file:
                        stdout_dest = None  # inherit our stdout directly
                    else:
                        stdout_dest = subprocess.PIPE

                    stderr_dest = (open(stderr_file, stderr_mode) if (stderr_file and is_last) else subprocess.PIPE)

                    if prev_output is not None:
                        proc = subprocess.Popen(
                            seg,
                            stdin=subprocess.PIPE,
                            stdout=stdout_dest,
                            stderr=stderr_dest
                        )
                        proc.stdin.write(prev_output)
                        proc.stdin.close()
                        prev_output = None
                    elif prev_proc is not None:
                        proc = subprocess.Popen(
                            seg,
                            stdin=prev_proc.stdout,
                            stdout=stdout_dest,
                            stderr=stderr_dest
                        )
                        prev_proc.stdout.close()
                    else:
                        proc = subprocess.Popen(
                            seg,
                            stdin=None,
                            stdout=stdout_dest,
                            stderr=stderr_dest
                        )
                    prev_proc = proc
                        

            # Handle final output
            if prev_proc is not None:
                if redirect_file:
                    out, _ = prev_proc.communicate()
                    stdout_dir = os.path.dirname(redirect_file)
                    if stdout_dir:
                        os.makedirs(stdout_dir, exist_ok=True)
                    with open(redirect_file, redirect_mode) as f:
                        f.write(out.decode())
                else:
                    prev_proc.wait()  # stdout already going to terminal directly
            elif prev_output:
                if redirect_file:
                    stdout_dir = os.path.dirname(redirect_file)
                    if stdout_dir:
                        os.makedirs(stdout_dir, exist_ok=True)
                    with open(redirect_file, redirect_mode) as f:
                        f.write(prev_output.decode())
                else:
                    sys.stdout.buffer.write(prev_output)
                    sys.stdout.buffer.flush()

        elif parts[0] == "echo":
            output = " ".join(parts[1:])
            if redirect_file:
                stdout_dir = os.path.dirname(redirect_file)
                if stdout_dir:
                    os.makedirs(stdout_dir, exist_ok=True)
                with open(redirect_file, redirect_mode) as f:
                    print(output, file=f)
            else:
                print(output)
            if stderr_file:
                stderr_dir = os.path.dirname(stderr_file)
                if stderr_dir:
                    os.makedirs(stderr_dir, exist_ok=True)
                with open(stderr_file, stderr_mode) as f:
                    pass

        elif command == "pwd":
            print(os.getcwd())

        elif command == "history" or command.startswith("history "):
            # Parse optional limit argument: history N
            limit = None
            if command.startswith("history "):
                try:
                    limit = int(command[8:].strip())
                except ValueError:
                    limit = None
            hist_len = readline.get_current_history_length()
            start = 1 if limit is None else max(1, hist_len - limit + 1)
            for i in range(start, hist_len + 1):
                print(f"    {i}  {readline.get_history_item(i)}")

        elif command.startswith("cd "):
            target_dir = command[3:].strip()
            if target_dir == "~":
                new_dir = os.environ.get("HOME", os.getcwd())
            elif target_dir.startswith("/"):
                new_dir = target_dir
            else:
                new_dir = os.path.join(os.getcwd(), target_dir)

            if os.path.isdir(new_dir):
                try:
                    os.chdir(new_dir)
                except Exception:
                    print(f"cd: {target_dir}: No such file or directory")
            else:
                print(f"cd: {target_dir}: No such file or directory")

        elif command.startswith("type "):
            cmd_name = command[5:].strip()
            if cmd_name in BUILTINS:
                print(f"{cmd_name} is a shell builtin")
            else:
                found = False
                path_dirs = os.environ.get("PATH", "").split(os.pathsep)
                for dir_path in path_dirs:
                    if not os.path.isdir(dir_path):
                        continue
                    full_path = os.path.join(dir_path, cmd_name)
                    if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                        print(f"{cmd_name} is {full_path}")
                        found = True
                        break
                if not found:
                    print(f"{cmd_name}: not found")

        else:
            if not parts:
                continue

            cmd_name = parts[0]
            args = parts
            found = False

            path_dirs = os.environ.get("PATH", "").split(os.pathsep)
            for dir_path in path_dirs:
                if not os.path.isdir(dir_path):
                    continue
                full_path = os.path.join(dir_path, cmd_name)
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    stdout_dest = None
                    stderr_dest = None
                    try:
                        if redirect_file:
                            stdout_dir = os.path.dirname(redirect_file)
                            if stdout_dir:
                                os.makedirs(stdout_dir, exist_ok=True)
                            stdout_dest = open(redirect_file, redirect_mode)
                        if stderr_file:
                            stderr_dir = os.path.dirname(stderr_file)
                            if stderr_dir:
                                os.makedirs(stderr_dir, exist_ok=True)
                            stderr_dest = open(stderr_file, stderr_mode)

                        process = subprocess.Popen(
                            args,
                            stdout=stdout_dest or None,
                            stderr=stderr_dest or None
                        )
                        process.communicate()

                    except Exception as e:
                        print(f"Error running {cmd_name}: {e}")
                    finally:
                        if stdout_dest:
                            stdout_dest.close()
                        if stderr_dest:
                            stderr_dest.close()

                    found = True
                    break

            if not found:
                print(f"{cmd_name}: command not found")
    


# Entry point of the program
# Ensures main() runs only when the script is executed directly
if __name__ == "__main__":
    main()

