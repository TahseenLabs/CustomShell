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
        if ">" in parts:
            idx = parts.index(">")
            redirect_file = parts[idx + 1]
            parts = parts[:idx]
        elif "1>" in parts:
            idx = parts.index("1>")
            redirect_file = parts[idx + 1]
            parts = parts[:idx]

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
                    try:
                        # Running the external program with all arguments
                        # If redirection is specified, send stdout to file (stderr remains on terminal)
                        # argv[0] must be the typed command, not full_path
                        if redirect_file:
                            with open(redirect_file, "w") as f:
                                subprocess.run(args, executable=full_path, stdout=f)
                        else:
                            subprocess.run(args, executable=full_path)
                    except Exception as e:
                        print(f"Error running {cmd_name}: {e}")
                    found = True
                    break
            # Case 3: not found anywhere
            if not found:
                print(f"{cmd_name}: command not found")

# Entry point of the program
# Ensures main() runs only when the script is executed directly
if __name__ == "__main__":
    main()
