"""
Git diff analyzer - extracts and analyzes code changes
"""
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from git import Repo, InvalidGitRepositoryError


class DiffAnalyzer:
    """Analyzes git diffs to extract meaningful code changes"""
    
    def __init__(self, repo_path: str = "."):
        try:
            self.repo = Repo(repo_path, search_parent_directories=True)
            self.repo_root = Path(self.repo.working_dir)
        except InvalidGitRepositoryError:
            raise ValueError(f"Not a git repository: {repo_path}")
    
    def get_last_commit_hash(self) -> str:
        """Get the hash of the last commit"""
        return self.repo.head.commit.hexsha[:8]
    
    def get_commit_message(self, commit_ref: str = "HEAD") -> str:
        """Get commit message"""
        commit = self.repo.commit(commit_ref)
        return commit.message.strip()
    
    def get_diff(self, commit_ref: str = "HEAD", parent_ref: Optional[str] = None) -> str:
        """
        Get the diff for a commit
        
        Args:
            commit_ref: The commit to analyze (default: HEAD)
            parent_ref: The parent commit to compare against (default: commit^)
        """
        if parent_ref is None:
            # Compare with parent commit
            parent_ref = f"{commit_ref}^"
        
        try:
            diff = self.repo.git.diff(parent_ref, commit_ref)
            return diff
        except Exception as e:
            # Handle initial commit case
            try:
                diff = self.repo.git.diff("--root", commit_ref)
                return diff
            except Exception:
                raise ValueError(f"Unable to get diff: {e}")
    
    def analyze_diff(self, diff_text: str) -> Dict[str, any]:
        """
        Analyze diff text and extract metadata
        
        Returns:
            Dict with:
            - files_changed: list of files
            - additions: total lines added
            - deletions: total lines deleted
            - file_types: set of file extensions
            - change_summary: brief summary of changes
        """
        lines = diff_text.split('\n')
        
        files_changed = []
        current_file = None
        additions = 0
        deletions = 0
        file_types = set()
        
        for line in lines:
            # Parse file headers
            if line.startswith('diff --git'):
                # Extract filename: diff --git a/path/file.ext b/path/file.ext
                match = re.search(r'b/(.+)$', line)
                if match:
                    current_file = match.group(1)
                    files_changed.append(current_file)
                    
                    # Extract file extension
                    ext = Path(current_file).suffix
                    if ext:
                        file_types.add(ext)
            
            # Count additions/deletions
            elif line.startswith('+') and not line.startswith('+++'):
                additions += 1
            elif line.startswith('-') and not line.startswith('---'):
                deletions += 1
        
        # Determine change type
        change_type = self._determine_change_type(files_changed, additions, deletions)
        
        return {
            'files_changed': files_changed,
            'additions': additions,
            'deletions': deletions,
            'file_types': list(file_types),
            'change_type': change_type,
            'file_count': len(files_changed)
        }
    
    def _determine_change_type(self, files: List[str], additions: int, deletions: int) -> str:
        """Determine the type of change based on files and line changes"""
        if deletions == 0 and additions > 0:
            return "new_feature"
        elif additions > deletions * 2:
            return "feature_addition"
        elif deletions > additions * 2:
            return "code_removal"
        elif abs(additions - deletions) < min(additions, deletions) * 0.3:
            return "refactoring"
        else:
            return "modification"
    
    def get_relevant_diff_context(self, diff_text: str, max_lines: int = 500) -> str:
        """
        Extract the most relevant parts of the diff for LLM analysis
        Removes binary files, truncates very long diffs, focuses on actual code changes
        """
        lines = diff_text.split('\n')
        relevant_lines = []
        in_binary = False
        
        for line in lines:
            # Skip binary file markers
            if 'Binary files' in line:
                in_binary = True
                continue
            
            # Keep file headers and actual code changes
            if (line.startswith('diff --git') or 
                line.startswith('+++') or 
                line.startswith('---') or
                line.startswith('@@') or
                line.startswith('+') or 
                line.startswith('-') or
                (not line.startswith(' ') and len(line) > 0)):
                relevant_lines.append(line)
                in_binary = False
            elif not in_binary and line.startswith(' '):
                # Include some context lines
                relevant_lines.append(line)
        
        # Truncate if too long
        if len(relevant_lines) > max_lines:
            # Keep beginning and end
            half = max_lines // 2
            relevant_lines = (
                relevant_lines[:half] + 
                [f"\n... (truncated {len(relevant_lines) - max_lines} lines) ...\n"] +
                relevant_lines[-half:]
            )
        
        return '\n'.join(relevant_lines)
    
    def is_trivial_change(self, analysis: Dict[str, any]) -> bool:
        """
        Determine if the change is too trivial to generate questions
        (e.g., only comments, whitespace, or very small changes)
        """
        total_changes = analysis['additions'] + analysis['deletions']
        
        # Very small changes
        if total_changes < 5:
            return True
        
        # Only config files or documentation
        trivial_extensions = {'.md', '.txt', '.json', '.yaml', '.yml', '.toml'}
        if all(ext in trivial_extensions for ext in analysis['file_types']):
            return True
        
        return False
