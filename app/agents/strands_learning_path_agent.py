"""
Strands-compatible Learning Path Agent for Merlin.
Uses the actual Strands framework for intelligent learning path generation and recommendations.
"""

import os
from typing import Dict, Any, Optional, List
from strands import Agent
from strands.models.anthropic import AnthropicModel
from app.agents.tools.knowledge_assessor import KnowledgeAssessor
from app.agents.tools.path_builder import PathBuilder
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LearningObjective(BaseModel):
    """Structured output for learning objectives."""
    objective: str = Field(description="Specific learning objective")
    priority: str = Field(description="Priority level: 'high', 'medium', 'low'")
    estimated_duration: str = Field(description="Estimated time to achieve objective")
    prerequisites: List[str] = Field(description="List of prerequisite knowledge or skills")
    success_criteria: List[str] = Field(description="Criteria for measuring success")


class LearningPathPhase(BaseModel):
    """Structured output for learning path phases."""
    phase_number: int = Field(description="Phase number in the learning path")
    title: str = Field(description="Phase title")
    description: str = Field(description="Detailed description of what will be learned in this phase")
    duration: str = Field(description="Estimated duration for this phase")
    difficulty: str = Field(description="Difficulty level: 'easy', 'medium', 'hard', 'expert'")
    learning_objectives: List[str] = Field(description="Specific learning objectives for this phase")
    resources: List[str] = Field(description="Recommended resources for this phase")
    activities: List[str] = Field(description="Learning activities for this phase")
    assessments: List[str] = Field(description="Assessment methods for this phase")


class LearningPathStructure(BaseModel):
    """Structured output for complete learning path."""
    topic: str = Field(description="Learning topic")
    current_level: str = Field(description="Current knowledge level")
    target_level: str = Field(description="Target knowledge level")
    total_duration: str = Field(description="Total estimated duration")
    difficulty_progression: List[str] = Field(description="Difficulty progression across phases")
    phases: List[dict] = Field(description="List of learning path phases")
    key_learning_outcomes: List[str] = Field(description="Key outcomes after completing the path")
    prerequisites: List[str] = Field(description="Prerequisites for starting this learning path")


