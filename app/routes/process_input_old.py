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
    Unified endpoint for processing all user inputs.
    
    This endpoint:
    1. Routes the input to the appropriate agent using RouterAgent
    2. Delegates processing to the specialized agent
    3. Returns a structured response
    """
    try:
        # Step 1: Route the input
        routing_result = router_agent.classify_input(request.input_text)
        
        if not router_agent.validate_routing(routing_result):
            raise HTTPException(
                status_code=400, 
                detail="Invalid routing result from router agent"
            )
        
        agent_type = routing_result['agent_type']
        action = routing_result['action']
        input_data = routing_result['input_data']
        confidence = routing_result['confidence']
        
        # Add request metadata to input data
        input_data['user_id'] = request.user_id
        input_data['metadata'] = request.metadata or {}
        
        # Step 2: Process with appropriate agent
        agent_result = None
        
        if agent_type == 'ingestion':
            agent_result = ingestion_agent.process_ingestion(action, input_data)
        elif agent_type == 'query':
            agent_result = query_agent.process_query(action, input_data)
        elif agent_type == 'summarization':
            agent_result = summarization_agent.process_summarization(action, input_data)
        elif agent_type == 'knowledge_gap':
            if action == 'detect_gaps':
                agent_result = knowledge_gap_agent.detect_gaps(
                    input_data.get('user_id', 'default_user'),
                    input_data.get('timeframe', '30d')
                )
            elif action == 'get_user_knowledge_gaps':
                agent_result = knowledge_gap_agent.get_user_knowledge_gaps(
                    input_data.get('user_id', 'default_user'),
                    input_data.get('resolved', False)
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown action '{action}' for knowledge_gap agent"
                )
        elif agent_type == 'conversational_query':
            if action == 'process_conversational_query':
                agent_result = conversational_query_agent.process_conversational_query(
                    input_data.get('query', request.input_text),
                    input_data.get('user_id', 'default_user'),
                    input_data.get('session_id'),
                    input_data.get('context')
                )
            elif action == 'get_conversation_history':
                agent_result = conversational_query_agent.get_conversation_history(
                    input_data.get('user_id', 'default_user'),
                    input_data.get('session_id'),
                    input_data.get('limit', 10)
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown action '{action}' for conversational_query agent"
                )
        elif agent_type == 'learning_path':
            if action == 'suggest_learning_path':
                agent_result = learning_path_agent.suggest_learning_path(
                    input_data.get('user_id', 'default_user'),
                    input_data.get('topic'),
                    input_data.get('current_level'),
                    input_data.get('objectives')
                )
            elif action == 'get_user_learning_paths':
                agent_result = learning_path_agent.get_user_learning_paths(
                    input_data.get('user_id', 'default_user')
                )
            elif action == 'update_learning_progress':
                agent_result = learning_path_agent.update_learning_progress(
                    input_data.get('path_id'),
                    input_data.get('progress_data')
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown action '{action}' for learning_path agent"
                )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown agent type: {agent_type}"
            )
        
        # Step 3: Prepare response
        if agent_result['success']:
            return ProcessInputResponse(
                success=True,
                agent_type=agent_type,
                action=action,
                result=agent_result['result'],
                message=agent_result.get('message', 'Processing completed successfully'),
                processing_metadata={
                    'routing_confidence': confidence,
                    'agent_used': agent_type,
                    'action_performed': action,
                    'input_length': len(request.input_text),
                    'user_id': request.user_id
                }
            )
        else:
            return ProcessInputResponse(
                success=False,
                agent_type=agent_type,
                action=action,
                error=agent_result.get('error', 'Processing failed'),
                message="Processing failed",
                processing_metadata={
                    'routing_confidence': confidence,
                    'agent_used': agent_type,
                    'action_attempted': action,
                    'input_length': len(request.input_text),
                    'user_id': request.user_id
                }
            )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"API Error: {e}")
        print(f"Traceback: {error_details}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/agents/info")
async def get_agents_info():
    """Get information about available agents and their capabilities."""
    try:
        return {
            'router_agent': router_agent.get_capabilities(),
            'ingestion_agent': ingestion_agent.get_capabilities(),
            'query_agent': query_agent.get_capabilities(),
            'summarization_agent': summarization_agent.get_capabilities(),
            'knowledge_gap_agent': knowledge_gap_agent.get_capabilities(),
            'conversational_query_agent': conversational_query_agent.get_capabilities(),
            'learning_path_agent': learning_path_agent.get_capabilities()
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
        if agent_type == 'router':
            return router_agent.get_capabilities()
        elif agent_type == 'ingestion':
            return ingestion_agent.get_capabilities()
        elif agent_type == 'query':
            return query_agent.get_capabilities()
        elif agent_type == 'summarization':
            return summarization_agent.get_capabilities()
        elif agent_type == 'knowledge_gap':
            return knowledge_gap_agent.get_capabilities()
        elif agent_type == 'conversational_query':
            return conversational_query_agent.get_capabilities()
        elif agent_type == 'learning_path':
            return learning_path_agent.get_capabilities()
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Agent type '{agent_type}' not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent capabilities: {str(e)}"
        )


@router.post("/agents/{agent_type}/validate")
async def validate_agent_input(agent_type: str, request: Dict[str, Any]):
    """Validate input for a specific agent."""
    try:
        action = request.get('action')
        input_data = request.get('input_data', {})
        
        if agent_type == 'ingestion':
            is_valid = ingestion_agent.validate_input(action, input_data)
        elif agent_type == 'query':
            is_valid = query_agent.validate_input(action, input_data)
        elif agent_type == 'summarization':
            is_valid = summarization_agent.validate_input(action, input_data)
        elif agent_type == 'knowledge_gap':
            is_valid = knowledge_gap_agent.validate_input(action, input_data)
        elif agent_type == 'conversational_query':
            is_valid = conversational_query_agent.validate_input(action, input_data)
        elif agent_type == 'learning_path':
            is_valid = learning_path_agent.validate_input(action, input_data)
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Agent type '{agent_type}' not found"
            )
        
        return {
            'valid': is_valid,
            'agent_type': agent_type,
            'action': action,
            'message': 'Input is valid' if is_valid else 'Input validation failed'
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
