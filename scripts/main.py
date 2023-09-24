import logging
import os
from argparse import ArgumentParser
from logging import Logger
from pathlib import Path

import gradio as gr
from amaterus_admin_gradio.tab import (
    create_add_program_live_archive_tab,
    create_add_program_niconico_video_tab,
    create_add_program_tab,
    create_add_program_twitter_announcement_tab,
    create_add_program_youtube_video_live_archive_tab,
)
from amaterus_admin_gradio.utility.logging_utility import setup_logger
from dotenv import load_dotenv
from pydantic import BaseModel


class LaunchGradioArgument(BaseModel):
    youtube_api_key: str
    hasura_endpoint: str
    hasura_admin_secret: str
    basic_auth_username: str | None
    basic_auth_password: str | None


class AppConfig(BaseModel):
    log_level: int
    log_file: Path | None
    youtube_api_key: str | None
    hasura_endpoint: str | None
    hasura_admin_secret: str | None
    basic_auth_username: str | None
    basic_auth_password: str | None


def launch_gradio(
    args: LaunchGradioArgument,
    logger: Logger,
) -> None:
    hasura_endpoint = args.hasura_endpoint
    hasura_admin_secret = args.hasura_admin_secret
    youtube_api_key = args.youtube_api_key
    basic_auth_username = args.basic_auth_username
    basic_auth_password = args.basic_auth_password

    auth: tuple[str, str] | None = None
    if basic_auth_username is not None or basic_auth_password is not None:
        if basic_auth_username is None or basic_auth_password is None:
            raise Exception(
                "Basic authentication is enabled but"
                "one of (basic_auth_username, basic_auth_password) is None. "
                "Set both values."
            )

        auth = (
            basic_auth_username,
            basic_auth_password,
        )

    with gr.Blocks(
        title="Amaterus Admin Gradio",
    ) as demo:
        create_add_program_tab(
            hasura_endpoint=hasura_endpoint,
            hasura_admin_secret=hasura_admin_secret,
            logger=logger,
        )
        create_add_program_twitter_announcement_tab(
            hasura_endpoint=hasura_endpoint,
            hasura_admin_secret=hasura_admin_secret,
            logger=logger,
        )
        create_add_program_live_archive_tab(
            hasura_endpoint=hasura_endpoint,
            hasura_admin_secret=hasura_admin_secret,
            youtube_api_key=youtube_api_key,
            logger=logger,
        )
        create_add_program_youtube_video_live_archive_tab(
            hasura_endpoint=hasura_endpoint,
            hasura_admin_secret=hasura_admin_secret,
            youtube_api_key=youtube_api_key,
            logger=logger,
        )
        create_add_program_niconico_video_tab(
            hasura_endpoint=hasura_endpoint,
            hasura_admin_secret=hasura_admin_secret,
            logger=logger,
        )

    demo.launch(
        auth=auth,
    )


def load_app_config_from_env() -> AppConfig:
    youtube_api_key = os.environ.get("AMATERUS_ADMIN_GRADIO_YOUTUBE_API_KEY")
    if youtube_api_key is not None and len(youtube_api_key) == 0:
        youtube_api_key = None

    hasura_endpoint = os.environ.get("AMATERUS_ADMIN_GRADIO_HASURA_ENDPOINT")
    if hasura_endpoint is not None and len(hasura_endpoint) == 0:
        hasura_endpoint = None

    hasura_admin_secret = os.environ.get("AMATERUS_ADMIN_GRADIO_HASURA_ADMIN_SECRET")
    if hasura_admin_secret is not None and len(hasura_admin_secret) == 0:
        hasura_admin_secret = None

    basic_auth_username = os.environ.get("AMATERUS_ADMIN_GRADIO_BASIC_AUTH_USERNAME")
    if basic_auth_username is not None and len(basic_auth_username) == 0:
        basic_auth_username = None

    basic_auth_password = os.environ.get("AMATERUS_ADMIN_GRADIO_BASIC_AUTH_PASSWORD")
    if basic_auth_password is not None and len(basic_auth_password) == 0:
        basic_auth_password = None

    log_level_string = os.environ.get("AMATERUS_ADMIN_GRADIO_LOG_LEVEL")
    log_level = logging.INFO
    if log_level_string is not None and len(log_level_string) > 0:
        log_level = int(log_level_string)

    log_file_string = os.environ.get("AMATERUS_ADMIN_GRADIO_LOG_FILE")
    log_file: Path | None = None
    if log_file_string is not None and len(log_file_string) > 0:
        log_file = Path(log_file_string)

    return AppConfig(
        youtube_api_key=youtube_api_key,
        hasura_endpoint=hasura_endpoint,
        hasura_admin_secret=hasura_admin_secret,
        basic_auth_username=basic_auth_username,
        basic_auth_password=basic_auth_password,
        log_level=log_level,
        log_file=log_file,
    )


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument(
        "--env_file",
        type=Path,
    )
    pre_args, _ = parser.parse_known_args()

    env_file: Path | None = pre_args.env_file
    if env_file is not None:
        load_dotenv(env_file)

    app_config = load_app_config_from_env()
    parser.add_argument(
        "--log_level",
        type=int,
        default=app_config.log_level,
    )
    parser.add_argument(
        "--log_file",
        type=Path,
        default=app_config.log_file,
    )
    parser.add_argument(
        "--youtube_api_key",
        type=str,
        default=app_config.youtube_api_key,
        required=app_config.youtube_api_key is None,
    )
    parser.add_argument(
        "--hasura_endpoint",
        type=str,
        default=app_config.hasura_endpoint,
        required=app_config.hasura_endpoint is None,
    )
    parser.add_argument(
        "--hasura_admin_secret",
        type=str,
        default=app_config.hasura_admin_secret,
        required=app_config.hasura_admin_secret is None,
    )
    parser.add_argument(
        "--basic_auth_username",
        type=str,
        default=app_config.basic_auth_username,
    )
    parser.add_argument(
        "--basic_auth_password",
        type=str,
        default=app_config.basic_auth_password,
    )

    args = parser.parse_args()

    log_level: int = args.log_level
    log_file: Path | None = args.log_file
    youtube_api_key: str = args.youtube_api_key
    hasura_endpoint: str = args.hasura_endpoint
    hasura_admin_secret: str = args.hasura_admin_secret
    basic_auth_username: str | None = args.basic_auth_username
    basic_auth_password: str | None = args.basic_auth_password

    logging.basicConfig(
        level=log_level,
    )

    logger = Logger(__file__)
    setup_logger(
        logger=logger,
        log_level=log_level,
        log_file=log_file,
    )

    launch_gradio(
        args=LaunchGradioArgument(
            youtube_api_key=youtube_api_key,
            hasura_endpoint=hasura_endpoint,
            hasura_admin_secret=hasura_admin_secret,
            basic_auth_username=basic_auth_username,
            basic_auth_password=basic_auth_password,
        ),
        logger=logger,
    )


if __name__ == "__main__":
    main()
