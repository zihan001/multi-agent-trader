"""
LangChain-based agent wrapper.

Wraps existing Instructor-based agents with LangChain for:
- Observability via custom callbacks
- RAG capabilities via ChromaDB
- Multi-agent orchestration via LangGraph
"""
from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.langchain.callbacks import DatabaseCallbackHandler, ConsoleCallbackHandler
from app.core.config import settings


class LangChainAgentWrapper:
    """
    Wraps an Instructor-based agent with LangChain capabilities.
    
    This provides:
    - Automatic logging via DatabaseCallbackHandler
    - Future RAG integration via ChromaDB
    - LangGraph orchestration support
    """
    
    def __init__(
        self,
        agent: BaseAgent,
        db: Session,
        enable_console_logging: bool = False,
    ):
        """
        Initialize LangChain wrapper.
        
        Args:
            agent: Original Instructor-based agent
            db: Database session for logging
            enable_console_logging: Whether to print logs to console
        """
        self.agent = agent
        self.db = db
        
        # Set up callbacks
        self.callbacks = [DatabaseCallbackHandler(db, agent.name)]
        if enable_console_logging:
            self.callbacks.append(ConsoleCallbackHandler())
        
        # Create LangChain LLM client
        if settings.llm_provider == "openrouter":
            base_url = settings.openrouter_base_url
        else:
            base_url = None
            
        self.llm = ChatOpenAI(
            model=agent.model,
            temperature=0.7,
            openai_api_key=settings.llm_api_key,
            openai_api_base=base_url,
            callbacks=self.callbacks,
        )
        
    def create_chain(self, response_model: Type[BaseModel]):
        """
        Create a LangChain LCEL chain with structured output.
        
        Args:
            response_model: Pydantic model for output parsing
            
        Returns:
            Runnable chain
        """
        # Create output parser
        parser = PydanticOutputParser(pydantic_object=response_model)
        
        # Create prompt template with format instructions
        prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}\n\n{format_instructions}"),
            ("human", "{user_prompt}")
        ])
        
        # Build LCEL chain
        chain = (
            {
                "system_prompt": RunnablePassthrough(),
                "user_prompt": RunnablePassthrough(),
                "format_instructions": lambda _: parser.get_format_instructions(),
            }
            | prompt
            | self.llm
            | parser
        )
        
        return chain
    
    def analyze(
        self,
        context: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run analysis using LangChain (with observability).
        
        This is an alternative to agent.analyze_structured() that adds
        LangChain observability via callbacks.
        
        Args:
            context: Context data for analysis
            temperature: LLM sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Structured analysis with metadata
        """
        # Get response model
        response_model = self.agent.get_response_model()
        if not response_model:
            raise NotImplementedError(
                f"Agent {self.agent.name} must implement get_response_model() "
                "for LangChain integration"
            )
        
        # Build prompt using agent's method
        messages = self.agent.build_prompt(context)
        
        # Extract system and user prompts
        system_prompt = ""
        user_prompt = ""
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            elif msg["role"] == "user":
                user_prompt = msg["content"]
        
        # Create chain
        chain = self.create_chain(response_model)
        
        # Run chain
        result = chain.invoke({
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        })
        
        # Convert to dict
        analysis = result.model_dump() if hasattr(result, 'model_dump') else result.dict()
        
        # Return in same format as agent.analyze_structured()
        return {
            "agent_name": self.agent.name,
            "analysis": analysis,
            "metadata": {
                "structured": True,
                "langchain": True,
                "model_type": response_model.__name__,
            }
        }
    
    async def aanalyze(
        self,
        context: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run analysis asynchronously using LangChain.
        
        Args:
            context: Context data for analysis
            temperature: LLM sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Structured analysis with metadata
        """
        # Get response model
        response_model = self.agent.get_response_model()
        if not response_model:
            raise NotImplementedError(
                f"Agent {self.agent.name} must implement get_response_model() "
                "for LangChain integration"
            )
        
        # Build prompt using agent's method
        messages = self.agent.build_prompt(context)
        
        # Extract system and user prompts
        system_prompt = ""
        user_prompt = ""
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            elif msg["role"] == "user":
                user_prompt = msg["content"]
        
        # Create chain
        chain = self.create_chain(response_model)
        
        # Run chain asynchronously
        result = await chain.ainvoke({
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        })
        
        # Convert to dict
        analysis = result.model_dump() if hasattr(result, 'model_dump') else result.dict()
        
        # Return in same format as agent.analyze_structured()
        return {
            "agent_name": self.agent.name,
            "analysis": analysis,
            "metadata": {
                "structured": True,
                "langchain": True,
                "model_type": response_model.__name__,
            }
        }
