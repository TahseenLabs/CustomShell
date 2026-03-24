import sys


def main():
    # List of shell builtin commands
    builtins = ["echo", "exit", "type"]
    # Infinite loop to continuously display the shell prompt,
    # mimicking how a real shell waits for user commands repeatedly
    while True:
        sys.stdout.write("$ ")
    
        # Reading a line of input from the user 
        command = input()
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
            # Extract the argument after "type "
            cmd_name = command[5:].strip()
            if cmd_name in builtins:
                print(f"{cmd_name} is a shell builtin")
            else:
                print(f"{cmd_name}: not found")
        # For any other command, print a "command not found" message
        else:
            print(f"{command}: command not found")
       

# Entry point of the program
# Ensures main() runs only when the script is executed directly
if __name__ == "__main__":
    main()


    