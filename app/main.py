import sys
import os
import subprocess


def main():
    # List of shell builtin commands
    builtins = ["echo", "exit", "type"]
    # Infinite loop to continuously display the shell prompt,
    # mimicking how a real shell waits for user commands repeatedly
    while True:
        sys.stdout.write("$ ")
    
        # Reading a line of input from the user 
        command = input()
        
        # Skip empty input
        if not command:
            continue
        
        # If the user types "exit", break out of the loop
        # This allows the shell to terminate gracefully
        if command == "exit":
            break
        
        # If the command starts with "echo ", print everything after "echo "
        # This simulates the basic behavior of the Unix 'echo' command
        elif command.startswith("echo "):
            print(command[5:])
            
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
            # Splitting command into program + arguments
            parts = command.split()
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
                        subprocess.run([full_path] + args[1:])
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


    
    
    
    




      

       
     
      

           
               
       