"""
OpenCode client - interfaces with OpenCode CLI for LLM capabilities
"""
import subprocess
import json
from typing import Optional, Dict, Any


class OpenCodeClient:
    """Client for interacting with OpenCode CLI"""
    
    def __init__(self, model: str = "auto"):
        """
        Initialize OpenCode client
        
        Args:
            model: Model to use (default: "auto" lets OpenCode choose)
                   Can be specific like "gpt-4o-mini", "claude-sonnet", etc.
        """
        self.model = model
        self._check_opencode_available()
    
    def _check_opencode_available(self) -> bool:
        """Check if OpenCode CLI is available"""
        try:
            result = subprocess.run(
                ["opencode", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            raise RuntimeError(
                "OpenCode CLI not found. Please ensure OpenCode is installed and in your PATH."
            )
    
    def ask(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7) -> str:
        """
        Send a prompt to OpenCode and get response
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0.0 to 1.0)
        
        Returns:
            The model's response text
        """
        try:
            # Build the command
            cmd = ["opencode", "ask"]
            
            # Add model if specified and not auto
            if self.model and self.model != "auto":
                cmd.extend(["--model", self.model])
            
            # Add temperature
            cmd.extend(["--temperature", str(temperature)])
            
            # Add system prompt if provided
            if system_prompt:
                cmd.extend(["--system", system_prompt])
            
            # Add the prompt
            cmd.append(prompt)
            
            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout for LLM response
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"OpenCode error: {result.stderr}")
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("OpenCode request timed out")
        except Exception as e:
            raise RuntimeError(f"Failed to call OpenCode: {e}")
    
    def ask_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Ask OpenCode and expect a JSON response
        
        Args:
            prompt: The prompt requesting JSON output
            system_prompt: Optional system prompt
        
        Returns:
            Parsed JSON response as dict
        """
        response = self.ask(prompt, system_prompt, temperature=0.3)
        
        # Try to extract JSON from the response
        # Sometimes models wrap JSON in markdown code blocks
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract from markdown code block
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_text = response[json_start:json_end].strip()
                return json.loads(json_text)
            elif "```" in response:
                # Generic code block
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_text = response[json_start:json_end].strip()
                return json.loads(json_text)
            else:
                raise ValueError(f"Could not parse JSON from response: {response[:200]}...")
