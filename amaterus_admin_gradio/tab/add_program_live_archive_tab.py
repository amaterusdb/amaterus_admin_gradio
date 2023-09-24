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


class AddProgramLiveArchiveResponseProgramLiveArchive(BaseModel):
    id: str


class AddProgramLiveArchiveResponseData(BaseModel):
    program_live_archive: AddProgramLiveArchiveResponseProgramLiveArchive


class AddProgramLiveArchiveResponse(BaseModel):
    data: AddProgramLiveArchiveResponseData


def add_program_live_archive(
    program_id: str,
    person_id: str,
    start_time: datetime | None,
    end_time: datetime | None,
    remote_youtube_video_id: str,
    title: str,
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
  $startTime: timestamptz
  $endTime: timestamptz
  $remoteYoutubeVideoId: String!
  $title: String!
  $remoteYoutubeChannelId: String!
  $youtubeChannelName: String!
) {
    program_live_archive: insert_program_live_archives_one(
        object: {
            program_id: $programId
            person_id: $personId
            start_time: $startTime
            end_time: $endTime
            youtube_live: {
                data: {
                    remote_youtube_video_id: $remoteYoutubeVideoId
                    title: $title
                    start_time: $startTime
                    end_time: $endTime
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
                    constraint: youtube_lives_remote_youtube_video_id_key
                    update_columns: [
                        title
                        start_time
                        end_time
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
                "startTime": start_time.isoformat() if start_time is not None else None,
                "endTime": end_time.isoformat() if end_time is not None else None,
                "remoteYoutubeVideoId": remote_youtube_video_id,
                "title": title,
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


def create_add_program_live_archive_tab(
    youtube_api_key: str,
    hasura_endpoint: str,
    hasura_admin_secret: str,
    logger: Logger,
) -> gr.Tab:
    initial_data = fetch_initial_data(
        hasura_endpoint=hasura_endpoint,
    )

    with gr.Tab(label="プログラムに配信アーカイブを追加") as tab:
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
                item.id,
                youtube_live_title,
                remote_youtube_channel_id,
                youtube_channel_title,
                youtube_live_start_time,
                youtube_live_end_time,
            ]

        def handle_add_live_archive_button_clicked(
            remote_youtube_video_id: str,
            youtube_live_title: str,
            remote_youtube_channel_id: str,
            youtube_channel_name: str,
            start_time_string: str,
            end_time_string: str,
            program_id: str,
            person_id: str,
        ) -> Any:
            start_time = (
                datetime.fromisoformat(start_time_string)
                if len(start_time_string) != 0
                else None
            )
            end_time = (
                datetime.fromisoformat(end_time_string)
                if len(end_time_string) != 0
                else None
            )

            program_live_archive = add_program_live_archive(
                program_id=program_id,
                person_id=person_id,
                start_time=start_time,
                end_time=end_time,
                remote_youtube_video_id=remote_youtube_video_id,
                title=youtube_live_title,
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
                remote_youtube_video_id_text_field,
                youtube_live_title_text_field,
                remote_youtube_channel_id_text_field,
                youtube_channel_name_text_field,
                start_time_text_field,
                end_time_text_field,
            ],
        )

        add_live_archive_button.click(
            fn=handle_add_live_archive_button_clicked,
            inputs=[
                remote_youtube_video_id_text_field,
                youtube_live_title_text_field,
                remote_youtube_channel_id_text_field,
                youtube_channel_name_text_field,
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
