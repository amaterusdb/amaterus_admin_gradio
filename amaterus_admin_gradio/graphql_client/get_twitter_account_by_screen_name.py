# Generated by ariadne-codegen on 2023-09-25 12:58
# Source: queries/

from typing import Any, List

from .base_model import BaseModel


class GetTwitterAccountByScreenName(BaseModel):
    twitter_account_list: List["GetTwitterAccountByScreenNameTwitterAccountList"]


class GetTwitterAccountByScreenNameTwitterAccountList(BaseModel):
    id: Any


GetTwitterAccountByScreenName.model_rebuild()
GetTwitterAccountByScreenNameTwitterAccountList.model_rebuild()
