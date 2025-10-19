"""
Agent Factory for dynamic agent instantiation based on YAML configuration.
"""

import importlib
import logging
from typing import Dict, Any, Optional, Type
from app.config import get_config_manager

logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Factory class for creating agent instances dynamically based on configuration.
    """
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self._agent_instances: Dict[str, Any] = {}
        self._agent_classes: Dict[str, Type] = {}
    
    def get_agent_class(self, agent_name: str) -> Type:
        """
        Get the agent class for a given agent name.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent class
        """
        if agent_name in self._agent_classes:
            return self._agent_classes[agent_name]
        
        try:
            # Get class path from configuration
            class_path = self.config_manager.get_agent_class_path(agent_name)
            module_path, class_name = class_path.rsplit('.', 1)
            
            # Import the module and get the class
            module = importlib.import_module(module_path)
            agent_class = getattr(module, class_name)
            
            # Cache the class
            self._agent_classes[agent_name] = agent_class
            
            logger.info(f"Successfully loaded agent class: {class_path}")
            return agent_class
            
        except Exception as e:
            logger.error(f"Failed to load agent class for '{agent_name}': {e}")
            raise
    
    def create_agent(self, agent_name: str, **kwargs) -> Any:
        """
        Create an agent instance.
        
        Args:
            agent_name: Name of the agent to create
            **kwargs: Additional arguments to pass to agent constructor
            
        Returns:
            Agent instance
        """
        if agent_name in self._agent_instances:
            return self._agent_instances[agent_name]
        
        try:
            # Get agent class
            agent_class = self.get_agent_class(agent_name)
            
            # Get agent configuration
            agent_config = self.config_manager.get_agent_config(agent_name)
            
            # Prepare initialization arguments
            init_args = {
                'name': agent_config.name,
                'description': agent_config.description,
                'model': agent_config.model,
                'capabilities': agent_config.capabilities,
                **kwargs
            }
            
            # Create agent instance
            agent_instance = agent_class(**init_args)
            
            # Cache the instance
            self._agent_instances[agent_name] = agent_instance
            
            logger.info(f"Successfully created agent instance: {agent_name}")
            return agent_instance
            
        except Exception as e:
            logger.error(f"Failed to create agent instance for '{agent_name}': {e}")
            raise
    
    def get_agent(self, agent_name: str) -> Any:
        """
        Get an agent instance (create if not exists).
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent instance
        """
        if agent_name not in self._agent_instances:
            self.create_agent(agent_name)
        
        return self._agent_instances[agent_name]
    
    def get_all_agents(self) -> Dict[str, Any]:
        """
        Get all configured agent instances.
        
        Returns:
            Dictionary mapping agent names to instances
        """
        available_agents = self.config_manager.get_available_agents()
        
        for agent_name in available_agents:
            if agent_name not in self._agent_instances:
                try:
                    self.create_agent(agent_name)
                except Exception as e:
                    logger.warning(f"Failed to create agent '{agent_name}': {e}")
        
        return self._agent_instances.copy()
    
    def reload_agents(self) -> None:
        """Reload all agent instances."""
        self._agent_instances.clear()
        self._agent_classes.clear()
        logger.info("Reloaded all agent instances")
    
    def validate_agents(self) -> Dict[str, bool]:
        """
        Validate that all configured agents can be loaded.
        
        Returns:
            Dictionary mapping agent names to validation results
        """
        return self.config_manager.validate_all_agents()


# Global agent factory instance
_agent_factory: Optional[AgentFactory] = None


def get_agent_factory() -> AgentFactory:
    """
    Get the global agent factory instance.
    
    Returns:
        AgentFactory instance
    """
    global _agent_factory
    if _agent_factory is None:
        _agent_factory = AgentFactory()
    return _agent_factory


def get_agent(agent_name: str) -> Any:
    """
    Get an agent instance by name.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        Agent instance
    """
    factory = get_agent_factory()
    return factory.get_agent(agent_name)


def reload_agents() -> None:
    """Reload all agents."""
    global _agent_factory
    if _agent_factory is not None:
        _agent_factory.reload_agents()