class StrandsLearningPathAgent:
    """
    Learning path generation agent using Strands framework for personalized recommendations.
    """
    
    def __init__(self):
        self.name = "StrandsLearningPathAgent"
        self.description = "AI-powered learning path generation using Strands and Claude"
        
        # Initialize Claude model via Strands
        self.model = AnthropicModel(
            client_args={
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
            },
            max_tokens=1500,
            model_id="claude-3-5-haiku-20241022",
            params={
                "temperature": 0.3,  # Balanced creativity for path generation
            }
        )
        
        # Create Strands agent for learning path generation
        self.agent = Agent(
            model=self.model,
            system_prompt=self._get_learning_path_prompt()
        )
        
        # Initialize tools
        self.knowledge_assessor = KnowledgeAssessor()
        self.path_builder = PathBuilder()
    
    def _get_learning_path_prompt(self) -> str:
        """Get the system prompt for learning path generation."""
        return """You are Merlin's intelligent learning path generator. Your job is to create personalized, structured learning paths that help users achieve their learning goals.

Your capabilities include:
1. **Knowledge Assessment**: Analyze current knowledge levels and identify gaps
2. **Goal Setting**: Create SMART learning objectives
3. **Path Planning**: Design structured learning sequences with clear progression
4. **Resource Recommendation**: Suggest appropriate learning materials and activities
5. **Progress Tracking**: Define clear milestones and assessment criteria

Guidelines for learning paths:
- Create realistic, achievable learning objectives
- Ensure logical progression from basic to advanced concepts
- Include diverse learning activities (reading, practice, projects)
- Provide clear success criteria and assessment methods
- Consider different learning styles and preferences
- Estimate realistic timeframes for each phase

Focus on creating actionable, personalized learning experiences that lead to meaningful knowledge growth."""
    
    def suggest_learning_path(self, user_id: str, topic: str = None, 
                            current_level: str = None, objectives: List[str] = None) -> Dict[str, Any]:
        """
        Generate personalized learning path suggestions using Strands framework.
        
        Args:
            user_id: User identifier
            topic: Learning topic (optional)
            current_level: Current knowledge level (optional)
            objectives: Learning objectives (optional)
            
        Returns:
            Dict containing learning path suggestions
        """
        try:
            # Assess current knowledge if not provided
            if not current_level:
                assessment_result = self.knowledge_assessor.assess_knowledge_level(user_id, topic)
                if 'error' in assessment_result:
                    return {
                        'success': False,
                        'error': f'Knowledge assessment failed: {assessment_result["error"]}',
                        'result': None
                    }
                current_level = assessment_result.get('knowledge_level', 'beginner')
            
            # Generate learning objectives if not provided
            if not objectives:
                objectives_result = self.knowledge_assessor.generate_learning_objectives(
                    user_id, topic or 'general learning', current_level
                )
                if 'error' in objectives_result:
                    objectives = [f"Improve knowledge in {topic or 'general topics'}"]
                else:
                    objectives = objectives_result.get('objectives', [])
            
            # Use Strands to generate learning path structure
            path_structure = self._generate_path_structure_with_strands(
                topic, current_level, objectives
            )
            
            if not path_structure:
                return {
                    'success': False,
                    'error': 'Failed to generate learning path structure',
                    'result': None
                }
            
            # Build personalized learning path
            path_result = self.path_builder.build_learning_path(
                user_id, topic or 'general', current_level, objectives
            )
            
            if not path_result.get('success'):
                return {
                    'success': False,
                    'error': f'Path building failed: {path_result.get("error")}',
                    'result': None
                }
            
            # Enhance path with Strands-generated structure
            enhanced_path = self._enhance_path_with_strands_structure(
                path_result['result'], path_structure
            )
            
            # Prepare comprehensive result
            result = {
                'user_id': user_id,
                'topic': topic or 'general learning',
                'current_level': current_level,
                'target_level': path_structure.get('target_level', 'intermediate'),
                'learning_objectives': objectives,
                'path_structure': enhanced_path,
                'strands_enhancement': path_structure,
                'path_metadata': {
                    'total_phases': len(enhanced_path.get('phases', [])),
                    'estimated_duration': enhanced_path.get('estimated_timeline', {}).get('total_weeks', 8),
                    'difficulty_progression': path_structure.get('difficulty_progression', []),
                    'learning_outcomes': path_structure.get('key_learning_outcomes', [])
                }
            }
            
            return {
                'success': True,
                'result': result,
                'message': f'Generated personalized learning path for {topic or "general learning"} at {current_level} level'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Learning path generation failed: {str(e)}',
                'result': None
            }
    
    def _generate_path_structure_with_strands(self, topic: str, current_level: str, 
                                            objectives: List[str]) -> Dict[str, Any]:
        """Generate learning path structure using Strands."""
        try:
            structure_input = f"""
Create a comprehensive learning path structure for the following scenario:

Topic: {topic or 'General Learning'}
Current Level: {current_level}
Learning Objectives: {objectives}

Please design a structured learning path that includes:
1. Clear progression from current level to next level
2. Specific phases with detailed descriptions
3. Realistic time estimates for each phase
4. Appropriate difficulty progression
5. Key learning outcomes
6. Prerequisites for success

Focus on creating a practical, achievable learning journey that builds knowledge systematically.
            """
            
            path_structure = self.agent.structured_output(
                LearningPathStructure,
                structure_input
            )
            
            return path_structure.dict()
            
        except Exception as e:
            print(f"Strands path structure generation failed: {e}")
            # Fallback to template-based structure
            return self._fallback_path_structure(topic, current_level, objectives)
    
    def _fallback_path_structure(self, topic: str, current_level: str, 
                               objectives: List[str]) -> Dict[str, Any]:
        """Fallback path structure generation using templates."""
        try:
            # Get next level
            level_progression = {
                'beginner': 'intermediate',
                'intermediate': 'advanced',
                'advanced': 'expert',
                'expert': 'master'
            }
            target_level = level_progression.get(current_level.lower(), 'intermediate')
            
            # Create basic phases based on level
            if current_level.lower() == 'beginner':
                phases = [
                    {
                        'phase_number': 1,
                        'title': f'{topic or "Topic"} Fundamentals',
                        'description': f'Learn the basic concepts and principles of {topic or "the topic"}',
                        'duration': '2-3 weeks',
                        'difficulty': 'easy',
                        'learning_objectives': [f'Understand basic {topic or "topic"} concepts'],
                        'resources': ['Tutorials', 'Documentation'],
                        'activities': ['Reading', 'Basic exercises'],
                        'assessments': ['Knowledge quiz', 'Basic project']
                    },
                    {
                        'phase_number': 2,
                        'title': f'{topic or "Topic"} Practice',
                        'description': f'Apply {topic or "topic"} knowledge through practical exercises',
                        'duration': '2-3 weeks',
                        'difficulty': 'medium',
                        'learning_objectives': [f'Apply {topic or "topic"} concepts practically'],
                        'resources': ['Practice projects', 'Exercises'],
                        'activities': ['Hands-on practice', 'Small projects'],
                        'assessments': ['Practical exercises', 'Project review']
                    }
                ]
            else:
                phases = [
                    {
                        'phase_number': 1,
                        'title': f'Advanced {topic or "Topic"} Concepts',
                        'description': f'Deepen understanding of advanced {topic or "topic"} concepts',
                        'duration': '3-4 weeks',
                        'difficulty': 'hard',
                        'learning_objectives': [f'Master advanced {topic or "topic"} concepts'],
                        'resources': ['Advanced tutorials', 'Research papers'],
                        'activities': ['Complex projects', 'Research'],
                        'assessments': ['Advanced project', 'Peer review']
                    }
                ]
            
            return {
                'topic': topic or 'General Learning',
                'current_level': current_level,
                'target_level': target_level,
                'total_duration': f'{sum(int(p["duration"].split("-")[0]) for p in phases)}-{sum(int(p["duration"].split("-")[1]) for p in phases)} weeks',
                'difficulty_progression': [p['difficulty'] for p in phases],
                'phases': phases,
                'key_learning_outcomes': [f'Master {topic or "topic"} at {target_level} level'],
                'prerequisites': [f'Basic understanding of {topic or "related topics"}']
            }
            
        except Exception as e:
            return {
                'topic': topic or 'General Learning',
                'current_level': current_level,
                'target_level': 'intermediate',
                'total_duration': '4-6 weeks',
                'difficulty_progression': ['easy', 'medium'],
                'phases': [],
                'key_learning_outcomes': ['Improve knowledge and skills'],
                'prerequisites': ['Basic interest in the topic'],
                'error': str(e)
            }
    
    def _enhance_path_with_strands_structure(self, base_path: Dict[str, Any], 
                                           strands_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance base path with Strands-generated structure."""
        try:
            enhanced_path = base_path.copy()
            
            # Enhance phases with Strands structure
            if 'phases' in strands_structure and strands_structure['phases']:
                enhanced_phases = []
                for i, phase in enumerate(strands_structure['phases']):
                    enhanced_phase = {
                        'phase': phase.get('phase_number', i + 1),
                        'title': phase.get('title', f'Phase {i + 1}'),
                        'duration': phase.get('duration', '2 weeks'),
                        'difficulty': phase.get('difficulty', 'medium'),
                        'description': phase.get('description', ''),
                        'learning_objectives': phase.get('learning_objectives', []),
                        'resources': phase.get('resources', []),
                        'activities': phase.get('activities', []),
                        'assessments': phase.get('assessments', []),
                        'estimated_effort': {
                            'estimated_hours': self._estimate_phase_hours(phase.get('difficulty', 'medium')),
                            'effort_level': phase.get('difficulty', 'medium')
                        }
                    }
                    enhanced_phases.append(enhanced_phase)
                
                enhanced_path['phases'] = enhanced_phases
            
            # Add Strands enhancements
            enhanced_path['strands_enhancements'] = {
                'target_level': strands_structure.get('target_level'),
                'key_learning_outcomes': strands_structure.get('key_learning_outcomes', []),
                'prerequisites': strands_structure.get('prerequisites', []),
                'difficulty_progression': strands_structure.get('difficulty_progression', [])
            }
            
            return enhanced_path
            
        except Exception as e:
            print(f"Error enhancing path: {e}")
            return base_path
    
    def _estimate_phase_hours(self, difficulty: str) -> int:
        """Estimate hours for a phase based on difficulty."""
        hour_estimates = {
            'easy': 10,
            'medium': 20,
            'hard': 40,
            'expert': 60
        }
        return hour_estimates.get(difficulty.lower(), 20)
    
    def get_user_learning_paths(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's learning paths.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict containing user's learning paths
        """
        try:
            paths = self.path_builder.get_user_learning_paths(user_id)
            
            return {
                'success': True,
                'result': {
                    'user_id': user_id,
                    'learning_paths': paths,
                    'total_paths': len(paths),
                    'active_paths': len([p for p in paths if p.get('progress', {}).get('overall_progress', 0) < 100])
                },
                'message': f'Retrieved {len(paths)} learning paths for user {user_id}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get learning paths: {str(e)}',
                'result': None
            }
    
    def update_learning_progress(self, path_id: str, progress_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update learning progress for a path.
        
        Args:
            path_id: Learning path identifier
            progress_data: Progress update data
            
        Returns:
            Dict containing update result
        """
        try:
            result = self.path_builder.update_learning_progress(path_id, progress_data)
            
            return {
                'success': result.get('success', False),
                'result': result,
                'message': result.get('message', 'Progress update completed')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to update progress: {str(e)}',
                'result': None
            }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get information about agent capabilities."""
        return {
            'name': self.name,
            'description': self.description,
            'framework': 'Strands',
            'model': 'claude-3-5-haiku-20241022',
            'supported_actions': ['suggest_learning_path', 'get_user_learning_paths', 'update_learning_progress'],
            'input_types': ['user_id', 'topic', 'current_level', 'objectives'],
            'output_format': 'personalized_learning_path_with_enhancements',
            'ai_features': [
                'intelligent_path_generation',
                'knowledge_level_assessment',
                'learning_objective_creation',
                'personalized_recommendations',
                'progress_tracking'
            ],
            'tools_used': [
                'knowledge_assessor',
                'path_builder'
            ]
        }
    
    def validate_input(self, action: str, input_data: Dict[str, Any]) -> bool:
        """Validate input data for the specified action."""
        if action == 'suggest_learning_path':
            return 'user_id' in input_data and input_data['user_id']
        elif action == 'get_user_learning_paths':
            return 'user_id' in input_data and input_data['user_id']
        elif action == 'update_learning_progress':
            return 'path_id' in input_data and input_data['path_id']
        return False
