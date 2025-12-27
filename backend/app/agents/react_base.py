"""
ReAct Agent Base Classes

Base implementation for ReAct (Reasoning + Acting) agents.
"""
from typing import Dict, Any, List, Optional, Callable
from sqlalchemy.orm import Session
import json
import re

from app.agents.base import DecisionAgent
from app.agents.llm_client import LLMClient
from app.core.config import settings


class ReActAgent(DecisionAgent):
    """
    Base class for ReAct agents that can reason and take actions.
    
    ReAct Pattern:
    1. Thought: Reason about what to do next
    2. Action: Execute a tool
    3. Observation: Observe the result
    4. Repeat until Final Answer
    """
    
    def __init__(
        self,
        db: Session,
        llm_client: Optional[LLMClient] = None,
        model: Optional[str] = None,
        max_iterations: int = 5
    ):
        """
        Initialize ReAct agent.
        
        Args:
            db: Database session
            llm_client: Optional LLM client
            model: Optional model override
            max_iterations: Maximum ReAct iterations before forcing conclusion
        """
        super().__init__(db, llm_client, model)
        self.max_iterations = max_iterations
        self.tools = self.initialize_tools()
    
    def initialize_tools(self) -> Dict[str, Callable]:
        """
        Initialize available tools for this agent.
        
        Returns:
            Dict mapping tool names to callable functions
        """
        raise NotImplementedError("Subclass must implement initialize_tools()")
    
    def get_tool_descriptions(self) -> str:
        """
        Get formatted descriptions of available tools.
        
        Returns:
            Formatted tool descriptions for prompt
        """
        descriptions = []
        for name, func in self.tools.items():
            # Extract docstring
            doc = func.__doc__ or "No description available"
            # Clean up docstring
            doc = doc.strip().split('\n')[0]
            descriptions.append(f"- {name}: {doc}")
        
        return "\n".join(descriptions)
    
    def parse_react_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response to extract thought, action, or final answer.
        
        Expected format:
        Thought: [reasoning]
        Action: tool_name(arg1="value1", arg2="value2")
        
        OR
        
        Final Answer: [structured JSON response]
        
        Args:
            response: Raw LLM response
            
        Returns:
            Parsed dict with type, content, and optionally tool/args
        """
        response = response.strip()
        
        # Check for Final Answer
        if "Final Answer:" in response or "FINAL ANSWER:" in response:
            # Extract JSON after Final Answer
            match = re.search(r'Final Answer:\s*({.*})', response, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    answer_json = json.loads(match.group(1))
                    return {
                        "type": "final_answer",
                        "content": answer_json
                    }
                except json.JSONDecodeError:
                    # If JSON parsing fails, return raw text
                    final_part = response.split("Final Answer:", 1)[1].strip()
                    return {
                        "type": "final_answer",
                        "content": final_part
                    }
        
        # Parse Thought and Action
        thought = None
        action = None
        action_args = {}
        
        # Extract Thought
        thought_match = re.search(r'Thought:\s*(.+?)(?=\nAction:|\Z)', response, re.IGNORECASE | re.DOTALL)
        if thought_match:
            thought = thought_match.group(1).strip()
        
        # Extract Action
        action_match = re.search(r'Action:\s*(\w+)\((.*?)\)', response, re.IGNORECASE | re.DOTALL)
        if action_match:
            action = action_match.group(1)
            args_str = action_match.group(2)
            
            # Parse arguments (simple key=value parser)
            if args_str:
                for arg in args_str.split(','):
                    arg = arg.strip()
                    if '=' in arg:
                        key, value = arg.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        
                        # Try to parse as JSON for complex values
                        try:
                            value = json.loads(value)
                        except:
                            pass
                        
                        action_args[key] = value
        
        return {
            "type": "action",
            "thought": thought,
            "action": action,
            "action_args": action_args
        }
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Execute a tool by name with given arguments.
        
        Args:
            tool_name: Name of tool to execute
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result
        """
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}"}
        
        tool_func = self.tools[tool_name]
        
        try:
            # Execute tool (handle both sync and async)
            import asyncio
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**kwargs)
            else:
                result = tool_func(**kwargs)
            
            return result
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
    
    def build_react_prompt(
        self,
        task_description: str,
        context: Dict[str, Any],
        history: List[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """
        Build ReAct prompt with task, tools, and history.
        
        Args:
            task_description: Description of the task
            context: Context data
            history: Previous thought/action/observation cycles
            
        Returns:
            Prompt messages
        """
        tool_descriptions = self.get_tool_descriptions()
        
        system_prompt = f"""You are a ReAct agent that reasons step-by-step and uses tools to accomplish tasks.

**REACT PATTERN:**
You must alternate between Thought, Action, and Observation until you reach a Final Answer.

**FORMAT:**
Thought: [Your reasoning about what to do next]
Action: tool_name(arg1="value1", arg2="value2")

After seeing the Observation, continue with another Thought/Action cycle, or provide:

Final Answer: {{"key": "value", ...}}

**AVAILABLE TOOLS:**
{tool_descriptions}

**RULES:**
1. Always start with a Thought
2. Use tools to gather information or perform actions
3. After each Action, wait for the Observation
4. Maximum {self.max_iterations} iterations
5. Provide Final Answer as valid JSON
6. Show your reasoning clearly in Thoughts
7. If a tool returns an error, try a different approach

**TASK:**
{task_description}
"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add history of previous iterations
        if history:
            history_text = "\n\n**PREVIOUS ITERATIONS:**\n"
            for i, item in enumerate(history, 1):
                if item["type"] == "thought":
                    history_text += f"\nIteration {i}:\nThought: {item['content']}\n"
                elif item["type"] == "action":
                    history_text += f"Action: {item['content']}\n"
                elif item["type"] == "observation":
                    history_text += f"Observation: {item['content']}\n"
            
            messages.append({"role": "assistant", "content": history_text})
        
        # Add current context
        context_str = json.dumps(context, indent=2, default=str)
        user_prompt = f"""**CONTEXT:**
{context_str}

Begin your analysis. Remember to follow the ReAct pattern: Thought → Action → (wait for Observation) → repeat or Final Answer."""
        
        messages.append({"role": "user", "content": user_prompt})
        
        return messages
    
    async def react_loop(
        self,
        task_description: str,
        context: Dict[str, Any],
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Execute the ReAct loop: Thought → Action → Observation → repeat.
        
        Args:
            task_description: Task to accomplish
            context: Context data
            temperature: LLM temperature
            
        Returns:
            Final analysis result
        """
        history = []
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            
            # Build prompt with history
            messages = self.build_react_prompt(task_description, context, history)
            
            # Get LLM response
            llm_response = await self.llm_client.acall(
                messages=messages,
                model=self.model,
                agent_name=self.name,
                temperature=temperature
            )
            
            response_text = llm_response["content"]
            
            # Parse response
            parsed = self.parse_react_response(response_text)
            
            if parsed["type"] == "final_answer":
                # Done! Return the answer
                return {
                    "agent": self.name,
                    "model": self.model,
                    "analysis": parsed["content"],
                    "metadata": {
                        "iterations": iteration,
                        "history": history,
                        "total_tokens": llm_response.get("total_tokens", 0),
                        "cost": llm_response.get("cost", 0),
                        "latency": llm_response.get("latency", 0)
                    }
                }
            
            elif parsed["type"] == "action":
                # Record thought
                if parsed.get("thought"):
                    history.append({
                        "type": "thought",
                        "content": parsed["thought"]
                    })
                
                # Record action
                action_str = f"{parsed['action']}({', '.join(f'{k}={v}' for k, v in parsed['action_args'].items())})"
                history.append({
                    "type": "action",
                    "content": action_str
                })
                
                # Execute tool
                observation = await self.execute_tool(
                    parsed["action"],
                    **parsed["action_args"]
                )
                
                # Record observation
                observation_str = json.dumps(observation, indent=2, default=str) if isinstance(observation, dict) else str(observation)
                history.append({
                    "type": "observation",
                    "content": observation_str
                })
                
                # Continue to next iteration
                continue
            
            else:
                # Couldn't parse response, force conclusion
                print(f"WARNING: Could not parse ReAct response at iteration {iteration}")
                break
        
        # Max iterations reached, force final answer
        return {
            "agent": self.name,
            "model": self.model,
            "analysis": {
                "error": "Max iterations reached without final answer",
                "last_history": history[-3:] if len(history) >= 3 else history
            },
            "metadata": {
                "iterations": iteration,
                "history": history,
                "max_iterations_reached": True
            }
        }
