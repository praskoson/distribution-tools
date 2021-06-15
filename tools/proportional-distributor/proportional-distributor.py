#!/usr/bin/env python3
from datetime import datetime, timezone
import time
import argparse
import sys
import signal
import os
import subprocess
import re
from collections import OrderedDict


def get_env():
    envre = re.compile(r'''^([^\s=]+)=(?:[\s"']*)(.+?)(?:[\s"']*)$''')
    result = {}
    try:
        with open('./config.env') as ins:
            for line in ins:
                match = envre.match(line)
                if match is not None:
                    result[match.group(1)] = match.group(2)
    except (OSError, IOError):
        return False, None
        # sys.exit(f"Error opening environment config file.\n{e.strerror}")
    return True, result


def input_number(prompt):
    while True:
        try:
            num = float(input(prompt))
            break
        except ValueError:
            pass
    return num


def display_menu(options):
    for i in range(len(options)):
        print("{:d}. {:s}".format(i+1, options[i]))

    choice = 0
    possible = list(range(1, len(options)+1))
    while choice not in possible:
        choice = input_number("Select an option:\n> ")
    return choice


def get_current_utc_time_str():
    now_utc = datetime.now(timezone.utc)
    return now_utc.strftime("%Y-%m-%d-%H%M%S")


def amount_prompt(amount):
    if amount is None:
        value = 0
        while True:
            try:
                str = input(
                    "No airdrop amount was specified. Please enter the amount. \n> ")
                value = float(str.strip())
                if value > 0:
                    break
                else:
                    print("Airdrop amount must be greater than 0.")
            except ValueError:
                print("Not a float.")
        return value
    else:
        return amount


def continue_airdrop_prompt(interactive, separator):
    mode = 'interactive' if interactive else 'non-interactive'
    interactive_msg = f'{bcolors.BOLD}You will be prompted to confirm each transaction.{bcolors.ENDC}'
    uninteractive_msg = f'{bcolors.BOLD}The airdrop will run without additional confirmations.{bcolors.ENDC}'
    detailed_info = interactive_msg if interactive else uninteractive_msg
    print(
        f"Running the airdrop in {bcolors.BOLD}{mode} mode{bcolors.ENDC}. {bcolors.BOLD}{detailed_info}{bcolors.ENDC}")
    print(f"{bcolors.WARNING}{separator}{bcolors.ENDC}")
    if input(f"Enter {bcolors.OKGREEN}Y{bcolors.ENDC} to proceed\n> ") != 'Y':
        sys.exit("Cancelling the airdrop.")


def single_transaction_prompt(full_cmd, amount, recipient, decimals):
    msg = f"Sending {bcolors.OKBLUE}{amount:,.{decimals}f}{bcolors.ENDC} tokens to recipient at: {bcolors.OKCYAN}{recipient}{bcolors.ENDC}.\n"
    msg += "Cmd to be ran: \n"
    msg += f"    {bcolors.BOLD}" + full_cmd + f"{bcolors.ENDC}"
    print(msg, flush=True)
    choice = input(
        "Press ENTER to confirm | Type anything to CANCEL | Type ALL to switch to non-interactive mode\n> ")
    if choice == "":
        return True, False
    elif choice == "ALL":
        return False, True
    else:
        return False, False


def gen_logfile(name, current_time, folder_prefix):
    filename = "./" + folder_prefix + current_time + "/" + name
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    # Don't open, but create it anyway
    f = open(filename, "w")
    f.close()
    return filename


def parse_sig(log):
    # Find the last line that has some text in it.
    # That line should have the signature.
    outlines = re.split('\n', log)
    idx = len(outlines) - 1
    while outlines[idx] == '':
        idx = idx - 1
    out = outlines[idx]
    sig = re.match(r"Signature: ([a-zA-Z0-9]+)", out)
    if sig:
        return sig.group(1)
    else:
        return 'Error parsing signature - check the detailed logs.'


