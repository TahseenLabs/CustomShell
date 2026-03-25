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
BUILTINS = ["echo", "exit", "type", "pwd", "cd"]

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
    # Complete on TAB only
    readline.parse_and_bind("tab: complete")
    # Treat only whitespace as word break so whole command is the "text"
    readline.set_completer_delims(" \t\n")

def main():
    builtins = BUILTINS
    setup_readline()
    # Infinite loop to continuously display the shell prompt,
    # mimicking how a real shell waits for user commands repeatedly
    while True:
        sys.stdout.write("$ ")
    
        # Reading a line of input from the user 
        command = input()
        
        # Parsing output redirection (>, 1>) while respecting quotes
        # Extracts the output file and removes redirection tokens from the command
        parts = shlex.split(command)

        redirect_file = None
        redirect_mode = "w"  # default mode for stdout
        stderr_file = None
        stderr_mode = "w"    # default mode for stderr

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
        
        # Rebuilding command without redirection so builtins and execution work normally
        command = " ".join(parts)
        
        # Skip empty input
        if not command:
            continue
        
        # If the user types "exit", break out of the loop
        # This allows the shell to terminate gracefully
        if command == "exit":
            break
        
        # If the command starts with "echo ", printing all arguments after 'echo'
        # This simulates the Unix 'echo' command while respecting single quotes
        # Single quotes preserve spaces and special characters literally
        elif parts[0] == "echo":
            output = " ".join(parts[1:])  # only arguments, no redirection

            # Handle stdout redirection
            if redirect_file:
                stdout_dir = os.path.dirname(redirect_file)
                if stdout_dir:
                    os.makedirs(stdout_dir, exist_ok=True)
                with open(redirect_file, redirect_mode) as f: 
                    print(output, file=f)
            else:
                print(output)
            
            # Always create the stderr file if 2> was used
            if stderr_file:
                stderr_dir = os.path.dirname(stderr_file)
                if stderr_dir:
                    os.makedirs(stderr_dir, exist_ok=True)
                # Open and immediately close to ensure the file exists (empty)
                with open(stderr_file, stderr_mode) as f:  # use correct mode
                    pass
        # pwd builtin
        elif command == "pwd":
            # Printing the current working directory
            print(os.getcwd())
        
        # cd builtin (absolute paths, relative paths, and ~)
        elif command.startswith("cd "):
            # Extracting the target directory
            target_dir = command[3:].strip()

            # Handling ~ for home directory
            if target_dir == "~":
                new_dir = os.environ.get("HOME", os.getcwd())
            # Handling absolute paths
            elif target_dir.startswith("/"):
                new_dir = target_dir
            # Handling relative paths
            else:
                new_dir = os.path.join(os.getcwd(), target_dir)

            # Checking if the directory exists
            if os.path.isdir(new_dir):
                try:
                    os.chdir(new_dir)
                except Exception:
                    # Directory exists but cannot be accessed
                    print(f"cd: {target_dir}: No such file or directory")
            else:
                # Directory does not exist
                print(f"cd: {target_dir}: No such file or directory")
        
        # Type builtin
        elif command.startswith("type "):
            # Extracting the argument after "type "
            cmd_name = command[5:].strip()
            # Case 1: builtin command
            if cmd_name in builtins:
                print(f"{cmd_name} is a shell builtin")

            # Case 2: searching for executable in PATH
            else:
                found = False
                # Getting PATH environment variable (use os.pathsep to split OS-agnostic)
                path_dirs = os.environ.get("PATH", "").split(os.pathsep)
                for dir_path in path_dirs:
                    # Skipping directories that don't exist
                    if not os.path.isdir(dir_path):
                        continue
                    full_path = os.path.join(dir_path, cmd_name)
                    # Checking if file exists and is executable
                    if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                        print(f"{cmd_name} is {full_path}")
                        found = True
                        break
                # Case 3: not found anywhere
                if not found:
                    print(f"{cmd_name}: not found")
        
        # For any other command, run it as an external program if executable
        else:
            if not parts:
                continue

            # --- Pipeline handling ---
            raw_parts = shlex.split(command)
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

            if len(pipeline_segments) > 1:
                processes = []
                prev_stdout = None

                for idx, seg in enumerate(pipeline_segments):
                    is_last = (idx == len(pipeline_segments) - 1)
                    stdin_src = prev_stdout

                    if is_last:
                        stdout_dest = open(redirect_file, redirect_mode) if redirect_file else None
                        stderr_dest = open(stderr_file, stderr_mode) if stderr_file else None
                    else:
                        stdout_dest = subprocess.PIPE
                        stderr_dest = None

                    proc = subprocess.Popen(
                        seg,
                        stdin=stdin_src,
                        stdout=stdout_dest,
                        stderr=stderr_dest
                    )

                    if prev_stdout is not None:
                        prev_stdout.close()

                    prev_stdout = proc.stdout
                    processes.append((proc, stdout_dest, stderr_dest))

                for proc, stdout_dest, stderr_dest in processes:
                    proc.wait()
                    if stdout_dest and stdout_dest != subprocess.PIPE:
                        stdout_dest.close()
                    if stderr_dest:
                        stderr_dest.close()

            else:
                # Single external command
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

