# Generated by ariadne-codegen on 2023-09-24 23:07
# Source: queries/

from typing import Any, Optional

from .base_model import BaseModel


class CreateProgramTwitterAnnouncement(BaseModel):
    program_twitter_announcement: Optional[
        "CreateProgramTwitterAnnouncementProgramTwitterAnnouncement"
    ]


class CreateProgramTwitterAnnouncementProgramTwitterAnnouncement(BaseModel):
    id: Any


CreateProgramTwitterAnnouncement.model_rebuild()
CreateProgramTwitterAnnouncementProgramTwitterAnnouncement.model_rebuild()