class TransferCmd:
    def __init__(self, cmd, instruction, mint_address, decimals, drop_amount, recipient, url, options=None):
        self.cmd = cmd
        self.instruction = instruction
        self.mint_address = mint_address
        self.decimals = decimals
        self.drop_amount = drop_amount
        self.recipient = recipient
        self.url = url
        if options is None:
            self.options = []
        else:
            self.options = options

    def to_str(self):
        return f"{self.cmd} {self.instruction} {self.mint_address} {self.drop_amount:.{self.decimals}f} {self.recipient} {' '.join(self.options)}"

    def to_list(self):
        #obj = [self.cmd, self.instruction, self.mint_address, str(self.drop_amount), self.recipient]
        obj = [self.cmd, self.instruction, self.mint_address,
               f"{self.drop_amount:.{self.decimals}f}", self.recipient, '--url', self.url]
        if self.options:
            obj.extend(self.options)
        return obj


def run(cmd):
    proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                            )
    stdout, stderr = proc.communicate()
    return proc.returncode, stdout, stderr


def try_transfer(cmd, addr, drop, log_success, log_unconfirmed, log_failed,
                 TOO_MANY_REQUESTS, RPC_ERROR, UNCONFIRMED):
    global RETRY_ON_429
    log_detail_entry = ''
    while True:
        code, out, err = run(cmd.to_list())
        if code == 0:
            output = out.decode('utf-8')
            print(
                f'{bcolors.OKGREEN}SUCCESS{bcolors.ENDC}', flush=True)
            sig = parse_sig(output)
            with open(log_success, 'a') as ls:
                ls.write(f'{addr},{drop:f},{sig}\n')
            log_detail_entry += output + '\n'
            break
        else:
            err_msg = err.decode('utf-8')
            if RPC_ERROR in err_msg:
                print('-32005 RPC Error, waiting 5... ',
                        end='', flush=True)
                log_detail_entry += err_msg + '\n'
                time.sleep(5)
                continue
            if RETRY_ON_429 and (TOO_MANY_REQUESTS in err_msg):
                print('429, waiting 5... ', end='', flush=True)
                time.sleep(5)
                log_detail_entry += err_msg + '\n'
                continue
            if UNCONFIRMED in err_msg or TOO_MANY_REQUESTS in err_msg:
                print(
                    f'{bcolors.DANGER}UNCONFIRMED{bcolors.ENDC}', flush=True)
                with open(log_unconfirmed, "a") as lu:
                    lu.write(f'{addr},{drop:f},{err_msg}')
                log_detail_entry += err_msg + '\n'
                break

            print(f'{bcolors.FAIL}FAILED{bcolors.ENDC}', flush=True)
            try:
                err_short = err_msg.split('\n', 1)[0] + '\n'
                err_short = re.sub(r"[,]", ' ', err_short)
            except (IndexError, Exception):
                err_short = 'Error parsing error description - read the full logs.\n'
            finally:
                with open(log_failed, 'a') as lfa:
                    lfa.write(f'{addr},{drop:f},{err_short}')
            log_detail_entry += err_msg + '\n'
            break
    return log_detail_entry


def get_assoc_addr(addr, mint, url):
    cmd = ['spl-token', 'address', '--token', mint, '--owner', addr,
           '--url', url, '--verbose']
    code, output, _ = run(cmd)
    if code == 0:
        decoded = output.decode('utf-8')
        out = (re.split('\n', decoded))[1]
        assoc = re.match(r"Associated token address: ([a-zA-Z0-9]+)", out)
        return True, assoc.group(1)
    else:
        return False, None


