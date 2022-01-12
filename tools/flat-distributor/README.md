# Flat Distributor

## TLDR

Typical usage scenario would look something like the following:

1. **Get an address list** - using the [`address-fetcher`](../address-fetcher) tool, get the file with only the addresses as an input for `flat-distributor`. Note the address type that you used (owner or token).
2. **Setup config.env** - Edit the existing config example template by renaming it to `config.env` and adding the values for RPC API URL, token address and token decimal count.
3. **OPTIONAL: Run check-before** - `./flat-distributor.py check-before -a ADDRESS_LIST --address-type ADDRESS_TYPE -d DROP_AMOUNT`
4. **Connect your wallet to Solana CLI** - [Read this](https://docs.solana.com/wallet-guide/file-system-wallet) if you are not sure how to do this
5. **Run transfer** - `./flat-distributor.py transfer -a ADDRESS_LIST --drop DROP_AMOUNT`
6. **OPTIONAL: Run check-after** - `./flat-distributor.py check-after --address-type ADDRESS_TYPE --before-file before.csv`

You can use `-h` or `--help` to view the help text for each subcommand.

## Overview

`flat-distributor` is used to distribute a fixed amount of tokens to each recipient address from an input file. Subcommands included are:

- `transfer` mode for running distributions,
- `check-before` and
- `check-after` optional subcommands for checking whether recipients received the expected amount of tokens.

The actual distribution commands are ran synchronously, meaning each transaction awaits it's confirmation before moving on to the next one. This might be changed in the future.

Run the application with `python3`, or do `chmod +x flat-distributor.py` and run it with `./flat-distributor.py`.

All application modes share the same config file, an example of which can be found in this directory. This file should be placed in the same directory as the script, and renamed to `config.env`. The app can also be ran without the config, in which case log file locations are set to default (same as in the example config), and the user will be prompted for other variables (token address, token decimals, RPC API URL).

Example `config.env` file:

```
TOKEN_MINT=mx3edW3gRoM9J4sJKtuobQW3ZB1HeuZH8hQeH9HDkF3
TOKEN_DECIMALS=4
RPC_URL=https://api.devnet.solana.com
LOG_FOLDER_PREFIX=logs-
FULL_LOGS=detailed.log
SUCCESS_LOGS=success.log
FAILED_LOGS=failed.log
CANCELED_LOGS=canceled.log
UNCONFIRMED_LOGS=unconfirmed.log
```

## flat-distributor check-before

`check-before` can be used before a distribution, and will generate a CSV file containing the current balances for all recipients, and their expected balances after the distribution. The generated file will be named **before.csv** and is used as input for the `check-after` command.

It is required to specify the address type used in the address list file (`-t` or `--address-type {owner|token}`) and the amount of tokens that will be distributed.

### Usage:

`python3 flat-distributor.py check-before -a address-list.txt --address-type owner --drop 500`

![check-before-gif](https://github.com/praskoson/distribution-tools/blob/main/assets/gifs/check-before.gif)

## flat-distributor transfer

Distribute the tokens to all accounts on the given address list. You should use the same address list as the one in the `check-before` command.

## flat-distributor transferSol

Distribute the solana to all accounts on the given address list. You should use the same address list as the one in the `check-before` command.

You have to connect your wallet to the `solana` CLI tool. In case of a file-system wallet:
`solana config set --keypair /absolute/path/to/wallet.json`.
Also, consider the possible security issues when using file-system wallets ([Solana documentation](https://docs.solana.com/wallet-guide/cli)).

This command will generate multiple log files, the location and names of which can be set in the 'config.env' file.
Use the option`--non-interactive` to run the distribution in non-interactive mode, where each transaction doesn't have to be confirmed.

If sending tokens to owner accounts that do not have a minted associated token address, use `--fund-recipient` option. For accounts that are unfunded (i.e. have 0 SOL), use `--allow-unfunded-recipient`. Both options behave just as they do in the `spl-token transfer` command.

The `--retry-on-429` option will retry any transaction if it returns with a HTTP Too Many Requests error (429). This error is NOT a guarantee that the transaction didn't happen, so it can cause double transactions in rare cases, due to a bug in how `spl-token` handles this error. The default behaviour will treat this error as an unconfirmed transaction, so use it at your own risk.

Execution can be interrupted at any time with SIGINT (CTRL+C).

### Usage for SPL:

`python3 flat-distributor.py transfer -a address-list.txt --drop 500 --non-interactive`

### Usage for SOL:

`python3 flat-distributor.py transferSol -a addresses.txt --drop 1 --non-interactive --allow-unfunded-recipient`

![transfer](https://github.com/praskoson/distribution-tools/blob/main/assets/gifs/transfer.gif)

## flat-distributor check-after

`check-after` subcommand is used to ensure all recipients received the expected amount of tokens after a distribution. The input for it is the `before.csv` file generated by the `check-before` subcommand.

This mode also generates a CSV file that can then be read to compare the expected vs actual balances of all recipients.

Address type must be specified with the `-t` or `address-type` argument, where the type can be `owner` or `token`.

### Usage

`python3 flat-distributor.py check-after --address-type owner --before-file before.csv`

![check-after-gif](https://github.com/praskoson/distribution-tools/blob/main/assets/gifs/check-after.gif)
