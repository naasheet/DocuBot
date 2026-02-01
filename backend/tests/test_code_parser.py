import pytest
from app.services.code_parser import CodeParserService

@pytest.fixture
def parser_service():
    return CodeParserService()

def test_parse_and_extract(parser_service):
    """
    Test that the parser correctly identifies classes and functions
    from a sample Python code snippet.
    """
    code_snippet = """
class UserManager:
    def __init__(self):
        pass

    def create_user(self, name):
        pass

def helper_function():
    return True

class Product:
    pass
"""
    # Convert to bytes as expected by the service
    content = code_snippet.encode('utf-8')
    
    # Parse
    result = parser_service.parse_python_file(content)
    
    # Extract
    functions = parser_service.extract_function_names(result)
    classes = parser_service.extract_class_names(result)
    assert isinstance(result["ast"], dict)
    
    # Verify Classes
    assert "UserManager" in classes
    assert "Product" in classes
    assert len(classes) == 2
    
    # Verify Functions
    # Note: methods inside classes are also function_definitions in tree-sitter python grammar
    assert "helper_function" in functions
    assert "create_user" in functions
    assert "__init__" in functions
    assert len(functions) == 3

def test_empty_content(parser_service):
    """Test parsing empty content returns empty lists."""
    result = parser_service.parse_python_file(b"")
    
    functions = parser_service.extract_function_names(result)
    classes = parser_service.extract_class_names(result)
    
    assert functions == []
    assert classes == []
