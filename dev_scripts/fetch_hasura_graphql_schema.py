import os
import subprocess
from argparse import ArgumentParser
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel


class ScriptEnvironmentConfig(BaseModel):
    hasura_endpoint: str | None
    hasura_admin_secret: str | None


def load_script_environment_config() -> ScriptEnvironmentConfig:
    hasura_endpoint: str | None = os.environ.get(
        "AMATERUS_ADMIN_GRADIO_HASURA_ENDPOINT"
    )
    if hasura_endpoint is not None and len(hasura_endpoint) == 0:
        hasura_endpoint = None

    hasura_admin_secret = os.environ.get("AMATERUS_ADMIN_GRADIO_HASURA_ADMIN_SECRET")
    if hasura_admin_secret is not None and len(hasura_admin_secret) == 0:
        hasura_admin_secret = None

    return ScriptEnvironmentConfig(
        hasura_endpoint=hasura_endpoint,
        hasura_admin_secret=hasura_admin_secret,
    )


def check_gq_exists() -> bool:
    proc = subprocess.run(
        args=["gq", "--version"],
        stdout=subprocess.DEVNULL,
    )
    return proc.returncode == 0


def fetch_hasura_graphql_schema(
    hasura_endpoint: str,
    hasura_admin_secret: str,
) -> str:
    proc = subprocess.run(
        args=[
            "gq",
            hasura_endpoint,
            "--header",
            f"X-Hasura-Admin-Secret: {hasura_admin_secret}",
            "--introspect",
        ],
        capture_output=True,
    )

    return proc.stdout.decode(encoding="utf-8")


def main() -> None:
    load_dotenv()

    script_env_config = load_script_environment_config()

    parser = ArgumentParser()
    parser.add_argument(
        "--hasura_endpoint",
        type=str,
        default=script_env_config.hasura_endpoint,
        required=script_env_config.hasura_endpoint is None,
    )
    parser.add_argument(
        "--hasura_admin_secret",
        type=str,
        default=script_env_config.hasura_admin_secret,
        required=script_env_config.hasura_admin_secret is None,
    )
    parser.add_argument(
        "-o",
        "--output_file",
        type=Path,
        default="schema.graphql",
    )
    args = parser.parse_args()

    hasura_endpoint: str = args.hasura_endpoint
    hasura_admin_secret: str = args.hasura_admin_secret
    output_file: Path = args.output_file

    gq_exist = check_gq_exists()
    if not gq_exist:
        raise Exception(
            "gq (hasura/graphqurl) is not installed: npm install -g graphqurl"
        )

    hasura_graphql_schema_text = fetch_hasura_graphql_schema(
        hasura_endpoint=hasura_endpoint,
        hasura_admin_secret=hasura_admin_secret,
    )
    output_file.write_text(
        hasura_graphql_schema_text,
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
