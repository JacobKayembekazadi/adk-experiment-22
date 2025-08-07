"""
Async Ollama client with comprehensive error handling and retry logic.

This module provides a robust client for communicating with Ollama's REST API,
including comprehensive error handling, retry logic, and proper async context management.
"""
import asyncio
import aiohttp
import json
import logging
import re
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class OllamaClientError(Exception):
    """Base exception class for Ollama client errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize OllamaClientError.
        
        Args:
            message: Error message
            details: Optional additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class OllamaConnectionError(OllamaClientError):
    """Raised when connection to Ollama server fails."""
    pass


class OllamaModelError(OllamaClientError):
    """Raised when there's an issue with the specified model."""
    pass


class OllamaRequestError(OllamaClientError):
    """Raised when the request is malformed or invalid."""
    pass


class OllamaTimeoutError(OllamaClientError):
    """Raised when requests timeout."""
    pass


class OllamaValidationError(OllamaClientError):
    """Raised when input validation fails."""
    pass

@dataclass
class OllamaConfig:
    """
    Configuration settings for the Ollama client.
    
    Attributes:
        base_url: Base URL for the Ollama API server
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts for failed requests
        retry_delay: Base delay between retries in seconds (uses exponential backoff)
        validate_models: Whether to validate model names before making requests
        default_options: Default generation options to apply to all requests
    """
    base_url: str = "http://localhost:11434"
    timeout: int = 120
    max_retries: int = 3
    retry_delay: float = 1.0
    validate_models: bool = True
    default_options: Dict[str, Any] = field(default_factory=lambda: {
        "num_predict": 1000,
        "top_k": 40,
        "top_p": 0.9,
        "repeat_penalty": 1.1
    })
    
    def __post_init__(self) -> None:
        """Validate configuration parameters after initialization."""
        self._validate_config()
    
    def _validate_config(self) -> None:
        """
        Validate configuration parameters.
        
        Raises:
            OllamaValidationError: If any configuration parameter is invalid
        """
        if not isinstance(self.base_url, str) or not self.base_url.strip():
            raise OllamaValidationError("base_url must be a non-empty string")
        
        if not self.base_url.startswith(('http://', 'https://')):
            raise OllamaValidationError("base_url must start with http:// or https://")
        
        if not isinstance(self.timeout, int) or self.timeout <= 0:
            raise OllamaValidationError("timeout must be a positive integer")
        
        if not isinstance(self.max_retries, int) or self.max_retries < 0:
            raise OllamaValidationError("max_retries must be a non-negative integer")
        
        if not isinstance(self.retry_delay, (int, float)) or self.retry_delay < 0:
            raise OllamaValidationError("retry_delay must be a non-negative number")
        
        if not isinstance(self.validate_models, bool):
            raise OllamaValidationError("validate_models must be a boolean")
        
        if not isinstance(self.default_options, dict):
            raise OllamaValidationError("default_options must be a dictionary")


@dataclass
class GenerationRequest:
    """
    Represents a generation request to the Ollama API.
    
    Attributes:
        model: Name of the model to use for generation
        prompt: The prompt text to generate from
        system: Optional system prompt/context
        temperature: Sampling temperature (0.0 to 2.0)
        format: Expected response format ("json" or None)
        options: Additional generation options
        stream: Whether to stream the response
    """
    model: str
    prompt: str
    system: str = ""
    temperature: float = 0.7
    format: Optional[str] = "json"
    options: Dict[str, Any] = field(default_factory=dict)
    stream: bool = False
    
    def __post_init__(self) -> None:
        """Validate request parameters after initialization."""
        self._validate_request()
    
    def _validate_request(self) -> None:
        """
        Validate generation request parameters.
        
        Raises:
            OllamaValidationError: If any parameter is invalid
        """
        if not isinstance(self.model, str) or not self.model.strip():
            raise OllamaValidationError("model must be a non-empty string")
        
        if not isinstance(self.prompt, str):
            raise OllamaValidationError("prompt must be a string")
        
        if not isinstance(self.system, str):
            raise OllamaValidationError("system must be a string")
        
        if not isinstance(self.temperature, (int, float)):
            raise OllamaValidationError("temperature must be a number")
        
        if not (0.0 <= self.temperature <= 2.0):
            raise OllamaValidationError("temperature must be between 0.0 and 2.0")
        
        if self.format is not None and not isinstance(self.format, str):
            raise OllamaValidationError("format must be a string or None")
        
        if self.format and self.format not in ("json",):
            raise OllamaValidationError("format must be 'json' or None")
        
        if not isinstance(self.options, dict):
            raise OllamaValidationError("options must be a dictionary")
        
        if not isinstance(self.stream, bool):
            raise OllamaValidationError("stream must be a boolean")


