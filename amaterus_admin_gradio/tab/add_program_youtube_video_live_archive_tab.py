from datetime import datetime
from logging import Logger
from typing import Any
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

import gradio as gr
import requests
from pydantic import BaseModel

JST = ZoneInfo("Asia/Tokyo")


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


def fetch_initial_data(
    hasura_endpoint: str,
) -> InitialDataResponseData:
    res = requests.post(
        hasura_endpoint,
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
    hasura_endpoint: str,
) -> ProjectDataResponseProject:
    res = requests.post(
        hasura_endpoint,
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
    publishedAt: datetime


class YoutubeApiVideoResponseItem(BaseModel):
    id: str
    snippet: YoutubeApiVideoResponseItemSnippet | None = None


class YoutubeApiVideoResponse(BaseModel):
    items: list[YoutubeApiVideoResponseItem]


def fetch_youtube_video_data(
    youtube_video_url_or_id: str,
    youtube_api_key: str,
) -> YoutubeApiVideoResponse:
    youtube_video_url_or_id = youtube_video_url_or_id.strip()

    remote_youtube_video_id: str | None = None
    if youtube_video_url_or_id.startswith("https://"):
        urlp = urlparse(youtube_video_url_or_id)
        if urlp.netloc != "www.youtube.com":
            raise Exception(f"Invalid URL: {youtube_video_url_or_id}")

        remote_youtube_video_id_param_list = parse_qs(urlp.query).get("v")
        if (
            remote_youtube_video_id_param_list is None
            or len(remote_youtube_video_id_param_list) == 0
        ):
            raise Exception(f"Invalid URL: {youtube_video_url_or_id}")

        remote_youtube_video_id = remote_youtube_video_id_param_list[0]
    else:
        if "," in youtube_video_url_or_id:
            raise Exception(f"Invalid YouTube video ID: {youtube_video_url_or_id}")

        remote_youtube_video_id = youtube_video_url_or_id

    res = requests.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={
            "key": youtube_api_key,
            "part": "id,snippet,liveStreamingDetails",
            "id": remote_youtube_video_id,
        },
    )
    res.raise_for_status()
    youtube_api_video_response = YoutubeApiVideoResponse.model_validate(res.json())
    return youtube_api_video_response


class AddProgramLiveArchiveResponseProgramLiveArchive(BaseModel):
    id: str


class AddProgramLiveArchiveResponseData(BaseModel):
    program_live_archive: AddProgramLiveArchiveResponseProgramLiveArchive


class AddProgramLiveArchiveResponse(BaseModel):
    data: AddProgramLiveArchiveResponseData


