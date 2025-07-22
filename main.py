"""
main.py

Entry point for the AI Resume System. Provides a simple CLI for HR users.
Accepts file paths for job description and resume, processes them, analyzes with LLM, and outputs results.
"""

import argparse
import logging
from resume_parser import parse_input, InputValidationError
from llm_orchestrator import analyze_resume, AnalysisResult
from output_formatter import format_result_as_json, save_result_to_file, format_human_readable_summary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description="AI Resume System: Analyze a candidate's resume against a job description using OpenAI LLM."
    )
    parser.add_argument('--job', required=True, help='Path to the job description file (PDF, DOCX, or TXT)')
    parser.add_argument('--resume', required=True, help='Path to the candidate resume file (PDF, DOCX, or TXT)')
    parser.add_argument('--output', required=False, help='Path to save the output JSON file')
    args = parser.parse_args()

    try:
        logger.info("Extracting and sanitizing job description...")
        job_desc = parse_input(args.job)
        logger.info("Extracting and sanitizing candidate resume...")
        resume = parse_input(args.resume)
    except InputValidationError as e:
        logger.error(f"Input error: {e}")
        print(f"Input error: {e}")
        return
    except Exception as e:
        logger.error(f"Unexpected error during input parsing: {e}")
        print(f"Unexpected error: {e}")
        return

    try:
        logger.info("Analyzing resume against job description using LLM...")
        result: AnalysisResult = analyze_resume(job_desc, resume)
    except Exception as e:
        logger.error(f"LLM analysis error: {e}")
        print(f"LLM analysis error: {e}")
        return

    print(format_human_readable_summary(result))
    print("\nFull JSON Output:\n")
    print(format_result_as_json(result))

    if args.output:
        try:
            save_result_to_file(result, args.output)
        except Exception as e:
            logger.error(f"Failed to save output: {e}")
            print(f"Failed to save output: {e}")

if __name__ == "__main__":
    main() 