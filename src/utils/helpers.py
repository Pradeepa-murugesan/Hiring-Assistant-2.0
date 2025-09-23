import json
import re

def clean_and_parse_json(llm_output: str) -> dict:
    """
    Cleans and parses a JSON string from an LLM, now with added logic
    to remove invalid control characters that cause parsing errors.

    Args:
        llm_output: The raw string output from the language model.

    Returns:
        A dictionary parsed from the JSON string. Returns an empty dictionary
        if parsing fails.
    """
    try:
        cleaned_string = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', llm_output)

        cleaned_string = cleaned_string.strip().replace('```json', '').replace('```', '')
        
        start_index = cleaned_string.find('{')
        end_index = cleaned_string.rfind('}') + 1
        
        if start_index != -1 and end_index != 0:
            json_string = cleaned_string[start_index:end_index]
            return json.loads(json_string)
        else:
            print("ERROR: No valid JSON object found in the LLM output.")
            return {}
            
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON from LLM response. Details: {e}")
        return {}

