"""
Unified input processing endpoint for Merlin.
Handles all user interactions through the Strands Agents architecture with YAML configuration.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from app.config import get_config_manager
from app.agents.agent_factory import get_agent_factory
from app.routing import get_routing_engine

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize configuration-driven components
config_manager = get_config_manager()
agent_factory = get_agent_factory()
routing_engine = get_routing_engine()


class ProcessInputRequest(BaseModel):
    """Request model for unified input processing."""
    input_text: str
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ProcessInputResponse(BaseModel):
    """Response model for unified input processing."""
    success: bool
    agent_type: str
    action: str
    result: Optional[Dict[str, Any]] = None
    message: str
    error: Optional[str] = None
    processing_metadata: Optional[Dict[str, Any]] = None


@router.post("/process", response_model=ProcessInputResponse)
def process_input(request: ProcessInputRequest):
    """
    Unified endpoint for processing all user inputs using YAML configuration.
    
    This endpoint:
    1. Routes the input using the YAML routing engine
    2. Dynamically loads and delegates to the appropriate agent
    3. Returns a structured response
    """
    try:
        # Step 1: Route the input using configuration-driven routing
        routing_decision = routing_engine.route_input(request.input_text, request.user_id)
        
        agent_type = routing_decision.agent_type
        action = routing_decision.action
        confidence = routing_decision.confidence
        reasoning = routing_decision.reasoning
        
        logger.info(f"Routing decision: {agent_type} -> {action} (confidence: {confidence})")
        
        # Step 2: Get the appropriate agent dynamically
        try:
            agent = agent_factory.get_agent(agent_type)
        except Exception as e:
            logger.error(f"Failed to get agent '{agent_type}': {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load agent '{agent_type}': {str(e)}"
            )
        
        # Step 3: Prepare input data for the agent
        input_data = {
            'input_text': request.input_text,
            'user_id': request.user_id or 'default_user',
            'metadata': request.metadata or {},
            'action': action
        }
        
        # Step 4: Process with the appropriate agent
        agent_result = None
        
        try:
            # Route to the appropriate agent method based on agent type and action
            if agent_type == 'ingestion':
                agent_result = agent.process_ingestion(action, input_data)
                    
            elif agent_type == 'query':
                agent_result = agent.process_query(action, input_data)
                    
            elif agent_type == 'summarization':
                agent_result = agent.process_summarization(action, input_data)
                    
            elif agent_type == 'knowledge_gap':
                if action == 'detect_gaps':
                    agent_result = agent.detect_gaps(
                        input_data.get('user_id', 'default_user'),
                        input_data.get('timeframe', '30d')
                    )
                elif action == 'get_user_knowledge_gaps':
                    agent_result = agent.get_user_knowledge_gaps(
                        input_data.get('user_id', 'default_user'),
                        input_data.get('resolved', False)
                    )
                else:
                    agent_result = agent.detect_gaps(
                        input_data.get('user_id', 'default_user')
                    )
                    
            elif agent_type == 'conversational_query':
                agent_result = agent.process_conversational_query(
                    request.input_text,
                    input_data.get('user_id', 'default_user'),
                    input_data.get('session_id'),
                    input_data.get('context', {})
                )
                
            elif agent_type == 'learning_path':
                if action == 'suggest_learning_path':
                    agent_result = agent.suggest_learning_path(
                        input_data.get('user_id', 'default_user'),
                        input_data.get('topic'),
                        input_data.get('current_level'),
                        input_data.get('objectives')
                    )
                elif action == 'get_user_learning_paths':
                    agent_result = agent.get_user_learning_paths(
                        input_data.get('user_id', 'default_user')
                    )
                else:
                    agent_result = agent.suggest_learning_path(
                        input_data.get('user_id', 'default_user')
                    )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown agent type: {agent_type}"
                )
                
        except Exception as e:
            logger.error(f"Error processing with agent '{agent_type}': {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing with agent '{agent_type}': {str(e)}"
            )
        
        # Step 5: Return structured response
        return ProcessInputResponse(
            success=True,
            agent_type=agent_type,
            action=action,
            result=agent_result,
            message=f"Successfully processed input using {agent_type} agent",
            processing_metadata={
                "routing_confidence": confidence,
                "routing_reasoning": reasoning,
                "agent_type": agent_type,
                "action": action,
                "input_length": len(request.input_text),
                "configuration_driven": True
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing input: {e}")
        return ProcessInputResponse(
            success=False,
            agent_type="unknown",
            action="error",
            result=None,
            message=f"Error processing input: {str(e)}",
            error=str(e),
            processing_metadata={
                "error_type": type(e).__name__,
                "input_length": len(request.input_text),
                "configuration_driven": True
            }
        )


@router.get("/agents/info")
async def get_agents_info():
    """Get information about available agents and their capabilities."""
    try:
        # Get all available agents from configuration
        available_agents = config_manager.get_available_agents()
        agents_info = {}
        
        for agent_name in available_agents:
            try:
                agent = agent_factory.get_agent(agent_name)
                agents_info[agent_name] = agent.get_capabilities()
            except Exception as e:
                logger.warning(f"Failed to get capabilities for agent '{agent_name}': {e}")
                agents_info[agent_name] = {"error": str(e)}
        
        return {
            "available_agents": available_agents,
            "agents_info": agents_info,
            "configuration_driven": True
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agents info: {str(e)}"
        )


@router.get("/agents/{agent_type}/capabilities")
async def get_agent_capabilities(agent_type: str):
    """Get detailed capabilities for a specific agent."""
    try:
        # Check if agent exists in configuration
        available_agents = config_manager.get_available_agents()
        if agent_type not in available_agents:
            raise HTTPException(
                status_code=404,
                detail=f"Agent type '{agent_type}' not found in configuration"
            )
        
        # Get agent and its capabilities
        agent = agent_factory.get_agent(agent_type)
        capabilities = agent.get_capabilities()
        
        # Add configuration information
        agent_config = config_manager.get_agent_config(agent_type)
        capabilities["configuration"] = {
            "name": agent_config.name,
            "description": agent_config.description,
            "type": agent_config.type,
            "framework": agent_config.framework,
            "model": agent_config.model,
            "capabilities": agent_config.capabilities,
            "input_types": agent_config.input_types,
            "output_format": agent_config.output_format,
            "tools": agent_config.tools
        }
        
        return capabilities
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent capabilities: {str(e)}"
        )


@router.get("/routing/rules")
async def get_routing_rules():
    """Get information about routing rules."""
    try:
        rules_info = routing_engine.get_routing_rules_info()
        return {
            "routing_rules": rules_info,
            "total_rules": len(rules_info),
            "configuration_driven": True
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get routing rules: {str(e)}"
        )


@router.post("/agents/{agent_type}/validate")
async def validate_agent_input(agent_type: str, request: Dict[str, Any]):
    """Validate input for a specific agent."""
    try:
        # Check if agent exists in configuration
        available_agents = config_manager.get_available_agents()
        if agent_type not in available_agents:
            raise HTTPException(
                status_code=404,
                detail=f"Agent type '{agent_type}' not found in configuration"
            )
        
        action = request.get('action')
        input_data = request.get('input_data', {})
        
        # Get agent and validate input
        agent = agent_factory.get_agent(agent_type)
        is_valid = agent.validate_input(action, input_data)
        
        return {
            'valid': is_valid,
            'agent_type': agent_type,
            'action': action,
            'message': 'Input is valid' if is_valid else 'Input validation failed',
            'configuration_driven': True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )


@router.get("/tags")
async def get_all_tags():
    """Get all unique tags from the database with their counts"""
    try:
        from db.crud import get_all_notes
        from collections import Counter
        
        notes = get_all_notes()
        all_tags = []
        
        for note in notes:
            if note.tags:
                all_tags.extend(note.tags)
        
        # Count tag frequency
        tag_counts = Counter(all_tags)
        
        # Sort by frequency (most popular first)
        popular_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "success": True,
            "tags": [{"tag": tag, "count": count} for tag, count in popular_tags],
            "total_unique_tags": len(tag_counts)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "tags": [],
            "total_unique_tags": 0
        }


@router.get("/config/reload")
async def reload_configuration():
    """Reload configuration from YAML file."""
    try:
        from app.config import reload_config
        from app.agents.agent_factory import reload_agents
        
        # Reload configuration and agents
        reload_config()
        reload_agents()
        
        return {
            "success": True,
            "message": "Configuration and agents reloaded successfully",
            "timestamp": "N/A"  # Could add actual timestamp
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reload configuration: {str(e)}"
        )
