# Proportional Distributor

## TLDR
Typical usage scenario would look something like the following:
1. **Get an address list** - using the [`address-fetcher`](../address-fetcher) tool, get the file with addresses and balances (`address-list-balance.txt`). Use it as input addresses for `proportional-distributor`. Note the address type that you used (owner or token).
2. **Setup config.env** - Edit the existing config example template by renaming it to `config.env` and adding the values for RPC API URL, token address and token decimal count.
3. **OPTIONAL: Run check-before** - `./proportional-distributor.py check-before -a ADDRESS_LIST --address-type ADDRESS_TYPE -d DROP_AMOUNT`
4. **Connect your wallet to Solana CLI** - [Read this](https://docs.solana.com/wallet-guide/file-system-wallet) if you are not sure how to do this
5. **Run transfer** - `./proportional-distributor.py transfer -a ADDRESS_LIST --drop DROP_AMOUNT`
6. **OPTIONAL: Run check-after** - `./proportional-distributor.py check-after --address-type ADDRESS_TYPE --before-file before.csv` 

You can use `-h` or `--help` to view the help text for each subcommand.

## Overview

Distribute a proportional amount of tokens to each recipient, based on the amount of tokens they are currently holding.
The proportional formula is the following:
```
proportional_factor = total_distributed_tokens / sum_of_all_balances
amount = balance * proportional_factor
Each user receives an amount of tokens equal to their balance multiplied by the proportional factor.
```

Run the application with `python3`, or do `chmod +x proportional-distributor.py` and run it with `./proportional-distributor.py`.

## Under construction
This README file is still under construction, but you can follow the same guidlines as in the `flat-distributor` readme.

Note that you should use an address list that also containes the balances of each address, seperated by a comma.

Example of an address-list-balances.txt file:
```
Ht7nUwAUQwGBQMKabRKMcQUjJa2tFQawp11t7Vm6hKFW,178.9117
6yGiNerjCZsexyExvwcUTTscKhaHGsftb3ssutcHA7Vb,176.3158
GkJoR3G44KksKaBGrSJcTPhuPVVCg3a9kKUuf1oFNEuT,154.4178
...
```
