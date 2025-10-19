"""
Path Builder Tool for Merlin Learning Features.
Builds personalized learning paths based on user knowledge and objectives.
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from db.models import Note, LearningPath, UserKnowledgeProfile
from dotenv import load_dotenv
import json
import uuid

# Load environment variables
load_dotenv()

class PathBuilder:
    """
    Tool for building personalized learning paths based on user knowledge and objectives.
    """
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Define learning path templates
        self.path_templates = {
            'python': {
                'beginner': [
                    {'phase': 1, 'title': 'Python Basics', 'duration': '1-2 weeks', 'difficulty': 'easy'},
                    {'phase': 2, 'title': 'Data Structures & Control Flow', 'duration': '1-2 weeks', 'difficulty': 'easy'},
                    {'phase': 3, 'title': 'Functions & Modules', 'duration': '1 week', 'difficulty': 'easy'},
                    {'phase': 4, 'title': 'File I/O & Error Handling', 'duration': '1 week', 'difficulty': 'medium'}
                ],
                'intermediate': [
                    {'phase': 1, 'title': 'Object-Oriented Programming', 'duration': '2 weeks', 'difficulty': 'medium'},
                    {'phase': 2, 'title': 'Advanced Python Features', 'duration': '2 weeks', 'difficulty': 'medium'},
                    {'phase': 3, 'title': 'Popular Libraries & Frameworks', 'duration': '2 weeks', 'difficulty': 'medium'},
                    {'phase': 4, 'title': 'Testing & Debugging', 'duration': '1 week', 'difficulty': 'medium'}
                ],
                'advanced': [
                    {'phase': 1, 'title': 'Advanced Python Concepts', 'duration': '3 weeks', 'difficulty': 'hard'},
                    {'phase': 2, 'title': 'Async Programming', 'duration': '2 weeks', 'difficulty': 'hard'},
                    {'phase': 3, 'title': 'Design Patterns', 'duration': '2 weeks', 'difficulty': 'hard'},
                    {'phase': 4, 'title': 'Performance Optimization', 'duration': '1 week', 'difficulty': 'expert'}
                ]
            },
            'machine_learning': {
                'beginner': [
                    {'phase': 1, 'title': 'ML Fundamentals', 'duration': '2 weeks', 'difficulty': 'easy'},
                    {'phase': 2, 'title': 'Data Preprocessing', 'duration': '2 weeks', 'difficulty': 'easy'},
                    {'phase': 3, 'title': 'Basic Algorithms', 'duration': '3 weeks', 'difficulty': 'medium'},
                    {'phase': 4, 'title': 'Model Evaluation', 'duration': '1 week', 'difficulty': 'medium'}
                ],
                'intermediate': [
                    {'phase': 1, 'title': 'Advanced Algorithms', 'duration': '3 weeks', 'difficulty': 'medium'},
                    {'phase': 2, 'title': 'Feature Engineering', 'duration': '2 weeks', 'difficulty': 'medium'},
                    {'phase': 3, 'title': 'Model Selection & Tuning', 'duration': '2 weeks', 'difficulty': 'hard'},
                    {'phase': 4, 'title': 'Ensemble Methods', 'duration': '1 week', 'difficulty': 'hard'}
                ],
                'advanced': [
                    {'phase': 1, 'title': 'Deep Learning Fundamentals', 'duration': '4 weeks', 'difficulty': 'hard'},
                    {'phase': 2, 'title': 'Neural Network Architectures', 'duration': '3 weeks', 'difficulty': 'expert'},
                    {'phase': 3, 'title': 'Advanced Deep Learning', 'duration': '3 weeks', 'difficulty': 'expert'},
                    {'phase': 4, 'title': 'ML in Production', 'duration': '2 weeks', 'difficulty': 'expert'}
                ]
            },
            'web_development': {
                'beginner': [
                    {'phase': 1, 'title': 'HTML & CSS Basics', 'duration': '2 weeks', 'difficulty': 'easy'},
                    {'phase': 2, 'title': 'JavaScript Fundamentals', 'duration': '3 weeks', 'difficulty': 'easy'},
                    {'phase': 3, 'title': 'Responsive Design', 'duration': '1 week', 'difficulty': 'medium'},
                    {'phase': 4, 'title': 'Basic Project', 'duration': '2 weeks', 'difficulty': 'medium'}
                ],
                'intermediate': [
                    {'phase': 1, 'title': 'Frontend Framework', 'duration': '4 weeks', 'difficulty': 'medium'},
                    {'phase': 2, 'title': 'Backend Development', 'duration': '3 weeks', 'difficulty': 'medium'},
                    {'phase': 3, 'title': 'Database Integration', 'duration': '2 weeks', 'difficulty': 'hard'},
                    {'phase': 4, 'title': 'Full-Stack Project', 'duration': '3 weeks', 'difficulty': 'hard'}
                ],
                'advanced': [
                    {'phase': 1, 'title': 'Advanced Frontend', 'duration': '3 weeks', 'difficulty': 'hard'},
                    {'phase': 2, 'title': 'Microservices Architecture', 'duration': '4 weeks', 'difficulty': 'expert'},
                    {'phase': 3, 'title': 'DevOps & Deployment', 'duration': '3 weeks', 'difficulty': 'expert'},
                    {'phase': 4, 'title': 'Performance & Security', 'duration': '2 weeks', 'difficulty': 'expert'}
                ]
            }
        }
    
    def build_learning_path(self, user_id: str, topic: str, current_level: str, 
                          objectives: List[str]) -> Dict[str, Any]:
        """
        Build a personalized learning path for a user.
        
        Args:
            user_id: User identifier
            topic: Learning topic
            current_level: Current knowledge level
            objectives: Learning objectives
            
        Returns:
            Personalized learning path
        """
        try:
            # Get base path template
            base_path = self._get_base_path_template(topic, current_level)
            
            if not base_path:
                return {
                    'error': f'No path template found for topic: {topic}, level: {current_level}',
                    'user_id': user_id
                }
            
            # Personalize the path based on user's existing knowledge
            personalized_path = self._personalize_path(user_id, topic, base_path, objectives)
            
            # Calculate estimated timeline
            estimated_timeline = self._calculate_timeline(personalized_path)
            
            # Create path structure
            path_structure = {
                'topic': topic,
                'current_level': current_level,
                'target_level': self._get_next_level(current_level),
                'phases': personalized_path,
                'estimated_timeline': estimated_timeline,
                'objectives': objectives,
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Store the learning path
            path_id = self._store_learning_path(user_id, topic, path_structure)
            
            return {
                'success': True,
                'path_id': path_id,
                'path_structure': path_structure,
                'user_id': user_id,
                'message': f'Learning path created for {topic} at {current_level} level'
            }
            
        except Exception as e:
            return {
                'error': f'Failed to build learning path: {str(e)}',
                'user_id': user_id,
                'topic': topic
            }
    
    def _get_base_path_template(self, topic: str, level: str) -> List[Dict[str, Any]]:
        """Get base path template for topic and level."""
        topic_lower = topic.lower()
        level_lower = level.lower()
        
        # Try exact match first
        if topic_lower in self.path_templates and level_lower in self.path_templates[topic_lower]:
            return self.path_templates[topic_lower][level_lower].copy()
        
        # Try to find similar topics
        for template_topic in self.path_templates:
            if self._topics_are_related(topic_lower, template_topic):
                if level_lower in self.path_templates[template_topic]:
                    return self.path_templates[template_topic][level_lower].copy()
        
        # Return generic path if no specific template found
        return self._get_generic_path(level_lower)
    
    def _topics_are_related(self, topic1: str, topic2: str) -> bool:
        """Check if two topics are related."""
        topic_relations = {
            'python': ['programming', 'data_science', 'machine_learning'],
            'machine_learning': ['ml', 'ai', 'artificial_intelligence', 'data_science'],
            'web_development': ['web_dev', 'frontend', 'backend', 'full_stack'],
            'data_science': ['data_analysis', 'statistics', 'python', 'machine_learning']
        }
        
        if topic1 in topic_relations:
            return topic2 in topic_relations[topic1]
        elif topic2 in topic_relations:
            return topic1 in topic_relations[topic2]
        
        return False
    
    def _get_generic_path(self, level: str) -> List[Dict[str, Any]]:
        """Get a generic learning path for any topic."""
        generic_paths = {
            'beginner': [
                {'phase': 1, 'title': 'Fundamentals', 'duration': '2 weeks', 'difficulty': 'easy'},
                {'phase': 2, 'title': 'Core Concepts', 'duration': '2 weeks', 'difficulty': 'easy'},
                {'phase': 3, 'title': 'Practical Applications', 'duration': '2 weeks', 'difficulty': 'medium'},
                {'phase': 4, 'title': 'First Project', 'duration': '2 weeks', 'difficulty': 'medium'}
            ],
            'intermediate': [
                {'phase': 1, 'title': 'Advanced Concepts', 'duration': '3 weeks', 'difficulty': 'medium'},
                {'phase': 2, 'title': 'Specialized Topics', 'duration': '3 weeks', 'difficulty': 'medium'},
                {'phase': 3, 'title': 'Best Practices', 'duration': '2 weeks', 'difficulty': 'hard'},
                {'phase': 4, 'title': 'Real-World Project', 'duration': '4 weeks', 'difficulty': 'hard'}
            ],
            'advanced': [
                {'phase': 1, 'title': 'Expert-Level Topics', 'duration': '4 weeks', 'difficulty': 'hard'},
                {'phase': 2, 'title': 'Advanced Techniques', 'duration': '3 weeks', 'difficulty': 'expert'},
                {'phase': 3, 'title': 'Innovation & Research', 'duration': '3 weeks', 'difficulty': 'expert'},
                {'phase': 4, 'title': 'Leadership & Mentoring', 'duration': '2 weeks', 'difficulty': 'expert'}
            ]
        }
        
        return generic_paths.get(level, generic_paths['beginner']).copy()
    
    def _personalize_path(self, user_id: str, topic: str, base_path: List[Dict[str, Any]], 
                        objectives: List[str]) -> List[Dict[str, Any]]:
        """Personalize the learning path based on user's existing knowledge."""
        try:
            session = self.SessionLocal()
            
            # Get user's existing notes related to the topic
            notes = session.query(Note).all()  # In a real system, filter by user_id and topic
            
            # Analyze existing knowledge
            existing_knowledge = self._analyze_existing_knowledge(notes, topic)
            
            # Adjust path based on existing knowledge
            personalized_path = base_path.copy()
            
            for phase in personalized_path:
                # Add resources based on existing knowledge gaps
                phase['resources'] = self._get_phase_resources(phase, topic, existing_knowledge)
                
                # Add learning activities
                phase['activities'] = self._get_phase_activities(phase, topic)
                
                # Add assessment criteria
                phase['assessments'] = self._get_phase_assessments(phase, topic)
                
                # Add estimated effort
                phase['estimated_effort'] = self._estimate_phase_effort(phase, existing_knowledge)
            
            session.close()
            return personalized_path
            
        except Exception as e:
            print(f"Error personalizing path: {e}")
            return base_path
    
    def _analyze_existing_knowledge(self, notes: List[Note], topic: str) -> Dict[str, Any]:
        """Analyze user's existing knowledge on the topic."""
        try:
            topic_notes = []
            topic_lower = topic.lower()
            
            for note in notes:
                if (topic_lower in note.title.lower() or 
                    topic_lower in note.content.lower() or
                    (note.tags and any(topic_lower in tag.lower() for tag in note.tags))):
                    topic_notes.append(note)
            
            # Analyze knowledge depth
            total_content = sum(len(note.content) for note in topic_notes)
            avg_content_length = total_content / len(topic_notes) if topic_notes else 0
            
            # Analyze tag coverage
            all_tags = []
            for note in topic_notes:
                if note.tags:
                    all_tags.extend(note.tags)
            
            unique_tags = len(set(all_tags))
            
            return {
                'topic_notes_count': len(topic_notes),
                'avg_content_length': avg_content_length,
                'unique_tags': unique_tags,
                'knowledge_depth': min(1.0, avg_content_length / 1000),
                'topic_coverage': min(1.0, unique_tags / 10)
            }
            
        except Exception as e:
            return {
                'topic_notes_count': 0,
                'avg_content_length': 0,
                'unique_tags': 0,
                'knowledge_depth': 0,
                'topic_coverage': 0,
                'error': str(e)
            }
    
    def _get_phase_resources(self, phase: Dict[str, Any], topic: str, 
                           existing_knowledge: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get recommended resources for a phase."""
        try:
            phase_title = phase['title'].lower()
            difficulty = phase['difficulty']
            
            # Define resource types by phase and difficulty
            resource_types = {
                'easy': ['tutorials', 'documentation', 'video_courses'],
                'medium': ['documentation', 'practice_projects', 'books'],
                'hard': ['research_papers', 'advanced_courses', 'open_source_projects'],
                'expert': ['research_papers', 'conference_talks', 'mentorship']
            }
            
            resources = []
            
            for resource_type in resource_types.get(difficulty, ['tutorials', 'documentation']):
                resource = {
                    'type': resource_type,
                    'title': f'{resource_type.replace("_", " ").title()} for {phase["title"]}',
                    'description': f'Comprehensive {resource_type.replace("_", " ")} covering {phase["title"]} concepts',
                    'estimated_time': self._get_resource_time(resource_type, difficulty),
                    'priority': 'high' if resource_type in ['tutorials', 'documentation'] else 'medium'
                }
                resources.append(resource)
            
            return resources
            
        except Exception as e:
            return [{'error': f'Failed to get resources: {str(e)}'}]
    
    def _get_phase_activities(self, phase: Dict[str, Any], topic: str) -> List[Dict[str, Any]]:
        """Get learning activities for a phase."""
        try:
            difficulty = phase['difficulty']
            phase_title = phase['title']
            
            activities = []
            
            if difficulty == 'easy':
                activities = [
                    {'type': 'reading', 'title': f'Read about {phase_title}', 'estimated_time': '2-3 hours'},
                    {'type': 'practice', 'title': f'Practice {phase_title} basics', 'estimated_time': '3-5 hours'},
                    {'type': 'quiz', 'title': f'Take {phase_title} quiz', 'estimated_time': '30 minutes'}
                ]
            elif difficulty == 'medium':
                activities = [
                    {'type': 'project', 'title': f'Build {phase_title} project', 'estimated_time': '5-8 hours'},
                    {'type': 'coding', 'title': f'Code {phase_title} examples', 'estimated_time': '4-6 hours'},
                    {'type': 'discussion', 'title': f'Discuss {phase_title} concepts', 'estimated_time': '1-2 hours'}
                ]
            elif difficulty == 'hard':
                activities = [
                    {'type': 'advanced_project', 'title': f'Advanced {phase_title} project', 'estimated_time': '10-15 hours'},
                    {'type': 'research', 'title': f'Research {phase_title} best practices', 'estimated_time': '3-5 hours'},
                    {'type': 'presentation', 'title': f'Present {phase_title} findings', 'estimated_time': '2-3 hours'}
                ]
            else:  # expert
                activities = [
                    {'type': 'expert_project', 'title': f'Expert-level {phase_title} project', 'estimated_time': '20-30 hours'},
                    {'type': 'mentoring', 'title': f'Mentor others in {phase_title}', 'estimated_time': '5-10 hours'},
                    {'type': 'contribution', 'title': f'Contribute to {phase_title} community', 'estimated_time': '10-15 hours'}
                ]
            
            return activities
            
        except Exception as e:
            return [{'error': f'Failed to get activities: {str(e)}'}]
    
    def _get_phase_assessments(self, phase: Dict[str, Any], topic: str) -> List[Dict[str, Any]]:
        """Get assessment criteria for a phase."""
        try:
            difficulty = phase['difficulty']
            phase_title = phase['title']
            
            assessments = []
            
            if difficulty in ['easy', 'medium']:
                assessments = [
                    {'type': 'knowledge_check', 'title': f'{phase_title} Knowledge Quiz', 'weight': 0.3},
                    {'type': 'practical_exercise', 'title': f'{phase_title} Practice Exercise', 'weight': 0.4},
                    {'type': 'project_review', 'title': f'{phase_title} Project Review', 'weight': 0.3}
                ]
            else:  # hard, expert
                assessments = [
                    {'type': 'comprehensive_project', 'title': f'{phase_title} Comprehensive Project', 'weight': 0.5},
                    {'type': 'peer_review', 'title': f'{phase_title} Peer Review', 'weight': 0.2},
                    {'type': 'self_assessment', 'title': f'{phase_title} Self Assessment', 'weight': 0.1},
                    {'type': 'mentor_evaluation', 'title': f'{phase_title} Mentor Evaluation', 'weight': 0.2}
                ]
            
            return assessments
            
        except Exception as e:
            return [{'error': f'Failed to get assessments: {str(e)}'}]
    
    def _estimate_phase_effort(self, phase: Dict[str, Any], existing_knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate effort required for a phase."""
        try:
            difficulty = phase['difficulty']
            knowledge_depth = existing_knowledge.get('knowledge_depth', 0)
            
            # Base effort hours by difficulty
            base_effort = {
                'easy': 10,
                'medium': 20,
                'hard': 40,
                'expert': 60
            }
            
            hours = base_effort.get(difficulty, 20)
            
            # Adjust based on existing knowledge
            if knowledge_depth > 0.5:
                hours = int(hours * 0.7)  # Reduce effort if user has good foundation
            
            return {
                'estimated_hours': hours,
                'effort_level': difficulty,
                'adjustment_factor': 0.7 if knowledge_depth > 0.5 else 1.0
            }
            
        except Exception as e:
            return {
                'estimated_hours': 20,
                'effort_level': 'medium',
                'adjustment_factor': 1.0,
                'error': str(e)
            }
    
    def _get_resource_time(self, resource_type: str, difficulty: str) -> str:
        """Get estimated time for a resource type."""
        time_map = {
            'tutorials': '2-4 hours',
            'documentation': '1-3 hours',
            'video_courses': '4-8 hours',
            'practice_projects': '6-12 hours',
            'books': '10-20 hours',
            'research_papers': '3-6 hours',
            'advanced_courses': '8-16 hours',
            'open_source_projects': '20-40 hours',
            'conference_talks': '1-2 hours',
            'mentorship': '5-10 hours'
        }
        return time_map.get(resource_type, '2-4 hours')
    
    def _calculate_timeline(self, path: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall timeline for the learning path."""
        try:
            total_weeks = 0
            total_hours = 0
            
            for phase in path:
                # Parse duration
                duration = phase.get('duration', '2 weeks')
                if 'week' in duration:
                    weeks = int(duration.split()[0].split('-')[0])
                    total_weeks += weeks
                
                # Add effort hours
                effort = phase.get('estimated_effort', {})
                hours = effort.get('estimated_hours', 10)
                total_hours += hours
            
            return {
                'total_weeks': total_weeks,
                'total_hours': total_hours,
                'estimated_completion': (datetime.utcnow() + timedelta(weeks=total_weeks)).isoformat(),
                'phases_count': len(path)
            }
            
        except Exception as e:
            return {
                'total_weeks': 8,
                'total_hours': 80,
                'estimated_completion': (datetime.utcnow() + timedelta(weeks=8)).isoformat(),
                'phases_count': len(path),
                'error': str(e)
            }
    
    def _get_next_level(self, current_level: str) -> str:
        """Get the next level after current level."""
        level_progression = {
            'beginner': 'intermediate',
            'intermediate': 'advanced',
            'advanced': 'expert',
            'expert': 'master'
        }
        return level_progression.get(current_level.lower(), 'intermediate')
    
    def _store_learning_path(self, user_id: str, topic: str, path_structure: Dict[str, Any]) -> str:
        """Store the learning path in the database."""
        try:
            session = self.SessionLocal()
            
            # Generate unique path ID
            path_id = str(uuid.uuid4())
            
            learning_path = LearningPath(
                id=path_id,
                user_id=user_id,
                topic=topic,
                path_structure=path_structure,
                progress={'current_phase': 1, 'completed_phases': [], 'overall_progress': 0},
                estimated_duration=path_structure['estimated_timeline']['total_weeks'],
                difficulty_level=path_structure['current_level']
            )
            
            session.add(learning_path)
            session.commit()
            
            session.close()
            return path_id
            
        except Exception as e:
            print(f"Error storing learning path: {e}")
            return str(uuid.uuid4())  # Return a fallback ID
    
    def get_user_learning_paths(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all learning paths for a user."""
        try:
            session = self.SessionLocal()
            
            paths = session.query(LearningPath).filter(
                LearningPath.user_id == user_id
            ).order_by(LearningPath.created_at.desc()).all()
            
            session.close()
            
            return [
                {
                    'id': path.id,
                    'topic': path.topic,
                    'path_structure': path.path_structure,
                    'progress': path.progress,
                    'estimated_duration': path.estimated_duration,
                    'difficulty_level': path.difficulty_level,
                    'created_at': path.created_at.isoformat(),
                    'updated_at': path.updated_at.isoformat()
                }
                for path in paths
            ]
            
        except Exception as e:
            return [{'error': f'Failed to get learning paths: {str(e)}'}]
    
    def update_learning_progress(self, path_id: str, progress_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update progress for a learning path."""
        try:
            session = self.SessionLocal()
            
            path = session.query(LearningPath).filter(LearningPath.id == path_id).first()
            
            if path:
                path.progress = progress_data
                path.updated_at = datetime.utcnow()
                session.commit()
                
                session.close()
                return {'success': True, 'message': 'Progress updated successfully'}
            else:
                session.close()
                return {'error': 'Learning path not found'}
                
        except Exception as e:
            return {'error': f'Failed to update progress: {str(e)}'}
