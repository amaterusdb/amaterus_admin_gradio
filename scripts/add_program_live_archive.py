import logging
import os
from argparse import ArgumentParser
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

import gradio as gr
import requests
from amaterus_admin_gradio.utility.logging_utility import setup_logger
from dotenv import load_dotenv
from pydantic import BaseModel

JST = ZoneInfo("Asia/Tokyo")


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


class InitialDataResponsePerson(BaseModel):
    id: str
    name: str


class InitialDataResponseData(BaseModel):
    project_list: list[InitialDataResponseProject]
    person_list: list[InitialDataResponsePerson]


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

    person_list: persons {
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


class YoutubeApiVideoResponseItemSnippet(BaseModel):
    title: str
    channelId: str
    channelTitle: str
    liveBroadcastContent: str


class YoutubeApiVideoResponseLiveStreamingDetails(BaseModel):
    actualStartTime: datetime | None = None
    actualEndTime: datetime | None = None


class YoutubeApiVideoResponseItem(BaseModel):
    id: str
    snippet: YoutubeApiVideoResponseItemSnippet | None = None
    liveStreamingDetails: YoutubeApiVideoResponseLiveStreamingDetails | None = None


class YoutubeApiVideoResponse(BaseModel):
    items: list[YoutubeApiVideoResponseItem]


def fetch_youtube_live_data(
    youtube_live_url_or_id: str,
    youtube_api_key: str,
) -> YoutubeApiVideoResponse:
    youtube_live_url_or_id = youtube_live_url_or_id.strip()

    remote_youtube_video_id: str | None = None
    if youtube_live_url_or_id.startswith("https://"):
        urlp = urlparse(youtube_live_url_or_id)
        if urlp.netloc != "www.youtube.com":
            raise Exception(f"Invalid URL: {youtube_live_url_or_id}")

        remote_youtube_video_id_param_list = parse_qs(urlp.query).get("v")
        if (
            remote_youtube_video_id_param_list is None
            or len(remote_youtube_video_id_param_list) == 0
        ):
            raise Exception(f"Invalid URL: {youtube_live_url_or_id}")

        remote_youtube_video_id = remote_youtube_video_id_param_list[0]
    else:
        if "," in youtube_live_url_or_id:
            raise Exception(f"Invalid YouTube video ID: {youtube_live_url_or_id}")

        remote_youtube_video_id = youtube_live_url_or_id

    res = requests.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={
            "key": youtube_api_key,
            "part": "id,snippet,liveStreamingDetails",
            "id": remote_youtube_video_id,
        },
    )
    res.raise_for_status()
    ytlive_api_video_response = YoutubeApiVideoResponse.model_validate(res.json())
    return ytlive_api_video_response


