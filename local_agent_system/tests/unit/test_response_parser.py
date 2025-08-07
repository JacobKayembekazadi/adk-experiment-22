"""
Unit tests for response parser
"""
import pytest
import json
from unittest.mock import patch
from utils.response_parser import ResponseParser


class TestResponseParser:
    """Test cases for the ResponseParser class"""
    
    def test_parse_valid_json_response(self, sample_valid_json_response):
        """Test parsing of valid JSON response"""
        json_str = json.dumps(sample_valid_json_response)
        result = ResponseParser.parse_agent_response(json_str, "TestAgent_Alpha")
        
        assert result["agent_id"] == "TestAgent_Alpha"
        assert result["main_response"] == sample_valid_json_response["main_response"]
        assert result["confidence_level"] == 0.85
        assert len(result["key_insights"]) == 3
        assert len(result["questions_for_others"]) == 2
        assert "next_action" in result
        assert "reasoning" in result
    
    def test_parse_json_with_extra_whitespace(self, sample_valid_json_response):
        """Test parsing JSON with extra whitespace"""
        json_str = "\n\n  " + json.dumps(sample_valid_json_response) + "  \n\n"
        result = ResponseParser.parse_agent_response(json_str, "TestAgent_Alpha")
        
        assert result["agent_id"] == "TestAgent_Alpha"
        assert result["confidence_level"] == 0.85
    
    def test_parse_json_from_mixed_content(self, sample_valid_json_response):
        """Test extracting JSON from mixed content"""
        mixed_content = f"""
        Here is some text before the JSON.
        
        {json.dumps(sample_valid_json_response)}
        
        And some text after the JSON.
        """
        result = ResponseParser.parse_agent_response(mixed_content, "TestAgent_Alpha")
        
        assert result["agent_id"] == "TestAgent_Alpha"
        assert result["main_response"] == sample_valid_json_response["main_response"]
    
    def test_parse_json_from_code_block(self, sample_valid_json_response):
        """Test extracting JSON from markdown code blocks"""
        code_block_content = f"""
        Here's my response:
        
        ```json
        {json.dumps(sample_valid_json_response)}
        ```
        
        That's my analysis.
        """
        result = ResponseParser.parse_agent_response(code_block_content, "TestAgent_Alpha")
        
        assert result["agent_id"] == "TestAgent_Alpha"
        assert result["confidence_level"] == 0.85
    
    def test_parse_code_block_without_language(self, sample_valid_json_response):
        """Test extracting JSON from code blocks without language specification"""
        code_block_content = f"""
        ```
        {json.dumps(sample_valid_json_response)}
        ```
        """
        result = ResponseParser.parse_agent_response(code_block_content, "TestAgent_Alpha")
        
        assert result["agent_id"] == "TestAgent_Alpha"
    
    @pytest.mark.parametrize("malformed_response", [
        '{"agent_id": "TestAgent", "main_response": "incomplete',
        '{"agent_id": "TestAgent", "main_response": "test",}',
        '',
        'Just plain text without JSON',
    ])
    def test_parse_malformed_responses(self, malformed_response):
        """Test handling of various malformed responses"""
        result = ResponseParser.parse_agent_response(malformed_response, "TestAgent_Alpha")
        
        # Should return valid response structure
        assert result["agent_id"] == "TestAgent_Alpha"
        assert "main_response" in result
        assert isinstance(result["confidence_level"], (int, float))
        assert 0.0 <= result["confidence_level"] <= 1.0
        assert isinstance(result["key_insights"], list)
        assert isinstance(result["questions_for_others"], list)
    
    def test_parse_structured_text_response(self):
        """Test parsing structured text that's not JSON"""
        structured_text = """
        main_response: This is a structured response about the problem
        confidence: 0.7
        insights: [First insight, Second insight, Third insight]
        questions_for_others: [What about scalability?, How does this affect users?]
        next_action: Implement the proposed solution
        reasoning: Based on analysis of requirements
        """
        
        result = ResponseParser.parse_agent_response(structured_text, "TestAgent_Alpha")
        
        assert result["agent_id"] == "TestAgent_Alpha" 
        assert "structured response" in result["main_response"]
        assert result["confidence_level"] == 0.7
        assert len(result["key_insights"]) == 3
        assert len(result["questions_for_others"]) == 2
    
    def test_fallback_response_creation(self):
        """Test fallback response creation from free text"""
        free_text = """
        This is a completely unstructured response. It contains multiple sentences
        that could be considered insights. The analysis shows that we need to
        consider several factors including performance, scalability, and user experience.
        The system should handle edge cases gracefully. Future improvements could
        include better error handling and more comprehensive testing coverage.
        """
        
        result = ResponseParser.parse_agent_response(free_text, "TestAgent_Alpha")
        
        assert result["agent_id"] == "TestAgent_Alpha"
        assert result["main_response"] == free_text.strip()
        assert result["confidence_level"] == 0.3  # Low confidence for fallback
        assert isinstance(result["key_insights"], list)
        assert len(result["key_insights"]) <= 5
        assert result["reasoning"] == "Response created from fallback parsing"
    
    def test_confidence_level_validation_and_clamping(self):
        """Test confidence level validation and clamping"""
        test_cases = [
            ('{"agent_id": "test", "main_response": "test", "confidence_level": 1.5}', 1.0),
            ('{"agent_id": "test", "main_response": "test", "confidence_level": -0.5}', 0.0),
            ('{"agent_id": "test", "main_response": "test", "confidence_level": "invalid"}', 0.5),
            ('{"agent_id": "test", "main_response": "test"}', 0.5),  # Missing confidence
        ]
        
        for json_str, expected_confidence in test_cases:
            result = ResponseParser.parse_agent_response(json_str, "TestAgent")
            assert result["confidence_level"] == expected_confidence
    
    def test_array_field_validation(self):
        """Test validation of array fields (insights, questions)"""
        # Test with non-array values
        json_str = '{"agent_id": "test", "main_response": "test", "confidence_level": 0.8, "key_insights": "not an array", "questions_for_others": "also not an array"}'
        result = ResponseParser.parse_agent_response(json_str, "TestAgent")
        
        assert isinstance(result["key_insights"], list)
        assert isinstance(result["questions_for_others"], list)
        assert result["key_insights"] == []  # Should be empty due to invalid format
        assert result["questions_for_others"] == []
    
    def test_field_length_limits(self):
        """Test enforcement of field length limits"""
        # Test main_response truncation
        long_response = "a" * 1500
        json_str = f'{{"agent_id": "test", "main_response": "{long_response}", "confidence_level": 0.8}}'
        result = ResponseParser.parse_agent_response(json_str, "TestAgent")
        
        assert len(result["main_response"]) == 1000
        assert result["main_response"].endswith("...")
        
        # Test insights limit (max 5)
        many_insights = ["insight"] * 10
        json_str = json.dumps({
            "agent_id": "test",
            "main_response": "test",
            "confidence_level": 0.8,
            "key_insights": many_insights
        })
        result = ResponseParser.parse_agent_response(json_str, "TestAgent")
        
        assert len(result["key_insights"]) == 5
        
        # Test questions limit (max 3)
        many_questions = ["question?"] * 8
        json_str = json.dumps({
            "agent_id": "test",
            "main_response": "test", 
            "confidence_level": 0.8,
            "questions_for_others": many_questions
        })
        result = ResponseParser.parse_agent_response(json_str, "TestAgent")
        
        assert len(result["questions_for_others"]) == 3
    
    def test_agent_id_override(self):
        """Test that agent_id is always set to the provided value"""
        json_str = '{"agent_id": "WrongAgent", "main_response": "test", "confidence_level": 0.8}'
        result = ResponseParser.parse_agent_response(json_str, "CorrectAgent")
        
        assert result["agent_id"] == "CorrectAgent"
    
    def test_required_field_defaults(self):
        """Test that missing required fields get default values"""
        json_str = '{"agent_id": "test"}'  # Only agent_id provided
        result = ResponseParser.parse_agent_response(json_str, "TestAgent")
        
        assert result["main_response"] == "Response could not be parsed properly"
        assert result["confidence_level"] == 0.5
        assert result["next_action"] == "Continue collaboration"
        assert result["reasoning"] == "Analysis completed"
        assert isinstance(result["key_insights"], list)
        assert isinstance(result["questions_for_others"], list)


