"""
OpenCode client - interfaces with OpenCode CLI for LLM capabilities
"""
import subprocess
import json
import re
from typing import Optional, Dict, Any
from .logger import get_logger

logger = get_logger()


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape codes from text"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


class OpenCodeClient:
    """Client for interacting with OpenCode CLI"""
    
    def __init__(self, model: str = "github-copilot/claude-sonnet-4.5"):
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
            logger.debug("Checking if OpenCode CLI is available...")
            result = subprocess.run(
                ["opencode", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            logger.debug(f"OpenCode version check: returncode={result.returncode}, stdout={result.stdout.strip()}")
            if result.returncode != 0:
                logger.error(f"OpenCode --version failed with returncode {result.returncode}")
                return False
            return True
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.error(f"OpenCode CLI not found: {e}")
            raise RuntimeError(
                "OpenCode CLI not found. Please ensure OpenCode is installed and in your PATH."
            )
    
    def test_connection(self) -> bool:
        """Test if OpenCode can actually respond to a simple query"""
        try:
            logger.info("Testing OpenCode connection with simple query...")
            response = self.ask("Say 'OK' if you can hear me.", temperature=0.0)
            logger.info(f"OpenCode test response: {response[:100]}")
            return len(response) > 0
        except Exception as e:
            logger.error(f"OpenCode test failed: {e}")
            return False
    
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
            # Combine system prompt with user prompt if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
                logger.debug(f"Combined system prompt with user prompt")
            
            # Build the command: opencode -m "model" run "prompt"
            cmd = ["opencode", "-m", self.model, "run", full_prompt]
            
            logger.debug(f"Executing OpenCode command: {' '.join(cmd[:4])}... (prompt length: {len(full_prompt)} chars)")
            if system_prompt:
                logger.debug(f"System prompt: {system_prompt[:100]}...")
            
            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # Increased to 120 second timeout for LLM response
            )
            
            logger.debug(f"OpenCode response: returncode={result.returncode}, stdout length={len(result.stdout)}, stderr length={len(result.stderr)}")
            
            if result.returncode != 0:
                logger.error(f"OpenCode error: returncode={result.returncode}, stderr={result.stderr}")
                raise RuntimeError(f"OpenCode error: {result.stderr}")
            
            # Check if we got any output
            if not result.stdout or result.stdout.strip() == "":
                logger.error("OpenCode returned empty response")
                logger.error(f"stderr: {result.stderr}")
                raise RuntimeError("OpenCode returned empty response. Check that OpenCode is working correctly.")
            
            # Strip ANSI escape codes from the response
            response = strip_ansi_codes(result.stdout).strip()
            
            # Remove any "> build" or similar prompt lines that OpenCode adds
            lines = response.split('\n')
            cleaned_lines = [line for line in lines if not line.startswith('> ')]
            response = '\n'.join(cleaned_lines).strip()
            
            logger.debug(f"OpenCode response preview: {response[:200]}...")
            logger.debug(f"Full response length: {len(response)} characters")
            
            return response
            
        except subprocess.TimeoutExpired:
            logger.error("OpenCode request timed out after 120 seconds")
            raise RuntimeError("OpenCode request timed out")
        except Exception as e:
            logger.error(f"Failed to call OpenCode: {e}", exc_info=True)
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
        logger.debug("Requesting JSON response from OpenCode...")
        response = self.ask(prompt, system_prompt, temperature=0.3)
        
        # Check if response is empty
        if not response or response.strip() == "":
            logger.error("Received empty response from OpenCode")
            raise ValueError("OpenCode returned empty response")
        
        logger.debug(f"Attempting to parse JSON from response (length: {len(response)})")
        logger.debug(f"Response starts with: {response[:100]}")
        
        # Try to extract JSON from the response
        # Sometimes models wrap JSON in markdown code blocks
        try:
            parsed = json.loads(response)
            logger.debug(f"Successfully parsed JSON directly: {list(parsed.keys())}")
            return parsed
        except json.JSONDecodeError as e:
            logger.debug(f"Direct JSON parsing failed: {e}. Trying to extract from markdown...")
            
            # Try to extract from markdown code block
            if "```json" in response:
                logger.debug("Found ```json markdown block")
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                if json_end == -1:
                    logger.error("Found ```json but no closing ```")
                    json_text = response[json_start:].strip()
                else:
                    json_text = response[json_start:json_end].strip()
                logger.debug(f"Extracted JSON text length: {len(json_text)}")
                logger.debug(f"Extracted JSON preview: {json_text[:200]}")
                try:
                    parsed = json.loads(json_text)
                    logger.debug(f"Successfully parsed JSON from ```json block: {list(parsed.keys())}")
                    return parsed
                except json.JSONDecodeError as e2:
                    logger.error(f"Failed to parse JSON from ```json block: {e2}")
                    logger.error(f"Extracted text: {json_text[:500]}")
                    raise ValueError(f"Could not parse JSON from ```json block: {e2}\nExtracted: {json_text[:200]}")
            elif "```" in response:
                logger.debug("Found generic ``` code block")
                # Generic code block
                json_start = response.find("```") + 3
                # Skip potential language identifier
                newline_pos = response.find("\n", json_start)
                if newline_pos != -1 and newline_pos - json_start < 20:
                    json_start = newline_pos + 1
                json_end = response.find("```", json_start)
                if json_end == -1:
                    logger.error("Found ``` but no closing ```")
                    json_text = response[json_start:].strip()
                else:
                    json_text = response[json_start:json_end].strip()
                logger.debug(f"Extracted JSON text length: {len(json_text)}")
                logger.debug(f"Extracted JSON preview: {json_text[:200]}")
                try:
                    parsed = json.loads(json_text)
                    logger.debug(f"Successfully parsed JSON from ``` block: {list(parsed.keys())}")
                    return parsed
                except json.JSONDecodeError as e2:
                    logger.error(f"Failed to parse JSON from ``` block: {e2}")
                    logger.error(f"Extracted text: {json_text[:500]}")
                    raise ValueError(f"Could not parse JSON from ``` block: {e2}\nExtracted: {json_text[:200]}")
            else:
                logger.error(f"No JSON or markdown blocks found in response")
                logger.error(f"Response preview: {response[:500]}")
                logger.error(f"Response ends with: {response[-100:]}")
                raise ValueError(f"Could not parse JSON from response: {response[:200]}...")
