"""
Strands-compatible Knowledge Gap Detection Agent for Merlin.
Uses the actual Strands framework for intelligent knowledge gap analysis.
"""

import os
from typing import Dict, Any, Optional, List
from strands import Agent
from strands.models.anthropic import AnthropicModel
from app.agents.tools.knowledge_analyzer import KnowledgeAnalyzer
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class KnowledgeGapAnalysis(BaseModel):
    """Structured output for knowledge gap analysis."""
    gap_type: str = Field(description="Type of knowledge gap: 'topic_gap', 'skill_gap', 'connection_gap'")
    topic: str = Field(description="The specific topic where a gap is identified")
    confidence_score: float = Field(description="Confidence score between 0 and 1", ge=0, le=1)
    gap_description: str = Field(description="Detailed description of the knowledge gap")
    suggested_content: List[str] = Field(description="List of suggested content or topics to fill the gap")
    learning_priority: str = Field(description="Learning priority: 'high', 'medium', 'low'")


class KnowledgeGapSummary(BaseModel):
    """Structured output for knowledge gap summary."""
    total_gaps_identified: int = Field(description="Total number of knowledge gaps found")
    high_priority_gaps: int = Field(description="Number of high priority gaps")
    medium_priority_gaps: int = Field(description="Number of medium priority gaps")
    low_priority_gaps: int = Field(description="Number of low priority gaps")
    top_gap_categories: List[str] = Field(description="Top categories where gaps exist")
    learning_opportunities: List[str] = Field(description="Key learning opportunities identified")
    overall_assessment: str = Field(description="Overall assessment of knowledge gaps")


