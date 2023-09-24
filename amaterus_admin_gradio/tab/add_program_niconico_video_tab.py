import json
import os
import re
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import gradio as gr
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel

from ..graphql_client import Client

JST = ZoneInfo("Asia/Tokyo")


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
        if urlp.netloc != "www.nicovideo.jp":
            raise Exception(f"Invalid URL: {niconico_video_url_or_id}")

        remote_niconico_content_id = os.path.basename(urlp.path)
        if len(remote_niconico_content_id) == 0:
            raise Exception(f"Invalid URL: {niconico_video_url_or_id}")
    else:
        if not re.match(r"^sm\d+$", niconico_video_url_or_id) and not re.match(
            r"^so\d+$", niconico_video_url_or_id
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


def create_add_program_niconico_video_tab(
    graphql_client: Client,
    logger: Logger,
) -> gr.Tab:
    initial_data = graphql_client.get_create_program_niconico_video_initial_data()

    with gr.Tab(label="プログラムにニコニコ動画の動画を追加") as tab:
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
                        value="ニコニコ動画 から動画情報を取得",
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

            response = graphql_client.get_program_project_list_by_project_id(
                project_id=project_id,
            )
            project = response.project
            if project is None:
                raise Exception("Project must not be None")

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
                video.thumbnail.url,
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
            response = graphql_client.create_program_niconico_video(
                project_id=project_id,
                program_id=program_id,
                person_id=person_id,
                start_time=datetime.fromisoformat(start_time_string),
                remote_niconico_content_id=remote_niconico_content_id,
                title=niconico_video_title,
                thumbnail_url=thumbnail_url,
                remote_niconico_account_id=remote_niconico_account_id,
                niconico_account_name=niconico_account_name,
            )
            program_niconico_video = response.program_niconico_video
            if program_niconico_video is None:
                raise Exception("program_niconico_video must not be None")

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
                thumbnail_url_text_field,
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
                thumbnail_url_text_field,
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

    return tab
