import sys


def main():
    # Infinite loop to continuously display the shell prompt,
    # mimicking how a real shell waits for user commands repeatedly
    while True:
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


    