# Crowdsale Example

This repository contains an example that shows how a crowd-sale might be structured. note that the example uses insecure randomness but it could be replaced with a commit-reveal scheme. 

> DISCLAIMER: the contracts were not tested properly and are solely meant for illustrative purposes.

## Requirements

This repo uses `uv` and `python3.13` furthermore `pytezos` might require system libraries to be installed.

If everything is installed a simple

```
uv sync
```

should do the trick.
Then either install the package in editable mode:

```
uv pip install -e .
```

or add this directory to your `PYTHONPATH`.

Then you need to add a deployer secret key to your environment variables or .env file.

e.g.:
```
TZ_SECRET_KEY=edsk3a1oJvYMi4YwdFJGgmE9bN5yqEy7HL3e4TryyeAS62xTfgMcUj
```

> NOTE: Don't use the secret key of your main wallet. Instead create a new one and fund it from your main wallet. Then (if applicable) switch admin rights over to your main wallet programatically after deployment.

## Compliation

Smartpy stores `test scenario` output in folders named after the scenarios.
To compile we can set up test scenarios that simply instantiate the contract.

See `contracts/example_contracts.py`, specifically the `compile_all` function.

```
python scripts/compile.py
```

## Deployment

Deployment is handled via `pytezos`:

1. Load the compiled *.contract.tz files
2. Dynamically construct the initial storage
3. Originate the contracts
4. Call entrypoints to wire the contracts together

Run:
```
python scripts/deploy.py
```