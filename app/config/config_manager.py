"""
Configuration Manager for Merlin Personal Knowledge Curator.
Handles loading, validation, and access to YAML configuration.
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
import importlib
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)


class AgentConfig(BaseModel):
    """Configuration model for individual agents."""
    name: str
    description: str
    type: str
    class_path: str = Field(alias='class')
    framework: str
    model: str
    capabilities: List[str] = []
    input_types: List[str] = []
    output_format: str = ""
    confidence_threshold: Optional[float] = None
    tools: List[str] = []
    actions: Dict[str, Any] = {}


class RoutingRule(BaseModel):
    """Configuration model for routing rules."""
    condition: str
    target_agent: str
    action: str
    confidence: float = Field(ge=0.0, le=1.0)


class GlobalConfig(BaseModel):
    """Global configuration model."""
    name: str
    version: str
    architecture: str
    description: str


class APIConfig(BaseModel):
    """API configuration model."""
    version: str
    base_path: str
    endpoints: Dict[str, str]
    request_timeout: int
    max_input_length: int
    cors_enabled: bool


class LLMConfig(BaseModel):
    """LLM configuration model."""
    provider: str
    primary_model: str
    fallback_model: str
    max_tokens: int
    temperature: float
    system_prompt: str


class PerformanceConfig(BaseModel):
    """Performance configuration model."""
    embedding_model: str
    embedding_dimension: int
    max_search_results: int
    default_search_results: int
    similarity_threshold: float
    cache_embeddings: bool


class ConfigModel(BaseModel):
    """Complete configuration model."""
    global_config: GlobalConfig = Field(alias='global')
    agents: Dict[str, AgentConfig]
    routing: Dict[str, List[RoutingRule]]
    api: APIConfig
    performance: PerformanceConfig
    llm: LLMConfig


class ConfigManager:
    """
    Manages configuration loading, validation, and access.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the YAML configuration file. 
                        Defaults to 'strands_config.yaml' in project root.
        """
        if config_path is None:
            # Default to strands_config.yaml in project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "strands_config.yaml"
        
        self.config_path = Path(config_path)
        self._config: Optional[ConfigModel] = None
        self._raw_config: Optional[Dict[str, Any]] = None
        
        # Load configuration
        self.load_config()
    
    def load_config(self) -> None:
        """Load and validate configuration from YAML file."""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self._raw_config = yaml.safe_load(file)
            
            # Validate configuration
            self._config = ConfigModel(**self._raw_config)
            logger.info(f"Configuration loaded successfully from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self.load_config()
    
    def get_config(self) -> ConfigModel:
        """Get the validated configuration."""
        if self._config is None:
            raise RuntimeError("Configuration not loaded")
        return self._config
    
    def get_raw_config(self) -> Dict[str, Any]:
        """Get the raw configuration dictionary."""
        if self._raw_config is None:
            raise RuntimeError("Configuration not loaded")
        return self._raw_config
    
    def get_agent_config(self, agent_name: str) -> AgentConfig:
        """Get configuration for a specific agent."""
        config = self.get_config()
        if agent_name not in config.agents:
            raise KeyError(f"Agent '{agent_name}' not found in configuration")
        return config.agents[agent_name]
    
    def get_routing_rules(self) -> List[RoutingRule]:
        """Get all routing rules."""
        config = self.get_config()
        return config.routing.get("rules", [])
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent names."""
        config = self.get_config()
        return list(config.agents.keys())
    
    def get_agent_class_path(self, agent_name: str) -> str:
        """Get the class path for an agent."""
        agent_config = self.get_agent_config(agent_name)
        return agent_config.class_path
    
    def get_api_config(self) -> APIConfig:
        """Get API configuration."""
        return self.get_config().api
    
    def get_llm_config(self) -> LLMConfig:
        """Get LLM configuration."""
        return self.get_config().llm
    
    def get_performance_config(self) -> PerformanceConfig:
        """Get performance configuration."""
        return self.get_config().performance
    
    def validate_agent_class(self, agent_name: str) -> bool:
        """
        Validate that an agent class can be imported.
        
        Args:
            agent_name: Name of the agent to validate
            
        Returns:
            True if agent class can be imported, False otherwise
        """
        try:
            class_path = self.get_agent_class_path(agent_name)
            module_path, class_name = class_path.rsplit('.', 1)
            
            module = importlib.import_module(module_path)
            agent_class = getattr(module, class_name)
            
            logger.debug(f"Successfully validated agent class: {class_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate agent class for '{agent_name}': {e}")
            return False
    
    def validate_all_agents(self) -> Dict[str, bool]:
        """
        Validate all agent classes in the configuration.
        
        Returns:
            Dictionary mapping agent names to validation results
        """
        results = {}
        for agent_name in self.get_available_agents():
            results[agent_name] = self.validate_agent_class(agent_name)
        
        return results


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """
    Get the global configuration manager instance.
    
    Returns:
        ConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def reload_config() -> None:
    """Reload the global configuration."""
    global _config_manager
    if _config_manager is not None:
        _config_manager.reload_config()
    else:
        _config_manager = ConfigManager()
