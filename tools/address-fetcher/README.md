# Address Fetcher

## Overview
`address-fetcher` gets a list of owner addresses that own a specified token account, or a list of token accounts that belong to a specified token.

The app will create an output folder in the same directory that it is ran from, using the name of the token (if it is available), or the first 5 characters of the address, and the current UTC time. This folder represents a snapshot of when the address list was collected.

## Outputs
The folder will contain a raw JSON file that was used to get the token account info from the Solana RPC API, a list of addresses seperated by new lines and a list of addresses and their corresponding balances for the given token, seperated by a comma. 

The type of addresses that will be written to output files is selected with the option `--address-type`. Possible choices are `token` and `owner`.

## Usage

The available arguments are:
```
  -m MINT, --mint MINT  Mint address of the SPL token
  --address-type {owner,token}  Select the address type used in the file (owner | token).
  -u URL, --url URL  URL of the Solana RPC endpoint.
  -e EXCLUDED, --excluded EXCLUDED  Path to the file that contains all addresses that will be removed from the final list. Each address should be in a seperate line, and the file must be UTF-8 encoded.
  ```

All of the arguments are optional, and if they are not set, the user will be prompted to enter them interactively.

### Usage example:
Run the application with `python3`, or use `chmod +x address-fetcher.py` and run it with `./address-fetcher.py`.
```
python3 address-fetcher.py
```
```
./address-fetcher.py -m 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU -u https://api.mainnet-beta.solana.com -e excluded-addresses.txt
```

![address-fetcher-gif](https://github.com/praskoson/distribution-tools/blob/main/assets/gifs/address-fetcher.gif)

## Issues
When using `token` address types, a single account owner can have multiple token accounts. Currently, we don't differentiate multiple token accounts belonging to the same owner. When using `owner` addresses, this is not an issue, as the app will only try to use the associated token account.
