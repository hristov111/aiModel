"""LLM client with provider abstraction for LM Studio."""

from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Dict, Any, Optional
import logging
from openai import AsyncOpenAI
import httpx

from app.core.config import settings
from app.core.exceptions import LLMConnectionError, LLMResponseError

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    async def stream_chat(self, messages: List[Dict[str, str]]) -> AsyncIterator[str]:
        """
        Stream chat completion responses.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            
        Yields:
            String chunks of the response
        """
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Get complete chat response (non-streaming).
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            
        Returns:
            Complete response string
        """
        pass


class LMStudioClient(LLMClient):
    """LM Studio client using OpenAI-compatible API."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: float = 60.0,
    ):
        """
        Initialize LM Studio client.
        
        Args:
            base_url: Base URL for LM Studio API
            model_name: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or settings.lm_studio_base_url
        self.model_name = model_name or settings.lm_studio_model_name
        self.temperature = temperature or settings.lm_studio_temperature
        self.max_tokens = max_tokens or settings.lm_studio_max_tokens
        
        # Create OpenAI client pointing to LM Studio
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key="not-needed",  # LM Studio doesn't require API key
            timeout=httpx.Timeout(timeout, connect=5.0),
            max_retries=2,
        )
        
        logger.info(f"Initialized LM Studio client: {self.base_url}")
    
    async def stream_chat(self, messages: List[Dict[str, str]]) -> AsyncIterator[str]:
        """
        Stream chat completion from LM Studio.
        
        Args:
            messages: List of message dictionaries
            
        Yields:
            Response text chunks
            
        Raises:
            LLMConnectionError: If connection to LM Studio fails
            LLMResponseError: If response is invalid
        """
        try:
            logger.debug(f"Streaming chat with {len(messages)} messages")
            
            stream = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content
                        
        except httpx.ConnectError as e:
            error_msg = f"Failed to connect to LM Studio at {self.base_url}: {e}"
            logger.error(error_msg)
            raise LLMConnectionError(error_msg)
        except httpx.TimeoutException as e:
            error_msg = f"LM Studio request timed out: {e}"
            logger.error(error_msg)
            raise LLMConnectionError(error_msg)
        except Exception as e:
            error_msg = f"LM Studio streaming error: {e}"
            logger.error(error_msg)
            raise LLMResponseError(error_msg)
    
    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Get complete chat response (non-streaming).
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Complete response string
            
        Raises:
            LLMConnectionError: If connection fails
            LLMResponseError: If response is invalid
        """
        try:
            logger.debug(f"Non-streaming chat with {len(messages)} messages")
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=False,
            )
            
            if not response.choices or len(response.choices) == 0:
                raise LLMResponseError("No response choices returned")
            
            content = response.choices[0].message.content
            if content is None:
                raise LLMResponseError("Response content is None")
            
            return content
            
        except httpx.ConnectError as e:
            error_msg = f"Failed to connect to LM Studio at {self.base_url}: {e}"
            logger.error(error_msg)
            raise LLMConnectionError(error_msg)
        except httpx.TimeoutException as e:
            error_msg = f"LM Studio request timed out: {e}"
            logger.error(error_msg)
            raise LLMConnectionError(error_msg)
        except (LLMConnectionError, LLMResponseError):
            raise
        except Exception as e:
            error_msg = f"LM Studio chat error: {e}"
            logger.error(error_msg)
            raise LLMResponseError(error_msg)
    
    async def health_check(self) -> bool:
        """
        Check if LM Studio is available.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try to list models as a health check
            await self.client.models.list()
            return True
        except Exception as e:
            logger.warning(f"LM Studio health check failed: {e}")
            return False


def get_llm_client() -> LLMClient:
    """
    Factory function to get LLM client instance.
    
    Returns:
        LLMClient instance (currently LMStudioClient)
    """
    return LMStudioClient()

