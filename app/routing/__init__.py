"""
Routing package for Merlin Personal Knowledge Curator.
"""

from .routing_engine import RoutingEngine, RoutingDecision, get_routing_engine, route_input

__all__ = ['RoutingEngine', 'RoutingDecision', 'get_routing_engine', 'route_input']