def get_balance(addr, addr_type, mint, url):
    if addr_type == 'token':
        cmd = ['spl-token', 'balance', '--address', addr, '--url', url]
        code, output, _ = run(cmd)
        if code == 0 and output.decode('utf-8') != '':
            return True, float(output.decode('utf-8'))
        else:
            return False, 'Could not find token account'
    else:
        ok, assoc_addr = get_assoc_addr(addr, mint, url)
        if ok:
            cmd = ['spl-token', 'balance',
                   '--address', assoc_addr, '--url', url]
            code, output, _ = run(cmd)
            if code == 0 and output.decode('utf-8') != '':
                return True, float(output.decode('utf-8'))
            else:
                return False, 'Could not find token account'
        else:
            return False, 'Could not find token account'


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    DANGER = '\u001b[38;5;208m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def main():
    args = parser.parse_args()
    mode = args.mode
    global TOKEN_MINT, TOKEN_DECIMALS, RPC_URL, LOG_FOLDER_PREFIX, FULL_LOGS, SUCCESS_LOGS, FAILED_LOGS, CANCELED_LOGS, UNCONFIRMED_LOGS, RETRY_ON_429
    if not mode:
        sys.exit('Select a subcommand (-h)')

    ok, env = get_env()
    if ok:
        try:
            TOKEN_MINT = env['TOKEN_MINT']
            TOKEN_DECIMALS = env['TOKEN_DECIMALS']
            RPC_URL = env['RPC_URL']
            LOG_FOLDER_PREFIX = env["LOG_FOLDER_PREFIX"]
            FULL_LOGS = env["FULL_LOGS"]
            SUCCESS_LOGS = env["SUCCESS_LOGS"]
            FAILED_LOGS = env["FAILED_LOGS"]
            CANCELED_LOGS = env["CANCELED_LOGS"]
            UNCONFIRMED_LOGS = env["UNCONFIRMED_LOGS"]
        except KeyError as e:
            sys.exit('Error reading config file: ' + str(e))
    else:
        if RPC_URL == "":
            rpc_endpoints = {
                'mainnet': 'https://api.mainnet-beta.solana.com',
                'testnet': 'https://api.testnet.solana.com',
                'devnet': 'https://api.devnet.solana.com'
            }
            print("Select an endpoint ")
            choice = display_menu(list(rpc_endpoints.values()))
            RPC_URL = rpc_endpoints[list(rpc_endpoints.keys())[int(choice)-1]]
        if TOKEN_MINT == "":
            TOKEN_MINT = input("\nEnter the token mint address:\n> ")
        if TOKEN_DECIMALS == "":
            TOKEN_DECIMALS = int(
                input("\nEnter the number of token decimals:\n> "))

    if mode == 'check-before':
        input_file = args.file_name
        address_type = args.address_type
        drop = args.drop
        before(input_file, drop, address_type)
    elif mode == 'check-after':
        before_file = args.before_file_name
        addr_type = args.address_type
        after(before_file, addr_type)
    elif mode == 'transfer':
        input_path = args.address_list
        interactive = args.interactive
        drop_amount = args.drop_amount
        fund_recipient = args.fund_recipient
        allow_unfunded_recipient = args.allow_unfunded_recipient
        RETRY_ON_429 = args.retry_on_429
        transfer(input_path, interactive, drop_amount, 
            fund_recipient, allow_unfunded_recipient
        )


def before(input_file, drop, addr_type):
    global TOKEN_DECIMALS
    output_file = './before.csv'
    print('recipient,current-balance,expected-balance')

    accounts = {}
    with open(input_file, 'r') as f:
        for line in f:
            try:
                addr, balance = line.split(',')
                accounts[addr.strip()] = float(balance.strip())
            except (IndexError, ValueError) as e:
                sys.exit('Error reading input file: ' + str(e))

    with open(output_file, 'w') as fw:
        sum_of_balances = sum(accounts.values())
        factor = float(drop) / sum_of_balances

        for addr in accounts:
            balance = accounts[addr]
            expected = balance + balance * factor
            print(f'{addr} - {balance:.3f} - {expected:.3f}')
            fw.write(f'{addr},{balance:.{TOKEN_DECIMALS}f},{expected:.{TOKEN_DECIMALS}f}\n')


