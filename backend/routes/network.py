# routes/network.py
# API endpoints for network graph analysis

from fastapi import APIRouter
from pydantic import BaseModel
from services.graph_service import (
    add_connection,
    get_network_data,
    get_user_connections,
    analyze_network
)

router = APIRouter(
    prefix="/api/network",
    tags=["Network"]
)

class ConnectionInput(BaseModel):
    from_user: str
    to_user: str
    interaction_type: str = "mentioned"

# POST /api/network/connect
# Add a connection between two users
@router.post("/connect")
async def create_connection(input: ConnectionInput):
    add_connection(input.from_user, input.to_user, input.interaction_type)
    return {
        "success": True,
        "message": f"Connection added: {input.from_user} -> {input.to_user}"
    }

# GET /api/network/graph
# Get the full network graph data
@router.get("/graph")
async def get_graph():
    data = get_network_data()
    return {"success": True, "data": data}

# GET /api/network/analyze
# Get network analysis and suspicious patterns
@router.get("/analyze")
async def analyze():
    data = analyze_network()
    return {"success": True, "data": data}

# GET /api/network/user/{username}
# Get connections for a specific user
@router.get("/user/{username}")
async def get_user(username: str):
    data = get_user_connections(username)
    return {"success": True, "data": data}