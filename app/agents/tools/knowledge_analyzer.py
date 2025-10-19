"""
Knowledge Analyzer Tool for Merlin Learning Features.
Analyzes user knowledge patterns and identifies gaps.
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from db.models import Note, KnowledgeGap, UserKnowledgeProfile
from app.agents.tools.embedding import generate_embedding, compute_similarity
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

class KnowledgeAnalyzer:
    """
    Tool for analyzing user knowledge patterns and identifying gaps.
    """
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def analyze_knowledge_patterns(self, user_id: str, timeframe_days: int = 30) -> Dict[str, Any]:
        """
        Analyze user's knowledge patterns over a specified timeframe.
        
        Args:
            user_id: User identifier
            timeframe_days: Number of days to analyze (default: 30)
            
        Returns:
            Dict containing knowledge analysis results
        """
        try:
            session = self.SessionLocal()
            
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=timeframe_days)
            
            # Get notes from the timeframe
            notes = session.query(Note).filter(
                Note.created_at >= start_date,
                Note.created_at <= end_date
            ).all()
            
            # Analyze topics from tags
            topic_frequency = {}
            total_notes = len(notes)
            
            for note in notes:
                if note.tags:
                    for tag in note.tags:
                        topic_frequency[tag] = topic_frequency.get(tag, 0) + 1
            
            # Calculate topic distribution
            topic_distribution = {
                topic: count / total_notes if total_notes > 0 else 0
                for topic, count in topic_frequency.items()
            }
            
            # Identify top topics
            top_topics = sorted(topic_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Calculate knowledge diversity (number of unique topics)
            knowledge_diversity = len(topic_frequency)
            
            # Analyze content patterns
            content_analysis = self._analyze_content_patterns(notes)
            
            session.close()
            
            return {
                'user_id': user_id,
                'timeframe_days': timeframe_days,
                'total_notes': total_notes,
                'knowledge_diversity': knowledge_diversity,
                'topic_frequency': topic_frequency,
                'topic_distribution': topic_distribution,
                'top_topics': top_topics,
                'content_analysis': content_analysis,
                'analysis_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'error': f'Knowledge analysis failed: {str(e)}',
                'user_id': user_id,
                'timeframe_days': timeframe_days
            }
    
    def identify_topic_gaps(self, user_id: str, existing_topics: List[str]) -> List[Dict[str, Any]]:
        """
        Identify potential knowledge gaps based on existing topics.
        
        Args:
            user_id: User identifier
            existing_topics: List of topics the user has covered
            
        Returns:
            List of identified knowledge gaps
        """
        try:
            # Define common topic relationships and gaps
            topic_relationships = {
                'python': ['data_science', 'machine_learning', 'web_development', 'automation'],
                'machine_learning': ['deep_learning', 'neural_networks', 'nlp', 'computer_vision'],
                'data_science': ['statistics', 'data_visualization', 'sql', 'pandas'],
                'web_development': ['javascript', 'react', 'nodejs', 'css', 'html'],
                'javascript': ['typescript', 'react', 'vue', 'angular', 'nodejs'],
                'react': ['redux', 'hooks', 'context', 'testing'],
                'sql': ['database_design', 'query_optimization', 'nosql', 'postgresql'],
                'statistics': ['probability', 'hypothesis_testing', 'regression', 'bayesian'],
                'design': ['user_research', 'ux_design', 'ui_design', 'prototyping'],
                'business': ['strategy', 'marketing', 'finance', 'operations']
            }
            
            identified_gaps = []
            
            for topic in existing_topics:
                topic_lower = topic.lower()
                
                # Find related topics that might be gaps
                if topic_lower in topic_relationships:
                    related_topics = topic_relationships[topic_lower]
                    
                    for related_topic in related_topics:
                        # Check if this related topic is not in existing topics
                        if related_topic not in [t.lower() for t in existing_topics]:
                            gap = {
                                'gap_type': 'topic_gap',
                                'topic': related_topic,
                                'confidence_score': 0.7,  # Base confidence
                                'gap_description': f'You have knowledge in {topic} but may be missing related knowledge in {related_topic}',
                                'suggested_content': [
                                    f'Introduction to {related_topic}',
                                    f'{topic} and {related_topic} integration',
                                    f'Advanced {related_topic} concepts'
                                ]
                            }
                            identified_gaps.append(gap)
            
            return identified_gaps
            
        except Exception as e:
            return [{'error': f'Gap identification failed: {str(e)}'}]
    
    def _analyze_content_patterns(self, notes: List[Note]) -> Dict[str, Any]:
        """Analyze content patterns from notes."""
        try:
            total_content_length = sum(len(note.content) for note in notes)
            avg_content_length = total_content_length / len(notes) if notes else 0
            
            # Analyze summary quality
            notes_with_summaries = [note for note in notes if note.summary]
            summary_coverage = len(notes_with_summaries) / len(notes) if notes else 0
            
            # Analyze tag usage
            notes_with_tags = [note for note in notes if note.tags]
            tag_coverage = len(notes_with_tags) / len(notes) if notes else 0
            
            return {
                'total_content_length': total_content_length,
                'avg_content_length': avg_content_length,
                'summary_coverage': summary_coverage,
                'tag_coverage': tag_coverage,
                'notes_with_summaries': len(notes_with_summaries),
                'notes_with_tags': len(notes_with_tags)
            }
            
        except Exception as e:
            return {'error': f'Content pattern analysis failed: {str(e)}'}
    
    def get_user_knowledge_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Get or create user knowledge profile.
        
        Args:
            user_id: User identifier
            
        Returns:
            User knowledge profile
        """
        try:
            session = self.SessionLocal()
            
            # Try to get existing profile
            profile = session.query(UserKnowledgeProfile).filter(
                UserKnowledgeProfile.user_id == user_id
            ).first()
            
            if not profile:
                # Create new profile
                profile = UserKnowledgeProfile(
                    user_id=user_id,
                    knowledge_topics={},
                    learning_preferences={},
                    knowledge_strengths=[],
                    knowledge_weaknesses=[]
                )
                session.add(profile)
                session.commit()
            
            session.close()
            
            return {
                'user_id': profile.user_id,
                'knowledge_topics': profile.knowledge_topics or {},
                'learning_preferences': profile.learning_preferences or {},
                'knowledge_strengths': profile.knowledge_strengths or [],
                'knowledge_weaknesses': profile.knowledge_weaknesses or [],
                'created_at': profile.created_at.isoformat(),
                'updated_at': profile.updated_at.isoformat()
            }
            
        except Exception as e:
            return {'error': f'Failed to get user knowledge profile: {str(e)}'}
    
    def update_user_knowledge_profile(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user knowledge profile.
        
        Args:
            user_id: User identifier
            updates: Dictionary of updates to apply
            
        Returns:
            Updated profile
        """
        try:
            session = self.SessionLocal()
            
            profile = session.query(UserKnowledgeProfile).filter(
                UserKnowledgeProfile.user_id == user_id
            ).first()
            
            if profile:
                # Update fields
                for key, value in updates.items():
                    if hasattr(profile, key):
                        setattr(profile, key, value)
                
                profile.updated_at = datetime.utcnow()
                session.commit()
                
                session.close()
                return {'success': True, 'message': 'Profile updated successfully'}
            else:
                session.close()
                return {'error': 'Profile not found'}
                
        except Exception as e:
            return {'error': f'Failed to update user knowledge profile: {str(e)}'}
    
    def store_knowledge_gap(self, user_id: str, gap_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store identified knowledge gap in database.
        
        Args:
            user_id: User identifier
            gap_data: Knowledge gap data
            
        Returns:
            Storage result
        """
        try:
            session = self.SessionLocal()
            
            gap = KnowledgeGap(
                user_id=user_id,
                gap_type=gap_data.get('gap_type', 'topic_gap'),
                topic=gap_data.get('topic', ''),
                confidence_score=gap_data.get('confidence_score', 0.0),
                suggested_content=gap_data.get('suggested_content', []),
                gap_description=gap_data.get('gap_description', ''),
                resolved='false'
            )
            
            session.add(gap)
            session.commit()
            
            gap_id = gap.id
            session.close()
            
            return {
                'success': True,
                'gap_id': gap_id,
                'message': 'Knowledge gap stored successfully'
            }
            
        except Exception as e:
            return {'error': f'Failed to store knowledge gap: {str(e)}'}
    
    def get_user_knowledge_gaps(self, user_id: str, resolved: bool = False) -> List[Dict[str, Any]]:
        """
        Get user's knowledge gaps.
        
        Args:
            user_id: User identifier
            resolved: Whether to include resolved gaps
            
        Returns:
            List of knowledge gaps
        """
        try:
            session = self.SessionLocal()
            
            query = session.query(KnowledgeGap).filter(
                KnowledgeGap.user_id == user_id
            )
            
            if not resolved:
                query = query.filter(KnowledgeGap.resolved == 'false')
            
            gaps = query.order_by(KnowledgeGap.created_at.desc()).all()
            
            session.close()
            
            return [
                {
                    'id': gap.id,
                    'gap_type': gap.gap_type,
                    'topic': gap.topic,
                    'confidence_score': gap.confidence_score,
                    'suggested_content': gap.suggested_content or [],
                    'gap_description': gap.gap_description,
                    'resolved': gap.resolved,
                    'created_at': gap.created_at.isoformat()
                }
                for gap in gaps
            ]
            
        except Exception as e:
            return [{'error': f'Failed to get knowledge gaps: {str(e)}'}]
