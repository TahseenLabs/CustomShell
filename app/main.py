import sys


def main():
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
        # For any other command, print a "command not found" message
        else:
            print(f"{command}: command not found")
       

# Entry point of the program
# Ensures main() runs only when the script is executed directly
if __name__ == "__main__":
    main()


    