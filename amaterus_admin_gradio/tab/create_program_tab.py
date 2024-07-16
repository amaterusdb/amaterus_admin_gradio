from datetime import datetime
from logging import Logger
from typing import Any
from zoneinfo import ZoneInfo

import gradio as gr

from ..graphql_client import Client

JST = ZoneInfo("Asia/Tokyo")


def create_create_program_tab(
    graphql_client: Client,
    logger: Logger,
) -> gr.Tab:
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
                    )
                with gr.Row():
                    game_drop = gr.Dropdown(
                        label="ゲーム",
                        interactive=True,
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
                    add_program_button = gr.Button(
                        value="プログラムを追加",
                        variant="primary",
                    )
                with gr.Row():
                    added_program_id_text_field = gr.Textbox(
                        label="追加されたプログラムのデータベース上のID",
                        interactive=False,
                    )

        def handle_tab_selected() -> Any:
            initial_data = graphql_client.get_create_program_initial_data()
            return [
                gr.Dropdown(
                    choices=list(
                        map(
                            lambda project: (project.name, project.id),
                            initial_data.project_list,
                        ),
                    ),
                ),
                gr.Dropdown(
                    choices=list(
                        map(
                            lambda game: (game.name, game.id),
                            initial_data.game_list,
                        ),
                    ),
                ),
            ]

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

            response = graphql_client.create_program(
                project_id=project_id,
                game_id=game_id,
                title=title,
                start_time=start_time.isoformat() if start_time is not None else None,
                end_time=end_time.isoformat() if end_time is not None else None,
            )
            program = response.program
            if program is None:
                raise Exception("program must not be None")

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
                added_program_id_text_field,
            ],
        )

        tab.select(
            fn=handle_tab_selected,
            outputs=[
                project_drop,
                game_drop,
            ],
        )

        add_program_button.click(
            fn=handle_add_program_button_clicked,
            inputs=[
                project_drop,
                game_drop,
                title_text_field,
                start_time_text_field,
                end_time_text_field,
            ],
            outputs=[
                added_program_id_text_field,
            ],
        )

    return tab