def launch_add_youtube_live(
    args: LaunchAddYouTubeLiveArgument,
    logger: Logger,
) -> None:
    youtube_api_key = args.youtube_api_key

    initial_data = fetch_initial_data()

    with gr.Blocks() as demo:
        gr.Markdown("# プログラムに配信アーカイブを追加")
        with gr.Row():
            with gr.Column():
                with gr.Row():
                    clear_youtube_live_field_button = gr.ClearButton(
                        value="以下のフィールドをクリア",
                    )
                with gr.Row():
                    youtube_live_url_or_id_text_field = gr.Textbox(
                        label="YouTube Live URL または ID",
                        interactive=True,
                    )
                with gr.Row():
                    fetch_youtube_live_data_button = gr.Button(
                        value="データベース または YouTube から配信情報を取得",
                    )
                with gr.Row():
                    source_text_field = gr.Textbox(
                        label="情報源",
                        interactive=False,
                    )
                    youtube_live_id_text_field = gr.Textbox(
                        label="データベース上のID",
                        interactive=False,
                    )
                with gr.Row():
                    youtube_live_title_text_field = gr.Textbox(
                        label="タイトル",
                        interactive=False,
                    )
                with gr.Row():
                    remote_youtube_channel_id_text_field = gr.Textbox(
                        label="YouTube上のチャンネルID",
                        interactive=False,
                    )
                    youtube_channel_id_text_field = gr.Textbox(
                        label="データベース上のチャンネルID",
                        interactive=False,
                    )
                with gr.Row():
                    youtube_channel_name_text_field = gr.Textbox(
                        label="チャンネル名",
                        interactive=False,
                    )
                with gr.Row():
                    start_time_text_field = gr.Textbox(
                        label="開始時間",
                        interactive=False,
                    )
                    end_time_text_field = gr.Textbox(
                        label="終了時間",
                        interactive=False,
                    )

            with gr.Column():
                with gr.Row():
                    clear_project_field_button = gr.ClearButton(
                        value="以下のフィールドをクリア",
                    )
                with gr.Row():
                    project_drop = gr.Dropdown(
                        label="プロジェクト",
                        interactive=True,
                        choices=list(
                            map(
                                lambda project: (project.name, project.id),
                                initial_data.project_list,
                            ),
                        ),
                    )
                with gr.Row():
                    program_drop = gr.Dropdown(
                        label="プログラム",
                        interactive=True,
                    )
                with gr.Row():
                    person_drop = gr.Dropdown(
                        label="放送者",
                        interactive=True,
                        choices=list(
                            map(
                                lambda person: (person.name, person.id),
                                initial_data.person_list,
                            ),
                        ),
                    )
                with gr.Row():
                    add_live_archive_button = gr.Button(
                        value="配信アーカイブを追加",
                        variant="primary",
                    )
                with gr.Row():
                    added_youtube_live_id_text_field = gr.Textbox(
                        label="追加された配信アーカイブのデータベース上のID",
                        interactive=False,
                    )

        def handle_project_changed(
            project_id: str,
        ) -> Any:
            if project_id is None or len(project_id) == 0:
                return gr.Dropdown.update(
                    value=None,
                    choices=None,
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

        def handle_fetch_youtube_live_data_button_clicked(
            youtube_live_url_or_id: str | None,
        ) -> Any:
            if youtube_live_url_or_id is None or len(youtube_live_url_or_id) == 0:
                raise Exception("Invalid YouTube live URL or ID")

            youtube_api_video_response = fetch_youtube_live_data(
                youtube_live_url_or_id=youtube_live_url_or_id,
                youtube_api_key=youtube_api_key,
            )
            items = youtube_api_video_response.items
            if len(items) == 0:
                raise Exception("Invalid YouTube API response")

            item = items[0]

            youtube_live_title = ""
            remote_youtube_channel_id = ""
            youtube_channel_title = ""
            if item.snippet is not None:
                youtube_live_title = item.snippet.title
                remote_youtube_channel_id = item.snippet.channelId
                youtube_channel_title = item.snippet.channelTitle

            youtube_live_start_time = ""
            youtube_live_end_time = ""
            if item.liveStreamingDetails is not None:
                if item.liveStreamingDetails.actualStartTime is not None:
                    youtube_live_start_time = (
                        item.liveStreamingDetails.actualStartTime.astimezone(
                            JST
                        ).isoformat()
                    )

                if item.liveStreamingDetails.actualEndTime is not None:
                    youtube_live_end_time = (
                        item.liveStreamingDetails.actualEndTime.astimezone(
                            JST
                        ).isoformat()
                    )

            return [
                "YouTube",
                item.id,
                youtube_live_title,
                remote_youtube_channel_id,
                "",
                youtube_channel_title,
                youtube_live_start_time,
                youtube_live_end_time,
            ]

        def handle_add_live_archive_button_clicked() -> Any:
            pass

        clear_youtube_live_field_button.add(
            components=[
                youtube_live_url_or_id_text_field,
                source_text_field,
                youtube_live_title_text_field,
                youtube_live_id_text_field,
                remote_youtube_channel_id_text_field,
                youtube_channel_id_text_field,
                start_time_text_field,
                end_time_text_field,
            ],
        )
        clear_project_field_button.add(
            components=[
                project_drop,
                program_drop,
                person_drop,
            ],
        )

        fetch_youtube_live_data_button.click(
            fn=handle_fetch_youtube_live_data_button_clicked,
            inputs=[youtube_live_url_or_id_text_field],
            outputs=[
                source_text_field,
                youtube_live_id_text_field,
                youtube_live_title_text_field,
                remote_youtube_channel_id_text_field,
                youtube_channel_id_text_field,
                youtube_channel_name_text_field,
                start_time_text_field,
                end_time_text_field,
            ],
        )

        add_live_archive_button.click(
            fn=handle_add_live_archive_button_clicked,
        )

        project_drop.select(
            fn=handle_project_changed,
            inputs=project_drop,
            outputs=program_drop,
        )

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
