#!/usr/bin/env python3
import json
import random
import requests
import argparse
import os
from datetime import datetime, timezone
import sys
from collections import OrderedDict

def get_current_utc_time_str():
    now_utc = datetime.now(timezone.utc)
    return now_utc.strftime("%Y-%m-%d-%H%M%S")

def write_files(data, raw_data):
    global OUTPUT_FILE, TOKEN, TOKEN_MINT
    # If token name is not resolved, use first 5 chars of address
    if TOKEN != TOKEN_MINT:
        token_name = TOKEN
    else:
        token_name = TOKEN_MINT[:5]

    current_time = get_current_utc_time_str()
    raw_filename = "./" + token_name + "-" + current_time + "/" + 'raw.json'
    filename = "./" + token_name + "-" + current_time + "/" + OUTPUT_FILE + ".txt"
    balance_filename = "./" + token_name + "-" + current_time + "/" + OUTPUT_FILE + "-balance.txt"
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(raw_filename, 'w') as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=4)

    with open(filename, 'w') as f:
        for acc in data:
            f.write(acc[0].strip() + '\n')

    with open(balance_filename, 'w') as f:
        for acc in data:
            f.write(f'{acc[0].strip()},{str(acc[1])}\n')


def extract_balance(json):
    try:
        return float(json['account']['data']['parsed']['info']['tokenAmount']['uiAmountString'])
    except KeyError:
        return 0

def extract_owner(json):
    global ADDRESS_TYPE
    if ADDRESS_TYPE == 'owner':
        return json['account']['data']['parsed']['info']['owner']
    elif ADDRESS_TYPE == 'token':
        return json['pubkey']

def get_accounts(endpoint, mint):
    headers = {
        'Content-Type': 'application/json',
    }   
    data = ' { "jsonrpc": "2.0", "id": 1, "method": "getProgramAccounts", "params": [ "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA", { "encoding": "jsonParsed", "filters": [ { "dataSize": 165 }, { "memcmp": { "offset": 0, "bytes": "' + f"{mint}" + '" } } ] } ] } '
    response = requests.post(endpoint, headers=headers, data=data)
    return response.json()

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

#region Menus
def top_menu():
    global ENDPOINT, TOKEN_MINT, TOKEN, EXCLUDED_PATH
    raw_data = get_accounts(ENDPOINT, TOKEN_MINT)['result']

    # Remove excluded
    if EXCLUDED_PATH != '':
        with open(EXCLUDED_PATH, 'r') as f:
            excluded = f.read().splitlines()
        data = [acc for acc in raw_data if extract_owner(acc) not in excluded]
    else:
        data = raw_data

    # Simplify the data with respect to the selected address-type
    data_list = map(lambda acc: [extract_owner(acc), extract_balance(acc)], data)

    # Eliminate duplicates
    data_dictionary = {}
    for address, balance in data_list:
        if address not in data_dictionary:
            data_dictionary[address] = float(balance)
        else:
            data_dictionary[address] += float(balance)

    # We need to convert this back to a list so we can sort it :(
    data_list = list(data_dictionary.items())

    print("\nSelect a filtering option for users:")
    menu_items = [
        f'Filter from all users with a minted address of {TOKEN}',
        f'Filter from users that have a positive balance of {TOKEN}',
        f'Filter from all users that have 0 {TOKEN} tokens'
    ]
    choice = display_menu(menu_items)

    if choice == 1:
        filtered_list = all_submenu(data_list)
    elif choice == 2:
        filtered_list = positive_balance_submenu(data_list)
    else:
        filtered_list = no_tokens_submenu(data_list)

    write_files(filtered_list, raw_data)

def positive_balance_submenu(data):
    menu_items = [
        f'Get all users',
        f'Get top N users by balance',
        f'Get bottom N users by balance',
        f'Get N random users',
        f'Get users with more than X tokens',
        f'Get users with more than or equal to X tokens',
        f'Get users with less than X and more than 0 tokens',
        f'Get users with less than X and more than or equal to Y tokens'
    ]
    choice = display_menu(menu_items)
    filtered = list(filter(lambda acc: acc[1] > 0, data))  
    if choice == 1:
        pass
    if choice == 2:
        n = input_number('> N=')
        filtered.sort(key=lambda acc: acc[1], reverse=True)
        filtered = filtered[:int(n)]
    if choice == 3:
        n = input_number('> N=')
        filtered.sort(key=lambda acc: acc[1], reverse=False)
        filtered = filtered[:int(n)]
    if choice == 4:
        n = input_number("> N=")
        try:
            filtered = random.sample(filtered, int(n))
        except ValueError:
            sys.exit('Failed to get random users, try using a smaller N value.')
    if choice == 5:
        x = input_number("> X=")
        filtered = list(filter(lambda acc: acc[1] > x, filtered)) 
    if choice == 6:
        x = input_number("> X=")
        filtered = list(filter(lambda acc: acc[1] >= x, filtered))   
    if choice == 7:
        x = input_number("> X=")
        filtered = list(filter(lambda acc: acc[1] < x
            and acc[1] > 0, filtered))  
    if choice == 8:
        x = input_number("> X=")
        y = input_number("> Y=")
        filtered = list(filter(lambda acc: acc[1] < x 
            and acc[1] >= y, filtered))

    filtered.sort(key=lambda acc: acc[1], reverse=True)
    return filtered