@dataclass
class GenerationResponse:
    """
    Represents a response from the Ollama API.
    
    Attributes:
        response: The generated text response
        model: Name of the model that generated the response
        created_at: Timestamp when the response was created
        done: Whether the generation is complete
        total_duration: Total time taken for generation (nanoseconds)
        load_duration: Time taken to load the model (nanoseconds)
        prompt_eval_count: Number of tokens in the prompt
        eval_count: Number of tokens in the response
        context: Context tokens for conversation continuation
    """
    response: str
    model: str
    created_at: Optional[str] = None
    done: bool = True
    total_duration: int = 0
    load_duration: int = 0
    prompt_eval_count: int = 0
    eval_count: int = 0
    context: Optional[List[int]] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'GenerationResponse':
        """
        Create a GenerationResponse from API response data.
        
        Args:
            data: Raw response data from the Ollama API
            
        Returns:
            GenerationResponse instance
            
        Raises:
            OllamaValidationError: If response data is invalid
        """
        try:
            return cls(
                response=data.get('response', ''),
                model=data.get('model', ''),
                created_at=data.get('created_at'),
                done=data.get('done', True),
                total_duration=data.get('total_duration', 0),
                load_duration=data.get('load_duration', 0),
                prompt_eval_count=data.get('prompt_eval_count', 0),
                eval_count=data.get('eval_count', 0),
                context=data.get('context')
            )
        except Exception as e:
            raise OllamaValidationError(f"Invalid API response data: {e}") from e

