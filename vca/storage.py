"""
Storage layer for vca - handles config and session persistence
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class VCAStorage:
    """Manages storage of configuration and learning sessions"""
    
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.vca_dir = self.repo_root / ".vca"
        self.sessions_dir = self.vca_dir / "sessions"
        self.config_file = self.vca_dir / "config.json"
        
    def initialize(self) -> bool:
        """Initialize vca storage structure"""
        try:
            self.vca_dir.mkdir(exist_ok=True)
            self.sessions_dir.mkdir(exist_ok=True)
            
            # Create default config if it doesn't exist
            if not self.config_file.exists():
                default_config = {
                    "model": "github-copilot/gpt-4.1",  # Let OpenCode choose the best free model
                    "question_count": 6,
                    "difficulty": "adaptive",
                    "categories": [
                        "architecture",
                        "syntax",
                        "design_patterns",
                        "alternatives",
                        "scalability",
                        "best_practices"
                    ],
                    "initialized_at": datetime.now().isoformat()
                }
                self.save_config(default_config)
            
            return True
        except Exception as e:
            print(f"Error initializing storage: {e}")
            return False
    
    def is_initialized(self) -> bool:
        """Check if vca is initialized in this repo"""
        return self.vca_dir.exists() and self.config_file.exists()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration"""
        if not self.config_file.exists():
            return {}
        
        with open(self.config_file, 'r') as f:
            return json.load(f)
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def save_session(self, commit_hash: str, session_data: Dict[str, Any]) -> None:
        """Save a learning session"""
        session_file = self.sessions_dir / f"{commit_hash}.json"
        
        session_data["saved_at"] = datetime.now().isoformat()
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
    
    def load_session(self, commit_hash: str) -> Optional[Dict[str, Any]]:
        """Load a specific session"""
        session_file = self.sessions_dir / f"{commit_hash}.json"
        
        if not session_file.exists():
            return None
        
        with open(session_file, 'r') as f:
            return json.load(f)
    
    def list_sessions(self) -> List[str]:
        """List all session commit hashes"""
        if not self.sessions_dir.exists():
            return []
        
        sessions = []
        for file in self.sessions_dir.glob("*.json"):
            sessions.append(file.stem)
        
        return sorted(sessions, reverse=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get learning statistics across all sessions"""
        sessions = self.list_sessions()
        
        total_questions = 0
        total_answered = 0
        category_stats = {}
        
        for session_hash in sessions:
            session = self.load_session(session_hash)
            if not session or 'questions' not in session:
                continue
            
            for q in session['questions']:
                total_questions += 1
                if q.get('answered'):
                    total_answered += 1
                
                category = q.get('category', 'unknown')
                if category not in category_stats:
                    category_stats[category] = {'total': 0, 'answered': 0}
                
                category_stats[category]['total'] += 1
                if q.get('answered'):
                    category_stats[category]['answered'] += 1
        
        return {
            'total_sessions': len(sessions),
            'total_questions': total_questions,
            'total_answered': total_answered,
            'answer_rate': total_answered / total_questions if total_questions > 0 else 0,
            'category_stats': category_stats
        }
