import logging
import os
from argparse import ArgumentParser
from logging import Logger, getLogger
from pathlib import Path
from typing import Any

import gradio as gr
import requests
from amaterus_admin_gradio.utility.logging_utility import setup_logger
from dotenv import load_dotenv
from pydantic import BaseModel


class AppConfig(BaseModel):
    log_level: int
    log_file: Path | None
    youtube_api_key: str | None
    hasura_admin_secret: str | None


class LaunchAddYouTubeLiveArgument(BaseModel):
    youtube_api_key: str
    hasura_admin_secret: str


class InitialDataResponseProject(BaseModel):
    id: str
    name: str


class InitialDataResponseData(BaseModel):
    project_list: list[InitialDataResponseProject]


class InitialDataResponse(BaseModel):
    data: InitialDataResponseData


def fetch_initial_data() -> InitialDataResponseData:
    res = requests.post(
        "https://amaterus-hasura.aoirint.com/v1/graphql",
        json={
            "query": """
query {
    project_list: projects {
        id
        name
    }
}
""",
        },
    )
    res.raise_for_status()
    initial_data_response = InitialDataResponse.model_validate(res.json())
    return initial_data_response.data


class ProjectDataResponseProgram(BaseModel):
    id: str
    title: str


class ProjectDataResponseProgramProject(BaseModel):
    program: ProjectDataResponseProgram


class ProjectDataResponseProject(BaseModel):
    program_project_list: list[ProjectDataResponseProgramProject]


class ProjectDataResponseData(BaseModel):
    project: ProjectDataResponseProject


class ProjectDataResponse(BaseModel):
    data: ProjectDataResponseData


def fetch_project_data(
    project_id: str,
) -> ProjectDataResponseProject:
    res = requests.post(
        "https://amaterus-hasura.aoirint.com/v1/graphql",
        json={
            "query": """
query A(
    $projectId: uuid!
) {
    project: projects_by_pk(
        id: $projectId
    ) {
        program_project_list: program_projects(
            order_by: {
                program: {
                    start_time: desc
                }
            }
        ) {
            program {
                id
                title
            }
        }
    }
}
""",
            "variables": {
                "projectId": project_id,
            },
        },
    )
    res.raise_for_status()
    project_data_response = ProjectDataResponse.model_validate(res.json())
    return project_data_response.data.project


def launch_add_youtube_live(
    args: LaunchAddYouTubeLiveArgument,
    logger: Logger,
) -> None:
    logger.info("!!!")
    initial_data = fetch_initial_data()

    with gr.Blocks() as demo:
        gr.Markdown("Add YouTube Live")
        with gr.Row():
            project_drop = gr.Dropdown(
                choices=list(
                    map(
                        lambda project: (project.name, project.id),
                        initial_data.project_list,
                    ),
                ),
                label="Project",
            )
        with gr.Row():
            program_drop = gr.Dropdown(
                label="Program",
            )

        def project_changed(
            project_id: str,
        ) -> Any:
            if not project_id:
                return gr.Dropdown.update(
                    value=None,
                )

            project = fetch_project_data(
                project_id=project_id,
            )

            return gr.Dropdown.update(
                choices=list(
                    map(
                        lambda program_project: (
                            program_project.program.title,
                            program_project.program.id,
                        ),
                        project.program_project_list,
                    ),
                ),
            )

        project_drop.select(project_changed, inputs=project_drop, outputs=program_drop)

    demo.launch()


def load_app_config_from_env() -> AppConfig:
    youtube_api_key = os.environ.get("AMATERUS_ADMIN_GRADIO_YOUTUBE_API_KEY")
    if youtube_api_key is not None and len(youtube_api_key) == 0:
        youtube_api_key = None

    hasura_admin_secret = os.environ.get("AMATERUS_ADMIN_GRADIO_HASURA_ADMIN_SECRET")
    if hasura_admin_secret is not None and len(hasura_admin_secret) == 0:
        hasura_admin_secret = None

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
        hasura_admin_secret=hasura_admin_secret,
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
        "--hasura_admin_secret",
        type=str,
        default=app_config.hasura_admin_secret,
        required=app_config.hasura_admin_secret is None,
    )
    args = parser.parse_args()

    log_level: int = args.log_level
    log_file: Path | None = args.log_file
    youtube_api_key: str = args.youtube_api_key
    hasura_admin_secret: str = args.hasura_admin_secret

    logging.basicConfig(
        level=log_level,
    )

    logger = Logger(__file__)
    setup_logger(
        logger=logger,
        log_level=log_level,
        log_file=log_file,
    )

    launch_add_youtube_live(
        args=LaunchAddYouTubeLiveArgument(
            youtube_api_key=youtube_api_key,
            hasura_admin_secret=hasura_admin_secret,
        ),
        logger=logger,
    )


if __name__ == "__main__":
    main()
