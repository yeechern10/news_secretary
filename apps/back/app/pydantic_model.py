from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime

class KeywordModel(BaseModel):
    id: UUID = Field(None, description="The UUID of the keyword")
    source_id: str = Field(None, description="The source ID of the keyword")
    label: str = Field(..., description="The label of the keyword")
    definition: str = Field(None, description="The definition of the keyword")
    synonyms: list = Field(None, description="The synonyms of the keyword")
    type: Literal["iptc_media_topic", "location", "custom"] | None = Field(None, description="The type of the keyword")
    embedding: list[float] = Field(None, description="The embedding of the keyword")
    created_at: datetime = Field(None, description="The creation timestamp of the keyword")
    last_updated: datetime = Field(None, description="The last updated timestamp of the keyword")
    embedded: bool = Field(False, description="Whether the keyword has been embedded")
    parent: UUID = Field(None, description="The parent UUID of the keyword")
    parent_source_id: str = Field(None, description="The parent source ID of the keyword")
    children: list[UUID] = Field(None, description="The children UUIDs of the keyword")
    children_source_ids: list[str] = Field(None, description="The children source IDs of the keyword")
    
class ArticleModel(BaseModel):
    id: UUID = Field(None, description="The UUID of the article")
    title: str = Field(..., description="The title of the article")
    link: str = Field(..., description="The link to the article")
    snippet: str = Field(None, description="A snippet of the article")
    published_at: datetime = Field(None, description="The publication timestamp of the article")
    source: str = Field(None, description="The source of the article")
    language: str = Field(None, description="The language of the article")
    article_type: str = Field(None, description="The type of the article")
    content: str = Field(None, description="The full content of the article")
    content_status: Literal["pending", "completed", "failed"] = Field(None, description="The status of the requesting article content")
    content_error: str = Field(None, description="The error message if the content request failed")
    embedding: list[float] = Field(None, description="The embedding of the article")
    created_at: datetime = Field(None, description="The creation timestamp of the article")
    last_updated: datetime = Field(None, description="The last updated timestamp of the article")
    embedded: bool = Field(False, description="Whether the article has been embedded")
    
class EventModel(BaseModel):
    id: UUID = Field(None, description="The UUID of the event")
    title: str = Field(..., description="The title of the event")
    summary: str = Field(None, description="The summary of the event")
    published_at_range_start: datetime = Field(None, description="The time of the event first published")
    published_at_range_end: datetime = Field(None, description="The time of the event last published")
    confidence_score: float = Field(None, description="The confidence score of the event")
    importance_score: int = Field(None, description="The importance score of the event")
    embedding: list[float] = Field(None, description="The embedding of the event")
    created_at: datetime = Field(None, description="The creation timestamp of the event")
    last_updated: datetime = Field(None, description="The last updated timestamp of the event")
    embedded: bool = Field(False, description="Whether the event has been embedded")
    article_ids: list[UUID] = Field(None, description="The UUIDs of the articles associated with the event")