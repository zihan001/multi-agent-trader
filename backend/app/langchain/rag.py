"""
RAG (Retrieval-Augmented Generation) module using ChromaDB.

Stores and retrieves market insights, trading patterns, and historical analyses
to enhance agent decision-making.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from app.core.config import settings


class MarketKnowledgeBase:
    """
    Vector database for storing and retrieving market insights.
    
    Uses ChromaDB (open-source) for vector storage and OpenAI embeddings.
    """
    
    def __init__(
        self,
        persist_directory: str = "./data/chromadb",
        collection_name: str = "market_insights",
    ):
        """
        Initialize knowledge base.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name of the collection
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.llm_api_key,
            openai_api_base=settings.openrouter_base_url if settings.llm_provider == "openrouter" else None,
        )
        
        # Initialize ChromaDB
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_directory,
        )
    
    def add_analysis(
        self,
        symbol: str,
        agent_name: str,
        analysis: Dict[str, Any],
        timestamp: Optional[datetime] = None,
    ) -> str:
        """
        Store an agent's analysis in the knowledge base.
        
        Args:
            symbol: Trading symbol
            agent_name: Name of the agent
            analysis: Analysis data
            timestamp: Timestamp of analysis (defaults to now)
            
        Returns:
            Document ID
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Create document with metadata
        content = self._format_analysis(agent_name, analysis)
        metadata = {
            "symbol": symbol,
            "agent": agent_name,
            "timestamp": timestamp.isoformat(),
            "type": "analysis",
        }
        
        doc = Document(page_content=content, metadata=metadata)
        
        # Add to vector store
        ids = self.vectorstore.add_documents([doc])
        return ids[0]
    
    def add_trade_outcome(
        self,
        symbol: str,
        trade_data: Optional[Dict[str, Any]] = None,
        outcome: str = "pending",
        # Legacy parameters for backward compatibility
        action: Optional[str] = None,
        entry_price: Optional[float] = None,
        exit_price: Optional[float] = None,
        pnl: Optional[float] = None,
        reasoning: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> str:
        """
        Store a trade outcome for learning.
        
        Args:
            symbol: Trading symbol
            trade_data: Dict with trade details (preferred)
            outcome: Trade outcome status (pending/win/loss)
            action: Trade action (buy/sell) - legacy
            entry_price: Entry price - legacy
            exit_price: Exit price (if closed) - legacy
            pnl: Profit/loss (if closed) - legacy
            reasoning: Reasoning for the trade - legacy
            timestamp: Timestamp (defaults to now)
            
        Returns:
            Document ID
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Support both dict-based and parameter-based calls
        if trade_data:
            action = trade_data.get("action", "unknown")
            entry_price = trade_data.get("entry_price", 0)
            exit_price = trade_data.get("exit_price")
            pnl = trade_data.get("pnl")
            reasoning = trade_data.get("reasoning", "")
        
        # Create document
        content = f"""
        Trade Outcome for {symbol}:
        Action: {action}
        Entry Price: ${entry_price:,.2f}
        Status: {outcome}
        """
        
        if exit_price:
            content += f"Exit Price: ${exit_price:,.2f}\n"
        if pnl is not None:
            content += f"PnL: ${pnl:,.2f} ({(pnl/entry_price)*100:.2f}%)\n"
        
        content += f"Reasoning: {reasoning}"
        
        # Build metadata, filtering out None values
        metadata = {
            "symbol": symbol,
            "type": "trade_outcome",
            "action": action or "unknown",
            "entry_price": entry_price or 0,
            "timestamp": timestamp.isoformat(),
        }
        
        if exit_price:
            metadata["exit_price"] = exit_price
        if pnl is not None:
            metadata["pnl"] = pnl
        
        # Filter out any remaining None values (ChromaDB doesn't accept them)
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        doc = Document(page_content=content, metadata=metadata)
        
        # Add to vector store
        ids = self.vectorstore.add_documents([doc])
        return ids[0]
    
    def retrieve_similar_analyses(
        self,
        query: str,
        symbol: Optional[str] = None,
        agent: Optional[str] = None,
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar past analyses.
        
        Args:
            query: Query string (e.g., current market context)
            symbol: Filter by symbol
            agent: Filter by agent name
            k: Number of results to return
            
        Returns:
            List of similar analyses with metadata
        """
        # Build metadata filter (ChromaDB $and operator for multiple conditions)
        conditions = [{"type": {"$eq": "analysis"}}]
        if symbol:
            conditions.append({"symbol": {"$eq": symbol}})
        if agent:
            conditions.append({"agent": {"$eq": agent}})
        
        # Combine with $and if multiple conditions, otherwise use single condition
        filter_dict = {"$and": conditions} if len(conditions) > 1 else conditions[0]
        
        # Search
        results = self.vectorstore.similarity_search(
            query,
            k=k,
            filter=filter_dict,
        )
        
        # Format results
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
            }
            for doc in results
        ]
    
    def retrieve_similar_trades(
        self,
        query: str,
        symbol: Optional[str] = None,
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar past trades and outcomes.
        
        Args:
            query: Query string (e.g., current market setup)
            symbol: Filter by symbol
            k: Number of results to return
            
        Returns:
            List of similar trades with outcomes
        """
        # Build metadata filter (ChromaDB $and operator for multiple conditions)
        conditions = [{"type": {"$eq": "trade"}}]
        if symbol:
            conditions.append({"symbol": {"$eq": symbol}})
        
        # Combine with $and if multiple conditions, otherwise use single condition
        filter_dict = {"$and": conditions} if len(conditions) > 1 else conditions[0]
        
        # Search
        results = self.vectorstore.similarity_search(
            query,
            k=k,
            filter=filter_dict,
        )
        
        # Format results
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
            }
            for doc in results
        ]
    
    def _format_analysis(self, agent_name: str, analysis: Dict[str, Any]) -> str:
        """
        Format analysis for embedding.
        
        Args:
            agent_name: Name of the agent
            analysis: Analysis data
            
        Returns:
            Formatted string
        """
        content = f"{agent_name} Analysis:\n"
        
        # Extract key fields
        if "recommendation" in analysis:
            content += f"Recommendation: {analysis['recommendation']}\n"
        if "confidence" in analysis:
            content += f"Confidence: {analysis['confidence']}%\n"
        if "reasoning" in analysis:
            content += f"Reasoning: {analysis['reasoning']}\n"
        if "key_observations" in analysis:
            content += f"Observations: {', '.join(analysis['key_observations'])}\n"
        if "risk_factors" in analysis:
            content += f"Risks: {', '.join(analysis['risk_factors'])}\n"
        
        return content
    
    def clear(self):
        """Clear all data from the collection."""
        self.vectorstore.delete_collection()
        
        # Recreate
        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
        )