class TestResponseValidation:
    """Test cases for response validation methods"""
    
    def test_validate_response_format_valid(self, sample_valid_json_response):
        """Test validation of valid response format"""
        assert ResponseParser._validate_response_format(sample_valid_json_response) is True
    
    def test_validate_response_format_missing_fields(self):
        """Test validation fails with missing required fields"""
        incomplete_responses = [
            {},  # Empty
            {"agent_id": "test"},  # Missing main_response and confidence
            {"main_response": "test"},  # Missing agent_id and confidence
            {"confidence_level": 0.8},  # Missing agent_id and main_response
        ]
        
        for response in incomplete_responses:
            assert ResponseParser._validate_response_format(response) is False
    
    def test_validate_response_format_invalid_confidence(self):
        """Test validation fails with invalid confidence levels"""
        invalid_confidence_cases = [
            {"agent_id": "test", "main_response": "test", "confidence_level": -0.1},
            {"agent_id": "test", "main_response": "test", "confidence_level": 1.1},
            {"agent_id": "test", "main_response": "test", "confidence_level": "invalid"},
            {"agent_id": "test", "main_response": "test", "confidence_level": None},
        ]
        
        for response in invalid_confidence_cases:
            assert ResponseParser._validate_response_format(response) is False
    
    def test_validate_response_format_invalid_arrays(self):
        """Test validation fails with invalid array fields"""
        invalid_array_cases = [
            {
                "agent_id": "test",
                "main_response": "test",
                "confidence_level": 0.8,
                "key_insights": "not an array"
            },
            {
                "agent_id": "test", 
                "main_response": "test",
                "confidence_level": 0.8,
                "questions_for_others": {"not": "array"}
            },
        ]
        
        for response in invalid_array_cases:
            assert ResponseParser._validate_response_format(response) is False
    
    @patch('utils.response_parser.logger')
    def test_validate_and_log_response(self, mock_logger, sample_valid_json_response):
        """Test response validation with logging"""
        # Test valid response
        result = ResponseParser.validate_and_log_response(
            sample_valid_json_response, "TestAgent"
        )
        assert result is True
        mock_logger.debug.assert_called()
        
        # Test invalid response
        invalid_response = {"agent_id": "test"}  # Missing required fields
        result = ResponseParser.validate_and_log_response(invalid_response, "TestAgent")
        assert result is False
        mock_logger.warning.assert_called()
    
    def test_ensure_required_fields_completion(self):
        """Test that ensure_required_fields completes incomplete responses"""
        incomplete = {"agent_id": "wrong_id", "main_response": "test"}
        result = ResponseParser._ensure_required_fields(incomplete, "correct_id")
        
        assert result["agent_id"] == "correct_id"
        assert result["main_response"] == "test"
        assert result["confidence_level"] == 0.5  # Default value
        assert isinstance(result["key_insights"], list)
        assert isinstance(result["questions_for_others"], list)
        assert "next_action" in result
        assert "reasoning" in result


