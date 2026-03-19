def is_critical_file(file_path: str, critical_patterns: list) -> bool:
    """Check if a file path matches any critical pattern."""
    for pattern in critical_patterns:
        if pattern in file_path:
            return True
    return False