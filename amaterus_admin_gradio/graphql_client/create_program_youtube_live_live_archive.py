# Generated by ariadne-codegen on 2023-09-24 22:12
# Source: queries/

from typing import Any, Optional

from .base_model import BaseModel


class CreateProgramYoutubeLiveLiveArchive(BaseModel):
    program_live_archive: Optional[
        "CreateProgramYoutubeLiveLiveArchiveProgramLiveArchive"
    ]


class CreateProgramYoutubeLiveLiveArchiveProgramLiveArchive(BaseModel):
    id: Any


CreateProgramYoutubeLiveLiveArchive.model_rebuild()
CreateProgramYoutubeLiveLiveArchiveProgramLiveArchive.model_rebuild()
