"""
Robust JSON response parser with multiple fallback strategies
"""
import json
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ResponseParser:
    """Handles parsing of agent responses with fallback strategies"""
    
    @staticmethod
    def parse_agent_response(raw_response: str, agent_id: str) -> Dict[str, Any]:
        """
        Parse agent response with multiple fallback strategies
        Returns validated response matching response_format.json schema
        """
        # Strategy 1: Try direct JSON parsing
        try:
            parsed = json.loads(raw_response.strip())
            if ResponseParser._validate_response_format(parsed):
                logger.debug(f"Direct JSON parsing successful for {agent_id}")
                return ResponseParser._ensure_required_fields(parsed, agent_id)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract JSON from mixed content
        try:
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                if ResponseParser._validate_response_format(parsed):
                    logger.debug(f"JSON extraction successful for {agent_id}")
                    return ResponseParser._ensure_required_fields(parsed, agent_id)
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Strategy 3: Extract JSON from code blocks
        try:
            code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
            code_match = re.search(code_block_pattern, raw_response, re.DOTALL)
            if code_match:
                parsed = json.loads(code_match.group(1))
                if ResponseParser._validate_response_format(parsed):
                    logger.debug(f"Code block extraction successful for {agent_id}")
                    return ResponseParser._ensure_required_fields(parsed, agent_id)
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Strategy 4: Parse structured text
        try:
            structured = ResponseParser._parse_structured_text(raw_response)
            if structured:
                logger.debug(f"Structured text parsing successful for {agent_id}")
                return ResponseParser._ensure_required_fields(structured, agent_id)
        except Exception:
            pass
        
        # Strategy 5: Create fallback response from free text
        logger.warning(f"All parsing strategies failed for {agent_id}, creating fallback response")
        return ResponseParser._create_fallback_response(raw_response, agent_id)
    
    @staticmethod
    def _validate_response_format(response: Dict[str, Any]) -> bool:
        """Validate response against schema requirements"""
        required_fields = ["agent_id", "main_response", "confidence_level"]
        
        # Check required fields exist
        for field in required_fields:
            if field not in response:
                return False
        
        # Validate confidence level range
        confidence = response.get("confidence_level")
        if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
            return False
        
        # Validate array fields
        for field in ["key_insights", "questions_for_others"]:
            if field in response and not isinstance(response[field], list):
                return False
        
        return True
    
    @staticmethod
    def _ensure_required_fields(response: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Ensure all required fields are present and valid"""
        # Ensure agent_id matches
        response["agent_id"] = agent_id
        
        # Ensure required fields exist
        if "main_response" not in response:
            response["main_response"] = "Response could not be parsed properly"
        
        if "confidence_level" not in response:
            response["confidence_level"] = 0.5
        
        # Validate and fix confidence level
        try:
            confidence = float(response["confidence_level"])
            response["confidence_level"] = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            response["confidence_level"] = 0.5
        
        # Ensure optional fields are lists
        for field in ["key_insights", "questions_for_others"]:
            if field not in response:
                response[field] = []
            elif not isinstance(response[field], list):
                response[field] = []
        
        # Apply validation limits
        response["key_insights"] = response["key_insights"][:5]  # max 5 insights
        response["questions_for_others"] = response["questions_for_others"][:3]  # max 3 questions
        
        # Truncate main response if too long
        if len(response["main_response"]) > 1000:
            response["main_response"] = response["main_response"][:997] + "..."
        
        # Ensure optional string fields exist
        if "next_action" not in response:
            response["next_action"] = "Continue collaboration"
        if "reasoning" not in response:
            response["reasoning"] = "Analysis completed"
        
        return response
    
    @staticmethod
    def _parse_structured_text(text: str) -> Optional[Dict[str, Any]]:
        """Parse structured text that might not be JSON"""
        response = {}
        
        # Try to extract main response
        main_match = re.search(r'(?:main_response|analysis|response):\s*(.+?)(?:\n|$)', text, re.IGNORECASE | re.DOTALL)
        if main_match:
            response["main_response"] = main_match.group(1).strip()
        
        # Try to extract confidence level
        conf_match = re.search(r'(?:confidence|confidence_level):\s*([0-9.]+)', text, re.IGNORECASE)
        if conf_match:
            try:
                response["confidence_level"] = float(conf_match.group(1))
            except ValueError:
                pass
        
        # Try to extract insights
        insights_match = re.search(r'(?:insights|key_insights):\s*\[(.*?)\]', text, re.IGNORECASE | re.DOTALL)
        if insights_match:
            insights_text = insights_match.group(1)
            insights = [insight.strip(' "\',') for insight in insights_text.split(',')]
            response["key_insights"] = [insight for insight in insights if insight]
        
        # Try to extract questions
        questions_match = re.search(r'(?:questions|questions_for_others):\s*\[(.*?)\]', text, re.IGNORECASE | re.DOTALL)
        if questions_match:
            questions_text = questions_match.group(1)
            questions = [q.strip(' "\',') for q in questions_text.split(',')]
            response["questions_for_others"] = [q for q in questions if q]
        
        # Only return if we found at least main_response
        if "main_response" in response:
            return response
        
        return None
    
    @staticmethod
    def _create_fallback_response(raw_text: str, agent_id: str) -> Dict[str, Any]:
        """Create a valid response structure from free text"""
        # Clean up the text
        main_response = raw_text.strip()
        if len(main_response) > 1000:
            main_response = main_response[:997] + "..."
        
        # Extract potential insights (sentences that seem insightful)
        sentences = [s.strip() for s in main_response.split('.') if s.strip()]
        potential_insights = [s for s in sentences if len(s) > 20 and len(s) < 200][:5]
        
        # Create basic response structure
        return {
            "agent_id": agent_id,
            "main_response": main_response or "Unable to generate proper response",
            "confidence_level": 0.3,  # Low confidence for fallback
            "key_insights": potential_insights,
            "questions_for_others": [],
            "next_action": "Review and clarify response",
            "reasoning": "Response created from fallback parsing"
        }
    
    @staticmethod
    def validate_and_log_response(response: Dict[str, Any], agent_id: str) -> bool:
        """Validate response and log any issues"""
        issues = []
        
        # Check required fields
        required_fields = ["agent_id", "main_response", "confidence_level"]
        for field in required_fields:
            if field not in response:
                issues.append(f"Missing required field: {field}")
        
        # Validate types and constraints
        if "confidence_level" in response:
            conf = response["confidence_level"]
            if not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
                issues.append(f"Invalid confidence_level: {conf}")
        
        if "main_response" in response and len(response["main_response"]) > 1000:
            issues.append("main_response exceeds 1000 characters")
        
        if "key_insights" in response and len(response["key_insights"]) > 5:
            issues.append("Too many key_insights (max 5)")
        
        if "questions_for_others" in response and len(response["questions_for_others"]) > 3:
            issues.append("Too many questions_for_others (max 3)")
        
        if issues:
            logger.warning(f"Response validation issues for {agent_id}: {issues}")
            return False
        
        logger.debug(f"Response validation successful for {agent_id}")
        return True
