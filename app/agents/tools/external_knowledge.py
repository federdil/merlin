"""
External knowledge integration tool for Merlin.
Uses LLMs to dynamically fetch and synthesize external knowledge for any topic.
"""

import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv
from strands import Agent
from strands.models.anthropic import AnthropicModel

load_dotenv()

class ExternalKnowledgeFetcher:
    """Uses LLMs to dynamically fetch and synthesize external knowledge for any topic."""
    
    def __init__(self):
        self.name = "ExternalKnowledgeFetcher"
        self.description = "Uses LLMs to dynamically fetch and synthesize external knowledge for any topic"
        
        # Initialize Claude model for external knowledge synthesis
        self.model = AnthropicModel(
            client_args={
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
            },
            max_tokens=2000,
            model_id="claude-3-5-haiku-20241022",
            params={
                "temperature": 0.3,
            }
        )
        
        self.agent = Agent(
            model=self.model,
            system_prompt=self._get_external_knowledge_prompt()
        )
        
    def _get_external_knowledge_prompt(self) -> str:
        """Get the system prompt for external knowledge synthesis."""
        return """You are an expert at synthesizing external knowledge to enhance user queries. Your role is to provide accurate, helpful information about any topic by drawing on your training knowledge.

Key capabilities:
1. **Movie/TV Analysis**: Provide detailed information about films, TV shows, including plot, themes, cast, and similar recommendations
2. **Recipe/Food Analysis**: Suggest similar recipes, cooking techniques, and food recommendations based on cuisine types or ingredients
3. **General Topic Knowledge**: Provide comprehensive information about any topic with key points and related concepts
4. **Recommendation Engine**: Suggest similar items, experiences, or learning paths based on user interests

Guidelines:
- Always provide accurate, factual information
- When making recommendations, explain WHY they are similar or relevant
- Be specific and detailed in your responses
- Consider different aspects: genre, themes, style, complexity, audience, etc.
- For movies: ALWAYS identify the specific film by title and year, consider plot, themes, tone, visual style, cultural impact, cast, and director
- For recipes: consider cuisine type, techniques, ingredients, complexity, dietary preferences
- For general topics: provide comprehensive overview with key insights

CRITICAL: When users mention movie titles, always research the SPECIFIC film they're referring to. Don't confuse movie titles with general concepts. For example:
- "Materialists (2025)" = the romantic comedy-drama by Celine Song, not a film about materialism
- "The Matrix" = the 1999 sci-fi film, not a general concept about matrices
- Always provide the correct genre, cast, plot, and themes for the actual film

Your responses should be informative, engaging, and help users discover new things they might enjoy or learn about."""
    
    def enhance_with_external_context(self, internal_results: List[Dict[str, Any]], 
                                    query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Enhance internal search results with external knowledge using LLM synthesis.
        This is the key differentiator - combining external knowledge with personal notes.
        """
        try:
            # Determine if external knowledge enhancement is needed
            should_enhance = self._should_enhance_with_external(query, internal_results)
            
            if not should_enhance:
                return {
                    "success": True,
                    "enhanced_results": {
                        "internal_results": internal_results,
                        "external_enhancement": None,
                        "combined_insights": [],
                        "recommendations": []
                    },
                    "has_external_enhancement": False
                }
            
            # Use LLM to synthesize external knowledge
            external_synthesis = self._synthesize_external_knowledge(query, internal_results, user_context)
            
            if external_synthesis.get("success"):
                return {
                    "success": True,
                    "enhanced_results": {
                        "internal_results": internal_results,
                        "external_enhancement": external_synthesis.get("external_info"),
                        "combined_insights": external_synthesis.get("combined_insights", []),
                        "recommendations": external_synthesis.get("recommendations", []),
                        "personal_connections": external_synthesis.get("personal_connections", [])
                    },
                    "has_external_enhancement": True,
                    "enhancement_source": "llm_synthesis"
                }
            else:
                return {
                    "success": False,
                    "error": external_synthesis.get("error", "Failed to synthesize external knowledge"),
                    "enhanced_results": {
                        "internal_results": internal_results,
                        "external_enhancement": None,
                        "combined_insights": [],
                        "recommendations": []
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to enhance with external context: {str(e)}",
                "enhanced_results": {
                    "internal_results": internal_results,
                    "external_enhancement": None,
                    "combined_insights": [],
                    "recommendations": []
                }
            }
    
    def _should_enhance_with_external(self, query: str, internal_results: List[Dict[str, Any]]) -> bool:
        """Determine if external knowledge enhancement is needed."""
        query_lower = query.lower()
        
        # Enhancement triggers
        enhancement_triggers = [
            len(internal_results) == 0,  # No internal results
            len(internal_results) < 2,   # Very few internal results
            any(word in query_lower for word in ['recommend', 'suggest', 'similar', 'like']),  # Recommendation queries
            any(word in query_lower for word in ['movie', 'film', 'method', 'recipe', 'book', 'song']),  # Specific content types
            any(word in query_lower for word in ['what is', 'tell me about', 'explain', 'how does']),  # Information queries
        ]
        
        return any(enhancement_triggers)
    
    def _synthesize_external_knowledge(self, query: str, internal_results: List[Dict[str, Any]], 
                                     user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Use LLM to synthesize external knowledge for any topic."""
        try:
            # Prepare context for LLM
            internal_context = self._format_internal_context(internal_results)
            user_context_str = self._format_user_context(user_context)
            
            llm_input = f"""
User Query: "{query}"

Internal Knowledge Base Results ({len(internal_results)} found):
{internal_context}

User Context:
{user_context_str}

Please provide external knowledge enhancement for this query. Based on the user's question and their internal knowledge, provide:

1. **External Information**: Relevant external knowledge about the topic
2. **Combined Insights**: How external knowledge connects to or enhances their internal knowledge
3. **Recommendations**: Specific recommendations based on the query type (similar movies, recipes, books, etc.)
4. **Personal Connections**: How this relates to their existing interests and knowledge

IMPORTANT: For movie queries, be very specific about the exact movie title and year. If the user mentions a movie title, research the specific film they're referring to, not just the general theme. For example:
- "Materialists (2025)" refers to the romantic comedy-drama film by Celine Song starring Dakota Johnson, Pedro Pascal, and Chris Evans
- Don't confuse movie titles with general themes (e.g., don't interpret "Materialists" as a film about materialism)

For movie queries: Provide plot, themes, cast info, and similar movie recommendations with explanations
For recipe queries: Suggest similar recipes, cooking techniques, and food recommendations
For general queries: Provide comprehensive information and related topics

Be specific, accurate, and helpful. Connect external knowledge to their personal context when possible.
            """
            
            # Get structured response from LLM
            response = self.agent.run(llm_input)
            
            # Parse and structure the response
            return self._parse_llm_response(response, query)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"LLM synthesis failed: {str(e)}"
            }
    
    def _format_internal_context(self, internal_results: List[Dict[str, Any]]) -> str:
        """Format internal search results for LLM context."""
        if not internal_results:
            return "No internal knowledge found."
        
        formatted = []
        for i, result in enumerate(internal_results[:5], 1):  # Limit to top 5
            formatted.append(f"{i}. {result.get('title', 'Untitled')}")
            if result.get('summary'):
                formatted.append(f"   Summary: {result['summary'][:200]}...")
            if result.get('tags'):
                formatted.append(f"   Tags: {', '.join(result['tags'][:5])}")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def _format_user_context(self, user_context: Dict[str, Any] = None) -> str:
        """Format user context for LLM."""
        if not user_context:
            return "No specific user context available."
        
        context_parts = []
        
        if user_context.get('knowledge_topics'):
            topics = user_context['knowledge_topics']
            if isinstance(topics, dict):
                context_parts.append(f"Knowledge areas: {', '.join(topics.keys())}")
            else:
                context_parts.append(f"Knowledge areas: {', '.join(topics)}")
        
        if user_context.get('recent_interests'):
            context_parts.append(f"Recent interests: {', '.join(user_context['recent_interests'])}")
        
        if user_context.get('preferences'):
            context_parts.append(f"Preferences: {user_context['preferences']}")
        
        return "\n".join(context_parts) if context_parts else "No specific user context available."
    
    def _parse_llm_response(self, response: str, query: str) -> Dict[str, Any]:
        """Parse LLM response into structured format."""
        try:
            # Extract key information from the LLM response
            lines = response.split('\n')
            recommendations = []
            insights = []
            
            # Simple parsing to extract recommendations and insights
            for line in lines:
                line = line.strip()
                if line.startswith(('1.', '2.', '3.', '4.', '5.')) or line.startswith('- '):
                    recommendations.append(line)
                elif line.startswith('•') or line.startswith('*'):
                    insights.append(line)
            
            return {
                "success": True,
                "external_info": {
                    "response_text": response,
                    "query": query,
                    "source": "llm_synthesis"
                },
                "combined_insights": insights[:5] if insights else [
                    "External knowledge has been synthesized to enhance your query",
                    "Recommendations are based on your personal context and interests"
                ],
                "recommendations": recommendations[:5] if recommendations else [
                    "See the detailed response below for specific recommendations"
                ],
                "personal_connections": [
                    "External knowledge has been connected to your personal interests and knowledge base"
                ]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse LLM response: {str(e)}"
            }
    
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get information about external knowledge capabilities."""
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": [
                "llm_based_external_knowledge_synthesis",
                "dynamic_topic_analysis", 
                "external_knowledge_enhancement",
                "personal_context_integration",
                "scalable_recommendation_engine"
            ],
            "supported_queries": [
                "movie recommendations and analysis",
                "recipe suggestions and cooking advice",
                "book and media recommendations",
                "general knowledge questions",
                "topic exploration and discovery",
                "similar content recommendations"
            ],
            "enhancement_features": [
                "combines_external_with_internal_knowledge",
                "personal_context_integration",
                "intelligent_insight_generation",
                "cross_domain_connections",
                "scalable_to_any_topic",
                "no_maintenance_required",
                "dynamic_knowledge_synthesis"
            ],
            "technical_approach": [
                "uses_llm_training_knowledge",
                "no_hardcoded_databases",
                "scalable_architecture",
                "topic_agnostic_design"
            ]
        }
