"""
Unified input processing endpoint for Merlin.
Handles all user interactions through the Strands Agents architecture.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.agents.strands_router_agent import StrandsRouterAgent
from app.agents.strands_ingestion_agent import StrandsIngestionAgent
from app.agents.query_agent import QueryAgent
from app.agents.summarization_agent import SummarizationAgent

router = APIRouter()

# Initialize Strands-compatible agents
router_agent = StrandsRouterAgent()
ingestion_agent = StrandsIngestionAgent()
query_agent = QueryAgent()
summarization_agent = SummarizationAgent()


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
            'router_agent': {
                'name': 'RouterAgent',
                'description': 'Classifies user input and routes to appropriate agents',
                'supported_agent_types': ['ingestion', 'query', 'summarization']
            },
            'ingestion_agent': ingestion_agent.get_capabilities(),
            'query_agent': query_agent.get_capabilities(),
            'summarization_agent': summarization_agent.get_capabilities()
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
            return {
                'name': 'RouterAgent',
                'description': 'Classifies user input and routes to appropriate agents',
                'supported_agent_types': ['ingestion', 'query', 'summarization'],
                'routing_logic': 'Analyzes input type, content, and intent to determine appropriate agent'
            }
        elif agent_type == 'ingestion':
            return ingestion_agent.get_capabilities()
        elif agent_type == 'query':
            return query_agent.get_capabilities()
        elif agent_type == 'summarization':
            return summarization_agent.get_capabilities()
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
