# Generated by ariadne-codegen
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
