# Movies From A Hat API

Movies from a Hat API Endpois

## Install

1. Create virtual environment and activate:

    `python -m venv .venv && source .venv/bin/activate`

2. Install package

    `pip install -e . -r requirements.txt`

    Or with optional dev dependencies:

    `pip install -e ".[dev]" -r requirements.txt -r requirements_dev.txt`

## Developer Notes

### Manage Dependencies

Dependencies are specified in `pyproject.toml` and managed with [pip-tools](https://github.com/jazzband/pip-tools/).

1. Install `pip-tools` (globally with [pipx](https://github.com/pypa/pipx) or in local virtual environment with pip)

2. Generate lock files:

    _base_

    ```sh
    pip-compile -o requirements.txt pyproject.toml
    ```

    _dev_

    ```sh
    pip-compile --extra dev -o requirements_dev.txt pyproject.toml
    ```

To upgrade a dependency, pass the `--upgrade-package` flag along with the name of the package, or to upgrade all packages, pass the `--upgrade` flag to the command.

More information at: <https://github.com/jazzband/pip-tools/>
