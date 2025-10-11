"""
Strands-compatible Router Agent for Merlin.
Uses the actual Strands framework for intelligent routing.
"""

import os
from typing import Dict, Any, Optional
from strands import Agent
from strands.models.anthropic import AnthropicModel
from app.agents.tools.content_fetcher import is_url, extract_content_from_input
from pydantic import BaseModel, Field


class RoutingDecision(BaseModel):
    """Structured output for routing decisions."""
    agent_type: str = Field(description="The agent type to route to: 'ingestion', 'query', or 'summarization'")
    action: str = Field(description="The specific action to take")
    confidence: float = Field(description="Confidence score between 0 and 1", ge=0, le=1)
    reasoning: str = Field(description="Brief explanation of the routing decision")


class StrandsRouterAgent:
    """
    Router agent using Strands framework to intelligently classify user input.
    """
    
    def __init__(self):
        self.name = "StrandsRouterAgent"
        self.description = "Intelligent input classification using Strands and Claude"
        
        # Initialize Claude model via Strands
        self.model = AnthropicModel(
            client_args={
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
            },
            max_tokens=512,
            model_id="claude-3-5-haiku-20241022",  # Using PRIMARY_MODEL
            params={
                "temperature": 0.1,  # Low temperature for consistent routing
            }
        )
        
        # Create Strands agent with routing capabilities
        self.agent = Agent(
            model=self.model,
            system_prompt=self._get_routing_prompt()
        )
    
    def _get_routing_prompt(self) -> str:
        """Get the system prompt for routing decisions."""
        return """You are Merlin's intelligent router agent. Your job is to analyze user input and determine which specialized agent should handle it.

Available agents and their purposes:
- **ingestion**: For URLs and text content that should be saved to the knowledge base
- **query**: For search questions and information retrieval requests  
- **summarization**: For requests to summarize or analyze existing content

Routing rules:
1. URLs (http/https) → ingestion agent with action "ingest_url"
2. Questions starting with "what", "how", "where", "when", "who", "find", "search" → query agent with action "search"
3. Text starting with "summarize", "summary", "brief", "overview" → summarization agent with action "summarize_existing"
4. Long text content (paragraphs) → ingestion agent with action "ingest_text"
5. Empty or minimal input → query agent with action "empty_input"

Always provide structured output with agent_type, action, confidence, and reasoning."""
    
    def classify_input(self, user_input: str) -> Dict[str, Any]:
        """
        Classify user input using Strands and Claude.
        
        Returns:
            Dict containing routing decision and processed input data
        """
        if not user_input or not user_input.strip():
            return {
                'agent_type': 'query',
                'action': 'empty_input',
                'input_data': {'original_input': user_input},
                'confidence': 1.0,
                'reasoning': 'Empty input - showing recent notes'
            }
        
        user_input = user_input.strip()
        
        # Extract basic content information
        title, content, input_type = extract_content_from_input(user_input)
        
        # Prepare input for Claude analysis
        analysis_input = f"""
User Input: "{user_input}"
Input Type: {input_type}
Content Length: {len(content) if content else 0} characters

Please analyze this input and provide a routing decision.
"""
        
        try:
            # Use Strands structured output for routing decision
            routing_decision = self.agent.structured_output(
                RoutingDecision,
                analysis_input
            )
            
            # Prepare input data based on routing decision
            input_data = self._prepare_input_data(
                routing_decision.agent_type,
                routing_decision.action,
                user_input,
                title,
                content,
                input_type
            )
            
            return {
                'agent_type': routing_decision.agent_type,
                'action': routing_decision.action,
                'input_data': input_data,
                'confidence': routing_decision.confidence,
                'reasoning': routing_decision.reasoning
            }
            
        except Exception as e:
            # Fallback to simple routing if Claude fails
            print(f"Strands routing failed, using fallback: {e}")
            return self._fallback_routing(user_input, title, content, input_type)
    
    def _prepare_input_data(self, agent_type: str, action: str, original_input: str, 
                           title: Optional[str], content: Optional[str], input_type: str) -> Dict[str, Any]:
        """Prepare input data based on the routing decision."""
        base_data = {
            'original_input': original_input,
            'input_type': input_type
        }
        
        if agent_type == 'ingestion':
            if action == 'ingest_url':
                return {
                    **base_data,
                    'url': original_input,
                    'title': title,
                    'content': content
                }
            elif action == 'ingest_text':
                return {
                    **base_data,
                    'title': title,
                    'content': content
                }
        
        elif agent_type == 'query':
            if action == 'search':
                return {
                    **base_data,
                    'query': content or original_input,
                    'search_type': 'semantic'
                }
            elif action == 'empty_input':
                return base_data
        
        elif agent_type == 'summarization':
            return {
                **base_data,
                'content': content or original_input
            }
        
        # Default fallback
        return base_data
    
    def _fallback_routing(self, user_input: str, title: Optional[str], 
                         content: Optional[str], input_type: str) -> Dict[str, Any]:
        """Fallback routing logic if Claude is unavailable."""
        if input_type == 'url':
            return {
                'agent_type': 'ingestion',
                'action': 'ingest_url',
                'input_data': {
                    'url': user_input,
                    'title': title,
                    'content': content,
                    'original_input': user_input
                },
                'confidence': 0.95,
                'reasoning': 'URL detected - routing to ingestion'
            }
        
        elif input_type == 'text':
            # Simple keyword-based routing
            text_lower = content.lower() if content else user_input.lower()
            
            if any(word in text_lower for word in ['summarize', 'summary', 'brief', 'overview']):
                return {
                    'agent_type': 'summarization',
                    'action': 'summarize_existing',
                    'input_data': {
                        'content': content or user_input,
                        'original_input': user_input
                    },
                    'confidence': 0.8,
                    'reasoning': 'Summarization keywords detected'
                }
            
            elif any(word in text_lower for word in ['what', 'how', 'where', 'when', 'who', 'find', 'search']):
                return {
                    'agent_type': 'query',
                    'action': 'search',
                    'input_data': {
                        'query': content or user_input,
                        'search_type': 'semantic',
                        'original_input': user_input
                    },
                    'confidence': 0.9,
                    'reasoning': 'Question keywords detected'
                }
            
            else:
                return {
                    'agent_type': 'ingestion',
                    'action': 'ingest_text',
                    'input_data': {
                        'title': title,
                        'content': content or user_input,
                        'original_input': user_input
                    },
                    'confidence': 0.85,
                    'reasoning': 'Text content - routing to ingestion'
                }
        
        # Final fallback
        return {
            'agent_type': 'query',
            'action': 'search',
            'input_data': {
                'query': user_input,
                'search_type': 'semantic',
                'original_input': user_input
            },
            'confidence': 0.5,
            'reasoning': 'Fallback routing to query'
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get information about agent capabilities."""
        return {
            'name': self.name,
            'description': self.description,
            'framework': 'Strands',
            'model': 'claude-3-5-haiku-20241022',
            'capabilities': [
                'intelligent_input_classification',
                'structured_output_routing',
                'confidence_scoring',
                'reasoning_explanation'
            ],
            'supported_agents': ['ingestion', 'query', 'summarization'],
            'output_format': 'structured_routing_decision'
        }
    
    def validate_routing(self, routing_result: Dict[str, Any]) -> bool:
        """Validate that the routing result is properly formatted."""
        required_fields = ['agent_type', 'action', 'input_data', 'confidence']
        
        if not all(field in routing_result for field in required_fields):
            return False
        
        valid_agents = ['ingestion', 'query', 'summarization']
        if routing_result['agent_type'] not in valid_agents:
            return False
        
        confidence = routing_result['confidence']
        if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
            return False
        
        return True
