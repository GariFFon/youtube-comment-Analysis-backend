from google import genai
from google.genai import types
import json

from app.core.config import settings
from app.models.schemas import GeminiAnalysis, GeminiBatchAnalysis

class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment variables.")
        
        # Initialize the new Google GenAI client
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.5-flash" # Use fast/cheap 2.5 flash model

    def analyze_comment(self, comment_text: str) -> GeminiAnalysis:
        """
        Sends a single comment to Gemini to classify and analyze it.
        Enforces a structured JSON Pydantic response matching our GeminiAnalysis schema.
        """
        prompt = f"""
        Analyze the following YouTube comment and extract the requested fields.
        Be extremely objective. Do not hallucinate.

        Comment text: "{comment_text}"
        """
        
        try:
            # We pass our Pydantic class directly to the response_schema config!
            # Gemini will use this to guarantee the output formatting.
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeminiAnalysis,
                    temperature=0.1, # Extremely low temperature so it strictly follows rules
                ),
            )
            
            # The response.text is a JSON string perfectly matching our schema.
            # We parse to dictionary, then load into our Pydantic model.
            analysis_dict = json.loads(response.text)
            return GeminiAnalysis(**analysis_dict)
            
        except Exception as e:
            print(f"Error during Gemini analysis: {e}")
            # Fallback if AI fails (e.g. comment too long, unsafe content tripped limit, network error)
            # so the entire pipeline doesn't crash on one bad comment.
            return GeminiAnalysis(
                classification="Neutral / General Discussion",
                sentiment_score=0.0,
                key_topics=["Analysis Failed"]
            )

    def analyze_comments_batch(self, comments: list[str]) -> list[GeminiAnalysis]:
        """
        Sends multiple comments to Gemini in a single request to save rate limits.
        """
        if not comments:
            return []
            
        prompt = "Analyze the following list of YouTube comments. Provide a classification for each comment in the exact same order as provided.\n\n"
        for i, comment_text in enumerate(comments):
            prompt += f"[{i}] {comment_text}\n"
            
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeminiBatchAnalysis,
                    temperature=0.1,
                ),
            )
            
            analysis_dict = json.loads(response.text)
            batch_result = GeminiBatchAnalysis(**analysis_dict)
            return batch_result.results
            
        except Exception as e:
            print(f"Error during Gemini batch analysis: {e}")
            # Fallback if AI fails
            return [GeminiAnalysis(
                classification="Neutral / General Discussion",
                sentiment_score=0.0,
                key_topics=["Analysis Failed"]
            ) for _ in comments]

# Instantiate a single service object to be imported and used elsewhere
gemini_service = GeminiService()
