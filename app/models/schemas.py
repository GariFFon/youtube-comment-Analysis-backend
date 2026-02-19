from pydantic import BaseModel, Field
from beanie import Document
from typing import List, Optional, Literal
from datetime import datetime

#Holds basic channel statistics (views, subscribers, total videos) that you fetch from YouTube.
class ChannelBase(BaseModel):
    channel_id: str
    title: str
    description: Optional[str] = None
    subscriber_count: Optional[int] = 0
    video_count: Optional[int] = 0
    view_count: Optional[int] = 0

#Holds metadata for a specific video (like counts, views, publish date, and tags).
class VideoBase(BaseModel):
    video_id: str
    channel_id: str
    channel_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    published_at: datetime
    view_count: Optional[int] = 0
    like_count: Optional[int] = 0
    comment_count: Optional[int] = 0
    thumbnail_url: Optional[str] = None
    tags: Optional[List[str]] = []

#A sub-model to neatly store details about who wrote the comment (name, profile URL, their own channel ID). 
class CommentAuthor(BaseModel):
    author_name: str
    author_channel_id: Optional[str] = None
    author_profile_image_url: Optional[str] = None

#This is a structured container for the AI's analysis of a single comment. It defines exactly what kind of data the Gemini service should return for each comment.
class GeminiAnalysis(BaseModel):
    classification: Literal[
        "Positive (Praise / Satisfaction)",
        "Negative (Complaint / Criticism)",
        "Neutral / General Discussion",
        "Question / Doubt (Support Requests)",
        "Spam / Irrelevant"
    ] = Field(..., description="The primary classification of the comment.")
    sentiment_score: float = Field(..., description="Score from -1.0 (very negative) to 1.0 (very positive)")
    key_topics: List[str] = Field(default_factory=list, description="Main topics discussed in the comment")
    summary: Optional[str] = Field(None, description="A brief summary of long comments")

class GeminiBatchAnalysis(BaseModel):
    results: List[GeminiAnalysis] = Field(..., description="A list of analyses, precisely matching the order of the input comments.")

#Combines the raw comment data from YouTube (text, likes, date) with the CommentAuthor and the GeminiAnalysis
class CommentBase(BaseModel):
    comment_id: str
    video_id: str
    channel_id: Optional[str] = None
    author: CommentAuthor
    text_original: str
    like_count: int = 0
    published_at: datetime
    updated_at: Optional[datetime] = None
    is_reply: bool = False
    parent_id: Optional[str] = None
    
    # AI Analysis fields (populated after Gemini service runs)
    analysis: Optional[GeminiAnalysis] = None

#This is what your API will eventually return to the front-end. It provides a complete summary: The raw Video metadata.
#Aggregate statistics: overall_sentiment, positive_percentage, negative_percentage, etc.
#The top discussed topics across all comments. The actual list of CommentBase objects (which include Gemini's analysis).
class VideoAnalysisReport(Document):
    class Settings:
        name = "video_reports"
    
    video: VideoBase
    comprehensive_summary: Optional[str] = None
    total_comments_analyzed: int
    positive_percentage: float
    negative_percentage: float
    neutral_percentage: float
    question_percentage: float
    spam_percentage: float
    top_topics: List[str]
    comments: List[CommentBase]
