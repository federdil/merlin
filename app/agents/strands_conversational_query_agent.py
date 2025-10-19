"""
Strands-compatible Conversational Query Agent for Merlin.
Uses the actual Strands framework for intelligent conversational search with temporal awareness.
"""

import os
from typing import Dict, Any, Optional, List
from strands import Agent
from strands.models.anthropic import AnthropicModel
from app.agents.tools.temporal_parser import TemporalParser
from app.agents.tools.search import semantic_search, search_by_content, hybrid_search
from app.agents.tools.database_ops import get_recent_notes, get_note_statistics
from app.agents.tools.external_knowledge import ExternalKnowledgeFetcher
from app.agents.tools.tag_utils import fix_tags_format, format_note_for_display
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()


class QueryIntent(BaseModel):
    """Structured output for query intent analysis."""
    intent_type: str = Field(description="Type of query intent: 'search', 'question', 'exploration', 'summary'")
    entities: List[str] = Field(description="Key entities mentioned in the query")
    temporal_focus: str = Field(description="Temporal focus: 'recent', 'historical', 'all_time', 'specific_period'")
    search_scope: str = Field(description="Search scope: 'broad', 'specific', 'comparative'")
    confidence: float = Field(description="Confidence score for intent analysis", ge=0, le=1)


class ConversationalResponse(BaseModel):
    """Structured output for conversational responses."""
    direct_answer: str = Field(description="Direct answer to the user's question")
    context_explanation: str = Field(description="Explanation of the context and findings")
    related_insights: List[str] = Field(description="Additional insights related to the query")
    follow_up_suggestions: List[str] = Field(description="Suggested follow-up questions or actions")
    confidence: float = Field(description="Confidence in the response", ge=0, le=1)


