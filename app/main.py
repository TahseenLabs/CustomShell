import sys
import os
import subprocess
import shlex


def main():
    # List of shell builtin commands
    builtins = ["echo", "exit", "type", "pwd", "cd"]
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
        stderr_file = None
        # Handle output redirections:
        # - 2> redirects standard error to a file
        # - > or 1> redirects standard output to a file
        # This loop scans the command parts and removes any redirection tokens and their filenames,
        # storing the target filenames in redirect_file and stderr_file.
        # Supports multiple redirections in any order (e.g., "2> err.txt > out.txt").
        i = 0
        while i < len(parts):
            if parts[i] == "2>":
                stderr_file = parts[i + 1]
                del parts[i:i+2]
            elif parts[i] == ">" or parts[i] == "1>":
                redirect_file = parts[i + 1]
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
        elif command.startswith("echo "):
            # Using already parsed parts (quotes and escapes already handled correctly)
            output = " ".join(parts[1:])
            if redirect_file:
                # If output is redirected, write to file instead of printing to terminal
                with open(redirect_file, "w") as f:
                    print(output, file=f)
            else:
                print(output)
                
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
            # Using already parsed parts (redirection removed)
            if not parts:
                continue # Skipping empty inputs
            cmd_name = parts[0]
            args = parts  # includes program name as arg0

            found = False
            # Searching PATH for executable
            path_dirs = os.environ.get("PATH", "").split(os.pathsep)
            for dir_path in path_dirs:
                if not os.path.isdir(dir_path):
                    continue
                full_path = os.path.join(dir_path, cmd_name)
                # Checking if file exists and is executable
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    # Open files for redirection if needed
                    stdout_dest = None
                    stderr_dest = None
                    try:
                        if redirect_file:
                            os.makedirs(os.path.dirname(redirect_file), exist_ok=True)
                            stdout_dest = open(redirect_file, "w")
                        if stderr_file:
                            os.makedirs(os.path.dirname(stderr_file), exist_ok=True)
                            stderr_dest = open(stderr_file, "w")
                        
                        # Run the external command with optional redirection
                        process = subprocess.Popen(
                            args,
                            stdout=stdout_dest or None,  # None means inherit parent's stdout
                            stderr=stderr_dest or None
                        )

                        # Wait for the process to finish
                        process.communicate()

                    except Exception as e:
                        print(f"Error running {cmd_name}: {e}")

                    finally:
                        # Close any opened files
                        if stdout_dest:
                            stdout_dest.close()
                        if stderr_dest:
                            stderr_dest.close()

                    found = True
                    break

# Entry point of the program
# Ensures main() runs only when the script is executed directly
if __name__ == "__main__":
    main()

