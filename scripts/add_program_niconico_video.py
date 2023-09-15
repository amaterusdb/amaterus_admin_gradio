import json
import logging
import os
import re
from argparse import ArgumentParser
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import gradio as gr
import requests
from amaterus_admin_gradio.utility.logging_utility import setup_logger
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pydantic import BaseModel

JST = ZoneInfo("Asia/Tokyo")


class AppConfig(BaseModel):
    log_level: int
    log_file: Path | None
    hasura_admin_secret: str | None


class LaunchAddProgramNiconicoVideoArgument(BaseModel):
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


class NiconicoVideoApiDataResponseVideoThumbnail(BaseModel):
    url: str


class NiconicoVideoApiDataResponseVideo(BaseModel):
    id: str
    title: str
    registeredAt: datetime
    thumbnail: NiconicoVideoApiDataResponseVideoThumbnail


class NiconicoVideoApiDataResponseOwner(BaseModel):
    id: int
    nickname: str


class NiconicoVideoApiDataResponse(BaseModel):
    video: NiconicoVideoApiDataResponseVideo
    owner: NiconicoVideoApiDataResponseOwner


def fetch_niconico_video_data(
    niconico_video_url_or_id: str,
) -> NiconicoVideoApiDataResponse:
    niconico_video_url_or_id = niconico_video_url_or_id.strip()

    remote_niconico_content_id: str | None = None
    if niconico_video_url_or_id.startswith("https://"):
        urlp = urlparse(niconico_video_url_or_id)
        if urlp.netloc != "www.nicovideo.com":
            raise Exception(f"Invalid URL: {niconico_video_url_or_id}")

        remote_niconico_content_id = os.path.basename(urlp.path)
        if len(remote_niconico_content_id) == 0:
            raise Exception(f"Invalid URL: {niconico_video_url_or_id}")
    else:
        if not re.match(r"sm\d+", niconico_video_url_or_id) or not re.match(
            r"so\d+", niconico_video_url_or_id
        ):
            raise Exception(f"Invalid Niconico video ID: {niconico_video_url_or_id}")

        remote_niconico_content_id = niconico_video_url_or_id

    res = requests.get(
        f"https://www.nicovideo.jp/watch/{remote_niconico_content_id}",
        headers={
            "User-Agent": (
                "facebookexternalhit/1.1;Googlebot/2.1;"
                "Amaterusbot (+https://amaterus.aoirint.com)"
            ),
        },
    )
    res.raise_for_status()

    bs = BeautifulSoup(res.text, "html5lib")
    js_initial_watch_data_tag = bs.find(id="js-initial-watch-data")

    api_data_json_text = js_initial_watch_data_tag.attrs.get("data-api-data")
    api_data_dict = json.loads(api_data_json_text)
    api_data_response = NiconicoVideoApiDataResponse.model_validate(api_data_dict)

    return api_data_response


class AddProgramNiconicoVideoResponseProgramNiconicoVideo(BaseModel):
    id: str


class AddProgramNiconicoVideoResponseData(BaseModel):
    program_niconico_video: AddProgramNiconicoVideoResponseProgramNiconicoVideo


class AddProgramNiconicoVideoResponse(BaseModel):
    data: AddProgramNiconicoVideoResponseData


def add_program_niconico_video(
    project_id: str,
    program_id: str,
    person_id: str,
    start_time: datetime,
    remote_niconico_content_id: str,
    title: str,
    thumbnail_url: str,
    remote_niconico_account_id: str,
    niconico_account_name: str,
    hasura_admin_secret: str,
) -> AddProgramNiconicoVideoResponseProgramNiconicoVideo:
    res = requests.post(
        "https://amaterus-hasura.aoirint.com/v1/graphql",
        headers={
            "X-Hasura-Admin-Secret": hasura_admin_secret,
        },
        json={
            "query": """
mutation A(
  $projectId: uuid!
  $programId: uuid!
  $personId: uuid!
  $remoteNiconicoContentId: String!
  $title: String!
  $startTime: timestamptz!
  $thumbnailUrl: String!
  $remoteNiconicoAccountId: String!
  $niconicoAccountName: String!
) {
    program_niconico_video: insert_program_niconico_videos_one(
        object: {
            program_id: $programId
            person_id: $personId
            niconico_video: {
                data: {
                    remote_niconico_content_id: $remoteNiconicoContentId
                    title: $title
                    start_time: $startTime
                    thumbnail_url: $thumbnailUrl
                    niconico_account: {
                        data: {
                            remote_niconico_account_id: $remoteNiconicoAccountId
                            name: $niconicoAccountName
                        }
                        on_conflict: {
                            constraint: niconico_accounts_remote_niconico_account_id_key
                            update_columns: [
                                name
                            ]
                        }
                    }
                    project_niconico_videos: {
                        data: {
                            project_id: $projectId
                        }
                        on_conflict: {
                            constraint: project_niconico_videos_project_id_niconico_video_id_key
                            update_columns: [
                                project_id
                                niconico_video_id
                            ]
                        }
                    }
                }
                on_conflict: {
                    constraint: niconico_videos_remote_niconico_content_id_key
                    update_columns: [
                        title
                        start_time
                        thumbnail_url
                    ]
                }
            }
        }
    ) {
        id
    }
}
""",
            "variables": {
                "projectId": project_id,
                "programId": program_id,
                "personId": person_id,
                "remoteNiconicoContentId": remote_niconico_content_id,
                "title": title,
                "startTime": start_time.isoformat(),
                "thumbnailUrl": thumbnail_url,
                "remoteNiconicoAccountId": remote_niconico_account_id,
                "niconicoAccountName": niconico_account_name,
            },
        },
    )
    print(res.json())
    res.raise_for_status()
    add_program_niconico_video_response = (
        AddProgramNiconicoVideoResponse.model_validate(res.json())
    )
    return add_program_niconico_video_response.data.program_niconico_video