def after(input_file, addr_type):
    global TOKEN_MINT, TOKEN_DECIMALS, RPC_URL
    lines = []
    output_file = './after.csv'
    print('recipient,expected-balance,actual-balance,difference')
    with open(input_file, 'r') as f:
        lines = f.readlines()

    with open(output_file, 'w') as f:
            # Read before.csv
            for line in lines:
                output_line = ''
                try:
                    addr, _, expected = [x.strip() for x in line.split(',')]
                    output_line += f'{addr},'
                except IndexError as e:
                    sys.exit('Error reading input file: ' + str(e))

                try:
                    expected = float(expected)
                    output_line += f'{expected:.{TOKEN_DECIMALS}f},'
                except ValueError:
                    # Not a number, expecting a No token account message
                    output_line += f'{expected},'

                ok, actual = get_balance(addr, addr_type, TOKEN_MINT, RPC_URL)
                if ok:
                    endc = '\033[0m'
                    startc = ''
                    try:
                        diff = actual - expected
                        if diff >= 0:
                            startc = '\033[92m'
                        else:
                            startc = '\033[91m'
                        output_line += f'{actual:.{TOKEN_DECIMALS}f},{diff:.{TOKEN_DECIMALS}f}'
                    except TypeError:
                        # Assuming actual was not a number
                        diff = 'NaN'
                        output_line += f'{actual},{diff}'          
                else:
                    output_line += f'{actual},NaN'

                print(startc + output_line + endc)
                f.write(output_line + '\n')


