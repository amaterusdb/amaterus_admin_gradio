# Generated by ariadne-codegen on 2023-09-24 23:07
# Source: queries/

from typing import Any, Optional

from .base_model import BaseModel


class CreateProgramYoutubeVideoLiveArchive(BaseModel):
    program_live_archive: Optional[
        "CreateProgramYoutubeVideoLiveArchiveProgramLiveArchive"
    ]


class CreateProgramYoutubeVideoLiveArchiveProgramLiveArchive(BaseModel):
    id: Any


CreateProgramYoutubeVideoLiveArchive.model_rebuild()
CreateProgramYoutubeVideoLiveArchiveProgramLiveArchive.model_rebuild()
