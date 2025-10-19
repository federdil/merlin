"""
Knowledge Assessor Tool for Merlin Learning Features.
Assesses user knowledge levels and generates learning objectives.
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from db.models import Note, UserKnowledgeProfile, LearningPath
from app.agents.tools.embedding import generate_embedding, compute_similarity
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

class KnowledgeAssessor:
    """
    Tool for assessing user knowledge levels and generating learning objectives.
    """
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Define knowledge levels
        self.knowledge_levels = {
            'beginner': 0,
            'intermediate': 1,
            'advanced': 2,
            'expert': 3
        }
        
        # Define topic categories and their relationships
        self.topic_categories = {
            'programming': {
                'python': ['data_science', 'machine_learning', 'web_development', 'automation'],
                'javascript': ['web_development', 'frontend', 'backend', 'mobile'],
                'java': ['enterprise', 'spring', 'android', 'backend'],
                'c++': ['systems_programming', 'game_development', 'embedded'],
                'sql': ['database_design', 'data_analysis', 'backend']
            },
            'data_science': {
                'statistics': ['probability', 'hypothesis_testing', 'regression'],
                'machine_learning': ['supervised_learning', 'unsupervised_learning', 'deep_learning'],
                'data_visualization': ['matplotlib', 'seaborn', 'plotly', 'd3'],
                'big_data': ['hadoop', 'spark', 'kafka', 'nosql']
            },
            'web_development': {
                'frontend': ['html', 'css', 'javascript', 'react', 'vue'],
                'backend': ['nodejs', 'python', 'java', 'php'],
                'full_stack': ['mern', 'mean', 'django', 'rails']
            },
            'design': {
                'ui_design': ['figma', 'sketch', 'adobe_xd'],
                'ux_design': ['user_research', 'wireframing', 'prototyping'],
                'graphic_design': ['photoshop', 'illustrator', 'indesign']
            },
            'business': {
                'strategy': ['business_model', 'market_analysis', 'competitive_analysis'],
                'marketing': ['digital_marketing', 'content_marketing', 'seo'],
                'finance': ['accounting', 'financial_modeling', 'investment']
            }
        }
    
    def assess_knowledge_level(self, user_id: str, topic: str = None) -> Dict[str, Any]:
        """
        Assess user's knowledge level for a specific topic or overall.
        
        Args:
            user_id: User identifier
            topic: Specific topic to assess (optional)
            
        Returns:
            Knowledge assessment results
        """
        try:
            session = self.SessionLocal()
            
            # Get user's notes
            notes = session.query(Note).all()  # In a real system, filter by user_id
            
            if not notes:
                return {
                    'user_id': user_id,
                    'topic': topic,
                    'knowledge_level': 'beginner',
                    'confidence': 0.0,
                    'assessment_reasoning': 'No content found for assessment'
                }
            
            if topic:
                # Assess specific topic
                topic_assessment = self._assess_topic_knowledge(notes, topic)
                return {
                    'user_id': user_id,
                    'topic': topic,
                    **topic_assessment
                }
            else:
                # Assess overall knowledge
                overall_assessment = self._assess_overall_knowledge(notes)
                return {
                    'user_id': user_id,
                    'topic': 'overall',
                    **overall_assessment
                }
            
        except Exception as e:
            return {
                'error': f'Knowledge assessment failed: {str(e)}',
                'user_id': user_id,
                'topic': topic
            }
        finally:
            session.close()
    
    def _assess_topic_knowledge(self, notes: List[Note], topic: str) -> Dict[str, Any]:
        """Assess knowledge level for a specific topic."""
        try:
            # Filter notes related to the topic
            topic_notes = []
            topic_lower = topic.lower()
            
            for note in notes:
                # Check if note is related to topic
                if (topic_lower in note.title.lower() or 
                    topic_lower in note.content.lower() or
                    (note.tags and any(topic_lower in tag.lower() for tag in note.tags))):
                    topic_notes.append(note)
            
            if not topic_notes:
                return {
                    'knowledge_level': 'beginner',
                    'confidence': 0.1,
                    'assessment_reasoning': f'No content found related to {topic}',
                    'related_notes_count': 0
                }
            
            # Analyze content depth and complexity
            content_analysis = self._analyze_content_depth(topic_notes, topic)
            
            # Determine knowledge level based on analysis
            knowledge_level = self._determine_knowledge_level(content_analysis)
            
            return {
                'knowledge_level': knowledge_level,
                'confidence': content_analysis['confidence'],
                'assessment_reasoning': content_analysis['reasoning'],
                'related_notes_count': len(topic_notes),
                'content_analysis': content_analysis
            }
            
        except Exception as e:
            return {
                'knowledge_level': 'beginner',
                'confidence': 0.0,
                'assessment_reasoning': f'Assessment error: {str(e)}',
                'related_notes_count': 0
            }
    
    def _assess_overall_knowledge(self, notes: List[Note]) -> Dict[str, Any]:
        """Assess overall knowledge level."""
        try:
            # Analyze topic diversity
            topic_diversity = self._analyze_topic_diversity(notes)
            
            # Analyze content quality
            content_quality = self._analyze_content_quality(notes)
            
            # Analyze learning progression
            learning_progression = self._analyze_learning_progression(notes)
            
            # Determine overall level
            overall_score = (
                topic_diversity['score'] * 0.3 +
                content_quality['score'] * 0.4 +
                learning_progression['score'] * 0.3
            )
            
            if overall_score >= 0.8:
                level = 'expert'
            elif overall_score >= 0.6:
                level = 'advanced'
            elif overall_score >= 0.4:
                level = 'intermediate'
            else:
                level = 'beginner'
            
            return {
                'knowledge_level': level,
                'confidence': overall_score,
                'assessment_reasoning': f'Overall assessment based on diversity, quality, and progression',
                'topic_diversity': topic_diversity,
                'content_quality': content_quality,
                'learning_progression': learning_progression,
                'total_notes': len(notes)
            }
            
        except Exception as e:
            return {
                'knowledge_level': 'beginner',
                'confidence': 0.0,
                'assessment_reasoning': f'Assessment error: {str(e)}',
                'total_notes': len(notes)
            }
    
    def _analyze_content_depth(self, notes: List[Note], topic: str) -> Dict[str, Any]:
        """Analyze content depth and complexity."""
        try:
            total_content_length = sum(len(note.content) for note in notes)
            avg_content_length = total_content_length / len(notes) if notes else 0
            
            # Analyze summary quality (indicates understanding)
            notes_with_summaries = [note for note in notes if note.summary]
            summary_quality_score = len(notes_with_summaries) / len(notes) if notes else 0
            
            # Analyze tag complexity
            complex_tags = []
            for note in notes:
                if note.tags:
                    for tag in note.tags:
                        if any(keyword in tag.lower() for keyword in ['advanced', 'expert', 'deep', 'complex']):
                            complex_tags.append(tag)
            
            complexity_score = len(complex_tags) / len(notes) if notes else 0
            
            # Determine reasoning
            reasoning_parts = []
            if avg_content_length > 1000:
                reasoning_parts.append('substantial content depth')
            if summary_quality_score > 0.8:
                reasoning_parts.append('high-quality summaries')
            if complexity_score > 0.3:
                reasoning_parts.append('complex topic coverage')
            
            reasoning = ', '.join(reasoning_parts) if reasoning_parts else 'basic topic coverage'
            
            # Calculate confidence
            confidence = min(0.9, (summary_quality_score + complexity_score + (avg_content_length / 2000)) / 3)
            
            return {
                'avg_content_length': avg_content_length,
                'summary_quality_score': summary_quality_score,
                'complexity_score': complexity_score,
                'confidence': confidence,
                'reasoning': reasoning
            }
            
        except Exception as e:
            return {
                'avg_content_length': 0,
                'summary_quality_score': 0,
                'complexity_score': 0,
                'confidence': 0.0,
                'reasoning': f'Analysis error: {str(e)}'
            }
    
    def _analyze_topic_diversity(self, notes: List[Note]) -> Dict[str, Any]:
        """Analyze topic diversity across notes."""
        try:
            all_tags = []
            for note in notes:
                if note.tags:
                    all_tags.extend(note.tags)
            
            unique_topics = len(set(all_tags))
            total_tags = len(all_tags)
            
            diversity_score = unique_topics / max(total_tags, 1)
            
            return {
                'unique_topics': unique_topics,
                'total_tags': total_tags,
                'score': min(1.0, diversity_score * 2)  # Scale to 0-1
            }
            
        except Exception as e:
            return {
                'unique_topics': 0,
                'total_tags': 0,
                'score': 0.0,
                'error': str(e)
            }
    
    def _analyze_content_quality(self, notes: List[Note]) -> Dict[str, Any]:
        """Analyze content quality indicators."""
        try:
            notes_with_summaries = [note for note in notes if note.summary]
            notes_with_tags = [note for note in notes if note.tags]
            
            summary_coverage = len(notes_with_summaries) / len(notes) if notes else 0
            tag_coverage = len(notes_with_tags) / len(notes) if notes else 0
            
            # Analyze summary length (indicator of depth)
            avg_summary_length = 0
            if notes_with_summaries:
                avg_summary_length = sum(len(note.summary) for note in notes_with_summaries) / len(notes_with_summaries)
            
            quality_score = (summary_coverage + tag_coverage + min(avg_summary_length / 200, 1)) / 3
            
            return {
                'summary_coverage': summary_coverage,
                'tag_coverage': tag_coverage,
                'avg_summary_length': avg_summary_length,
                'score': quality_score
            }
            
        except Exception as e:
            return {
                'summary_coverage': 0,
                'tag_coverage': 0,
                'avg_summary_length': 0,
                'score': 0.0,
                'error': str(e)
            }
    
    def _analyze_learning_progression(self, notes: List[Note]) -> Dict[str, Any]:
        """Analyze learning progression over time."""
        try:
            if len(notes) < 2:
                return {'score': 0.5, 'reasoning': 'Insufficient data for progression analysis'}
            
            # Sort notes by creation date
            sorted_notes = sorted(notes, key=lambda x: x.created_at)
            
            # Analyze progression indicators
            early_notes = sorted_notes[:len(sorted_notes)//3]
            late_notes = sorted_notes[-len(sorted_notes)//3:]
            
            early_avg_length = sum(len(note.content) for note in early_notes) / len(early_notes)
            late_avg_length = sum(len(note.content) for note in late_notes) / len(late_notes)
            
            length_progression = (late_avg_length - early_avg_length) / max(early_avg_length, 1)
            
            # Analyze tag complexity progression
            early_tags = []
            late_tags = []
            
            for note in early_notes:
                if note.tags:
                    early_tags.extend(note.tags)
            
            for note in late_notes:
                if note.tags:
                    late_tags.extend(note.tags)
            
            early_unique = len(set(early_tags))
            late_unique = len(set(late_tags))
            
            tag_progression = (late_unique - early_unique) / max(early_unique, 1)
            
            progression_score = (length_progression + tag_progression) / 2
            progression_score = max(0, min(1, progression_score + 0.5))  # Normalize to 0-1
            
            return {
                'score': progression_score,
                'reasoning': f'Content length and topic diversity progression analysis',
                'length_progression': length_progression,
                'tag_progression': tag_progression
            }
            
        except Exception as e:
            return {
                'score': 0.5,
                'reasoning': f'Progression analysis error: {str(e)}'
            }
    
    def _determine_knowledge_level(self, content_analysis: Dict[str, Any]) -> str:
        """Determine knowledge level based on content analysis."""
        try:
            confidence = content_analysis.get('confidence', 0)
            complexity_score = content_analysis.get('complexity_score', 0)
            summary_quality = content_analysis.get('summary_quality_score', 0)
            
            # Weighted score
            weighted_score = (confidence * 0.4 + complexity_score * 0.3 + summary_quality * 0.3)
            
            if weighted_score >= 0.8:
                return 'expert'
            elif weighted_score >= 0.6:
                return 'advanced'
            elif weighted_score >= 0.4:
                return 'intermediate'
            else:
                return 'beginner'
                
        except Exception as e:
            return 'beginner'
    
    def generate_learning_objectives(self, user_id: str, topic: str, 
                                  current_level: str) -> Dict[str, Any]:
        """
        Generate learning objectives based on current knowledge level.
        
        Args:
            user_id: User identifier
            topic: Topic to generate objectives for
            current_level: Current knowledge level
            
        Returns:
            Learning objectives
        """
        try:
            # Define learning objectives by level
            learning_objectives = {
                'beginner': {
                    'python': [
                        'Learn basic Python syntax and data types',
                        'Understand control structures (if/else, loops)',
                        'Practice with functions and modules',
                        'Work with basic data structures (lists, dictionaries)'
                    ],
                    'machine_learning': [
                        'Understand what machine learning is',
                        'Learn about supervised vs unsupervised learning',
                        'Practice with basic algorithms (linear regression)',
                        'Understand data preprocessing basics'
                    ],
                    'web_development': [
                        'Learn HTML fundamentals',
                        'Understand CSS styling basics',
                        'Practice with JavaScript basics',
                        'Build a simple static website'
                    ]
                },
                'intermediate': {
                    'python': [
                        'Master object-oriented programming concepts',
                        'Learn about decorators and generators',
                        'Practice with file I/O and error handling',
                        'Explore popular Python libraries'
                    ],
                    'machine_learning': [
                        'Implement various ML algorithms from scratch',
                        'Learn about feature engineering',
                        'Practice with model evaluation techniques',
                        'Understand cross-validation and hyperparameter tuning'
                    ],
                    'web_development': [
                        'Learn a frontend framework (React/Vue)',
                        'Understand backend development basics',
                        'Practice with databases and APIs',
                        'Learn about version control with Git'
                    ]
                },
                'advanced': {
                    'python': [
                        'Master advanced Python concepts (metaclasses, descriptors)',
                        'Learn about async programming',
                        'Practice with design patterns',
                        'Contribute to open source projects'
                    ],
                    'machine_learning': [
                        'Implement deep learning models',
                        'Learn about advanced architectures (CNNs, RNNs)',
                        'Practice with transfer learning',
                        'Understand model deployment and production'
                    ],
                    'web_development': [
                        'Master full-stack development',
                        'Learn about microservices architecture',
                        'Practice with DevOps and deployment',
                        'Understand performance optimization'
                    ]
                },
                'expert': {
                    'python': [
                        'Contribute to Python core development',
                        'Write advanced libraries and frameworks',
                        'Mentor other developers',
                        'Speak at conferences and write technical articles'
                    ],
                    'machine_learning': [
                        'Research and publish papers',
                        'Develop novel algorithms',
                        'Lead ML teams and projects',
                        'Contribute to open source ML frameworks'
                    ],
                    'web_development': [
                        'Architect large-scale systems',
                        'Lead development teams',
                        'Contribute to web standards',
                        'Mentor and teach others'
                    ]
                }
            }
            
            topic_lower = topic.lower()
            level_lower = current_level.lower()
            
            # Get objectives for the topic and level
            if level_lower in learning_objectives and topic_lower in learning_objectives[level_lower]:
                objectives = learning_objectives[level_lower][topic_lower]
            else:
                # Generate generic objectives
                objectives = [
                    f'Deepen understanding of {topic} concepts',
                    f'Practice advanced {topic} techniques',
                    f'Apply {topic} knowledge to real-world problems',
                    f'Stay updated with latest {topic} developments'
                ]
            
            return {
                'user_id': user_id,
                'topic': topic,
                'current_level': current_level,
                'objectives': objectives,
                'estimated_duration': self._estimate_duration(current_level),
                'difficulty_progression': self._get_difficulty_progression(current_level)
            }
            
        except Exception as e:
            return {
                'error': f'Failed to generate learning objectives: {str(e)}',
                'user_id': user_id,
                'topic': topic,
                'current_level': current_level
            }
    
    def _estimate_duration(self, level: str) -> str:
        """Estimate learning duration based on level."""
        duration_map = {
            'beginner': '2-4 weeks',
            'intermediate': '4-8 weeks',
            'advanced': '8-12 weeks',
            'expert': '12+ weeks'
        }
        return duration_map.get(level.lower(), '4-6 weeks')
    
    def _get_difficulty_progression(self, level: str) -> List[str]:
        """Get difficulty progression for a level."""
        progression_map = {
            'beginner': ['easy', 'easy', 'medium'],
            'intermediate': ['medium', 'medium', 'hard'],
            'advanced': ['hard', 'hard', 'expert'],
            'expert': ['expert', 'expert', 'master']
        }
        return progression_map.get(level.lower(), ['medium', 'hard', 'expert'])
