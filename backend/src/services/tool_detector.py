"""Tool detection service with keyword-based pattern matching."""

import re
from typing import Optional

import structlog

logger = structlog.get_logger()


class ToolDetector:
    """Detect AI tool mentions in text content."""

    def __init__(self):
        """Initialize tool detector."""
        self.tool_patterns: dict[str, list[str]] = {}
        self.tool_thresholds: dict[str, float] = {}

    def register_tool(
        self, tool_id: str, aliases: list[str], threshold: float = 0.7
    ) -> None:
        """
        Register a tool with its aliases for detection.

        Args:
            tool_id: Unique tool identifier
            aliases: List of keywords/patterns to match
            threshold: Detection confidence threshold
        """
        self.tool_patterns[tool_id] = aliases
        self.tool_thresholds[tool_id] = threshold
        logger.debug(
            "Registered tool for detection", tool_id=tool_id, alias_count=len(aliases)
        )

    def detect_tools(self, content: str) -> list[dict[str, str | float]]:
        """
        Detect AI tool mentions in content.

        Args:
            content: Text to scan for tool mentions

        Returns:
            List of detected tools with confidence scores
        """
        content_lower = content.lower()
        detected = []

        for tool_id, aliases in self.tool_patterns.items():
            matches = []

            for alias in aliases:
                # Create regex pattern (word boundaries)
                pattern = r"\b" + re.escape(alias.lower()) + r"\b"
                if re.search(pattern, content_lower):
                    matches.append(alias)

            if matches:
                # Calculate confidence based on match count
                confidence = min(1.0, len(matches) * 0.3 + 0.5)

                # Check if meets threshold
                threshold = self.tool_thresholds.get(tool_id, 0.7)
                if confidence >= threshold:
                    detected.append(
                        {
                            "tool_id": tool_id,
                            "confidence": confidence,
                            "matched_aliases": matches,
                        }
                    )

        return detected

    def detect_tools_in_content(
        self, content: str, include_context: bool = False
    ) -> list[dict]:
        """
        Detect AI tools with regex patterns and fuzzy matching.

        Enhanced detection with:
        - Case-insensitive matching
        - Word boundary enforcement
        - Confidence scoring based on match count
        - Optional context extraction

        Args:
            content: Text content to analyze
            include_context: Whether to extract mention context

        Returns:
            List of detected tools with confidence and optional context
        """
        detected = self.detect_tools(content)

        if include_context:
            for detection in detected:
                # Get first matched alias for context
                alias = detection.get("matched_aliases", [None])[0]
                if alias:
                    context = self.extract_mention_context(
                        content, alias, context_chars=100
                    )
                    detection["context"] = context

        logger.debug(
            "Tool detection completed",
            detected_count=len(detected),
            include_context=include_context,
        )

        return detected

    def extract_mention_context(
        self, content: str, alias: str, context_chars: int = 100
    ) -> Optional[str]:
        """
        Extract text snippet around a tool mention.

        Args:
            content: Full content text
            alias: Matched alias keyword
            context_chars: Characters to include before/after

        Returns:
            Text snippet containing the mention
        """
        content_lower = content.lower()
        alias_lower = alias.lower()

        # Find position of alias
        pos = content_lower.find(alias_lower)
        if pos == -1:
            return None

        # Extract context window
        start = max(0, pos - context_chars)
        end = min(len(content), pos + len(alias) + context_chars)

        snippet = content[start:end].strip()

        # Add ellipsis if truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet


# Global instance
tool_detector = ToolDetector()