def add_program_youtube_video_live_archive(
    program_id: str,
    person_id: str,
    post_time: datetime,
    start_time: datetime,
    end_time: datetime,
    remote_youtube_video_id: str,
    title: str,
    is_premiere: bool,
    remote_youtube_channel_id: str,
    youtube_channel_name: str,
    hasura_endpoint: str,
    hasura_admin_secret: str,
) -> AddProgramLiveArchiveResponseProgramLiveArchive:
    res = requests.post(
        hasura_endpoint,
        headers={
            "X-Hasura-Admin-Secret": hasura_admin_secret,
        },
        json={
            "query": """
mutation A(
  $programId: uuid!
  $personId: uuid!
  $postTime: timestamptz!
  $startTime: timestamptz!
  $endTime: timestamptz!
  $remoteYoutubeVideoId: String!
  $title: String!
  $isPremiere: Boolean!
  $remoteYoutubeChannelId: String!
  $youtubeChannelName: String!
) {
    program_live_archive: insert_program_live_archives_one(
        object: {
            program_id: $programId
            person_id: $personId
            start_time: $startTime
            end_time: $endTime
            youtube_video: {
                data: {
                    remote_youtube_video_id: $remoteYoutubeVideoId
                    title: $title
                    post_time: $postTime
                    is_premiere: $isPremiere
                    youtube_channel: {
                        data: {
                            remote_youtube_channel_id: $remoteYoutubeChannelId
                            name: $youtubeChannelName
                        }
                        on_conflict: {
                            constraint: youtube_channels_youtube_channel_id_key
                            update_columns: [
                                name
                            ]
                        }
                    }
                }
                on_conflict: {
                    constraint: youtube_videos_remote_youtube_video_id_key
                    update_columns: [
                        title
                        post_time
                        is_premiere
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
                "programId": program_id,
                "personId": person_id,
                "postTime": post_time.isoformat() if post_time is not None else None,
                "startTime": start_time.isoformat() if start_time is not None else None,
                "endTime": end_time.isoformat() if end_time is not None else None,
                "remoteYoutubeVideoId": remote_youtube_video_id,
                "title": title,
                "isPremiere": is_premiere,
                "remoteYoutubeChannelId": remote_youtube_channel_id,
                "youtubeChannelName": youtube_channel_name,
            },
        },
    )
    print(res.json())
    res.raise_for_status()
    add_program_live_archive_response = AddProgramLiveArchiveResponse.model_validate(
        res.json()
    )
    return add_program_live_archive_response.data.program_live_archive


def create_add_program_youtube_video_live_archive_tab(
    youtube_api_key: str,
    hasura_endpoint: str,
    hasura_admin_secret: str,
    logger: Logger,
) -> gr.Tab:
    initial_data = fetch_initial_data(
        hasura_endpoint=hasura_endpoint,
    )

    with gr.Tab(label="プログラムに動画として投稿された配信アーカイブを追加") as tab:
        gr.Markdown("# プログラムに動画として投稿された配信アーカイブを追加")
        with gr.Row():
            with gr.Column():
                with gr.Row():
                    clear_youtube_live_field_button = gr.ClearButton(
                        value="以下のフィールドをクリア",
                    )
                with gr.Row():
                    youtube_live_url_or_id_text_field = gr.Textbox(
                        label="YouTube Video URL または ID",
                        interactive=True,
                    )
                with gr.Row():
                    fetch_youtube_video_data_button = gr.Button(
                        value="YouTube から配信情報を取得",
                    )
                with gr.Row():
                    remote_youtube_video_id_text_field = gr.Textbox(
                        label="YouTube Video ID",
                        interactive=False,
                    )
                    youtube_live_title_text_field = gr.Textbox(
                        label="タイトル",
                        interactive=False,
                    )
                with gr.Row():
                    remote_youtube_channel_id_text_field = gr.Textbox(
                        label="YouTube上のチャンネルID",
                        interactive=False,
                    )
                    youtube_channel_name_text_field = gr.Textbox(
                        label="チャンネル名",
                        interactive=False,
                    )
                with gr.Row():
                    post_time_text_field = gr.Textbox(
                        label="投稿時間",
                        interactive=True,
                    )

            with gr.Column():
                with gr.Row():
                    clear_time_field_button = gr.ClearButton(
                        value="以下のフィールドをクリア",
                    )
                with gr.Row():
                    is_premiere_checkbox_field = gr.Checkbox(label="プレミア公開?")
                with gr.Row():
                    start_time_text_field = gr.Textbox(
                        label="開始時間",
                        interactive=True,
                    )
                    end_time_text_field = gr.Textbox(
                        label="終了時間",
                        interactive=True,
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
                    add_program_youtube_video_live_archive_button = gr.Button(
                        value="配信アーカイブを追加",
                        variant="primary",
                    )
                with gr.Row():
                    added_program_live_archive_id_text_field = gr.Textbox(
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
                hasura_endpoint=hasura_endpoint,
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

        def handle_fetch_youtube_video_data_button_clicked(
            youtube_video_url_or_id: str | None,
        ) -> Any:
            if youtube_video_url_or_id is None or len(youtube_video_url_or_id) == 0:
                raise Exception("Invalid YouTube video URL or ID")

            youtube_api_video_response = fetch_youtube_video_data(
                youtube_video_url_or_id=youtube_video_url_or_id,
                youtube_api_key=youtube_api_key,
            )
            items = youtube_api_video_response.items
            if len(items) == 0:
                raise Exception("Invalid YouTube API response")

            item = items[0]

            youtube_live_title = ""
            remote_youtube_channel_id = ""
            youtube_channel_title = ""
            youtube_video_post_time = ""
            if item.snippet is not None:
                youtube_live_title = item.snippet.title
                remote_youtube_channel_id = item.snippet.channelId
                youtube_channel_title = item.snippet.channelTitle
                youtube_video_post_time = item.snippet.publishedAt.astimezone(
                    JST
                ).isoformat()

            return [
                item.id,
                youtube_live_title,
                remote_youtube_channel_id,
                youtube_channel_title,
                youtube_video_post_time,
            ]

        def handle_add_program_youtube_video_live_archive_button_clicked(
            remote_youtube_video_id: str,
            youtube_video_title: str,
            remote_youtube_channel_id: str,
            youtube_channel_name: str,
            post_time_string: str,
            is_premiere: bool,
            start_time_string: str,
            end_time_string: str,
            program_id: str,
            person_id: str,
        ) -> Any:
            post_time = datetime.fromisoformat(post_time_string)
            start_time = datetime.fromisoformat(start_time_string)
            end_time = datetime.fromisoformat(end_time_string)

            program_live_archive = add_program_youtube_video_live_archive(
                program_id=program_id,
                person_id=person_id,
                post_time=post_time,
                start_time=start_time,
                end_time=end_time,
                remote_youtube_video_id=remote_youtube_video_id,
                title=youtube_video_title,
                is_premiere=is_premiere,
                remote_youtube_channel_id=remote_youtube_channel_id,
                youtube_channel_name=youtube_channel_name,
                hasura_endpoint=hasura_endpoint,
                hasura_admin_secret=hasura_admin_secret,
            )

            return [
                program_live_archive.id,
            ]

        clear_youtube_live_field_button.add(
            components=[
                youtube_live_url_or_id_text_field,
                remote_youtube_video_id_text_field,
                youtube_live_title_text_field,
                remote_youtube_channel_id_text_field,
                youtube_channel_name_text_field,
                post_time_text_field,
            ],
        )
        clear_time_field_button.add(
            components=[
                is_premiere_checkbox_field,
                start_time_text_field,
                end_time_text_field,
            ]
        )
        clear_project_field_button.add(
            components=[
                project_drop,
                program_drop,
                person_drop,
            ],
        )

        fetch_youtube_video_data_button.click(
            fn=handle_fetch_youtube_video_data_button_clicked,
            inputs=[youtube_live_url_or_id_text_field],
            outputs=[
                remote_youtube_video_id_text_field,
                youtube_live_title_text_field,
                remote_youtube_channel_id_text_field,
                youtube_channel_name_text_field,
                post_time_text_field,
            ],
        )

        add_program_youtube_video_live_archive_button.click(
            fn=handle_add_program_youtube_video_live_archive_button_clicked,
            inputs=[
                remote_youtube_video_id_text_field,
                youtube_live_title_text_field,
                remote_youtube_channel_id_text_field,
                youtube_channel_name_text_field,
                post_time_text_field,
                is_premiere_checkbox_field,
                start_time_text_field,
                end_time_text_field,
                program_drop,
                person_drop,
            ],
            outputs=[
                added_program_live_archive_id_text_field,
            ],
        )

        project_drop.select(
            fn=handle_project_changed,
            inputs=project_drop,
            outputs=program_drop,
        )

    return tab