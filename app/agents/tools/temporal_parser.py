"""
Temporal Parser Tool for Merlin Learning Features.
Parses temporal references in queries and filters content by time.
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from db.models import Note, ConversationHistory
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class TemporalParser:
    """
    Tool for parsing temporal references in queries and filtering content by time.
    """
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Define temporal patterns
        self.temporal_patterns = {
            'today': r'\b(today)\b',
            'yesterday': r'\b(yesterday)\b',
            'this_week': r'\b(this week)\b',
            'last_week': r'\b(last week)\b',
            'this_month': r'\b(this month)\b',
            'last_month': r'\b(last month)\b',
            'this_year': r'\b(this year)\b',
            'last_year': r'\b(last year)\b',
            'recently': r'\b(recently|lately)\b',
            'ago': r'(\d+)\s+(day|week|month|year)s?\s+ago',
            'since': r'since\s+(\w+)',
            'during': r'during\s+(\w+)',
            'in_the_last': r'in\s+the\s+last\s+(\d+)\s+(day|week|month|year)s?',
            'past': r'past\s+(\d+)\s+(day|week|month|year)s?'
        }
    
    def extract_timeframe(self, query: str) -> Dict[str, Any]:
        """
        Extract temporal information from a query.
        
        Args:
            query: Input query string
            
        Returns:
            Dictionary containing temporal information
        """
        try:
            query_lower = query.lower()
            temporal_info = {
                'has_temporal': False,
                'timeframe_type': None,
                'start_date': None,
                'end_date': None,
                'relative_period': None,
                'confidence': 0.0
            }
            
            # Check for exact matches first
            for pattern_name, pattern in self.temporal_patterns.items():
                match = re.search(pattern, query_lower)
                if match:
                    temporal_info['has_temporal'] = True
                    temporal_info['timeframe_type'] = pattern_name
                    temporal_info['confidence'] = 0.9
                    
                    # Parse the specific timeframe
                    if pattern_name == 'today':
                        temporal_info.update(self._parse_today())
                    elif pattern_name == 'yesterday':
                        temporal_info.update(self._parse_yesterday())
                    elif pattern_name == 'this_week':
                        temporal_info.update(self._parse_this_week())
                    elif pattern_name == 'last_week':
                        temporal_info.update(self._parse_last_week())
                    elif pattern_name == 'this_month':
                        temporal_info.update(self._parse_this_month())
                    elif pattern_name == 'last_month':
                        temporal_info.update(self._parse_last_month())
                    elif pattern_name == 'this_year':
                        temporal_info.update(self._parse_this_year())
                    elif pattern_name == 'last_year':
                        temporal_info.update(self._parse_last_year())
                    elif pattern_name == 'recently':
                        temporal_info.update(self._parse_recently())
                    elif pattern_name == 'ago':
                        temporal_info.update(self._parse_ago(match))
                    elif pattern_name == 'in_the_last':
                        temporal_info.update(self._parse_in_the_last(match))
                    elif pattern_name == 'past':
                        temporal_info.update(self._parse_past(match))
                    
                    break
            
            return temporal_info
            
        except Exception as e:
            return {
                'has_temporal': False,
                'error': f'Temporal parsing failed: {str(e)}'
            }
    
    def filter_by_time(self, notes: List[Note], timeframe: Dict[str, Any]) -> List[Note]:
        """
        Filter notes by temporal criteria.
        
        Args:
            notes: List of notes to filter
            timeframe: Temporal filtering criteria
            
        Returns:
            Filtered list of notes
        """
        try:
            if not timeframe.get('has_temporal', False):
                return notes
            
            start_date = timeframe.get('start_date')
            end_date = timeframe.get('end_date')
            
            if not start_date and not end_date:
                return notes
            
            filtered_notes = []
            
            for note in notes:
                note_date = note.created_at
                
                # Apply date filtering
                if start_date and note_date < start_date:
                    continue
                if end_date and note_date > end_date:
                    continue
                
                filtered_notes.append(note)
            
            return filtered_notes
            
        except Exception as e:
            print(f"Error filtering notes by time: {e}")
            return notes
    
    def _parse_today(self) -> Dict[str, Any]:
        """Parse 'today' reference."""
        today = datetime.utcnow().date()
        start_date = datetime.combine(today, datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'relative_period': 'today'
        }
    
    def _parse_yesterday(self) -> Dict[str, Any]:
        """Parse 'yesterday' reference."""
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        start_date = datetime.combine(yesterday, datetime.min.time())
        end_date = datetime.combine(yesterday, datetime.max.time())
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'relative_period': 'yesterday'
        }
    
    def _parse_this_week(self) -> Dict[str, Any]:
        """Parse 'this week' reference."""
        today = datetime.utcnow()
        start_of_week = today - timedelta(days=today.weekday())
        start_date = datetime.combine(start_of_week.date(), datetime.min.time())
        end_date = datetime.utcnow()
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'relative_period': 'this_week'
        }
    
    def _parse_last_week(self) -> Dict[str, Any]:
        """Parse 'last week' reference."""
        today = datetime.utcnow()
        start_of_last_week = today - timedelta(days=today.weekday() + 7)
        end_of_last_week = start_of_last_week + timedelta(days=6)
        
        start_date = datetime.combine(start_of_last_week.date(), datetime.min.time())
        end_date = datetime.combine(end_of_last_week.date(), datetime.max.time())
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'relative_period': 'last_week'
        }
    
    def _parse_this_month(self) -> Dict[str, Any]:
        """Parse 'this month' reference."""
        today = datetime.utcnow()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = today
        
        return {
            'start_date': start_of_month,
            'end_date': end_date,
            'relative_period': 'this_month'
        }
    
    def _parse_last_month(self) -> Dict[str, Any]:
        """Parse 'last month' reference."""
        today = datetime.utcnow()
        first_of_last_month = today.replace(day=1) - relativedelta(months=1)
        last_of_last_month = today.replace(day=1) - timedelta(days=1)
        
        start_date = datetime.combine(first_of_last_month.date(), datetime.min.time())
        end_date = datetime.combine(last_of_last_month.date(), datetime.max.time())
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'relative_period': 'last_month'
        }
    
    def _parse_this_year(self) -> Dict[str, Any]:
        """Parse 'this year' reference."""
        today = datetime.utcnow()
        start_of_year = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = today
        
        return {
            'start_date': start_of_year,
            'end_date': end_date,
            'relative_period': 'this_year'
        }
    
    def _parse_last_year(self) -> Dict[str, Any]:
        """Parse 'last year' reference."""
        today = datetime.utcnow()
        start_of_last_year = today.replace(year=today.year-1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_of_last_year = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        return {
            'start_date': start_of_last_year,
            'end_date': end_of_last_year,
            'relative_period': 'last_year'
        }
    
    def _parse_recently(self) -> Dict[str, Any]:
        """Parse 'recently' reference (last 7 days)."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'relative_period': 'recently'
        }
    
    def _parse_ago(self, match) -> Dict[str, Any]:
        """Parse 'X days/weeks/months/years ago' reference."""
        try:
            amount = int(match.group(1))
            unit = match.group(2)
            
            end_date = datetime.utcnow()
            
            if unit == 'day':
                start_date = end_date - timedelta(days=amount)
            elif unit == 'week':
                start_date = end_date - timedelta(weeks=amount)
            elif unit == 'month':
                start_date = end_date - relativedelta(months=amount)
            elif unit == 'year':
                start_date = end_date - relativedelta(years=amount)
            else:
                start_date = end_date - timedelta(days=amount)
            
            return {
                'start_date': start_date,
                'end_date': end_date,
                'relative_period': f'{amount}_{unit}s_ago'
            }
            
        except Exception as e:
            return {'error': f'Failed to parse ago reference: {str(e)}'}
    
    def _parse_in_the_last(self, match) -> Dict[str, Any]:
        """Parse 'in the last X days/weeks/months/years' reference."""
        try:
            amount = int(match.group(1))
            unit = match.group(2)
            
            end_date = datetime.utcnow()
            
            if unit == 'day':
                start_date = end_date - timedelta(days=amount)
            elif unit == 'week':
                start_date = end_date - timedelta(weeks=amount)
            elif unit == 'month':
                start_date = end_date - relativedelta(months=amount)
            elif unit == 'year':
                start_date = end_date - relativedelta(years=amount)
            else:
                start_date = end_date - timedelta(days=amount)
            
            return {
                'start_date': start_date,
                'end_date': end_date,
                'relative_period': f'last_{amount}_{unit}s'
            }
            
        except Exception as e:
            return {'error': f'Failed to parse in_the_last reference: {str(e)}'}
    
    def _parse_past(self, match) -> Dict[str, Any]:
        """Parse 'past X days/weeks/months/years' reference."""
        try:
            amount = int(match.group(1))
            unit = match.group(2)
            
            end_date = datetime.utcnow()
            
            if unit == 'day':
                start_date = end_date - timedelta(days=amount)
            elif unit == 'week':
                start_date = end_date - timedelta(weeks=amount)
            elif unit == 'month':
                start_date = end_date - relativedelta(months=amount)
            elif unit == 'year':
                start_date = end_date - relativedelta(years=amount)
            else:
                start_date = end_date - timedelta(days=amount)
            
            return {
                'start_date': start_date,
                'end_date': end_date,
                'relative_period': f'past_{amount}_{unit}s'
            }
            
        except Exception as e:
            return {'error': f'Failed to parse past reference: {str(e)}'}
    
    def store_conversation_history(self, user_id: str, session_id: str, 
                                 query: str, response: str, agent_type: str,
                                 context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Store conversation history for temporal context.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            query: User query
            response: Agent response
            agent_type: Type of agent that handled the query
            context: Additional context
            
        Returns:
            Storage result
        """
        try:
            session = self.SessionLocal()
            
            history = ConversationHistory(
                user_id=user_id,
                session_id=session_id,
                query=query,
                response=response,
                context=context or {},
                agent_type=agent_type
            )
            
            session.add(history)
            session.commit()
            
            history_id = history.id
            session.close()
            
            return {
                'success': True,
                'history_id': history_id,
                'message': 'Conversation history stored successfully'
            }
            
        except Exception as e:
            return {'error': f'Failed to store conversation history: {str(e)}'}
    
    def get_conversation_history(self, user_id: str, session_id: str = None, 
                               limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get conversation history for context.
        
        Args:
            user_id: User identifier
            session_id: Optional session identifier
            limit: Maximum number of records to return
            
        Returns:
            List of conversation history records
        """
        try:
            session = self.SessionLocal()
            
            query = session.query(ConversationHistory).filter(
                ConversationHistory.user_id == user_id
            )
            
            if session_id:
                query = query.filter(ConversationHistory.session_id == session_id)
            
            history = query.order_by(ConversationHistory.created_at.desc()).limit(limit).all()
            
            session.close()
            
            return [
                {
                    'id': record.id,
                    'query': record.query,
                    'response': record.response,
                    'context': record.context or {},
                    'agent_type': record.agent_type,
                    'created_at': record.created_at.isoformat()
                }
                for record in history
            ]
            
        except Exception as e:
            return [{'error': f'Failed to get conversation history: {str(e)}'}]