def launch_add_program_niconico_video(
    args: LaunchAddProgramNiconicoVideoArgument,
    logger: Logger,
) -> None:
    hasura_admin_secret = args.hasura_admin_secret

    initial_data = fetch_initial_data()

    with gr.Blocks() as demo:
        gr.Markdown("# プログラムにニコニコ動画の動画を追加")
        with gr.Row():
            with gr.Column():
                with gr.Row():
                    clear_niconico_video_field_button = gr.ClearButton(
                        value="以下のフィールドをクリア",
                    )
                with gr.Row():
                    niconico_video_url_or_id_text_field = gr.Textbox(
                        label="ニコニコ動画の動画URL または ID",
                        interactive=True,
                    )
                with gr.Row():
                    fetch_niconico_video_data_button = gr.Button(
                        value="データベース または ニコニコ動画 から動画情報を取得",
                    )
                with gr.Row():
                    remote_niconico_content_id_text_field = gr.Textbox(
                        label="動画ID",
                        interactive=False,
                    )
                    niconico_video_title_text_field = gr.Textbox(
                        label="タイトル",
                        interactive=False,
                    )
                with gr.Row():
                    remote_niconico_account_id_text_field = gr.Textbox(
                        label="ニコニコ動画上のアカウントID",
                        interactive=False,
                    )
                    niconico_account_name_text_field = gr.Textbox(
                        label="アカウント名",
                        interactive=False,
                    )
                with gr.Row():
                    start_time_text_field = gr.Textbox(
                        label="投稿時間",
                        interactive=False,
                    )
                    thumbnail_url_text_field = gr.Textbox(
                        label="サムネイルURL",
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
                        label="投稿者",
                        interactive=True,
                        choices=list(
                            map(
                                lambda person: (person.name, person.id),
                                initial_data.person_list,
                            ),
                        ),
                    )
                with gr.Row():
                    add_niconico_video_button = gr.Button(
                        value="動画を追加",
                        variant="primary",
                    )
                with gr.Row():
                    added_program_niconico_video_id_text_field = gr.Textbox(
                        label="追加された動画のデータベース上のID",
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

        def handle_fetch_niconico_video_data_button_clicked(
            niconico_video_url_or_id: str | None,
        ) -> Any:
            if niconico_video_url_or_id is None or len(niconico_video_url_or_id) == 0:
                raise Exception("Invalid Niconico video URL or ID")

            niconico_video_api_response = fetch_niconico_video_data(
                niconico_video_url_or_id=niconico_video_url_or_id,
            )
            video = niconico_video_api_response.video
            owner = niconico_video_api_response.owner

            return [
                video.id,
                video.title,
                str(owner.id),
                owner.nickname,
                video.registeredAt.astimezone(JST).isoformat(),
            ]

        def handle_add_niconico_video_button_clicked(
            remote_niconico_content_id: str,
            niconico_video_title: str,
            remote_niconico_account_id: str,
            niconico_account_name: str,
            start_time_string: str,
            thumbnail_url: str,
            project_id: str,
            program_id: str,
            person_id: str,
        ) -> Any:
            program_niconico_video = add_program_niconico_video(
                project_id=project_id,
                program_id=program_id,
                person_id=person_id,
                start_time=datetime.fromisoformat(start_time_string),
                remote_niconico_content_id=remote_niconico_content_id,
                title=niconico_video_title,
                thumbnail_url=thumbnail_url,
                remote_niconico_account_id=remote_niconico_account_id,
                niconico_account_name=niconico_account_name,
                hasura_admin_secret=hasura_admin_secret,
            )

            return [
                program_niconico_video.id,
            ]

        clear_niconico_video_field_button.add(
            components=[
                niconico_video_url_or_id_text_field,
                remote_niconico_content_id_text_field,
                niconico_video_title_text_field,
                remote_niconico_account_id_text_field,
                niconico_account_name_text_field,
                start_time_text_field,
            ],
        )
        clear_project_field_button.add(
            components=[
                project_drop,
                program_drop,
                person_drop,
            ],
        )

        fetch_niconico_video_data_button.click(
            fn=handle_fetch_niconico_video_data_button_clicked,
            inputs=[niconico_video_url_or_id_text_field],
            outputs=[
                remote_niconico_content_id_text_field,
                niconico_video_title_text_field,
                remote_niconico_account_id_text_field,
                niconico_account_name_text_field,
                start_time_text_field,
            ],
        )

        add_niconico_video_button.click(
            fn=handle_add_niconico_video_button_clicked,
            inputs=[
                remote_niconico_content_id_text_field,
                niconico_video_title_text_field,
                remote_niconico_account_id_text_field,
                niconico_account_name_text_field,
                start_time_text_field,
                thumbnail_url_text_field,
                project_drop,
                program_drop,
                person_drop,
            ],
            outputs=[
                added_program_niconico_video_id_text_field,
            ],
        )

        project_drop.select(
            fn=handle_project_changed,
            inputs=project_drop,
            outputs=program_drop,
        )

    demo.launch()


def load_app_config_from_env() -> AppConfig:
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
        "--hasura_admin_secret",
        type=str,
        default=app_config.hasura_admin_secret,
        required=app_config.hasura_admin_secret is None,
    )
    args = parser.parse_args()

    log_level: int = args.log_level
    log_file: Path | None = args.log_file
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

    launch_add_program_niconico_video(
        args=LaunchAddProgramNiconicoVideoArgument(
            hasura_admin_secret=hasura_admin_secret,
        ),
        logger=logger,
    )


if __name__ == "__main__":
    main()
