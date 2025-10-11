from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.routes.process_input import router as process_input_router
import traceback

# Create FastAPI app
app = FastAPI(
    title="Merlin - Personal Knowledge Curator",
    description="AI-powered personal knowledge curation system with Strands Agents architecture",
    version="2.0.0"
)

# Enable CORS for local development (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom exception handler for serialization errors
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions including serialization errors."""
    error_details = traceback.format_exc()
    print(f"API Error: {exc}")
    print(f"Traceback: {error_details}")
    
    # Check if it's a serialization error
    if "PydanticSerializationError" in str(exc) or "Unable to serialize" in str(exc):
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Data serialization error - please try again",
                "detail": "The response contained data that couldn't be serialized to JSON"
            }
        )
    
    # For other errors, return generic error
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc)
        }
    )

# Include routers
app.include_router(process_input_router, prefix="/api/v1", tags=["agents"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Merlin - Personal Knowledge Curator API",
        "version": "2.0.0",
        "architecture": "Strands Agents",
        "endpoints": {
            "process_input": "/api/v1/process",
            "agents_info": "/api/v1/agents/info",
            "agent_capabilities": "/api/v1/agents/{agent_type}/capabilities",
            "validate_input": "/api/v1/agents/{agent_type}/validate"
        },
        "agents": ["router", "ingestion", "query", "summarization"]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "merlin-api"}

@app.post("/test")
async def test_endpoint(data: dict):
    """Test endpoint for debugging."""
    return {"received": data, "status": "ok"}

@app.post("/test-ingestion")
def test_ingestion():
    """Test ingestion agent directly."""
    try:
        from app.routes.process_input import ingestion_agent
        result = ingestion_agent.process_ingestion('ingest_url', {'url': 'https://example.com'})
        return {"success": result.get('success', False), "message": "Ingestion test completed"}
    except Exception as e:
        import traceback
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}
