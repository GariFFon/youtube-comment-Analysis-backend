import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Optional
from datetime import datetime

from app.core.config import settings
from app.models.schemas import VideoBase, CommentBase, CommentAuthor

class YouTubeService:
    def __init__(self):
        self.api_key = settings.YOUTUBE_API_KEY
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY is not set in environment variables.")
        
        # Initialize the YouTube API client
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)

    def get_video_details(self, video_id: str) -> Optional[VideoBase]:
        """
        Fetches metadata for a specific video.
        Uses the videos.list YouTube API method.
        """
        try:
            request = self.youtube.videos().list(
                part="snippet,statistics",
                id=video_id
            )
            response = request.execute()

            if not response.get('items'):
                return None

            item = response['items'][0]
            snippet = item['snippet']
            statistics = item.get('statistics', {})

            # Extract thumbnail URL (try high resolution first, fallback to default)
            thumbnails = snippet.get('thumbnails', {})
            thumbnail_url = None
            if 'high' in thumbnails:
                thumbnail_url = thumbnails['high'].get('url')
            elif 'default' in thumbnails:
                thumbnail_url = thumbnails['default'].get('url')

            return VideoBase(
                video_id=video_id,
                channel_id=snippet['channelId'],
                channel_name=snippet.get('channelTitle'),
                title=snippet['title'],
                description=snippet.get('description'),
                published_at=self._parse_datetime(snippet['publishedAt']),
                view_count=int(statistics.get('viewCount', 0)),
                like_count=int(statistics.get('likeCount', 0)),
                comment_count=int(statistics.get('commentCount', 0)),
                thumbnail_url=thumbnail_url,
                tags=snippet.get('tags', [])
            )
        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred: {e.content}")
            return None

    def get_video_comments(self, video_id: str, max_results: int = 100) -> List[CommentBase]:
        """
        Fetches top-level comments for a video.
        Uses the commentThreads.list YouTube API method.
        """
        comments_list: List[CommentBase] = []
        
        try:
            request = self.youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=min(max_results, 100), # API limit per page is 100
                textFormat="plainText"
            )
            response = request.execute()

            for item in response.get('items', []):
                top_level_comment_snippet = item['snippet']['topLevelComment']['snippet']
                
                # Extract author details safely
                author_channel_id = None
                if 'authorChannelId' in top_level_comment_snippet and 'value' in top_level_comment_snippet['authorChannelId']:
                    author_channel_id = top_level_comment_snippet['authorChannelId']['value']

                author = CommentAuthor(
                    author_name=top_level_comment_snippet.get('authorDisplayName', 'Unknown'),
                    author_channel_id=author_channel_id,
                    author_profile_image_url=top_level_comment_snippet.get('authorProfileImageUrl')
                )

                comment = CommentBase(
                    comment_id=item['id'],
                    video_id=video_id,
                    channel_id=top_level_comment_snippet.get('channelId'),
                    author=author,
                    text_original=top_level_comment_snippet.get('textDisplay', ''),
                    like_count=int(top_level_comment_snippet.get('likeCount', 0)),
                    published_at=self._parse_datetime(top_level_comment_snippet['publishedAt']),
                    updated_at=self._parse_datetime(top_level_comment_snippet['updatedAt']) if 'updatedAt' in top_level_comment_snippet else None,
                    is_reply=False,
                    parent_id=None
                )
                comments_list.append(comment)

            return comments_list

        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred: {e.content}")
            return []

    def _parse_datetime(self, datetime_str: str) -> datetime:
        """Helper to parse YouTube's ISO 8601 datetime strings to Python datetime objects."""
        # YouTube returns '2023-10-30T23:15:00Z', replacing Z with +00:00 for python fromisoformat
        return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))

# Instantiate a single service object to be imported and used elsewhere
youtube_service = YouTubeService()
