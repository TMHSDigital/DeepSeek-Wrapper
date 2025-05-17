import re
from typing import Optional

def extract_final_answer(response: str) -> str:
    """
    Extract the final answer from a Chain of Thought reasoning response.
    
    This function attempts to identify and extract just the conclusion or final answer
    from a detailed reasoning process, looking for patterns like "Answer:", 
    the last step in a numbered sequence, or the last paragraph.
    
    Args:
        response: The full response from the model including reasoning steps
        
    Returns:
        Just the final answer, or the original response if no clear answer could be extracted
    """
    # Check if the response is empty
    if not response or response.strip() == "":
        return response
    
    # Look for explicit "Answer:" or "Conclusion:" markers
    answer_match = re.search(r'(?:Answer|Conclusion|Therefore|Thus|Hence|Result):?\s*(.*?)(?:\n\n|$)', response, re.IGNORECASE | re.DOTALL)
    if answer_match:
        return answer_match.group(1).strip()
    
    # Look for the last step in a step-by-step solution
    step_matches = re.findall(r'Step\s+\d+:?\s*(.*?)(?=Step\s+\d+:|$)', response, re.IGNORECASE | re.DOTALL)
    if step_matches:
        return step_matches[-1].strip()
    
    # Look for a final calculated value
    calculation_match = re.search(r'(?:=|equals|is)\s*([\d.]+\s*(?:hours|minutes|seconds|days|km|miles|meters|\w+))(?!.*(?:=|equals|is)\s*[\d.]+)', response, re.IGNORECASE)
    if calculation_match:
        # Find the sentence containing this calculation
        sentences = re.split(r'(?<=[.!?])\s+', response)
        for sentence in reversed(sentences):
            if calculation_match.group(1) in sentence:
                return sentence.strip()
    
    # Fall back to the last non-empty paragraph if no other patterns match
    paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]
    if paragraphs:
        return paragraphs[-1]
    
    # If all else fails, return the original response
    return response

def process_model_response(response: str, model_name: str, extract_answer_only: bool = False) -> str:
    """
    Process a model response based on model type and user preferences.
    
    Args:
        response: The full response from the model
        model_name: The name of the model used
        extract_answer_only: Whether to extract just the final answer for reasoning models
        
    Returns:
        The processed response
    """
    if not extract_answer_only:
        return response
    
    # Only extract answers for the reasoner model
    if "reasoner" in model_name.lower():
        return extract_final_answer(response)
    
    return response 