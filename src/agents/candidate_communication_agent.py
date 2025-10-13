import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from src.utils.helpers import clean_and_parse_json

try:
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.1)
except ImportError:
    print("langchain_groq is not installed. Please install it with 'pip install langchain-groq'")
    llm = None
except Exception as e:
    print(f"Could not initialize ChatGroq. Please check your GROQ_API_KEY. Error: {e}")
    llm = None


draft_prompt_template = ChatPromptTemplate.from_template(
    """
    You are a senior recruitment coordinator. Your task is to generate the content for a professional interview invitation email.

    **CRITICAL INSTRUCTIONS:**
    1.  First, analyze the provided Job Description to identify the official **Job Title** and **Company Name**.
    2.  You MUST return a single, valid JSON object. Do not add any text before or after the JSON.
    3.  The JSON object must have exactly two keys: "subject" and "body".
    4.  **"subject" key:** The value must be a professional subject line in the format: "Invitation to Interview for [Extracted Job Title] at [Extracted Company Name]".
    5.  **"body" key:** The value must be the full, professionally formatted email body. It should welcome the candidate by name, reference their impressive background from the summary, clearly state the invitation for a 30-45 minute interview, ask for their availability, and sign off with "The [Extracted Company Name] Hiring Team".

    **Candidate Name:** {candidate_name}
    **Candidate's AI Summary:**
    "{summary}"

    **Full Job Description:**
    ---
    {job_description}
    ---

    **JSON Output:**
    """
)

def draft_email_node(state):
    """
    This agent node drafts a professional interview invitation email and returns
    it as a structured JSON object with separate 'subject' and 'body' fields.
    """
    print("---NODE: DRAFTING STRUCTURED CANDIDATE EMAIL---")
    if not llm:
        print("ERROR: LLM not initialized. Using fallback.")
        return {"drafted_email": {"subject": "Update on your application", "body": "There was an error generating the email content due to LLM initialization failure."}}

    screening_results = state.get("screening_results", {})
    job_description = state.get("job_description", "")
    candidate_name = screening_results.get("candidateName", "Candidate")
    summary = screening_results.get("summary", "No summary available.")
    
    chain = draft_prompt_template | llm
    
    try:
        response = chain.invoke({
            "candidate_name": candidate_name,
            "summary": summary,
            "job_description": job_description
        })
        email_data = clean_and_parse_json(response.content)

        if not email_data or "subject" not in email_data or "body" not in email_data:
            raise ValueError("AI failed to generate valid email JSON.")

        return {"drafted_email": email_data}

    except Exception as e:
        print(f"ERROR: Could not draft email. {e}. Using fallback.")
        return {"drafted_email": {"subject": "Update on your application", "body": "There was an error generating the email content."}}



refinement_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert hiring manager and a professional communication assistant. "
            "Your task is to refine and rewrite a draft email to a job candidate based on specific feedback. "
            "Maintain a professional, encouraging, and clear tone. Only output the revised email body, nothing else."
        ),
        (
            "human",
            "Please refine the following DRAFT EMAIL based on the provided FEEDBACK.\n\n"
            "FEEDBACK:\n---\n{feedback}\n---\n\n"
            "DRAFT EMAIL:\n---\n{original_email}\n---\n\n"
            "REFINED EMAIL:"
        ),
    ]
)


def refine_email_with_feedback(original_email: str, feedback: str) -> str:
    """
    Refines an email draft using the Groq LLM based on user feedback.
    """
    if not llm:
        return "ERROR: LLM not initialized. Cannot refine email. Please check your API key and dependencies."

    try:
        refinement_chain = refinement_prompt_template | llm | StrOutputParser()

        response = refinement_chain.invoke({
            "original_email": original_email,
            "feedback": feedback
        })
        print(f"Successfully refined email based on feedback: '{feedback}'")
        return response
    except Exception as e:
        print(f"An error occurred during email refinement: {e}")
        return f"An error occurred while trying to refine the email. Details: {e}"

