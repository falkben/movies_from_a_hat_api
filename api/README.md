# API

## Install

1. Create virtual environment and activate:

    `python -m venv .venv && source .venv/bin/activate`

2. Install package

    `pip install -e . -r requirements.txt`

    Or with optional dev dependencies:

    `pip install -e ".[dev]" -r requirements.txt -r requirements_dev.txt`

## API Key for TMDB

1. Register for and verify an [account](https://www.themoviedb.org/account/signup).
2. [Log into](https://www.themoviedb.org/login) your account.
3. Select the [API section](https://www.themoviedb.org/settings/api) on account settings.
4. Click on the link to generate a new API key and follow the instructions.

Copy the `.env.example` into a new `.env` file

Edit the file and enter your API token.

## Run

```sh
uvicorn app.api:app --reload
```

## Developer Notes

### Manage Dependencies

Dependencies are specified in `pyproject.toml` and managed with [pip-tools](https://github.com/jazzband/pip-tools/).

1. Install `pip-tools` (globally with [pipx](https://github.com/pypa/pipx) or in local virtual environment with pip)

2. Generate lock files:

    ```sh
    pip-compile --output-file=requirements.txt pyproject.toml --quiet && pip-compile --extra=dev --output-file=requirements_dev.txt pyproject.toml --quiet
    ```

To upgrade a dependency, pass the `--upgrade-package` flag along with the name of the package, or to upgrade all packages, pass the `--upgrade` flag to the command.

More information at: <https://github.com/jazzband/pip-tools/>
