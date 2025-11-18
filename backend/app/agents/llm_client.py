"""
LLM Client wrapper for AI agent interactions.

Handles API calls to OpenAI/OpenRouter with:
- Retry logic
- Error handling
- Token counting
- Daily budget tracking
- Cost calculation
"""
import asyncio
import json
import time
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from decimal import Decimal

import tiktoken
from openai import AsyncOpenAI, OpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import AgentLog


class BudgetExceededError(Exception):
    """Raised when daily token budget is exceeded."""
    pass


class LLMClient:
    """
    Client for interacting with LLM APIs with cost tracking and budget enforcement.
    """
    
    # Cost per 1K tokens (as of Nov 2024, subject to change)
    # OpenRouter models typically follow similar pricing tiers
    COSTS = {
        # OpenAI models
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        # OpenRouter models (common ones)
        "openai/gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "openai/gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "openai/gpt-4": {"input": 0.03, "output": 0.06},
        "openai/gpt-4o": {"input": 0.005, "output": 0.015},
        "openai/gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "anthropic/claude-3-haiku": {"input": 0.00025, "output": 0.00125},
        "anthropic/claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "anthropic/claude-3.5-sonnet": {"input": 0.003, "output": 0.015},
        "anthropic/claude-3-opus": {"input": 0.015, "output": 0.075},
        "meta-llama/llama-3.1-8b-instruct": {"input": 0.00006, "output": 0.00006},
        "meta-llama/llama-3.1-70b-instruct": {"input": 0.00052, "output": 0.00075},
        "google/gemini-pro": {"input": 0.000125, "output": 0.000375},
        "google/gemini-pro-1.5": {"input": 0.00125, "output": 0.00375},
    }
    
    def __init__(self, db: Session, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize LLM client.
        
        Args:
            db: Database session for logging
            api_key: Optional API key (defaults to settings)
            base_url: Optional base URL for OpenRouter (defaults to settings)
        """
        self.db = db
        self.api_key = api_key or settings.llm_api_key
        
        # Use OpenRouter if provider is openrouter, otherwise use OpenAI
        if settings.llm_provider == "openrouter":
            openrouter_url = base_url or getattr(settings, "openrouter_base_url", "https://openrouter.ai/api/v1")
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=openrouter_url
            )
            self.async_client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=openrouter_url
            )
        else:
            self.client = OpenAI(api_key=self.api_key)
            self.async_client = AsyncOpenAI(api_key=self.api_key)
        
        # Initialize tokenizer for GPT models
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.
        
        Args:
            text: Input text
            
        Returns:
            Number of tokens
        """
        return len(self.tokenizer.encode(text))
    
    def get_today_usage(self) -> Dict[str, int]:
        """
        Get today's token usage from database.
        
        Returns:
            Dict with total_tokens, input_tokens, output_tokens
        """
        today = date.today()
        
        # Query today's logs
        logs = (
            self.db.query(AgentLog)
            .filter(AgentLog.timestamp >= today)
            .all()
        )
        
        total_tokens = sum(log.tokens_used or 0 for log in logs)
        input_tokens = sum(log.input_tokens or 0 for log in logs)
        output_tokens = sum(log.output_tokens or 0 for log in logs)
        
        return {
            "total_tokens": total_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }
    
    def check_budget(self, estimated_tokens: int = 0) -> bool:
        """
        Check if we're within daily budget.
        
        Args:
            estimated_tokens: Estimated tokens for upcoming call
            
        Returns:
            True if within budget, False otherwise
        """
        usage = self.get_today_usage()
        projected = usage["total_tokens"] + estimated_tokens
        return projected <= settings.daily_token_budget
    
    def calculate_cost(
        self, 
        model: str, 
        input_tokens: int, 
        output_tokens: int
    ) -> Decimal:
        """
        Calculate cost for LLM call.
        
        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in USD
        """
        costs = self.COSTS.get(model, {"input": 0.01, "output": 0.03})
        
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        
        return Decimal(str(input_cost + output_cost)).quantize(Decimal("0.000001"))
    
    def call(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        agent_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Make a synchronous LLM API call with retry logic.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to cheap_model)
            agent_name: Name of agent making the call
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            response_format: Optional response format (e.g., {"type": "json_object"})
            max_retries: Number of retry attempts
            
        Returns:
            Dict with response, tokens, cost, etc.
            
        Raises:
            BudgetExceededError: If daily budget exceeded
            Exception: If API call fails after retries
        """
        model = model or settings.cheap_model
        
        # Estimate input tokens
        input_text = "\n".join(msg["content"] for msg in messages)
        estimated_input_tokens = self.count_tokens(input_text)
        estimated_total_tokens = estimated_input_tokens + (max_tokens or 1000)
        
        # Check budget
        if not self.check_budget(estimated_total_tokens):
            usage = self.get_today_usage()
            raise BudgetExceededError(
                f"Daily budget exceeded. Used: {usage['total_tokens']}, "
                f"Budget: {settings.daily_token_budget}"
            )
        
        # Retry logic
        last_exception = None
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                # Make API call
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                }
                
                if max_tokens:
                    kwargs["max_tokens"] = max_tokens
                
                if response_format:
                    kwargs["response_format"] = response_format
                
                response = self.client.chat.completions.create(**kwargs)
                
                # Extract response
                content = response.choices[0].message.content
                finish_reason = response.choices[0].finish_reason
                
                # Get token usage
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                total_tokens = response.usage.total_tokens
                
                # Calculate cost
                cost = self.calculate_cost(model, input_tokens, output_tokens)
                
                # Calculate latency
                latency = time.time() - start_time
                
                # Log to database
                log_entry = AgentLog(
                    agent_name=agent_name or "unknown",
                    model=model,
                    input_data=json.dumps(messages),
                    output_data=content,
                    tokens_used=total_tokens,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost=cost,
                    latency_seconds=latency,
                    timestamp=datetime.utcnow(),
                )
                self.db.add(log_entry)
                self.db.commit()
                
                return {
                    "content": content,
                    "finish_reason": finish_reason,
                    "model": model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "cost": float(cost),
                    "latency": latency,
                }
                
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    # Log failed attempt
                    log_entry = AgentLog(
                        agent_name=agent_name or "unknown",
                        model=model,
                        input_data=json.dumps(messages),
                        output_data=f"ERROR: {str(e)}",
                        tokens_used=0,
                        cost=Decimal("0"),
                        latency_seconds=time.time() - start_time,
                        timestamp=datetime.utcnow(),
                    )
                    self.db.add(log_entry)
                    self.db.commit()
                    
                    raise Exception(
                        f"LLM call failed after {max_retries} attempts: {str(e)}"
                    ) from last_exception
    
    async def acall(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        agent_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Make an asynchronous LLM API call with retry logic.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to cheap_model)
            agent_name: Name of agent making the call
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            response_format: Optional response format (e.g., {"type": "json_object"})
            max_retries: Number of retry attempts
            
        Returns:
            Dict with response, tokens, cost, etc.
            
        Raises:
            BudgetExceededError: If daily budget exceeded
            Exception: If API call fails after retries
        """
        model = model or settings.cheap_model
        
        # Estimate input tokens
        input_text = "\n".join(msg["content"] for msg in messages)
        estimated_input_tokens = self.count_tokens(input_text)
        estimated_total_tokens = estimated_input_tokens + (max_tokens or 1000)
        
        # Check budget
        if not self.check_budget(estimated_total_tokens):
            usage = self.get_today_usage()
            raise BudgetExceededError(
                f"Daily budget exceeded. Used: {usage['total_tokens']}, "
                f"Budget: {settings.daily_token_budget}"
            )
        
        # Retry logic
        last_exception = None
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                # Make API call
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                }
                
                if max_tokens:
                    kwargs["max_tokens"] = max_tokens
                
                if response_format:
                    kwargs["response_format"] = response_format
                
                response = await self.async_client.chat.completions.create(**kwargs)
                
                # Extract response
                content = response.choices[0].message.content
                finish_reason = response.choices[0].finish_reason
                
                # Get token usage
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                total_tokens = response.usage.total_tokens
                
                # Calculate cost
                cost = self.calculate_cost(model, input_tokens, output_tokens)
                
                # Calculate latency
                latency = time.time() - start_time
                
                # Log to database
                log_entry = AgentLog(
                    agent_name=agent_name or "unknown",
                    model=model,
                    input_data=json.dumps(messages),
                    output_data=content,
                    tokens_used=total_tokens,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost=cost,
                    latency_seconds=latency,
                    timestamp=datetime.utcnow(),
                )
                self.db.add(log_entry)
                self.db.commit()
                
                return {
                    "content": content,
                    "finish_reason": finish_reason,
                    "model": model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "cost": float(cost),
                    "latency": latency,
                }
                
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                else:
                    # Log failed attempt
                    log_entry = AgentLog(
                        agent_name=agent_name or "unknown",
                        model=model,
                        input_data=json.dumps(messages),
                        output_data=f"ERROR: {str(e)}",
                        tokens_used=0,
                        cost=Decimal("0"),
                        latency_seconds=time.time() - start_time,
                        timestamp=datetime.utcnow(),
                    )
                    self.db.add(log_entry)
                    self.db.commit()
                    
                    raise Exception(
                        f"LLM call failed after {max_retries} attempts: {str(e)}"
                    ) from last_exception
