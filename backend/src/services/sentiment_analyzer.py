"""Sentiment analysis service."""

import logging
from typing import Optional

from openai import AzureOpenAI
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from ..config import settings
from ..models import SentimentScore
from .tool_detector import tool_detector

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Analyzes sentiment of text using VADER or LLM."""

    def __init__(self):
        """Initialize sentiment analyzer."""
        self.vader = SentimentIntensityAnalyzer()

        # Initialize LLM client if configured
        self.llm_client: Optional[AzureOpenAI] = None
        if settings.azure_openai_endpoint and settings.azure_openai_api_key:
            try:
                self.llm_client = AzureOpenAI(
                    api_key=settings.azure_openai_api_key,
                    api_version=settings.azure_openai_api_version,
                    azure_endpoint=settings.azure_openai_endpoint,
                )
                logger.info("LLM client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM client: {e}")

        logger.info(
            f"Sentiment analyzer initialized with method: {
                settings.sentiment_method}"
        )

    def analyze(
        self, content_id: str, content_type: str, subreddit: str, text: str
    ) -> SentimentScore:
        """
        Analyze sentiment of text.

        Args:
            content_id: ID of the content being analyzed
            content_type: Type of content ('post' or 'comment')
            subreddit: Source subreddit
            text: Text to analyze

        Returns:
            SentimentScore object
        """
        if not text or not text.strip():
            return self._neutral_sentiment(content_id, content_type, subreddit, "VADER")

        # Detect tools mentioned in the content
        detected_tool_ids = self._detect_tools(text)

        # Primary analysis method
        if settings.sentiment_method == "LLM" and self.llm_client:
            sentiment_result = self._analyze_with_llm(
                content_id, content_type, subreddit, text
            )
        else:
            vader_result = self._analyze_with_vader(
                content_id, content_type, subreddit, text
            )

            # Use LLM for ambiguous cases if configured
            if settings.use_llm_for_ambiguous and self.llm_client:
                if vader_result.confidence < 0.6:  # Low confidence threshold
                    logger.debug(
                        f"Low confidence VADER result, using LLM fallback for {content_id}"
                    )
                    sentiment_result = self._analyze_with_llm(
                        content_id, content_type, subreddit, text
                    )
                else:
                    sentiment_result = vader_result
            else:
                sentiment_result = vader_result

        # Add detected tools to the result
        sentiment_result.detected_tool_ids = detected_tool_ids

        if detected_tool_ids:
            logger.debug(
                "Tools detected in content",
                content_id=content_id,
                tool_count=len(detected_tool_ids),
                tools=detected_tool_ids[:3],  # Log first 3 tools
            )

        return sentiment_result

    def _detect_tools(self, text: str) -> list[str]:
        """
        Detect AI tools mentioned in text.

        Args:
            text: Text to analyze

        Returns:
            List of detected tool IDs
        """
        try:
            detected = tool_detector.detect_tools(text)
            return [tool["tool_id"] for tool in detected]
        except Exception as e:
            logger.error(f"Tool detection error: {e}", exc_info=True)
            return []

    def _analyze_with_vader(
        self, content_id: str, content_type: str, subreddit: str, text: str
    ) -> SentimentScore:
        """Analyze sentiment using VADER."""
        try:
            scores = self.vader.polarity_scores(text)

            compound = scores["compound"]

            # Classify sentiment
            if compound >= 0.05:
                sentiment = "positive"
            elif compound <= -0.05:
                sentiment = "negative"
            else:
                sentiment = "neutral"

            # Calculate confidence based on how far from neutral
            confidence = min(abs(compound) * 2, 1.0)

            return SentimentScore(
                content_id=content_id,
                content_type=content_type,
                subreddit=subreddit,
                sentiment=sentiment,
                confidence=confidence,
                compound_score=compound,
                positive_score=scores["pos"],
                negative_score=scores["neg"],
                neutral_score=scores["neu"],
                analysis_method="VADER",
            )

        except Exception as e:
            logger.error(f"VADER analysis error for {content_id}: {e}")
            return self._neutral_sentiment(content_id, content_type, subreddit, "VADER")

    def _analyze_with_llm(
        self, content_id: str, content_type: str, subreddit: str, text: str
    ) -> SentimentScore:
        """Analyze sentiment using LLM."""
        if not self.llm_client:
            logger.warning("LLM client not available, falling back to VADER")
            return self._analyze_with_vader(content_id, content_type, subreddit, text)

        try:
            prompt = f"""Analyze the sentiment of the following text from Reddit.

Text: {text[:1000]}

Provide a JSON response with:
- sentiment: "positive", "negative", or "neutral"
- confidence: float between 0 and 1
- compound_score: float between -1 and 1 (negative to positive)

Focus on the overall emotional tone regarding AI developer tools."""

            response = self.llm_client.chat.completions.create(
                model=settings.azure_openai_deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a sentiment analysis expert specializing in developer tool discussions.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=150,
            )

            # Parse LLM response
            result_text = response.choices[0].message.content

            # Simple parsing (in production, use more robust JSON parsing)
            import json

            result = json.loads(result_text)

            sentiment = result.get("sentiment", "neutral")
            confidence = float(result.get("confidence", 0.5))
            compound_score = float(result.get("compound_score", 0.0))

            return SentimentScore(
                content_id=content_id,
                content_type=content_type,
                subreddit=subreddit,
                sentiment=sentiment,
                confidence=confidence,
                compound_score=compound_score,
                positive_score=(
                    max(0, compound_score) if sentiment == "positive" else 0.0
                ),
                negative_score=(
                    abs(min(0, compound_score)) if sentiment == "negative" else 0.0
                ),
                neutral_score=(
                    1.0 - abs(compound_score) if sentiment == "neutral" else 0.0
                ),
                analysis_method="LLM",
            )

        except Exception as e:
            logger.error(f"LLM analysis error for {content_id}: {e}")
            # Fallback to VADER
            return self._analyze_with_vader(content_id, content_type, subreddit, text)

    def _neutral_sentiment(
        self, content_id: str, content_type: str, subreddit: str, method: str
    ) -> SentimentScore:
        """Return neutral sentiment score."""
        return SentimentScore(
            content_id=content_id,
            content_type=content_type,
            subreddit=subreddit,
            sentiment="neutral",
            confidence=0.5,
            compound_score=0.0,
            positive_score=0.0,
            negative_score=0.0,
            neutral_score=1.0,
            analysis_method=method,
        )