def all_submenu(data):
    menu_items = [
        f'Get all users that created a token address',
        f'Get N random users that created a token address'
    ]
    choice = display_menu(menu_items)
    if choice == 1:
        filtered = data
    else:
        n = input_number("N=")
        try:
            filtered = random.sample(data, int(n))
        except ValueError:
            sys.exit('Failed to get random users, try using a smaller N value.')
    # Sort by balance before writing
    filtered.sort(key=lambda acc: acc[1], reverse=True)
    return filtered

def no_tokens_submenu(data):
    menu_items = [
        f'Get all users with 0 tokens',
        f'Get N random users with 0 tokens'
    ]
    choice = display_menu(menu_items)
    if choice == 1:
        filtered = [acc for acc in data if acc[1] == 0]
    else:
        n = input_number("N=")
        filtered = [acc for acc in data if acc[1] == 0]
        try:
            filtered = random.sample(filtered, int(n))
        except ValueError:
            sys.exit('Failed to get random users, try using a smaller N value.')
    return filtered
#endregion

def get_token_name(mint):
    response = requests.get(token_repos['github_token_list'])
    data = json.loads(response.text)
    for token in data['tokens']:
        if token['address'] == mint:
            return True, token['symbol']
    return False, None

#region Argument parsing
parser = argparse.ArgumentParser(
    description='''Get a list of owner accounts or token addresses 
                   for a given SPL token mint address.'''
)
parser.add_argument(
    '-m',
    '--mint',
    required=False,
    default = '',
    help='Mint address of the SPL token'
)
parser.add_argument(
    '-t',
    '--address-type',
    dest="atype",
    choices={'owner', 'token'},
    default='',
    required=False,
    help='Select the address type used in the file {owner | token}.'
)
parser.add_argument(
    '-u',
    '--url',
    required=False,
    type=str,
    dest='url',
    default = '',
    help='URL of the Solana RPC endpoint.'
)
parser.add_argument(
    '-e',
    '--excluded',
    dest="excluded",
    required=False,
    default = '',
    help='Path to the file that contains all addresses that will be removed from the \
        final list. Each address should be in a seperate line, and the file must be \
        UTF-8 encoded.'
)
#endregion

# Constants
rpc_endpoints = {
    'mainnet': 'https://api.mainnet-beta.solana.com',
    'testnet': 'https://api.testnet.solana.com',
    'devnet': 'https://api.devnet.solana.com'
    }
token_repos = {
    'github_token_list': 'https://raw.githubusercontent.com/solana-labs/token-list/main/src/tokens/solana.tokenlist.json',
    'cdn_token_list': 'https://cdn.jsdelivr.net/gh/solana-labs/token-list@main/src/tokens/solana.tokenlist.json',
    }
ENDPOINT = ""
TOKEN_MINT = TOKEN = ""
ADDRESS_TYPE = ""
OUTPUT_FILE = 'address-list'

def main():
    global ENDPOINT, TOKEN_MINT, TOKEN, ADDRESS_TYPE, EXCLUDED_PATH

    args = parser.parse_args()
    ENDPOINT = args.url
    TOKEN_MINT = TOKEN = args.mint
    ADDRESS_TYPE = args.atype
    EXCLUDED_PATH = args.excluded

    if ENDPOINT == '':
        print("Select an endpoint ")
        choice = display_menu(list(rpc_endpoints.values()))
        ENDPOINT = rpc_endpoints[list(rpc_endpoints.keys())[int(choice)-1]]

    if TOKEN_MINT == '':
        TOKEN_MINT = input("\nEnter the token mint address:\n> ")
        TOKEN = TOKEN_MINT
    
    if ADDRESS_TYPE == '':
        print("\nSelect the address type.")
        choice = display_menu(['Owner account address', 'Token account address'])
        if choice == 1:
            ADDRESS_TYPE = 'owner'
        else:
            ADDRESS_TYPE = 'token'

    if EXCLUDED_PATH == '':
        print("\nNo exclusion file set, use option -e to set it.")

    if ENDPOINT == rpc_endpoints['mainnet']:
        print("\nMainnet endpoint, trying to fetch token name.")
        ok, name = get_token_name(TOKEN_MINT)
        if ok:
            TOKEN = name
            print(f'Token name: {TOKEN}')
        else:
            print('No token name found')

    top_menu()

if __name__ == "__main__":
    main()