class StrandsKnowledgeGapAgent:
    """
    Knowledge gap detection agent using Strands framework for intelligent analysis.
    """
    
    def __init__(self):
        self.name = "StrandsKnowledgeGapAgent"
        self.description = "AI-powered knowledge gap detection using Strands and Claude"
        
        # Initialize Claude model via Strands
        self.model = AnthropicModel(
            client_args={
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
            },
            max_tokens=1000,
            model_id="claude-3-5-haiku-20241022",
            params={
                "temperature": 0.1,  # Low temperature for consistent analysis
            }
        )
        
        # Create Strands agent for gap analysis
        self.agent = Agent(
            model=self.model,
            system_prompt=self._get_gap_analysis_prompt()
        )
        
        # Initialize knowledge analyzer tool
        self.knowledge_analyzer = KnowledgeAnalyzer()
    
    def _get_gap_analysis_prompt(self) -> str:
        """Get the system prompt for knowledge gap analysis."""
        return """You are Merlin's intelligent knowledge gap analyzer. Your job is to analyze user knowledge patterns and identify learning opportunities.

Your analysis should focus on:
1. **Topic Gaps**: Missing knowledge in related topics
2. **Skill Gaps**: Missing practical skills or abilities
3. **Connection Gaps**: Missing connections between concepts
4. **Depth Gaps**: Insufficient depth in existing topics

For each gap identified:
- Provide a clear description of what's missing
- Suggest specific content or learning resources
- Assign a confidence score based on the evidence
- Prioritize gaps based on learning impact

Be thoughtful and accurate in your analysis. Focus on actionable learning opportunities that would significantly enhance the user's knowledge base."""
    
    def detect_gaps(self, user_id: str, timeframe: str = "30d") -> Dict[str, Any]:
        """
        Detect knowledge gaps for a user using Strands framework.
        
        Args:
            user_id: User identifier
            timeframe: Timeframe for analysis (e.g., "30d", "90d")
            
        Returns:
            Dict containing knowledge gap analysis results
        """
        try:
            # Parse timeframe
            timeframe_days = self._parse_timeframe(timeframe)
            
            # Analyze user's knowledge patterns
            knowledge_analysis = self.knowledge_analyzer.analyze_knowledge_patterns(
                user_id, timeframe_days
            )
            
            if 'error' in knowledge_analysis:
                return {
                    'success': False,
                    'error': f'Knowledge analysis failed: {knowledge_analysis["error"]}',
                    'result': None
                }
            
            # Use Strands to analyze gaps
            gap_analysis = self._analyze_gaps_with_strands(knowledge_analysis)
            
            if not gap_analysis:
                return {
                    'success': False,
                    'error': 'Failed to analyze gaps with Strands',
                    'result': None
                }
            
            # Store identified gaps
            stored_gaps = []
            for gap in gap_analysis.get('gaps', []):
                storage_result = self.knowledge_analyzer.store_knowledge_gap(user_id, gap)
                if storage_result.get('success'):
                    stored_gaps.append({
                        'gap_id': storage_result.get('gap_id'),
                        'gap_data': gap
                    })
            
            # Prepare comprehensive result
            result = {
                'user_id': user_id,
                'timeframe': timeframe,
                'knowledge_analysis': knowledge_analysis,
                'gap_analysis': gap_analysis,
                'stored_gaps': stored_gaps,
                'analysis_metadata': {
                    'total_gaps_found': len(gap_analysis.get('gaps', [])),
                    'gaps_stored': len(stored_gaps),
                    'analysis_date': knowledge_analysis.get('analysis_date'),
                    'confidence_avg': sum(gap.get('confidence_score', 0) for gap in gap_analysis.get('gaps', [])) / max(len(gap_analysis.get('gaps', [])), 1)
                }
            }
            
            return {
                'success': True,
                'result': result,
                'message': f'Identified {len(gap_analysis.get("gaps", []))} knowledge gaps for user {user_id}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Knowledge gap detection failed: {str(e)}',
                'result': None
            }
    
    def _analyze_gaps_with_strands(self, knowledge_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Use Strands to analyze knowledge gaps."""
        try:
            # Prepare input for Strands analysis
            analysis_input = f"""
Based on the following knowledge analysis, identify potential knowledge gaps and learning opportunities:

**User Knowledge Overview:**
- Total notes: {knowledge_analysis.get('total_notes', 0)}
- Knowledge diversity: {knowledge_analysis.get('knowledge_diversity', 0)} unique topics
- Top topics: {knowledge_analysis.get('top_topics', [])}
- Topic distribution: {knowledge_analysis.get('topic_distribution', {})}

**Content Analysis:**
- Average content length: {knowledge_analysis.get('content_analysis', {}).get('avg_content_length', 0)}
- Summary coverage: {knowledge_analysis.get('content_analysis', {}).get('summary_coverage', 0)}
- Tag coverage: {knowledge_analysis.get('content_analysis', {}).get('tag_coverage', 0)}

Please analyze this knowledge profile and identify:
1. Missing connections between topics
2. Underexplored areas in existing topics
3. Related topics that could enhance learning
4. Skill gaps that need attention

Provide specific, actionable learning recommendations.
            """
            
            # Use Strands to analyze gaps
            gap_analysis = self.agent.structured_output(
                KnowledgeGapAnalysis,
                analysis_input
            )
            
            # Generate multiple gap analyses
            gaps = []
            for _ in range(3):  # Generate multiple gap analyses
                try:
                    gap = self.agent.structured_output(
                        KnowledgeGapAnalysis,
                        analysis_input
                    )
                    gaps.append(gap.dict())
                except Exception as e:
                    print(f"Error generating gap analysis: {e}")
                    continue
            
            # Generate summary
            summary_input = f"""
Based on the identified knowledge gaps, provide a comprehensive summary:

Gaps identified: {len(gaps)}
Gap details: {gaps}

Provide an overall assessment and learning recommendations.
            """
            
            try:
                summary = self.agent.structured_output(
                    KnowledgeGapSummary,
                    summary_input
                )
                summary_dict = summary.dict()
            except Exception as e:
                print(f"Error generating summary: {e}")
                summary_dict = {
                    'total_gaps_identified': len(gaps),
                    'high_priority_gaps': len([g for g in gaps if g.get('learning_priority') == 'high']),
                    'medium_priority_gaps': len([g for g in gaps if g.get('learning_priority') == 'medium']),
                    'low_priority_gaps': len([g for g in gaps if g.get('learning_priority') == 'low']),
                    'top_gap_categories': list(set(g.get('gap_type', '') for g in gaps)),
                    'learning_opportunities': [g.get('topic', '') for g in gaps[:5]],
                    'overall_assessment': f'Identified {len(gaps)} knowledge gaps across {len(set(g.get("gap_type", "") for g in gaps))} categories'
                }
            
            return {
                'gaps': gaps,
                'summary': summary_dict,
                'analysis_method': 'strands_claude'
            }
            
        except Exception as e:
            print(f"Strands gap analysis failed: {e}")
            # Fallback to rule-based gap detection
            return self._fallback_gap_analysis(knowledge_analysis)
    
    def _fallback_gap_analysis(self, knowledge_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback gap analysis using rule-based approach."""
        try:
            gaps = []
            topic_frequency = knowledge_analysis.get('topic_frequency', {})
            top_topics = knowledge_analysis.get('top_topics', [])
            
            # Identify gaps based on topic relationships
            identified_gaps = self.knowledge_analyzer.identify_topic_gaps(
                knowledge_analysis.get('user_id', 'unknown'),
                list(topic_frequency.keys())
            )
            
            for gap in identified_gaps:
                if 'error' not in gap:
                    gaps.append(gap)
            
            return {
                'gaps': gaps,
                'summary': {
                    'total_gaps_identified': len(gaps),
                    'high_priority_gaps': len([g for g in gaps if g.get('confidence_score', 0) > 0.8]),
                    'medium_priority_gaps': len([g for g in gaps if 0.5 <= g.get('confidence_score', 0) <= 0.8]),
                    'low_priority_gaps': len([g for g in gaps if g.get('confidence_score', 0) < 0.5]),
                    'top_gap_categories': list(set(g.get('gap_type', '') for g in gaps)),
                    'learning_opportunities': [g.get('topic', '') for g in gaps[:5]],
                    'overall_assessment': f'Identified {len(gaps)} knowledge gaps using rule-based analysis'
                },
                'analysis_method': 'rule_based_fallback'
            }
            
        except Exception as e:
            return {
                'gaps': [],
                'summary': {
                    'total_gaps_identified': 0,
                    'high_priority_gaps': 0,
                    'medium_priority_gaps': 0,
                    'low_priority_gaps': 0,
                    'top_gap_categories': [],
                    'learning_opportunities': [],
                    'overall_assessment': f'Gap analysis failed: {str(e)}'
                },
                'analysis_method': 'error'
            }
    
    def _parse_timeframe(self, timeframe: str) -> int:
        """Parse timeframe string to days."""
        try:
            if timeframe.endswith('d'):
                return int(timeframe[:-1])
            elif timeframe.endswith('w'):
                return int(timeframe[:-1]) * 7
            elif timeframe.endswith('m'):
                return int(timeframe[:-1]) * 30
            elif timeframe.endswith('y'):
                return int(timeframe[:-1]) * 365
            else:
                return 30  # Default to 30 days
        except:
            return 30
    
    def get_user_knowledge_gaps(self, user_id: str, resolved: bool = False) -> Dict[str, Any]:
        """
        Get user's stored knowledge gaps.
        
        Args:
            user_id: User identifier
            resolved: Whether to include resolved gaps
            
        Returns:
            Dict containing user's knowledge gaps
        """
        try:
            gaps = self.knowledge_analyzer.get_user_knowledge_gaps(user_id, resolved)
            
            return {
                'success': True,
                'result': {
                    'user_id': user_id,
                    'gaps': gaps,
                    'total_gaps': len(gaps),
                    'unresolved_gaps': len([g for g in gaps if g.get('resolved', 'false') == 'false'])
                },
                'message': f'Retrieved {len(gaps)} knowledge gaps for user {user_id}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get knowledge gaps: {str(e)}',
                'result': None
            }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get information about agent capabilities."""
        return {
            'name': self.name,
            'description': self.description,
            'framework': 'Strands',
            'model': 'claude-3-5-haiku-20241022',
            'supported_actions': ['detect_gaps', 'get_user_knowledge_gaps'],
            'input_types': ['user_id', 'timeframe'],
            'output_format': 'knowledge_gap_analysis_with_recommendations',
            'ai_features': [
                'intelligent_gap_detection',
                'learning_opportunity_identification',
                'priority_assessment',
                'personalized_recommendations'
            ],
            'tools_used': [
                'knowledge_analyzer'
            ]
        }
    
    def validate_input(self, action: str, input_data: Dict[str, Any]) -> bool:
        """Validate input data for the specified action."""
        if action == 'detect_gaps':
            return 'user_id' in input_data and bool(input_data.get('user_id'))
        elif action == 'get_user_knowledge_gaps':
            return 'user_id' in input_data and bool(input_data.get('user_id'))
        return False
