"""Safe wrapper around Anthropic's Claude API with cost tracking, rate limiting, and retry logic."""

import asyncio
import time
import logging
from typing import Optional, Dict, Any, List
from anthropic import AsyncAnthropic
from core.config import settings

logger = logging.getLogger(__name__)


class ClaudeClient:
    """
    Safe wrapper around Anthropic's Claude API with:
    - Cost tracking
    - Rate limiting
    - Retry logic
    - Timeout protection
    - Token counting
    """
    
    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required but not set")
        
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.total_cost = 0.0
        self.total_tokens = 0
        self.request_count = 0
        self.last_request_time = 0
        
        # Pricing for Claude Sonnet 4 (update as needed)
        # These are approximate - check Anthropic pricing page for current rates
        self.cost_per_input_token = 0.003 / 1000  # $3 per MTok
        self.cost_per_output_token = 0.015 / 1000  # $15 per MTok
    
    async def call(
        self,
        messages: List[Dict[str, str]],
        system: str,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        model: str = "claude-sonnet-4-20250514",
        max_retries: int = 3,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Make a Claude API call with retries and safety checks.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system: System prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            model: Claude model identifier
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds
        
        Returns:
        {
            "content": str,
            "usage": {
                "input_tokens": int,
                "output_tokens": int
            },
            "cost": float,
            "model": str
        }
        
        Raises:
            Exception: If cost limit reached, timeout, or all retries failed
        """
        # Cost check before making request
        if self.total_cost >= settings.MAX_JOB_COST_USD:
            raise Exception(f"Cost limit reached: ${self.total_cost:.4f} >= ${settings.MAX_JOB_COST_USD}")
        
        # Rate limiting (basic: 1 request per second minimum)
        time_since_last = time.time() - self.last_request_time
        if time_since_last < 1.0:
            await asyncio.sleep(1.0 - time_since_last)
        
        # Retry loop
        last_error = None
        for attempt in range(max_retries):
            try:
                logger.info(f"Claude API call attempt {attempt + 1}/{max_retries} (model: {model})")
                
                # Make API call with timeout
                response = await asyncio.wait_for(
                    self.client.messages.create(
                        model=model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        system=system,
                        messages=messages
                    ),
                    timeout=timeout
                )
                
                # Extract usage
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                
                # Calculate cost
                cost = (
                    input_tokens * self.cost_per_input_token +
                    output_tokens * self.cost_per_output_token
                )
                
                # Check cost limit after request
                if self.total_cost + cost > settings.MAX_JOB_COST_USD:
                    logger.warning(f"Cost limit would be exceeded. Current: ${self.total_cost:.4f}, Request: ${cost:.4f}")
                    raise Exception(f"Cost limit would be exceeded: ${self.total_cost + cost:.4f} > ${settings.MAX_JOB_COST_USD}")
                
                # Update tracking
                self.total_cost += cost
                self.total_tokens += input_tokens + output_tokens
                self.request_count += 1
                self.last_request_time = time.time()
                
                # Extract text content (handle multiple content blocks)
                content = ""
                for block in response.content:
                    if block.type == "text":
                        content += block.text
                
                logger.info(
                    f"Claude API call successful: {input_tokens} input, {output_tokens} output tokens, "
                    f"cost: ${cost:.4f}, total: ${self.total_cost:.4f}"
                )
                
                return {
                    "content": content,
                    "usage": {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": input_tokens + output_tokens
                    },
                    "cost": cost,
                    "model": model
                }
                
            except asyncio.TimeoutError:
                last_error = f"Timeout after {timeout}s"
                logger.warning(f"Claude API timeout on attempt {attempt + 1}: {last_error}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # exponential backoff
            except Exception as e:
                error_str = str(e)
                last_error = error_str
                logger.warning(f"Claude API error on attempt {attempt + 1}: {error_str}")
                
                # Handle rate limiting specifically
                if "rate_limit" in error_str.lower() or "429" in error_str:
                    wait_time = 5 * (attempt + 1)
                    logger.info(f"Rate limited, waiting {wait_time}s before retry")
                    await asyncio.sleep(wait_time)
                elif attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # exponential backoff
                else:
                    # Don't retry on cost limit errors
                    if "cost" in error_str.lower() or "limit" in error_str.lower():
                        raise
        
        raise Exception(f"Claude API call failed after {max_retries} attempts: {last_error}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Return usage statistics"""
        return {
            "total_cost": round(self.total_cost, 4),
            "total_tokens": self.total_tokens,
            "request_count": self.request_count,
            "average_cost_per_request": round(self.total_cost / max(self.request_count, 1), 4)
        }
    
    def reset_stats(self):
        """Reset usage statistics (for testing or new job)"""
        self.total_cost = 0.0
        self.total_tokens = 0
        self.request_count = 0
        self.last_request_time = 0
