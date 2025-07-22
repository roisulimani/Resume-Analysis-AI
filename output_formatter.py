"""
output_formatter.py

Module for formatting and exporting the results of the LLM analysis.
Provides functions for pretty-printing, saving to file, and generating human-readable summaries.
"""

import json
from typing import Any
from llm_orchestrator import AnalysisResult
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_result_as_json(result: AnalysisResult) -> str:
    """
    Formats the AnalysisResult as a pretty-printed JSON string.
    Args:
        result (AnalysisResult): The analysis result object.
    Returns:
        str: Pretty-printed JSON string.
    """
    try:
        return result.model_dump_json(indent=2)
    except Exception as e:
        logger.error(f"Failed to format result as JSON: {e}")
        raise

def save_result_to_file(result: AnalysisResult, file_path: str) -> None:
    """
    Saves the AnalysisResult as a JSON file.
    Args:
        result (AnalysisResult): The analysis result object.
        file_path (str): Path to save the JSON file.
    Raises:
        IOError: If the file cannot be written.
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(format_result_as_json(result))
        logger.info(f"Result saved to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save result to file: {e}")
        raise

def format_human_readable_summary(result: AnalysisResult) -> str:
    """
    Generates a human-readable summary of the analysis result.
    Args:
        result (AnalysisResult): The analysis result object.
    Returns:
        str: Human-readable summary string.
    """
    try:
        summary = (
            f"\n=== Resume Analysis Summary ===\n"
            f"Matching Score: {result.matching_score}/100\n"
            f"\nMatched Skills: {', '.join(result.matched_skills) if result.matched_skills else 'None'}\n"
            f"Missing Skills: {', '.join(result.missing_skills) if result.missing_skills else 'None'}\n"
            f"\nMatched Experience: {', '.join(result.matched_experience) if result.matched_experience else 'None'}\n"
            f"Missing Experience: {', '.join(result.missing_experience) if result.missing_experience else 'None'}\n"
            f"\nSummary: {result.summary}\n"
            f"\nToken Usage: {result.cost_estimate.get('total_tokens', 'N/A')} (Cost: ${result.cost_estimate.get('usd', 'N/A')})\n"
        )
        return summary
    except Exception as e:
        logger.error(f"Failed to generate human-readable summary: {e}")
        raise 