def transfer(input_path, interactive, drop_amount, 
            fund_recipient, allow_unfunded_recipient):
    global TOKEN_MINT, TOKEN_DECIMALS, RPC_URL, LOG_FOLDER_PREFIX, FULL_LOGS, SUCCESS_LOGS, FAILED_LOGS, CANCELED_LOGS, UNCONFIRMED_LOGS
    SEPARATOR = "-" * 50
    LOG_SEPARATOR = "-" * 30 + "\n"
    TOO_MANY_REQUESTS = "429 Too Many Requests"
    UNCONFIRMED = "unable to confirm transaction"
    RPC_ERROR = "RPC response error -32005"

    signal.signal(signal.SIGINT, signal.default_int_handler)
    supply_code, current_supply, _ = run(['solana', 'address'])

    if supply_code != 0:
        sys.exit('Exiting, failed to read the current wallet account address. Try checking the output of \'solana address\'.')

    print(f"{bcolors.DANGER}WARNING: MAKE SURE YOU ARE USING THE CORRECT WALLET TO DISTRIBUTE.\
        \nYour current wallet address is: {current_supply.decode('utf-8')}{bcolors.ENDC}")
    print(
        f"Running airdrop for the Token Mint: {bcolors.OKGREEN}{TOKEN_MINT}{bcolors.ENDC}")
    total_drop = amount_prompt(drop_amount)
    print(
        f"Total airdrop amount: {bcolors.OKGREEN}{total_drop:,.{TOKEN_DECIMALS}f}{bcolors.ENDC}")

    accounts = OrderedDict()
    try:
        with open(input_path) as f:
            for line in f:
                address, balance = line.split(',')
                accounts[address.strip()] = float(balance.strip())
        print(f'Airdropping to {bcolors.OKGREEN}{len(accounts)}{bcolors.ENDC} users\n')

    except (OSError, IOError, IndexError, ValueError) as e:
        sys.exit(f"Error opening or reading address/exclusion files: {str(e)}")

    # region Create log files, print locations, write headers
    timestamp = get_current_utc_time_str()
    log_success = gen_logfile(SUCCESS_LOGS, timestamp, LOG_FOLDER_PREFIX)
    log_canceled = gen_logfile(CANCELED_LOGS, timestamp, LOG_FOLDER_PREFIX)
    log_failed = gen_logfile(FAILED_LOGS, timestamp, LOG_FOLDER_PREFIX)
    log_unconfirmed = gen_logfile(UNCONFIRMED_LOGS, timestamp, LOG_FOLDER_PREFIX)
    log_full = gen_logfile(FULL_LOGS, timestamp, LOG_FOLDER_PREFIX)

    print(f"  Successful logs: (tail -f {log_success})")
    print(f"  Canceled logs: (tail -f {log_canceled})")
    print(f"  Failed logs: (tail -f {log_failed})")
    print(f"  Unconfirmed logs: (tail -f {log_unconfirmed})")
    print(f"  Detailed logs: (tail -f {log_full})")

    with open(log_success, "a") as ls:
        ls.write('recipient,amount,signature\n')
    with open(log_canceled, "a") as lc:
        lc.write('recipient,amount\n')
    with open(log_failed, "a") as lfa:
        lfa.write('recipient,amount,error\n')
    with open(log_unconfirmed, "a") as lu:
        lu.write('recipient,amount,error\n')
    # endregion

    print()
    try:
        continue_airdrop_prompt(interactive, SEPARATOR)
        # Determine factor for proportional drop.
        proportional_factor = total_drop / sum(accounts.values())

        i = 0
        for addr in accounts:
            # Calculate proportional drop 
            current_balance = accounts[addr]
            drop = current_balance * proportional_factor
            options = []
            if fund_recipient:
                options.append('--fund-recipient')
            if allow_unfunded_recipient:
                options.append('--allow-unfunded-recipient')
            cmd = TransferCmd("spl-token", "transfer",
                TOKEN_MINT, TOKEN_DECIMALS, drop, addr, RPC_URL, options)

            if not interactive:
                log_detail_entry = ""
                print(f"{i+1}. Airdrop to {addr}: ", end="", flush=True)
                log_detail_entry += f"{i+1}. Cmdline: {cmd.to_str()}\n"
                log_detail_entry += try_transfer(
                    cmd, addr, drop,
                    log_success, log_unconfirmed, log_failed,
                    TOO_MANY_REQUESTS, RPC_ERROR, UNCONFIRMED
                )

                with open(log_full, "a") as lf:
                    lf.write(log_detail_entry + LOG_SEPARATOR)
                del cmd
                i += 1
            elif interactive:
                log_detail_entry = ""
                print(f"{i+1}. ", end="", flush=True)
                log_detail_entry += f"{i+1}. Cmdline: {cmd.to_str()}\n"

                confirm, switch_mode = single_transaction_prompt(
                    cmd.to_str(), drop, addr, TOKEN_DECIMALS)
                if switch_mode:
                    print("Switching to non-interactive mode on next address.")
                    interactive = False
                    confirm = True

                if confirm:
                    log_detail_entry += try_transfer(
                        cmd, addr, drop,
                        log_success, log_unconfirmed, log_failed,
                        TOO_MANY_REQUESTS, RPC_ERROR, UNCONFIRMED
                    )

                    with open(log_full, "a") as lf:
                        lf.write(log_detail_entry + LOG_SEPARATOR)
                elif not confirm:
                    print(
                        f"{bcolors.DANGER}CANCELED{bcolors.ENDC}", flush=True)
                    cancel = f"{addr},{drop:f}"
                    with open(log_canceled, "a") as lc:
                        lc.write(cancel + "\n")
                    log_detail_entry += f"Cancel: {cancel}\n"
                    with open(log_full, "a") as lf:
                        lf.write(log_detail_entry + LOG_SEPARATOR)

                print(f"{bcolors.WARNING}{SEPARATOR}{bcolors.ENDC}")
                del cmd
                i += 1

    except KeyboardInterrupt:
        sys.exit("Interrupted, exiting.")
    finally:
        print("Log file handlers closed.")

    print("Done!")


