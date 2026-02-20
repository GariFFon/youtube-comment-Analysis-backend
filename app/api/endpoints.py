from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.security import HTTPAuthorizationCredentials
from typing import List
from collections import Counter

from app.models.schemas import VideoAnalysisReport, CommentBase
from app.models.user import User
from app.services.youtube_service import youtube_service
from app.services.gemini_service import gemini_service
from app.api.auth import get_current_user, security

router = APIRouter()

@router.get("/analyze/{video_id}", response_model=VideoAnalysisReport)
async def analyze_youtube_video(
    video_id: str, 
    force_refresh: bool = False,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Analyzes a YouTube video's comments using Gemini AI.
    If the report already exists in MongoDB, it returns the cached version 
    unless force_refresh is True.
    """
    user_dict = await get_current_user(credentials)
    current_user_id = user_dict["id"]

    # 1. Check if we already have this in MongoDB!
    if not force_refresh:
        existing_report = await VideoAnalysisReport.find_one({"video.video_id": video_id, "user_id": current_user_id})
        if existing_report:
            return existing_report

    # 2. Fetch Video Metadata from YouTube API
    video_details = youtube_service.get_video_details(video_id)
    if not video_details:
        raise HTTPException(status_code=404, detail="YouTube video not found or API quota exceeded")

    # 3. Fetch top Comments from YouTube API
    # Let's cap at 50 comments for now to save Gemini API costs / time during testing
    comments = youtube_service.get_video_comments(video_id, max_results=50)
    
    if not comments:
        raise HTTPException(status_code=404, detail="No comments found for this video")

    # 4. Analyze all comments in ONE request using Gemini AI (to prevent Rate Limits!)
    comment_texts = [c.text_original for c in comments]
    batch_analyses = gemini_service.analyze_comments_batch(comment_texts)
    
    analyzed_comments = []
    classifications_counter = Counter()
    all_topics = []

    for idx, comment in enumerate(comments):
        # Prevent index out of bounds just in case Gemini returned a slightly shorter array
        if idx < len(batch_analyses):
            analysis = batch_analyses[idx]
        else:
            # Fallback for individual comment if batching missed it
            analysis = gemini_service.analyze_comment(comment.text_original)
            # Safe Fallback (No API Call) so we don't drain the user's quota!
            #analysis = GeminiAnalysis(
                #classification="Neutral / General Discussion",
                #sentiment_score=0.0,
                #key_topics=["Skipped to save quota"]
            #)
            
        # Attach the Gemini insight to the original comment
        comment.analysis = analysis
        analyzed_comments.append(comment)
        
        # Keep track for the aggregate stats
        classifications_counter[analysis.classification] += 1
        all_topics.extend(analysis.key_topics)

    # 5. Calculate overall percentages for the dashboard
    total_comments = len(analyzed_comments)
    
    def get_percentage(cat_name: str) -> float:
        return round((classifications_counter.get(cat_name, 0) / total_comments) * 100, 2)

    # Find the top 10 most discussed topics overall
    top_topics = [topic for topic, count in Counter(all_topics).most_common(10)]

    # Generate a programmatic Comprehensive Summary
    summary_sentences = []
    pos = get_percentage("Positive (Praise / Satisfaction)")
    neg = get_percentage("Negative (Complaint / Criticism)")
    
    if pos > 50:
        summary_sentences.append(f"The overall audience response is highly positive ({pos}%).")
    elif neg > 50:
        summary_sentences.append(f"The audience response is largely negative ({neg}%).")
    else:
        summary_sentences.append("The audience has a mixed or neutral reaction to this video.")
        
    if top_topics:
        summary_sentences.append(f"Viewers are primarily discussing: {', '.join(top_topics[:3])}.")
        
    comprehensive_summary = " ".join(summary_sentences)

    # 6. Build the final massive Report
    report = VideoAnalysisReport(
        user_id=current_user_id,
        video=video_details,
        comprehensive_summary=comprehensive_summary,
        total_comments_analyzed=total_comments,
        positive_percentage=pos,
        negative_percentage=neg,
        neutral_percentage=get_percentage("Neutral / General Discussion"),
        question_percentage=get_percentage("Question / Doubt (Support Requests)"),
        spam_percentage=get_percentage("Spam / Irrelevant"),
        top_topics=top_topics,
        comments=analyzed_comments
    )

    # 7. Save this exact structured report natively into MongoDB using Beanie!
    # If we are doing a force_refresh and it exists, we replace it.
    existing_report = await VideoAnalysisReport.find_one({"video.video_id": video_id, "user_id": current_user_id})
    if existing_report:
        report.id = existing_report.id  # Keep the same MongoDB _id
        await report.replace()
    else:
        await report.insert()
        
    # 8. Add to User's history
    user = await User.get(current_user_id)
    if user and video_id not in user.analyzed_videos:
        user.analyzed_videos.append(video_id)
        await user.replace()

    return report

@router.get("/user/history")
async def get_user_history(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Fetches the history of analyzed videos for the current user.
    Returns a lightweight summary of each report to display on the profile page.
    """
    user_dict = await get_current_user(credentials)
    current_user_id = user_dict["id"]
    
    # Fetch all reports owned by the user
    reports = await VideoAnalysisReport.find({"user_id": current_user_id}).to_list()
    
    # Build a condensed response to save bandwidth (exclude the massive comments array)
    history = []
    for r in reports:
        history.append({
            "video_id": r.video.video_id,
            "title": r.video.title,
            "thumbnail_url": r.video.thumbnail_url,
            "channel_name": r.video.channel_name,
            "total_comments_analyzed": r.total_comments_analyzed,
            "positive_percentage": r.positive_percentage,
            "negative_percentage": r.negative_percentage,
            "neutral_percentage": r.neutral_percentage,
            "summary": r.comprehensive_summary
        })
        
    # Reverse so newest are first
    return history[::-1]
