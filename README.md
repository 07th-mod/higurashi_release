# higurashi_release

This repository contains scripts used for deploying the 07th-mod Higurashi mods.

## compile_higurashi_scripts.py

This python program builds the main .zip file containing scripts and other misc small files that we the Higurashi mods. It also pre-compiles the scripts (this step can be disabled).

It can either be called automatically by the Github Actions script in each higurashi repository, or manually on your computer (see below).

It should be called from the root of a higurashi mod github repo, as it will expect a folder called `Update` containing the scripts to be copied/compiled.

### Prerequisites

The example github workflow file already has the prerequisites setup, but if you are running this manually you will need these tools on your path:

- Python 3.8 or higher
- Curl (`curl`)
- 7zip (script only works with `7z` at the moment, not `7za`)

### Running on your computer (tested only on Windows)

1. Copy the file at `deploy_higurashi/deploy_higurashi.py` into the root of the repository (in this example, the `onikakushi` repository)
2. Run the command `py deploy_higurashi.py onikakushi --nocompile` (replace `onikakushi` with the name of the repository, such as `tsumihoroboshi`)

The `--nocompile` argument prevents compilation of script files. If you want to also compile scripts manually, contact drojf for instructions, or just manually run the game to compile scripts.

## pr_workflow_example.yml

This is an example Github Actions workflow which downloads and calls the `compile_higurashi_scripts.py`, then creates a new pull request with the compiled scripts.

## Old deployment script

See the [old_scripts](https://github.com/07th-mod/higurashi_release/tree/old_scripts) branch for info and usage of the old, stand-alone script.
