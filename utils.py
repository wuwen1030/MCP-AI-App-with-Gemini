

from typing import Any
import mcp
from google import genai


def map_tool_to_gemini_schema(tool: mcp.types.Tool) -> genai.types.FunctionDeclaration:
    """
    Map MCP tool to Gemini function declaration 
    """ 
    input_schema = tool.inputSchema if tool.inputSchema else {}
    parameters = {
        "type": input_schema.get("type", "object"),
        "properties": clean_schema_for_gemini(input_schema.get("properties", {})),
        "required": input_schema.get("required", []),
    }

    return genai.types.FunctionDeclaration(
        name=tool.name,
        description=tool.description,
        parameters=parameters
    )


def clean_schema_for_gemini(schema: dict[str, Any]) -> genai.types.Schema:
    """
    Clean JSON schema to only include fields supported by Gemini API
    """
    # Fields supported by Gemini for function parameters (based on genai.types.Schema)
    supported_fields = {
        'additional_properties', 'defs', 'ref', 'any_of', 'default', 'description', 
        'enum', 'example', 'format', 'items', 'max_items', 'max_length', 
        'max_properties', 'maximum', 'min_items', 'min_length', 'min_properties', 
        'minimum', 'nullable', 'pattern', 'properties', 'property_ordering', 
        'required', 'title', 'type'
    }

    cleaned = {}
    for key, value in schema.items():
        if key in supported_fields:
            if key == 'properties' and isinstance(value, dict):
                # Recursively clean properties
                cleaned[key] = {
                    prop_name: clean_schema_for_gemini(prop_schema)
                    for prop_name, prop_schema in value.items()
                }
            elif key == 'items' and isinstance(value, dict):
                # Recursively clean array items schema
                cleaned[key] = clean_schema_for_gemini(value)
            elif key == 'defs' and isinstance(value, dict):
                # Recursively clean schema definitions
                cleaned[key] = {
                    def_name: clean_schema_for_gemini(def_schema)
                    for def_name, def_schema in value.items()
                }
            elif key == 'any_of' and isinstance(value, list):
                # Recursively clean any_of schemas
                cleaned[key] = [
                    clean_schema_for_gemini(schema_item) 
                    for schema_item in value if isinstance(schema_item, dict)
                ]
            else:
                cleaned[key] = value

    return cleaned