class StrandsConversationalQueryAgent:
    """
    Conversational search agent using Strands framework with temporal awareness.
    """
    
    def __init__(self):
        self.name = "StrandsConversationalQueryAgent"
        self.description = "AI-powered conversational search with temporal awareness using Strands and Claude"
        
        # Initialize Claude model via Strands
        self.model = AnthropicModel(
            client_args={
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
            },
            max_tokens=1200,
            model_id="claude-3-5-haiku-20241022",
            params={
                "temperature": 0.2,  # Slightly higher for more natural responses
            }
        )
        
        # Create Strands agent for conversational processing
        self.agent = Agent(
            model=self.model,
            system_prompt=self._get_conversational_prompt()
        )
        
        # Initialize tools
        self.temporal_parser = TemporalParser()
        self.external_knowledge = ExternalKnowledgeFetcher()
    
    def _get_conversational_prompt(self) -> str:
        """Get the system prompt for conversational query processing."""
        return """You are Merlin's intelligent conversational search assistant. Your job is to understand user queries and provide helpful, contextual responses that combine external knowledge with the user's personal knowledge base.

Your capabilities include:
1. **Natural Language Understanding**: Parse complex, conversational queries
2. **Temporal Awareness**: Understand time-based references like "last month", "recently", "when I started learning"
3. **External Knowledge Integration**: Access external knowledge sources to enhance responses
4. **Personal Context Integration**: Combine external knowledge with the user's personal notes and preferences
5. **Contextual Responses**: Provide answers that consider both external information and the user's knowledge history
6. **Follow-up Suggestions**: Suggest related questions and learning opportunities

Guidelines for responses:
- Be conversational and helpful, not robotic
- When internal search yields few results, enhance with external knowledge
- Always connect external information to the user's personal context when possible
- Provide direct answers when possible, enhanced with external context
- Explain the context of your findings (both internal and external)
- Offer additional insights and connections between external and personal knowledge
- Suggest logical follow-up questions
- Acknowledge uncertainty when appropriate

Key differentiator: You enhance external knowledge with personal context, making you more valuable than generic AI assistants by providing personalized, contextually relevant responses that build on the user's existing knowledge."""
    
    def process_conversational_query(self, query: str, user_id: str, 
                                  session_id: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process conversational queries using Strands framework.
        
        Args:
            query: User's conversational query
            user_id: User identifier
            session_id: Session identifier for conversation history
            context: Additional context for the query
            
        Returns:
            Dict containing conversational response and search results
        """
        try:
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Parse temporal references in the query
            temporal_info = self.temporal_parser.extract_timeframe(query)
            
            # Analyze query intent using Strands
            intent_analysis = self._analyze_query_intent(query, temporal_info)
            
            if not intent_analysis:
                return {
                    'success': False,
                    'error': 'Failed to analyze query intent',
                    'result': None
                }
            
            # Execute search based on intent and temporal info
            search_results = self._execute_contextual_search(
                query, intent_analysis, temporal_info, user_id
            )
            
            # Enhance with external knowledge if needed
            enhanced_results = self._enhance_with_external_knowledge(
                query, search_results, intent_analysis, user_id, context
            )
            
            # Generate conversational response using Strands
            conversational_response = self._generate_conversational_response(
                query, intent_analysis, enhanced_results, temporal_info
            )
            
            if not conversational_response:
                return {
                    'success': False,
                    'error': 'Failed to generate conversational response',
                    'result': None
                }
            
            # Store conversation history
            self._store_conversation_history(
                user_id, session_id, query, conversational_response, context
            )
            
            # Prepare comprehensive result
            result = {
                'query': query,
                'user_id': user_id,
                'session_id': session_id,
                'intent_analysis': intent_analysis,
                'temporal_info': temporal_info,
                'search_results': search_results,
                'conversational_response': conversational_response,
                'response_metadata': {
                    'response_confidence': conversational_response.get('confidence', 0),
                    'search_results_count': len(search_results.get('results', [])),
                    'temporal_filter_applied': temporal_info.get('has_temporal', False),
                    'intent_confidence': intent_analysis.get('confidence', 0)
                }
            }
            
            return {
                'success': True,
                'result': result,
                'message': f'Processed conversational query with {len(search_results.get("results", []))} results'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Conversational query processing failed: {str(e)}',
                'result': None
            }
    
    def _analyze_query_intent(self, query: str, temporal_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze query intent using Strands."""
        try:
            intent_input = f"""
Analyze the following conversational query to understand the user's intent:

Query: "{query}"

Temporal Information:
- Has temporal reference: {temporal_info.get('has_temporal', False)}
- Timeframe type: {temporal_info.get('timeframe_type', 'none')}
- Time period: {temporal_info.get('relative_period', 'none')}

Please analyze:
1. What type of query is this? (search, question, exploration, summary)
2. What key entities or topics are mentioned?
3. What is the temporal focus?
4. How broad or specific is the search scope?
5. How confident are you in this analysis?

Provide a structured analysis of the query intent.
            """
            
            intent_analysis = self.agent.structured_output(
                QueryIntent,
                intent_input
            )
            
            return intent_analysis.dict()
            
        except Exception as e:
            print(f"Strands intent analysis failed: {e}")
            # Fallback to simple intent detection
            return self._fallback_intent_analysis(query, temporal_info)
    
    def _fallback_intent_analysis(self, query: str, temporal_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback intent analysis using simple pattern matching."""
        try:
            query_lower = query.lower()
            
            # Determine intent type
            if any(word in query_lower for word in ['what', 'how', 'why', 'when', 'where', 'who']):
                intent_type = 'question'
            elif any(word in query_lower for word in ['find', 'search', 'show', 'list']):
                intent_type = 'search'
            elif any(word in query_lower for word in ['explore', 'discover', 'learn', 'study']):
                intent_type = 'exploration'
            elif any(word in query_lower for word in ['summarize', 'summary', 'overview', 'brief']):
                intent_type = 'summary'
            else:
                intent_type = 'search'
            
            # Extract entities (simple keyword extraction)
            entities = []
            for word in query.split():
                if len(word) > 3 and word.lower() not in ['what', 'how', 'why', 'when', 'where', 'who', 'the', 'and', 'or', 'but']:
                    entities.append(word.lower())
            
            # Determine temporal focus
            if temporal_info.get('has_temporal', False):
                temporal_focus = 'specific_period'
            else:
                temporal_focus = 'all_time'
            
            # Determine search scope
            if len(entities) > 3:
                search_scope = 'broad'
            elif len(entities) == 1:
                search_scope = 'specific'
            else:
                search_scope = 'comparative'
            
            return {
                'intent_type': intent_type,
                'entities': entities[:5],  # Limit to 5 entities
                'temporal_focus': temporal_focus,
                'search_scope': search_scope,
                'confidence': 0.7  # Moderate confidence for fallback
            }
            
        except Exception as e:
            return {
                'intent_type': 'search',
                'entities': [],
                'temporal_focus': 'all_time',
                'search_scope': 'broad',
                'confidence': 0.5,
                'error': str(e)
            }
    
    def _execute_contextual_search(self, query: str, intent_analysis: Dict[str, Any], 
                                 temporal_info: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Execute search based on intent and temporal information."""
        try:
            # Determine search type based on intent
            intent_type = intent_analysis.get('intent_type', 'search')
            search_scope = intent_analysis.get('search_scope', 'broad')
            
            # Choose search method
            if intent_type == 'question' and search_scope == 'specific':
                search_method = 'semantic'
            elif intent_type == 'exploration' or search_scope == 'broad':
                search_method = 'hybrid'
            else:
                search_method = 'semantic'
            
            # Execute search
            if search_method == 'semantic':
                results = semantic_search(query, top_k=5)
            elif search_method == 'hybrid':
                results = hybrid_search(query, top_k=5)
            else:
                results = search_by_content(query, top_k=5)
            
            # Apply temporal filtering if needed
            if temporal_info.get('has_temporal', False):
                results = self.temporal_parser.filter_by_time(results, temporal_info)
            
            # Format results
            formatted_results = []
            for note in results:
                formatted_results.append(format_note_for_display(note))
            
            return {
                'search_method': search_method,
                'results': formatted_results,
                'total_results': len(formatted_results),
                'temporal_filter_applied': temporal_info.get('has_temporal', False)
            }
            
        except Exception as e:
            return {
                'search_method': 'error',
                'results': [],
                'total_results': 0,
                'error': str(e)
            }
    
    def _enhance_with_external_knowledge(self, query: str, search_results: Dict[str, Any], 
                                       intent_analysis: Dict[str, Any], user_id: str, 
                                       context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Enhance search results with external knowledge."""
        try:
            internal_results = search_results.get('results', [])
            result_count = len(internal_results)
            
            # Determine if external knowledge enhancement is needed
            should_enhance = (
                result_count == 0 or  # No internal results
                result_count < 2 or   # Very few internal results
                intent_analysis.get('intent_type') == 'exploration' or  # Exploration queries
                any(word in query.lower() for word in ['movie', 'film', 'watch', 'recommend'])  # Movie queries
            )
            
            if should_enhance:
                # Get user context for personalization
                user_context = self._get_user_context(user_id)
                
                # Enhance with external knowledge
                enhancement_result = self.external_knowledge.enhance_with_external_context(
                    internal_results, query, user_context
                )
                
                if enhancement_result.get('success'):
                    # Merge enhanced results with original search results
                    enhanced_results = enhancement_result['enhanced_results']
                    
                    return {
                        'search_method': search_results.get('search_method', 'enhanced'),
                        'results': internal_results,
                        'total_results': result_count,
                        'temporal_filter_applied': search_results.get('temporal_filter_applied', False),
                        'external_enhancement': enhanced_results.get('external_enhancement'),
                        'combined_insights': enhanced_results.get('combined_insights', []),
                        'recommendations': enhanced_results.get('recommendations', []),
                        'has_external_enhancement': True,
                        'enhancement_source': 'external_knowledge_fetcher'
                    }
            
            # Return original results with enhancement flag
            return {
                **search_results,
                'has_external_enhancement': False,
                'external_enhancement': None,
                'combined_insights': [],
                'recommendations': []
            }
            
        except Exception as e:
            # Return original results if enhancement fails
            return {
                **search_results,
                'has_external_enhancement': False,
                'enhancement_error': str(e)
            }
    
    def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get user context for personalization."""
        try:
            # This would fetch user knowledge profile, preferences, etc.
            # For now, return basic context
            return {
                'user_id': user_id,
                'knowledge_topics': {},  # Would be populated from user profile
                'preferences': {},       # Would be populated from user preferences
                'recent_interests': []   # Would be populated from recent activity
            }
        except Exception as e:
            return {
                'user_id': user_id,
                'knowledge_topics': {},
                'preferences': {},
                'recent_interests': []
            }
    
    def _generate_conversational_response(self, query: str, intent_analysis: Dict[str, Any], 
                                        search_results: Dict[str, Any], 
                                        temporal_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate conversational response using Strands."""
        try:
            # Check if external knowledge is available
            has_external = search_results.get('has_external_enhancement', False)
            internal_count = len(search_results.get('results', []))
            
            response_input = f"""
Generate a conversational response to the user's query based on the search results and external knowledge:

User Query: "{query}"

Intent Analysis:
- Intent type: {intent_analysis.get('intent_type', 'search')}
- Entities: {intent_analysis.get('entities', [])}
- Temporal focus: {intent_analysis.get('temporal_focus', 'all_time')}
- Search scope: {intent_analysis.get('search_scope', 'broad')}

Temporal Information:
- Has temporal reference: {temporal_info.get('has_temporal', False)}
- Time period: {temporal_info.get('relative_period', 'none')}

Search Results ({internal_count} found):
{self._format_search_results_for_response(search_results.get('results', []))}

External Knowledge Enhancement:
{self._format_external_enhancement_for_response(search_results)}

IMPORTANT INSTRUCTIONS:
- If NO internal results were found ({internal_count} = 0) but external knowledge is available, start your response with: "I could not find similar content in your notes, however based on external sources I can suggest..."
- If FEW internal results were found ({internal_count} < 2) but external knowledge is available, combine both internal and external knowledge
- Always use external knowledge when available to provide comprehensive recommendations
- Be specific about why recommendations are relevant (themes, style, genre, etc.)
- Connect external knowledge to the user's personal context when possible

Please provide:
1. A direct answer to the user's question (use external knowledge when internal results are limited)
2. Context explanation of what was found (both internal and external)
3. Related insights and connections between external knowledge and user's personal context
4. Helpful follow-up suggestions

Be conversational, helpful, and acknowledge both internal findings and external enhancements. When external knowledge is available, connect it to the user's personal context and interests.
            """
            
            conversational_response = self.agent.structured_output(
                ConversationalResponse,
                response_input
            )
            
            return conversational_response.dict()
            
        except Exception as e:
            print(f"Strands response generation failed: {e}")
            # Fallback to simple response
            return self._fallback_conversational_response(query, search_results, temporal_info)
    
    def _fallback_conversational_response(self, query: str, search_results: Dict[str, Any], 
                                        temporal_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback conversational response generation."""
        try:
            results = search_results.get('results', [])
            result_count = len(results)
            
            if result_count == 0:
                direct_answer = f"I couldn't find any notes related to your query about '{query}'. You might want to try different keywords or add some content first."
                context_explanation = "No matching content was found in your knowledge base."
                related_insights = ["Consider adding more content to your knowledge base", "Try using different search terms"]
            else:
                direct_answer = f"I found {result_count} note{'s' if result_count != 1 else ''} related to your query."
                context_explanation = f"These notes were found using {'temporal filtering' if temporal_info.get('has_temporal') else 'semantic search'}."
                related_insights = [f"Your most recent note on this topic is: {results[0]['title']}" if results else "No specific insights available"]
            
            follow_up_suggestions = [
                "Would you like to see more details about any of these notes?",
                "Would you like to search for something else?",
                "Would you like to add new content on this topic?"
            ]
            
            if temporal_info.get('has_temporal'):
                follow_up_suggestions.append(f"Would you like to explore this topic in a different time period?")
            
            return {
                'direct_answer': direct_answer,
                'context_explanation': context_explanation,
                'related_insights': related_insights,
                'follow_up_suggestions': follow_up_suggestions,
                'confidence': 0.7  # Moderate confidence for fallback
            }
            
        except Exception as e:
            return {
                'direct_answer': "I encountered an error processing your query. Please try again.",
                'context_explanation': "An error occurred while generating the response.",
                'related_insights': [],
                'follow_up_suggestions': ["Please try rephrasing your question", "Contact support if the issue persists"],
                'confidence': 0.3,
                'error': str(e)
            }
    
    def _format_search_results_for_response(self, results: List[Dict[str, Any]]) -> str:
        """Format search results for response generation."""
        try:
            if not results:
                return "No results found."
            
            formatted = []
            for i, result in enumerate(results[:3], 1):  # Limit to top 3 for response
                formatted.append(f"{i}. {result.get('title', 'Untitled')} - {result.get('summary', 'No summary')[:100]}...")
            
            return "\n".join(formatted)
            
        except Exception as e:
            return f"Error formatting results: {str(e)}"
    
    def _format_external_enhancement_for_response(self, search_results: Dict[str, Any]) -> str:
        """Format external enhancement information for response generation."""
        try:
            if not search_results.get('has_external_enhancement', False):
                return "No external knowledge enhancement available."
            
            enhancement = search_results.get('external_enhancement')
            combined_insights = search_results.get('combined_insights', [])
            recommendations = search_results.get('recommendations', [])
            
            formatted = []
            
            if enhancement:
                if isinstance(enhancement, dict):
                    if 'response_text' in enhancement:  # LLM synthesized response
                        formatted.append("External Knowledge Available:")
                        formatted.append(enhancement.get('response_text', 'No external information available'))
                    elif 'title' in enhancement:  # Movie information
                        formatted.append(f"Movie: {enhancement.get('title', 'Unknown')} ({enhancement.get('year', 'Unknown year')})")
                        formatted.append(f"Genre: {', '.join(enhancement.get('genre', []))}")
                        formatted.append(f"Plot: {enhancement.get('plot', 'No plot available')}")
                        formatted.append(f"Themes: {', '.join(enhancement.get('themes', [])[:5])}")
                    else:  # General topic information
                        formatted.append(f"Topic: {enhancement.get('topic', 'Unknown topic')}")
                        formatted.append(f"Summary: {enhancement.get('summary', 'No summary available')}")
            
            if combined_insights:
                formatted.append("\nCombined Insights:")
                formatted.extend([f"• {insight}" for insight in combined_insights[:3]])
            
            if recommendations:
                formatted.append("\nRecommendations:")
                for i, rec in enumerate(recommendations[:3], 1):
                    if isinstance(rec, dict):
                        formatted.append(f"{i}. {rec.get('title', 'Unknown')} ({rec.get('year', '')}) - {rec.get('reason', '')}")
                    else:
                        formatted.append(f"{i}. {rec}")
            
            return "\n".join(formatted) if formatted else "External enhancement details not available."
            
        except Exception as e:
            return f"Error formatting external enhancement: {str(e)}"
    
    def _store_conversation_history(self, user_id: str, session_id: str, query: str, 
                                  response: Dict[str, Any], context: Dict[str, Any] = None):
        """Store conversation history."""
        try:
            # Format response for storage
            response_text = response.get('direct_answer', 'No response generated')
            
            # Store in conversation history
            storage_result = self.temporal_parser.store_conversation_history(
                user_id=user_id,
                session_id=session_id,
                query=query,
                response=response_text,
                agent_type='conversational_query',
                context=context
            )
            
            return storage_result
            
        except Exception as e:
            print(f"Failed to store conversation history: {e}")
            return {'error': str(e)}
    
    def get_conversation_history(self, user_id: str, session_id: str = None, 
                               limit: int = 10) -> Dict[str, Any]:
        """
        Get conversation history for context.
        
        Args:
            user_id: User identifier
            session_id: Optional session identifier
            limit: Maximum number of records to return
            
        Returns:
            Dict containing conversation history
        """
        try:
            history = self.temporal_parser.get_conversation_history(user_id, session_id, limit)
            
            return {
                'success': True,
                'result': {
                    'user_id': user_id,
                    'session_id': session_id,
                    'history': history,
                    'total_records': len(history)
                },
                'message': f'Retrieved {len(history)} conversation records'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get conversation history: {str(e)}',
                'result': None
            }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get information about agent capabilities."""
        return {
            'name': self.name,
            'description': self.description,
            'framework': 'Strands',
            'model': 'claude-3-5-haiku-20241022',
            'supported_actions': ['process_conversational_query', 'get_conversation_history'],
            'input_types': ['conversational_query', 'user_id', 'session_id'],
            'output_format': 'conversational_response_with_context',
            'ai_features': [
                'natural_language_understanding',
                'temporal_query_processing',
                'conversational_response_generation',
                'context_aware_search',
                'external_knowledge_integration',
                'personal_context_enhancement',
                'cross_domain_knowledge_synthesis',
                'follow_up_suggestion'
            ],
            'tools_used': [
                'temporal_parser',
                'search',
                'database_ops',
                'external_knowledge_fetcher'
            ]
        }
    
    def validate_input(self, action: str, input_data: Dict[str, Any]) -> bool:
        """Validate input data for the specified action."""
        if action == 'process_conversational_query':
            return ('query' in input_data and input_data['query'] and 
                   'user_id' in input_data and input_data['user_id'])
        elif action == 'get_conversation_history':
            return 'user_id' in input_data and input_data['user_id']
        return False
