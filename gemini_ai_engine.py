"""
Gemini AI Engine - Optional secondary AI model
Uses Google Gemini API for stock suggestions
"""

import google.generativeai as genai
import json
from typing import List, Dict, Optional


class GeminiAIEngine:
    """
    Optional AI engine using Google Gemini for stock suggestions.
    """
    
    def __init__(self, api_key: str, prompt_config: Dict):
        """
        Initialize Gemini AI engine.
        
        Args:
            api_key: Gemini API key
            prompt_config: Prompt configuration
        """
        self.api_key = api_key
        self.prompt_type = prompt_config.get('type', 'UNKNOWN')
        self.name = prompt_config['name']
        self.system_prompt = prompt_config['system_prompt']
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def suggest_stocks(self, date: str, market_context: str = "", 
                      news_context: str = "") -> List[Dict]:
        """
        Get real AI stock suggestions from Gemini.
        
        Args:
            date: Trading date
            market_context: Market news and context
            news_context: Stock-specific news
        
        Returns:
            List of stock suggestions
        """
        try:
            # Format the prompt with context
            formatted_prompt = self.system_prompt.format(
                date=date,
                market_context=market_context if market_context else "No specific market context available.",
                news_context=news_context if news_context else "No specific news available."
            )
            
            print(f"Calling Gemini AI for {self.name} on {date}...")
            
            # Call Gemini API
            response = self.model.generate_content(formatted_prompt)
            
            # Parse response
            ai_response = response.text
            
            # Extract JSON from response
            suggestions = self._parse_ai_response(ai_response)
            
            # Validate suggestions
            validated = []
            for suggestion in suggestions:
                if self._validate_suggestion(suggestion):
                    validated.append(suggestion)
            
            print(f"✅ Gemini suggested {len(validated)} stocks for {self.name}")
            
            return validated
        
        except Exception as e:
            print(f"Error calling Gemini AI: {str(e)}")
            return []
    
    def _parse_ai_response(self, response_text: str) -> List[Dict]:
        """
        Parse AI response to extract stock suggestions.
        """
        try:
            # Try to find JSON array in the response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                suggestions = json.loads(json_str)
                return suggestions
            
            # If no JSON found, try to parse the entire response
            suggestions = json.loads(response_text)
            return suggestions
        
        except json.JSONDecodeError as e:
            print(f"Failed to parse AI response as JSON: {str(e)}")
            print(f"Response was: {response_text[:200]}...")
            return []
    
    def _validate_suggestion(self, suggestion: Dict) -> bool:
        """
        Validate a stock suggestion.
        """
        required_fields = ['symbol', 'confidence', 'bias', 'reason']
        
        # Check all fields exist
        if not all(field in suggestion for field in required_fields):
            return False
        
        # Validate confidence
        if not (0 <= suggestion['confidence'] <= 100):
            return False
        
        # Validate bias
        if suggestion['bias'] not in ['BULLISH', 'BEARISH']:
            return False
        
        return True
    
    def get_prompt_info(self) -> Dict:
        """
        Get information about this prompt.
        """
        return {
            'type': self.prompt_type,
            'name': self.name,
            'model': 'Google Gemini'
        }
