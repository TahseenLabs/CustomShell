import sys


def main():
    # Displaying the shell prompt ("$ ") without adding a newline
    sys.stdout.write("$ ")
    
    # Reading a line of input from the user 
    command = input()

    # Since no actual command execution is implemented yet,
    # printing a "command not found" message like a real shell
    print(f"{command}: command not found")


# Entry point of the program
# Ensures main() runs only when the script is executed directly
if __name__ == "__main__":
    main()


    