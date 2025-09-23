from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from src.utils.helpers import clean_and_parse_json # We'll use our helper again!

def draft_email_node(state):
    """
    This agent node drafts a professional interview invitation email and returns
    it as a structured JSON object with separate 'subject' and 'body' fields.
    """
    print("---NODE: DRAFTING STRUCTURED CANDIDATE EMAIL---")

    screening_results = state.get("screening_results", {})
    job_description = state.get("job_description", "")
    
    candidate_name = screening_results.get("candidateName", "Candidate")
    summary = screening_results.get("summary", "No summary available.")

    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.7)

    
    prompt_template = """
    You are a senior recruitment coordinator. Your task is to generate the content for a professional interview invitation email.

    **CRITICAL INSTRUCTIONS:**
    1.  First, analyze the provided Job Description to identify the official **Job Title** and **Company Name**.
    2.  You MUST return a single, valid JSON object. Do not add any text before or after the JSON.
    3.  The JSON object must have exactly two keys: "subject" and "body".
    4.  **"subject" key:** The value must be a professional subject line in the format: "Invitation to Interview for [Extracted Job Title] at [Extracted Company Name]".
    5.  **"body" key:** The value must be the full, professionally formatted HTML body of the email. It should welcome the candidate, reference their impressive background from the summary, clearly state the invitation for a 30-45 minute interview, ask for their availability, and sign off with "The [Extracted Company Name] Hiring Team".

    **Candidate's AI Summary:**
    "{summary}"

    **Full Job Description:**
    ---
    {job_description}
    ---

    **JSON Output:**
    """

    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = prompt | llm

    response = chain.invoke({
        "candidate_name": candidate_name,
        "summary": summary,
        "job_description": job_description
    })

    email_data = clean_and_parse_json(response.content)

    if not email_data or "subject" not in email_data or "body" not in email_data:
        print("ERROR: AI failed to generate valid email JSON. Using fallback.")
        return {"drafted_email": {"subject": "Update on your application", "body": "There was an error generating the email content."}}

    return {"drafted_email": email_data}

