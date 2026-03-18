# services/graph_service.py
# This builds a NETWORK GRAPH of connections between users
# Think of it like a map showing who talks to who

import networkx as nx

# Create a global graph that stores all connections
# NetworkX is a Python library for network analysis
G = nx.DiGraph()  # DiGraph = Directed Graph (arrows showing direction)


def add_connection(from_user: str, to_user: str, interaction_type: str = "mentioned"):
    """
    Adds a connection between two users in the graph
    Example: user_A mentioned user_B in a post
    """
    # Add both users as "nodes" (dots on the map)
    G.add_node(from_user)
    G.add_node(to_user)

    # Add a connection "edge" (line between dots)
    if G.has_edge(from_user, to_user):
        # If connection already exists, increase its weight
        G[from_user][to_user]["weight"] += 1
        G[from_user][to_user]["interactions"].append(interaction_type)
    else:
        # Create new connection
        G.add_edge(
            from_user,
            to_user,
            weight=1,
            interaction_type=interaction_type,
            interactions=[interaction_type]
        )


def get_network_data() -> dict:
    """
    Returns the full network as nodes and edges
    This format is ready to display on a frontend chart
    """
    nodes = []
    edges = []

    # Build nodes list with risk info
    for node in G.nodes():
        nodes.append({
            "id": node,
            "label": node,
            "connections": G.degree(node)
        })

    # Build edges list
    for edge in G.edges(data=True):
        edges.append({
            "from": edge[0],
            "to": edge[1],
            "weight": edge[2].get("weight", 1),
            "interaction_type": edge[2].get("interaction_type", "unknown")
        })

    return {
        "nodes": nodes,
        "edges": edges,
        "total_users": len(nodes),
        "total_connections": len(edges)
    }


def get_user_connections(username: str) -> dict:
    """
    Gets all connections for a specific user
    """
    if username not in G.nodes():
        return {
            "username": username,
            "found": False,
            "message": "User not found in network"
        }

    # People this user connects TO
    outgoing = list(G.successors(username))

    # People who connect TO this user
    incoming = list(G.predecessors(username))

    return {
        "username": username,
        "found": True,
        "outgoing_connections": outgoing,
        "incoming_connections": incoming,
        "total_connections": G.degree(username)
    }


def analyze_network() -> dict:
    """
    Analyzes the entire network for suspicious patterns
    """
    if len(G.nodes()) == 0:
        return {"message": "Network is empty — submit some evidence first!"}

    # Find most connected users (potential hubs/influencers)
    degree_centrality = nx.degree_centrality(G)
    most_connected = sorted(
        degree_centrality.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]  # Top 5 most connected users

    return {
        "total_users": len(G.nodes()),
        "total_connections": len(G.edges()),
        "most_connected_users": [
            {"username": user, "centrality_score": round(score, 4)}
            for user, score in most_connected
        ],
        "network_density": round(nx.density(G), 4)
    }