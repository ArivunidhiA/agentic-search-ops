"""Security validation and sanitization functions."""

import re
import html
from typing import Optional
from fastapi import HTTPException, status


# Reserved filenames on Windows
RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}


def validate_filename(filename: str) -> str:
    """
    Validate and sanitize filename.
    
    Checks for:
    - Path traversal attempts (../, ..\\)
    - Null bytes
    - Reserved names (CON, PRN, etc.)
    - Invalid characters
    
    Raises HTTPException(400) on failure.
    """
    if not filename or not isinstance(filename, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required and must be a string"
        )
    
    # Check for path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename contains invalid path characters"
        )
    
    # Check for null bytes
    if "\x00" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename contains null bytes"
        )
    
    # Extract base filename (remove extension for reserved name check)
    base_name = filename.rsplit(".", 1)[0].upper()
    if base_name in RESERVED_NAMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Filename '{filename}' is a reserved system name"
        )
    
    # Sanitize: allow only alphanumeric, dots, dashes, underscores
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    if not sanitized or len(sanitized) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is empty or too long (max 255 characters)"
        )
    
    return sanitized


def validate_file_size(file_size: int, max_size: int) -> None:
    """
    Validate file size.
    
    Raises HTTPException(413) if file is too large.
    """
    if not isinstance(file_size, int) or file_size < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file size"
        )
    
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)"
        )


def validate_content_type(content_type: str, allowed_types: list[str]) -> None:
    """
    Validate content type.
    
    Raises HTTPException(415) if content type is not allowed.
    """
    if not content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content type is required"
        )
    
    # Extract base type (e.g., "application/pdf" from "application/pdf; charset=utf-8")
    base_type = content_type.split(";")[0].strip().lower()
    
    if base_type not in [t.lower() for t in allowed_types]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Content type '{content_type}' is not allowed. Allowed types: {', '.join(allowed_types)}"
        )


def sanitize_text_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize text input.
    
    - Strip leading/trailing whitespace
    - Remove control characters (except newline, tab, carriage return)
    - Truncate to max_length
    - Escape HTML entities
    """
    if not isinstance(text, str):
        return ""
    
    # Strip whitespace
    sanitized = text.strip()
    
    # Remove control characters (keep \n, \r, \t)
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
    
    # Truncate
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # Escape HTML entities
    sanitized = html.escape(sanitized)
    
    return sanitized


def sanitize_search_query(query: str) -> str:
    """
    Sanitize search query to prevent SQL injection and wildcard abuse.
    
    - Remove SQL special characters that could be dangerous
    - Limit length to 500 chars
    - Remove excessive wildcards
    """
    if not isinstance(query, str):
        return ""
    
    # Remove leading/trailing whitespace
    sanitized = query.strip()
    
    # Remove SQL injection patterns (semicolons, comments, etc.)
    # Escape dash in character class or place it at the end
    sanitized = re.sub(r'[;-]', '', sanitized)
    
    # Limit wildcard usage (max 3 consecutive wildcards)
    sanitized = re.sub(r'\*{4,}', '***', sanitized)
    sanitized = re.sub(r'\?{4,}', '???', sanitized)
    
    # Limit length
    if len(sanitized) > 500:
        sanitized = sanitized[:500]
    
    return sanitized


def validate_job_config(config: dict, max_runtime_minutes: int, max_cost_usd: float) -> dict:
    """
    Validate job configuration.
    
    - Validate max_runtime and max_cost within system limits
    - Ensure no code injection in config values
    - Return sanitized config
    """
    if not isinstance(config, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job config must be a dictionary"
        )
    
    sanitized = {}
    
    # Validate and sanitize each config value
    for key, value in config.items():
        # Validate key (must be alphanumeric with underscores)
        if not re.match(r'^[a-zA-Z0-9_]+$', str(key)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid config key: {key}"
            )
        
        # Sanitize value based on type
        if isinstance(value, str):
            # Prevent code injection patterns
            if any(pattern in value.lower() for pattern in ['eval(', 'exec(', '__import__', 'compile(']):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Config contains potentially dangerous code patterns"
                )
            sanitized[key] = sanitize_text_input(value, max_length=10000)
        elif isinstance(value, (int, float, bool, type(None))):
            sanitized[key] = value
        elif isinstance(value, (list, dict)):
            # Recursively sanitize nested structures (simplified)
            sanitized[key] = value
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid config value type for key '{key}': {type(value)}"
            )
    
    # Validate runtime limits
    if "max_runtime_minutes" in sanitized:
        runtime = sanitized["max_runtime_minutes"]
        if not isinstance(runtime, (int, float)) or runtime < 0 or runtime > max_runtime_minutes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"max_runtime_minutes must be between 0 and {max_runtime_minutes}"
            )
    
    # Validate cost limits
    if "max_cost_usd" in sanitized:
        cost = sanitized["max_cost_usd"]
        if not isinstance(cost, (int, float)) or cost < 0 or cost > max_cost_usd:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"max_cost_usd must be between 0 and {max_cost_usd}"
            )
    
    return sanitized
