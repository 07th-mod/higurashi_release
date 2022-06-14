# higurashi_release

This repository contains scripts used for deploying the 07th-mod Higurashi mods.

## compile_higurashi_scripts.py

This python program compiles the scripts for each game. It is called by the Github Actions script in each higurashi repository which automatically creates a release with the compiled scripts, and is not intended to be called directly from the command line on your local computer. It should be called from the root of a higurashi mod github repo, as it will expect a folder called `Update` containing the scripts to be compiled.

### Prerequisites

The example github workflow file already has the prerequisites setup, but if you are running this manually you will need:

- Python 3.8 or higher
- Curl
- 7zip (script only works with `7z` at the moment, not `7za`)

## pr_workflow_example.yml

This is an example Github Actions workflow which downloads and calls the `compile_higurashi_scripts.py`, then creates a new pull request with the compiled scripts.

## Old deployment script

See the [old_scripts](https://github.com/07th-mod/higurashi_release/tree/old_scripts) branch for info and usage of the old, stand-alone script.
