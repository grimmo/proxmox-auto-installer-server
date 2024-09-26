import logging
import json
import pathlib
import requests

try:
    import tomlkit
    from aiohttp import web
except ImportError as e:
    import sys

    message = """Could not import required packages.
Please ensure you've installed all necessary packages first!

On Debian-based distributions, you should be able to install them via:

\tapt update
\tapt install python3-aiohttp python3-tomlkit"""

    print(message, file=sys.stderr)

    raise e

DEFAULT_ANSWER_FILE_PATH = pathlib.Path("./default.toml")
ANSWER_FILE_DIR = pathlib.Path("./answers/")

routes = web.RouteTableDef()


@routes.post("/answer")
async def answer(request: web.Request):
    try:
        request_data = json.loads(await request.text())
    except json.JSONDecodeError as e:
        return web.Response(
            status=500,
            text=f"Internal Server Error: failed to parse request contents: {e}",
        )

    logging.info(
        f"Request data for peer '{request.remote}':\n"
        f"{json.dumps(request_data, indent=1)}"
    )

    try:
        answer = create_answer(request_data)

        logging.info(f"Answer file for peer '{request.remote}':\n{answer}")

        return web.Response(text=answer)
    except Exception as e:
        logging.exception(f"failed to create answer: {e}")
        return web.Response(status=500, text=f"Internal Server Error: {e}")


def create_answer(request_data: dict) -> str:
    with open(DEFAULT_ANSWER_FILE_PATH) as file:
        answer = tomlkit.parse(file.read())

    for nic in request_data.get("network_interfaces", []):
        if "mac" not in nic:
            continue

        answer_mac = lookup_answer_for_mac(nic["mac"])
        if answer_mac is not None:
            answer = answer_mac

    return tomlkit.dumps(answer)


def lookup_answer_for_mac(mac: str) -> tomlkit.TOMLDocument | None:
    mac = mac.lower()

    for filename in ANSWER_FILE_DIR.glob("*.toml"):
        if mac in filename.name.lower():
            with open(filename) as mac_file:
                toml_data = tomlkit.parse(mac_file.read())
                toml_data_processed = process_custom_gh_username(toml_data)
                return toml_data_processed


def process_custom_gh_username(toml_data: tomlkit.TOMLDocument):
    if 'custom' in toml_data:
        toml_data['custom'] = tomlkit.table()

        if 'gh_username' in toml_data['custom']:

            # Extract the custom.gh_username string value
            gh_username = toml_data['custom']['gh_username']

            # HTTP GET request to fetch the keys
            keys_uri = f'https://github.com/{gh_username}.keys'
            response = requests.get(keys_uri)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Failed to fetch keys for {gh_username}. Response from GitHub: HTTP/{response.status_code}: {response.reason}"
                )
            keys = response.text.splitlines()
            # Append keys to global.root_ssh_keys
            if 'global' not in toml_data:
                toml_data['global'] = tomlkit.table()
            if 'root_ssh_keys' not in toml_data['global']:
                toml_data['global']['root_ssh_keys'] = tomlkit.array()
            toml_data['global']['root_ssh_keys'].extend(keys)
            # Remove custom/custom.gh_username
            del toml_data['custom']['gh_username']
            if not toml_data['custom']:
                del toml_data['custom']
    return toml_data


def assert_default_answer_file_exists():
    if not DEFAULT_ANSWER_FILE_PATH.exists():
        raise RuntimeError(
            f"Default answer file '{DEFAULT_ANSWER_FILE_PATH}' does not exist"
        )


def assert_default_answer_file_parseable():
    with open(DEFAULT_ANSWER_FILE_PATH) as file:
        try:
            tomlkit.parse(file.read())
        except Exception as e:
            raise RuntimeError(
                "Could not parse default answer file "
                f"'{DEFAULT_ANSWER_FILE_PATH}':\n{e}"
            )


def assert_answer_dir_exists():
    if not ANSWER_FILE_DIR.exists():
        raise RuntimeError(f"Answer file directory '{ANSWER_FILE_DIR}' does not exist")


if __name__ == "__main__":
    assert_default_answer_file_exists()
    assert_answer_dir_exists()
    assert_default_answer_file_parseable()

    app = web.Application()

    logging.basicConfig(level=logging.INFO)

    app.add_routes(routes)
    web.run_app(app, host="0.0.0.0", port=8000)
