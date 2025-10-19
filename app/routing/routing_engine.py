"""
Routing Engine for intelligent agent routing based on YAML configuration rules.
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from app.config import get_config_manager
from app.agents.tools.content_fetcher import is_url

logger = logging.getLogger(__name__)


class RoutingDecision:
    """Represents a routing decision."""
    
    def __init__(self, agent_type: str, action: str, confidence: float, reasoning: str):
        self.agent_type = agent_type
        self.action = action
        self.confidence = confidence
        self.reasoning = reasoning
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'agent_type': self.agent_type,
            'action': self.action,
            'confidence': self.confidence,
            'reasoning': self.reasoning
        }


class RoutingEngine:
    """
    Engine for routing user inputs to appropriate agents based on YAML configuration rules.
    """
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.routing_rules = self.config_manager.get_routing_rules()
        
        # Compile regex patterns for better performance
        self._compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for routing conditions."""
        patterns = {}
        
        # URL pattern
        patterns['url'] = re.compile(
            r'^https?://[^\s/$.?#].[^\s]*$',
            re.IGNORECASE
        )
        
        # Temporal references pattern
        patterns['temporal'] = re.compile(
            r'\b(yesterday|today|tomorrow|last week|next week|last month|next month|'
            r'last year|next year|recently|lately|ago|before|after|since|until|'
            r'january|february|march|april|may|june|july|august|september|'
            r'october|november|december|monday|tuesday|wednesday|thursday|'
            r'friday|saturday|sunday)\b',
            re.IGNORECASE
        )
        
        # Knowledge gap keywords pattern
        patterns['knowledge_gap'] = re.compile(
            r'\b(gap|missing|don\'t know|unfamiliar|learn about|understand|'
            r'knowledge gap|what should I learn|what do I need to know|'
            r'help me learn|teach me about)\b',
            re.IGNORECASE
        )
        
        # Learning path keywords pattern
        patterns['learning_path'] = re.compile(
            r'\b(learning path|study plan|curriculum|course|tutorial|guide|'
            r'step by step|beginner to advanced|roadmap|learning journey|'
            r'how to learn|where to start|what to study next)\b',
            re.IGNORECASE
        )
        
        # Summarization keywords pattern
        patterns['summarization'] = re.compile(
            r'\b(summarize|summary|sum up|brief|overview|key points|main ideas|'
            r'what are the highlights|give me a summary)\b',
            re.IGNORECASE
        )
        
        # Question pattern
        patterns['question'] = re.compile(
            r'^\s*[?].*|.*\?$|^\s*(what|how|why|when|where|who|which|can|could|'
            r'would|should|do|does|did|is|are|was|were|have|has|had)\b',
            re.IGNORECASE
        )
        
        return patterns
    
    def _evaluate_condition(self, condition: str, input_text: str) -> bool:
        """
        Evaluate a routing condition against input text.
        
        Args:
            condition: The condition string from YAML
            input_text: User input text
            
        Returns:
            True if condition matches, False otherwise
        """
        input_text = input_text.strip()
        
        # Handle different condition types
        if condition == "input is URL":
            return is_url(input_text)
        
        elif condition == "input is empty or minimal":
            return len(input_text) <= 3 or not input_text.strip()
        
        elif condition == "input contains temporal references":
            return bool(self._compiled_patterns['temporal'].search(input_text))
        
        elif condition == "input contains knowledge gap keywords":
            return bool(self._compiled_patterns['knowledge_gap'].search(input_text))
        
        elif condition == "input contains learning path keywords":
            return bool(self._compiled_patterns['learning_path'].search(input_text))
        
        elif condition == "input contains summarization keywords":
            return bool(self._compiled_patterns['summarization'].search(input_text))
        
        elif condition == "input is question or search query":
            return bool(self._compiled_patterns['question'].search(input_text))
        
        elif condition == "input is long text content":
            return len(input_text) > 200 and not is_url(input_text)
        
        elif condition == "default fallback":
            return True
        
        else:
            logger.warning(f"Unknown routing condition: {condition}")
            return False
    
    def route_input(self, input_text: str, user_id: Optional[str] = None) -> RoutingDecision:
        """
        Route user input to the appropriate agent based on configuration rules.
        
        Args:
            input_text: User input text
            user_id: Optional user ID for context
            
        Returns:
            RoutingDecision object
        """
        input_text = input_text.strip()
        
        # Process routing rules in order
        for rule in self.routing_rules:
            try:
                if self._evaluate_condition(rule.condition, input_text):
                    reasoning = f"Input matches condition: '{rule.condition}'"
                    
                    # Generate more detailed reasoning
                    if rule.condition == "input is URL":
                        reasoning = f"Detected URL input: {input_text[:50]}..."
                    elif rule.condition == "input is question or search query":
                        reasoning = "Input appears to be a question or search query"
                    elif rule.condition == "input contains temporal references":
                        reasoning = "Input contains temporal references"
                    elif rule.condition == "input contains knowledge gap keywords":
                        reasoning = "Input indicates knowledge gap analysis request"
                    elif rule.condition == "input contains learning path keywords":
                        reasoning = "Input requests learning path generation"
                    elif rule.condition == "input contains summarization keywords":
                        reasoning = "Input requests content summarization"
                    elif rule.condition == "input is long text content":
                        reasoning = f"Input is long text content ({len(input_text)} characters)"
                    elif rule.condition == "input is empty or minimal":
                        reasoning = "Input is empty or minimal"
                    elif rule.condition == "default fallback":
                        reasoning = "No specific condition matched, using default fallback"
                    
                    logger.info(f"Routing decision: {rule.target_agent} -> {rule.action} "
                              f"(confidence: {rule.confidence})")
                    
                    return RoutingDecision(
                        agent_type=rule.target_agent,
                        action=rule.action,
                        confidence=rule.confidence,
                        reasoning=reasoning
                    )
            
            except Exception as e:
                logger.error(f"Error evaluating routing rule '{rule.condition}': {e}")
                continue
        
        # Fallback routing decision
        logger.warning("No routing rules matched, using fallback")
        return RoutingDecision(
            agent_type="query",
            action="search",
            confidence=0.3,
            reasoning="No routing rules matched, using fallback routing"
        )
    
    def get_routing_rules_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all routing rules.
        
        Returns:
            List of routing rule information dictionaries
        """
        rules_info = []
        for rule in self.routing_rules:
            rules_info.append({
                'condition': rule.condition,
                'target_agent': rule.target_agent,
                'action': rule.action,
                'confidence': rule.confidence
            })
        
        return rules_info
    
    def reload_rules(self) -> None:
        """Reload routing rules from configuration."""
        self.config_manager.reload_config()
        self.routing_rules = self.config_manager.get_routing_rules()
        self._compiled_patterns = self._compile_patterns()
        logger.info("Routing rules reloaded")


# Global routing engine instance
_routing_engine: Optional[RoutingEngine] = None


def get_routing_engine() -> RoutingEngine:
    """
    Get the global routing engine instance.
    
    Returns:
        RoutingEngine instance
    """
    global _routing_engine
    if _routing_engine is None:
        _routing_engine = RoutingEngine()
    return _routing_engine


def route_input(input_text: str, user_id: Optional[str] = None) -> RoutingDecision:
    """
    Route user input to the appropriate agent.
    
    Args:
        input_text: User input text
        user_id: Optional user ID for context
        
    Returns:
        RoutingDecision object
    """
    engine = get_routing_engine()
    return engine.route_input(input_text, user_id)
