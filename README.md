## Overview
This repository contains some of the scripts we have used for running our airdrop campaigns and other distributions. 

Initially, all of these were made purely for internal use and there were little to none UI considerations. However, as we decided to release these publicly, we have made some improvements on that front. We also created accompanying README documents that will hopefully allow you to use these in your own projects without issues.

Before using our scripts, we *strongly* recommend that you get to grips with the mechanics of using the tools on Solana's [testnet/devnet](https://docs.solana.com/cluster/rpc-endpoints) before doing any live mainnet transactions. Any mistakes you make there are completely harmless and will serve as a learning experience.


## Built with
Everything was written and tested on a Linux-based 64-bit system running Ubuntu 20.04 and Python 3.8.5. These tools should also work on other Linux distros and MacOS systems, but they will definitely not run on Windows. If you are on a Windows machine, we recommend looking into [WSL and WSL2](https://docs.microsoft.com/en-us/windows/wsl/install-win10).

All tools currently available are built with python3 and no external modules or packages, but they are dependant on having local installations of Solana CLI tools available on the PATH.

Below are links on the installation steps for `solana-cli` and `spl-token-cli` tools:
* [solana-cli](https://docs.solana.com/cli/install-solana-cli-tools)
* [spl-token-cli](https://spl.solana.com/token)

If you haven't used these tools before, we would recommend following along with the documentation, as it explains some basic usage scenarios that will familiarize you with them.

## Available tools
| Tools                    | Description                                      |
|--------------------------|:------------------------------------------------:|
| [address-fetcher](tools/address-fetcher)          | Fetching addresses of token holders and accounts |
| [flat-distributor](tools/flat-distributor)         | Distribute a fixed amount of tokens              |
| [proportional-distributor](tools/proportional-distributor) | Distribute a proportional amount of tokens       |

The accompanying README for each tool is located in its directory. Refer to them for usage examples.

## Issues
Feel free to report any issues you encounter while using these tools, or ideas you may have for improvement. We will try to help out with any problems when we can, but understand that these tools were made for private use and there might be usage scenarios that we never thought of or got around to testing.

## License
Distributed under the MIT License

## Links
* [Solana](https://solana.com/)
* [Solana Discord](https://discord.com/invite/pquxPsq)

Contact me on Discord: praskOo#0892
