import sys
import asyncio

def test_pydantic():
    from app.models.user import YouTubeChannelData
    try:
        data = {
            "channel_id": "123",
            "title": "title",
            "description": "desc",
            "subscriber_count": int(None or 0),
            "video_count": int(0),
            "view_count": int(0),
            "thumbnail_url": ""
        }
        yt = YouTubeChannelData(**data)
        yt.dict()
        print("Pydantic is working fine")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pydantic()