class OllamaClient:
    """
    Async client for communicating with Ollama's REST API.
    
    This client provides comprehensive error handling, retry logic, connection pooling,
    and proper async context management for interacting with Ollama models.
    
    Example:
        async with OllamaClient() as client:
            response = await client.generate_with_retry(
                model="llama3.1:8b",
                prompt="Hello, world!",
                temperature=0.7
            )
            print(response.response)
    
    Attributes:
        config: Configuration settings for the client
        session: aiohttp ClientSession for making HTTP requests
    """
    
    def __init__(self, config: Optional[OllamaConfig] = None) -> None:
        """
        Initialize the Ollama client.
        
        Args:
            config: Optional configuration settings. Uses default if not provided.
        """
        self.config = config or OllamaConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self._available_models: Optional[List[str]] = None
        self._models_cache_time: Optional[float] = None
        self._models_cache_ttl: float = 300.0  # 5 minutes
        
    async def __aenter__(self) -> 'OllamaClient':
        """
        Async context manager entry.
        
        Returns:
            Self for method chaining
            
        Raises:
            OllamaConnectionError: If session creation fails
        """
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                connector=aiohttp.TCPConnector(limit=100, limit_per_host=30)
            )
            return self
        except Exception as e:
            raise OllamaConnectionError(f"Failed to create HTTP session: {e}") from e
        
    async def __aexit__(self, exc_type: Optional[type], exc_val: Optional[Exception], 
                       exc_tb: Optional[Any]) -> None:
        """
        Async context manager exit.
        
        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        if self.session:
            try:
                await self.session.close()
            except Exception as e:
                logger.warning(f"Error closing HTTP session: {e}")
            finally:
                self.session = None
    
    async def test_connection(self) -> bool:
        """
        Test if Ollama is running and accessible.
        
        Returns:
            True if connection is successful, False otherwise
            
        Raises:
            OllamaConnectionError: If session is not initialized
        """
        if not self.session:
            raise OllamaConnectionError("Client session not initialized. Use async context manager.")
        
        try:
            async with self.session.get(
                f"{self.config.base_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model['name'] for model in data.get('models', [])]
                    logger.info(f"Ollama connection successful. Available models: {models}")
                    return True
                else:
                    logger.error(f"Ollama connection failed with status: {response.status}")
                    return False
        except asyncio.TimeoutError:
            logger.error("Ollama connection test timed out")
            return False
        except aiohttp.ClientError as e:
            logger.error(f"Network error during connection test: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during connection test: {e}")
            return False
    
    async def generate_with_retry(self, model: str, prompt: str, system: str = "", 
                                temperature: float = 0.7, format: Optional[str] = "json",
                                options: Optional[Dict[str, Any]] = None) -> GenerationResponse:
        """
        Generate response with retry logic and comprehensive error handling.
        
        Args:
            model: Name of the model to use
            prompt: The prompt text to generate from
            system: Optional system prompt/context
            temperature: Sampling temperature (0.0 to 2.0)
            format: Expected response format ("json" or None)
            options: Additional generation options
            
        Returns:
            GenerationResponse containing the generated text and metadata
            
        Raises:
            OllamaConnectionError: If session is not initialized
            OllamaModelError: If the specified model is not available
            OllamaRequestError: If the request is malformed
            OllamaTimeoutError: If all retry attempts timeout
            OllamaValidationError: If input parameters are invalid
        """
        if not self.session:
            raise OllamaConnectionError("Client session not initialized. Use async context manager.")
        
        # Create and validate request
        request = GenerationRequest(
            model=model,
            prompt=prompt,
            system=system,
            temperature=temperature,
            format=format,
            options=options or {},
            stream=False
        )
        
        # Validate model if enabled
        if self.config.validate_models:
            await self._validate_model(request.model)
        
        last_exception: Optional[Exception] = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                response = await self._generate_single_request(request)
                logger.debug(f"Generation successful for model {model} on attempt {attempt + 1}")
                return response
            except asyncio.TimeoutError as e:
                last_exception = OllamaTimeoutError(f"Request timed out on attempt {attempt + 1}")
                logger.warning(f"Attempt {attempt + 1} timed out for model {model}")
            except aiohttp.ClientError as e:
                last_exception = OllamaConnectionError(f"Network error on attempt {attempt + 1}: {e}")
                logger.warning(f"Attempt {attempt + 1} failed with network error for model {model}: {e}")
            except OllamaModelError as e:
                # Don't retry model errors
                raise e
            except Exception as e:
                last_exception = OllamaClientError(f"Unexpected error on attempt {attempt + 1}: {e}")
                logger.warning(f"Attempt {attempt + 1} failed for model {model}: {e}")
            
            # Wait before retry (exponential backoff)
            if attempt < self.config.max_retries:
                delay = self.config.retry_delay * (2 ** attempt)
                logger.debug(f"Waiting {delay:.2f}s before retry attempt {attempt + 2}")
                await asyncio.sleep(delay)
        
        # All retries failed
        error_msg = f"All {self.config.max_retries + 1} attempts failed for model {model}"
        logger.error(error_msg)
        
        if isinstance(last_exception, OllamaTimeoutError):
            raise last_exception
        elif last_exception:
            raise OllamaClientError(error_msg) from last_exception
        else:
            raise OllamaClientError(error_msg)
    
    async def _generate_single_request(self, request: GenerationRequest) -> GenerationResponse:
        """
        Execute a single generation request to the Ollama API.
        
        Args:
            request: The generation request to execute
            
        Returns:
            GenerationResponse containing the generated text and metadata
            
        Raises:
            OllamaConnectionError: If session is not initialized
            OllamaModelError: If the model returns an error
            OllamaRequestError: If the request is malformed
            aiohttp.ClientError: For network-related errors
            asyncio.TimeoutError: If the request times out
        """
        if not self.session:
            raise OllamaConnectionError("Client session not initialized. Use async context manager.")
        
        # Prepare payload
        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "stream": request.stream,
            "options": {**self.config.default_options, **request.options}
        }
        
        # Add optional fields
        if request.system:
            payload["system"] = request.system
        if request.format:
            payload["format"] = request.format
        
        # Update temperature in options
        payload["options"]["temperature"] = request.temperature
        
        logger.debug(f"Sending request to {request.model}: {request.prompt[:100]}...")
        
        try:
            async with self.session.post(
                f"{self.config.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                if response.status == 404:
                    raise OllamaModelError(f"Model '{request.model}' not found")
                elif response.status == 400:
                    error_text = await response.text()
                    raise OllamaRequestError(f"Bad request: {error_text}")
                elif response.status != 200:
                    error_text = await response.text()
                    raise OllamaConnectionError(f"HTTP {response.status}: {error_text}")
                
                try:
                    data = await response.json()
                except json.JSONDecodeError as e:
                    raise OllamaRequestError(f"Invalid JSON response: {e}") from e
                
                # Check for API-level errors
                if 'error' in data:
                    error_msg = data['error']
                    if 'not found' in error_msg.lower():
                        raise OllamaModelError(f"Model error: {error_msg}")
                    else:
                        raise OllamaRequestError(f"API error: {error_msg}")
                
                return GenerationResponse.from_api_response(data)
                
        except asyncio.TimeoutError:
            logger.error(f"Request timed out for model {request.model}")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Network error calling Ollama: {e}")
            raise
        except (OllamaModelError, OllamaRequestError, OllamaConnectionError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Ollama: {e}")
            raise OllamaClientError(f"Unexpected error: {e}") from e

    async def list_models(self, force_refresh: bool = False) -> List[str]:
        """
        List available models with caching support.
        
        Args:
            force_refresh: Whether to force refresh the model cache
            
        Returns:
            List of available model names
            
        Raises:
            OllamaConnectionError: If session is not initialized or connection fails
        """
        if not self.session:
            raise OllamaConnectionError("Client session not initialized. Use async context manager.")
        
        # Check cache
        current_time = asyncio.get_event_loop().time()
        if (not force_refresh and 
            self._available_models is not None and 
            self._models_cache_time is not None and
            current_time - self._models_cache_time < self._models_cache_ttl):
            return self._available_models.copy()
        
        try:
            async with self.session.get(
                f"{self.config.base_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model['name'] for model in data.get('models', [])]
                    
                    # Update cache
                    self._available_models = models
                    self._models_cache_time = current_time
                    
                    logger.debug(f"Retrieved {len(models)} available models")
                    return models.copy()
                else:
                    raise OllamaConnectionError(f"Failed to list models: HTTP {response.status}")
        except asyncio.TimeoutError:
            raise OllamaConnectionError("Timeout while listing models")
        except aiohttp.ClientError as e:
            raise OllamaConnectionError(f"Network error while listing models: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error listing models: {e}")
            raise OllamaConnectionError(f"Failed to list models: {e}") from e
    
    async def _validate_model(self, model_name: str) -> None:
        """
        Validate that a model is available on the server.
        
        Args:
            model_name: Name of the model to validate
            
        Raises:
            OllamaModelError: If the model is not available
            OllamaConnectionError: If unable to retrieve model list
        """
        try:
            available_models = await self.list_models()
            if model_name not in available_models:
                raise OllamaModelError(
                    f"Model '{model_name}' not found. Available models: {available_models}",
                    details={"available_models": available_models, "requested_model": model_name}
                )
        except OllamaModelError:
            # Re-raise model errors
            raise
        except Exception as e:
            raise OllamaConnectionError(f"Failed to validate model '{model_name}': {e}") from e
    
    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary containing model information
            
        Raises:
            OllamaConnectionError: If session is not initialized or connection fails
            OllamaModelError: If the model is not found
        """
        if not self.session:
            raise OllamaConnectionError("Client session not initialized. Use async context manager.")
        
        try:
            async with self.session.post(
                f"{self.config.base_url}/api/show",
                json={"name": model_name},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 404:
                    raise OllamaModelError(f"Model '{model_name}' not found")
                elif response.status != 200:
                    error_text = await response.text()
                    raise OllamaConnectionError(f"Failed to get model info: HTTP {response.status}: {error_text}")
                
                return await response.json()
        except OllamaModelError:
            raise
        except asyncio.TimeoutError:
            raise OllamaConnectionError(f"Timeout while getting info for model '{model_name}'")
        except aiohttp.ClientError as e:
            raise OllamaConnectionError(f"Network error while getting model info: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error getting model info: {e}")
            raise OllamaConnectionError(f"Failed to get model info: {e}") from e
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive health check of the Ollama service.
        
        Returns:
            Dictionary containing health check results
            
        Raises:
            OllamaConnectionError: If session is not initialized
        """
        if not self.session:
            raise OllamaConnectionError("Client session not initialized. Use async context manager.")
        
        health_status = {
            "service_available": False,
            "models_available": [],
            "response_time_ms": None,
            "error": None
        }
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Test basic connectivity
            if await self.test_connection():
                health_status["service_available"] = True
                
                # Get available models
                try:
                    models = await self.list_models()
                    health_status["models_available"] = models
                except Exception as e:
                    health_status["error"] = f"Failed to list models: {e}"
            else:
                health_status["error"] = "Service not available"
            
        except Exception as e:
            health_status["error"] = str(e)
        finally:
            end_time = asyncio.get_event_loop().time()
            health_status["response_time_ms"] = round((end_time - start_time) * 1000, 2)
        
        return health_status
    
    def get_config(self) -> OllamaConfig:
        """
        Get the current client configuration.
        
        Returns:
            Copy of the current configuration
        """
        return OllamaConfig(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
            validate_models=self.config.validate_models,
            default_options=self.config.default_options.copy()
        )
    
    async def close(self) -> None:
        """
        Manually close the client session.
        
        Note: Prefer using the async context manager (__aenter__/__aexit__)
        """
        if self.session:
            try:
                await self.session.close()
            except Exception as e:
                logger.warning(f"Error closing HTTP session: {e}")
            finally:
                self.session = None
                self._available_models = None
                self._models_cache_time = None


# Utility functions for easier usage
async def create_client(config: Optional[OllamaConfig] = None) -> OllamaClient:
    """
    Create and initialize an OllamaClient.
    
    Args:
        config: Optional configuration settings
        
    Returns:
        Initialized OllamaClient ready for use
        
    Example:
        client = await create_client()
        async with client:
            response = await client.generate_with_retry("llama3.1:8b", "Hello!")
    """
    client = OllamaClient(config)
    return client


def validate_model_name(model_name: str) -> bool:
    """
    Validate model name format.
    
    Args:
        model_name: Model name to validate
        
    Returns:
        True if the model name format is valid
    """
    if not isinstance(model_name, str) or not model_name.strip():
        return False
    
    # Basic model name validation (alphanumeric, hyphens, underscores, colons, dots)
    pattern = r'^[a-zA-Z0-9._:-]+$'
    return bool(re.match(pattern, model_name))


def validate_temperature(temperature: Union[int, float]) -> bool:
    """
    Validate temperature value.
    
    Args:
        temperature: Temperature value to validate
        
    Returns:
        True if the temperature is valid
    """
    return isinstance(temperature, (int, float)) and 0.0 <= temperature <= 2.0
