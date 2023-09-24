from datetime import datetime
from logging import Logger
from typing import Any
from zoneinfo import ZoneInfo

import gradio as gr
import requests
from pydantic import BaseModel

JST = ZoneInfo("Asia/Tokyo")


class InitialDataResponseProject(BaseModel):
    id: str
    name: str


class InitialDataResponseGame(BaseModel):
    id: str
    name: str


class InitialDataResponseData(BaseModel):
    project_list: list[InitialDataResponseProject]
    game_list: list[InitialDataResponseGame]


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
    game_list: games {
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


class AddProgramResponseProgram(BaseModel):
    id: str


class AddProgramResponseData(BaseModel):
    program: AddProgramResponseProgram


class AddProgramResponse(BaseModel):
    data: AddProgramResponseData


def add_program(
    project_id: str,
    game_id: str | None,
    title: str,
    start_time: datetime | None,
    end_time: datetime | None,
    hasura_admin_secret: str,
) -> AddProgramResponseProgram:
    res = requests.post(
        "https://amaterus-hasura.aoirint.com/v1/graphql",
        headers={
            "X-Hasura-Admin-Secret": hasura_admin_secret,
        },
        json={
            "query": """
mutation A(
  $project_id: uuid!
  $game_id: uuid
  $title: String!
  $start_time: timestamptz
  $end_time: timestamptz
) {
    program: insert_programs_one(
        object: {
            game_id: $game_id
            title: $title
            start_time: $start_time
            end_time: $end_time
            program_projects: {
                data: {
                    project_id: $project_id
                }
            }
        }
    ) {
        id
    }
}
""",
            "variables": {
                "project_id": project_id,
                "game_id": game_id,
                "title": title,
                "start_time": start_time.isoformat()
                if start_time is not None
                else None,
                "end_time": end_time.isoformat() if end_time is not None else None,
            },
        },
    )
    print(res.json())
    res.raise_for_status()
    add_program_response = AddProgramResponse.model_validate(res.json())
    return add_program_response.data.program


def create_add_program_tab(
    hasura_admin_secret: str,
    logger: Logger,
) -> gr.Tab:
    initial_data = fetch_initial_data()

    with gr.Tab(label="プログラムを追加") as tab:
        gr.Markdown("# プログラムを追加")
        with gr.Row():
            with gr.Column():
                with gr.Row():
                    clear_field_button = gr.ClearButton(
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
                    game_drop = gr.Dropdown(
                        label="ゲーム",
                        interactive=True,
                        choices=list(
                            map(
                                lambda game: (game.name, game.id),
                                initial_data.game_list,
                            ),
                        ),
                    )
                with gr.Row():
                    title_text_field = gr.Textbox(
                        label="タイトル",
                        interactive=True,
                    )
                with gr.Row():
                    start_time_text_field = gr.Textbox(
                        label="開始時間",
                        interactive=True,
                    )
                    end_time_text_field = gr.Textbox(
                        label="終了時間",
                        interactive=True,
                    )
                with gr.Row():
                    add_program_youtube_video_live_archive_button = gr.Button(
                        value="プログラムを追加",
                        variant="primary",
                    )
                with gr.Row():
                    added_program_live_archive_id_text_field = gr.Textbox(
                        label="追加されたプログラムのデータベース上のID",
                        interactive=False,
                    )

        def handle_add_program_button_clicked(
            project_id: str,
            game_id: str,
            title: str,
            start_time_string: str,
            end_time_string: str,
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

            program = add_program(
                project_id=project_id,
                game_id=game_id,
                title=title,
                start_time=start_time,
                end_time=end_time,
                hasura_admin_secret=hasura_admin_secret,
            )

            return [
                program.id,
            ]

        clear_field_button.add(
            components=[
                project_drop,
                game_drop,
                title_text_field,
                start_time_text_field,
                end_time_text_field,
            ],
        )

        add_program_youtube_video_live_archive_button.click(
            fn=handle_add_program_button_clicked,
            inputs=[
                project_drop,
                game_drop,
                title_text_field,
                start_time_text_field,
                end_time_text_field,
            ],
            outputs=[
                added_program_live_archive_id_text_field,
            ],
        )

    return tab