# region Argument parsing
parser = argparse.ArgumentParser(
    description='''Token distribution application for transferring a proportional amount of tokens 
           to given Solana or SPL token addresses, based on their current holdings. 
           The proportional_factor is a sum of all balances of given addresses, divided by 
           the total drop amount, and the drop for an individual account is current 
           balance multiplied by the proportional factor.
           
           The application also includes checking tools that can be ran before and after 
           a distribution, to check if all users received the expected amount of tokens.'''
)

subparsers = parser.add_subparsers(
    help='Select usage mode: check-before a distribution, check-after or run a distribution (transfer).',
    dest='mode')

parser_b = subparsers.add_parser(
    'check-before', help='Checker before a distribution, generates a CSV file with a snapshot of current balances of all accounts, and the expected balance after the distribution.')
parser_b.add_argument(
    '-a',
    '--address-list',
    dest='file_name',
    metavar='ADDRESS_LIST_FILE',
    required=True,
    help='Path to the file containing a list of addresses and balances, seperated by a comma, and with each pair in a seperate line.'
)
parser_b.add_argument(
    '-t',
    '--address-type',
    metavar='ADDRESS_TYPE',
    dest='address_type',
    choices={'token', 'owner'},
    required=True,
    help='Select from using token addresses or owner addresses in the input file {owner | token}.'
)
parser_b.add_argument(
    '-d',
    '--drop',
    metavar='TOTAL_DROP_AMOUNT',
    dest='drop',
    type=float,
    required=True,
    help='Total amount of tokens that will be proportionally distributed to each recipient.'
)

parser_a = subparsers.add_parser(
    'check-after', help='Run the checker after a distribution, to check if all recipients received the expected amount of tokens.')
parser_a.add_argument(
    '-t',
    '--address-type',
    metavar='ADDRESS_TYPE',
    dest='address_type',
    choices={'token', 'owner'},
    required=True,
    help='Select from using token addresses, or owner account addresses in the input file {token | owner}.'
)
parser_a.add_argument(
    '-b',
    '--before-file',
    metavar='BEFORE_FILE',
    dest='before_file_name',
    required=True,
    help='Path to the CSV file generated by the \'before\' command (before.csv).'
)

parser_t = subparsers.add_parser(
    'transfer', help='Distribute a proportional amount of tokens to all given addresses.')

parser_t.add_argument(
    '-d',
    '--drop',
    dest="drop_amount",
    type=float,
    required=False,
    help='Total amount of tokens used in the distribution, each recipient will receive a proportion of this value.'
)
parser_t.add_argument(
    '--non-interactive',
    dest="interactive",
    default=True,
    action='store_false',
    required=False,
    help='Run in non-interactive mode (no confirmation prompts).'
)
parser_t.add_argument(
    '-a',
    '--address-list',
    dest="address_list",
    required=True,
    help='Path to the file containing a list of addresses and balances, \
        seperated by a comma, and with each pair in a separate line.'
)
parser_t.add_argument(
    '--fund-recipient',
    action='store_true',
    required=False,
    help='Create the associated token account for the recipient if it does not exist.'
)
parser_t.add_argument(
    '--allow-unfunded-recipient',
    action='store_true',
    required=False,
    help='Complete the transfer even if the recipient\'s address is not funded.'
)
parser_t.add_argument(
    '--retry-on-429',
    dest='retry_on_429',
    action='store_true',
    default=False,
    required=False,
    help='Retry when a HTTP 429 error code is encountered. Use this at your own risk.'
)
#endregion

if __name__ == '__main__':
    TOKEN_MINT = ""
    TOKEN_DECIMALS = ""
    RPC_URL = ""
    LOG_FOLDER_PREFIX = 'logs-'
    FULL_LOGS = 'detailed.log'
    SUCCESS_LOGS = 'success.log'
    FAILED_LOGS = 'failed.log'
    CANCELED_LOGS = 'canceled.log'
    UNCONFIRMED_LOGS = 'unconfirmed.log'
    RETRY_ON_429 = False
    main()