class TestStructuredTextParsing:
    """Test cases for structured text parsing"""
    
    def test_parse_structured_text_complete(self):
        """Test parsing complete structured text"""
        text = """
        main_response: This is the main analysis of the problem
        confidence_level: 0.75
        key_insights: [First insight, Second insight, Third insight]
        questions_for_others: [Question 1?, Question 2?]
        """
        
        result = ResponseParser._parse_structured_text(text)
        
        assert result is not None
        assert result["main_response"] == "This is the main analysis of the problem"
        assert result["confidence_level"] == 0.75
        assert len(result["key_insights"]) == 3
        assert len(result["questions_for_others"]) == 2
    
    def test_parse_structured_text_partial(self):
        """Test parsing partial structured text"""
        text = """
        analysis: This is just the main analysis
        confidence: 0.9
        """
        
        result = ResponseParser._parse_structured_text(text)
        
        assert result is not None
        assert result["main_response"] == "This is just the main analysis"
        assert result["confidence_level"] == 0.9
    
    def test_parse_structured_text_no_main_response(self):
        """Test that parsing fails without main response"""
        text = """
        confidence: 0.8
        insights: [Some insight]
        """
        
        result = ResponseParser._parse_structured_text(text)
        assert result is None
    
    def test_parse_structured_text_various_field_names(self):
        """Test parsing with various field name variations"""
        text = """
        response: Main response here
        confidence: 0.6
        insights: [Insight one, Insight two]
        questions: [Question?]
        """
        
        result = ResponseParser._parse_structured_text(text)
        
        assert result["main_response"] == "Main response here"
        assert result["confidence_level"] == 0.6
        assert len(result["key_insights"]) == 2
        assert len(result["questions_for_others"]) == 1


class TestFallbackResponse:
    """Test cases for fallback response creation"""
    
    def test_create_fallback_response_normal_text(self):
        """Test creating fallback response from normal text"""
        text = "This is a normal response with some analysis."
        result = ResponseParser._create_fallback_response(text, "TestAgent")
        
        assert result["agent_id"] == "TestAgent"
        assert result["main_response"] == text
        assert result["confidence_level"] == 0.3
        assert result["reasoning"] == "Response created from fallback parsing"
    
    def test_create_fallback_response_long_text(self):
        """Test creating fallback response from long text (should be truncated)"""
        long_text = "a" * 1500
        result = ResponseParser._create_fallback_response(long_text, "TestAgent")
        
        assert len(result["main_response"]) == 1000
        assert result["main_response"].endswith("...")
    
    def test_create_fallback_response_empty_text(self):
        """Test creating fallback response from empty text"""
        result = ResponseParser._create_fallback_response("", "TestAgent")
        
        assert result["main_response"] == "Unable to generate proper response"
        assert result["confidence_level"] == 0.3
    
    def test_create_fallback_response_extracts_insights(self):
        """Test that fallback response extracts potential insights"""
        text = """
        This is the first sentence that could be an insight.
        This is another sentence with meaningful content for extraction.
        Short. This sentence is too short.
        This is a very long sentence that exceeds the maximum length threshold for what could be considered a reasonable insight and should be excluded from the insights list.
        This is the final reasonable insight sentence.
        """
        
        result = ResponseParser._create_fallback_response(text, "TestAgent")
        
        # Should extract sentences that are between 20-200 characters
        insights = result["key_insights"]
        assert len(insights) <= 5
        for insight in insights:
            assert 20 <= len(insight) <= 200