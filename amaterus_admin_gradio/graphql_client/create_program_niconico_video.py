# Generated by ariadne-codegen
# Source: queries/

from typing import Any, Optional

from .base_model import BaseModel


class CreateProgramNiconicoVideo(BaseModel):
    program_niconico_video: Optional["CreateProgramNiconicoVideoProgramNiconicoVideo"]


class CreateProgramNiconicoVideoProgramNiconicoVideo(BaseModel):
    id: Any


CreateProgramNiconicoVideo.model_rebuild()
