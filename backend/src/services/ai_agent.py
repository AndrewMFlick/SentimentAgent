"""AI Agent for natural language queries about sentiment data."""

import logging
from datetime import datetime
from typing import Optional

from openai import AzureOpenAI

from ..config import settings
from .database import db

logger = logging.getLogger(__name__)


class AIAgent:
    """AI agent for querying sentiment data with natural language."""

    def __init__(self):
        """Initialize AI agent."""
        self.llm_client: Optional[AzureOpenAI] = None

        if settings.azure_openai_endpoint and settings.azure_openai_api_key:
            try:
                self.llm_client = AzureOpenAI(
                    api_key=settings.azure_openai_api_key,
                    api_version=settings.azure_openai_api_version,
                    azure_endpoint=settings.azure_openai_endpoint,
                )
                logger.info("AI Agent initialized with LLM")
            except Exception as e:
                logger.warning(f"Failed to initialize AI Agent: {e}")
        else:
            logger.warning("AI Agent requires Azure OpenAI configuration")

    async def query(self, question: str) -> dict:
        """
        Process a natural language query about sentiment data.

        Args:
            question: User's question about sentiment

        Returns:
            Dictionary with answer, data sources, and metadata
        """
        if not self.llm_client:
            return {
                "answer": "AI Agent is not configured. Please set up Azure OpenAI credentials.",
                "sources": [],
                "timestamp": datetime.utcnow().isoformat(),
            }

        try:
            # Gather relevant context data
            context = await self._gather_context(question)

            # Generate prompt with context
            prompt = self._build_prompt(question, context)

            # Query LLM
            response = self.llm_client.chat.completions.create(
                model=settings.azure_openai_deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI analyst expert in sentiment analysis of developer tool discussions. Provide clear, data-driven insights based on the provided context.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=800,
            )

            answer = response.choices[0].message.content

            return {
                "answer": answer,
                "sources": context.get("sources", []),
                "data_summary": context.get("summary", {}),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"AI Agent query error: {e}")
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _gather_context(self, question: str) -> dict:
        """Gather relevant data context for the question."""
        context = {"sources": [], "summary": {}}

        # Extract mentioned tools/subreddits from question
        mentioned_subreddits = self._extract_subreddits(question)

        # Gather sentiment stats for mentioned tools
        for subreddit in mentioned_subreddits:
            # Recent stats (24 hours)
            stats_24h = await db.get_sentiment_stats(subreddit=subreddit, hours=24)

            # Weekly stats
            stats_week = await db.get_sentiment_stats(subreddit=subreddit, hours=168)

            context["summary"][subreddit] = {
                "last_24h": stats_24h,
                "last_week": stats_week,
            }

            context["sources"].append(
                {
                    "type": "sentiment_stats",
                    "subreddit": subreddit,
                    "timeframe": "24h and 7d",
                }
            )

        # If no specific subreddits mentioned, get overall stats
        if not mentioned_subreddits:
            overall_stats = await db.get_sentiment_stats(hours=168)
            context["summary"]["overall"] = overall_stats
            context["sources"].append(
                {"type": "sentiment_stats", "subreddit": "all", "timeframe": "7d"}
            )

        # Get recent posts for context
        if mentioned_subreddits:
            for subreddit in mentioned_subreddits[:3]:  # Limit to 3 for context size
                posts = db.get_recent_posts(subreddit=subreddit, hours=48, limit=10)
                if posts:
                    context["sources"].append(
                        {
                            "type": "recent_posts",
                            "subreddit": subreddit,
                            "count": len(posts),
                        }
                    )

        return context

    def _extract_subreddits(self, question: str) -> list[str]:
        """Extract mentioned subreddits from question."""
        question_lower = question.lower()
        mentioned = []

        # Check each monitored subreddit
        for subreddit in settings.subreddit_list:
            subreddit_lower = subreddit.lower()

            # Check various formats
            if (
                subreddit_lower in question_lower
                or f"r/{subreddit_lower}" in question_lower
                or subreddit_lower.replace(" ", "") in question_lower
            ):
                mentioned.append(subreddit)

        # Also check for common tool names that map to subreddits
        tool_mappings = {
            "github copilot": "GithubCopilot",
            "copilot": "GithubCopilot",
            "chatgpt": "ChatGPTCoding",
            "cursor": "Cursor",
            "claude": "Claude",
            "windsurf": "Windsurf",
            "bard": "Bard",
        }

        for tool_name, subreddit in tool_mappings.items():
            if tool_name in question_lower and subreddit not in mentioned:
                mentioned.append(subreddit)

        return mentioned

    def _build_prompt(self, question: str, context: dict) -> str:
        """Build prompt with question and context data."""
        prompt_parts = [f"Question: {question}", "", "Available Data Context:"]

        # Add sentiment summary
        if context.get("summary"):
            prompt_parts.append("\nSentiment Statistics:")
            for key, data in context["summary"].items():
                if key == "overall":
                    prompt_parts.append(f"\nOverall (all subreddits):")
                    prompt_parts.append(f"  Total analyzed: {data.get('total', 0)}")
                    prompt_parts.append(f"  Positive: {data.get('positive', 0)}")
                    prompt_parts.append(f"  Negative: {data.get('negative', 0)}")
                    prompt_parts.append(f"  Neutral: {data.get('neutral', 0)}")
                    prompt_parts.append(
                        f"  Average sentiment: {
                            data.get(
                                'avg_sentiment',
                                0):.3f}"
                    )
                else:
                    prompt_parts.append(f"\nr/{key}:")

                    if "last_24h" in data:
                        stats = data["last_24h"]
                        prompt_parts.append(f"  Last 24 hours:")
                        prompt_parts.append(f"    Total: {stats.get('total', 0)}")
                        prompt_parts.append(
                            f"    Positive: {
                                stats.get(
                                    'positive',
                                    0)}, Negative: {
                                stats.get(
                                    'negative',
                                    0)}, Neutral: {
                                stats.get(
                                    'neutral',
                                    0)}"
                        )
                        prompt_parts.append(
                            f"    Avg sentiment: {
                                stats.get(
                                    'avg_sentiment',
                                    0):.3f}"
                        )

                    if "last_week" in data:
                        stats = data["last_week"]
                        prompt_parts.append(f"  Last 7 days:")
                        prompt_parts.append(f"    Total: {stats.get('total', 0)}")
                        prompt_parts.append(
                            f"    Positive: {
                                stats.get(
                                    'positive',
                                    0)}, Negative: {
                                stats.get(
                                    'negative',
                                    0)}, Neutral: {
                                stats.get(
                                    'neutral',
                                    0)}"
                        )
                        prompt_parts.append(
                            f"    Avg sentiment: {
                                stats.get(
                                    'avg_sentiment',
                                    0):.3f}"
                        )

        prompt_parts.extend(
            [
                "",
                "Instructions:",
                "- Provide a clear, data-driven answer to the question",
                "- Reference specific numbers from the data",
                "- Explain trends and patterns",
                "- If comparing tools, highlight key differences",
                "- If data is insufficient, acknowledge it",
                "- Keep response concise but informative",
            ]
        )

        return "\n".join(prompt_parts)


# Global AI agent instance
ai_agent = AIAgent()
