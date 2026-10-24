import json
import re

def json_interpretation(response, logger=None):
    try:
        # remove json formatting from the result_text
        result_text = response.strip()

        # if the result is wrapped in ```json ... ``` , extract the content in the middle
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", result_text, re.DOTALL)
        if match:
            result_text = match.group(1).strip()
        
        if result_text.startswith("json"):
            result_text = result_text[len("json"):].strip()
        result = json.loads(result_text)
    except json.JSONDecodeError as e:
        if logger:
            logger.error(f"Error decoding JSON: {e}: {result_text}")
        else:
            print(f"Error decoding JSON: {e}: {result_text}")
        raise e
    except Exception as e:
        if logger:
            logger.error(f"Unexpected error: {e}")
        else:
            print(f"Unexpected error: {e}")
        raise e
    
    return result