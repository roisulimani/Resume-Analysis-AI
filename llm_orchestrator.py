"""
llm_orchestrator.py

Module for orchestrating LLM analysis using LangChain and OpenAI API.
Constructs prompts, ensures structured output, and returns validated results.
Tracks token usage and cost. Implements robust error handling and logging.
"""

import os
import logging
from typing import List, Any, Dict, Optional
from pydantic import BaseModel, ValidationError, Field
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import tiktoken
import dotenv
import re

dotenv.load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load OpenAI API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY not found in environment variables.")

# Cost per 1K tokens for gpt-3.5-turbo (adjust as needed)
COST_PER_1K_TOKENS = 0.0015

class AnalysisResult(BaseModel):
    """
    Pydantic model for the structured output of the LLM analysis.
    """
    matching_score: float = Field(..., ge=0, le=100, description="Overall match score (0-100)")
    matched_skills: List[str]
    missing_skills: List[str]
    matched_experience: List[str]
    missing_experience: List[str]
    summary: str
    cost_estimate: Optional[Dict[str, Any]] = None  # Make optional


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """
    Counts the number of tokens in a text string for the specified model.
    Args:
        text (str): The text to count tokens for.
        model (str): The model name (default: gpt-3.5-turbo).
    Returns:
        int: Number of tokens.
    """
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))


def build_prompt(job_desc: str, resume: str) -> str:
    """
    Constructs the prompt for the LLM to analyze the resume against the job description.
    Args:
        job_desc (str): The job description text.
        resume (str): The candidate's resume text.
    Returns:
        str: The constructed prompt.
    """
    return (
        "You are an expert HR assistant. Analyze the following candidate resume against the job description. "
        "Extract and compare skills and experience. Output a JSON object with the following fields: "
        "matching_score (0-100), matched_skills (list), missing_skills (list), matched_experience (list), "
        "missing_experience (list), summary (string)."
        "\n\nJob Description:\n" + job_desc +
        "\n\nCandidate Resume:\n" + resume +
        "\n\nRespond ONLY with the JSON object."
    )


def extract_json_from_llm_output(text: str) -> str:
    """
    Removes Markdown code block markers (``` or ```json) from LLM output.
    Args:
        text (str): Raw LLM output.
    Returns:
        str: Cleaned JSON string.
    """
    # Remove triple backticks and optional 'json' after them
    cleaned = re.sub(r"^```(?:json)?\s*|```$", "", text.strip(), flags=re.IGNORECASE | re.MULTILINE)
    return cleaned.strip()


def analyze_resume(job_desc: str, resume: str, model_name: str = "gpt-3.5-turbo") -> AnalysisResult:
    """
    Analyzes the resume against the job description using OpenAI LLM via LangChain.
    Ensures structured output and returns a validated AnalysisResult.
    Args:
        job_desc (str): The job description text.
        resume (str): The candidate's resume text.
        model_name (str): The OpenAI model to use (default: gpt-3.5-turbo).
    Returns:
        AnalysisResult: The structured analysis result.
    Raises:
        RuntimeError: If the LLM call or output parsing fails.
    """
    parser = PydanticOutputParser(pydantic_object=AnalysisResult)
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are an expert HR assistant. Respond only with valid JSON as per the schema."),
        ("human", "{input_prompt}")
    ])
    input_prompt = build_prompt(job_desc, resume)
    prompt = prompt_template.format_messages(input_prompt=input_prompt)

    # Token counting for prompt
    prompt_tokens = count_tokens(input_prompt, model=model_name)

    llm = ChatOpenAI(api_key=OPENAI_API_KEY, model=model_name, temperature=0.3)
    try:
        response = llm(prompt)
        # Clean LLM output
        cleaned_output = extract_json_from_llm_output(response.content)
        # Token counting for completion
        completion_tokens = count_tokens(response.content, model=model_name)
        total_tokens = prompt_tokens + completion_tokens
        usd_cost = total_tokens / 1000 * COST_PER_1K_TOKENS
        logger.info(f"Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens}, Total: {total_tokens}, Cost: ${usd_cost:.4f}")
        # Parse and validate output
        result = parser.parse(cleaned_output)
        result.cost_estimate = {
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': total_tokens,
            'usd': round(usd_cost, 6)
        }
        return result
    except ValidationError as ve:
        logger.error(f"Output validation error: {ve}")
        raise RuntimeError(f"LLM output validation failed: {ve}")
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        raise RuntimeError(f"LLM analysis failed: {e}") 