from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from src.utils.helpers import clean_and_parse_json

def draft_rejection_node(state):
    """
    This agent node drafts a polite and professional rejection email for
    candidates who did not meet the minimum score.

    Args:
        state (AgentState): The current state of the graph.

    Returns:
        dict: A dictionary containing the structured rejection email
              (subject and body) to be added to the state.
    """
    print("---NODE: DRAFTING REJECTION EMAIL---")

    screening_results = state.get("screening_results", {})
    job_description = state.get("job_description", "")
    
    candidate_name = screening_results.get("candidateName", "Candidate")

    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.6)

    prompt_template = """
    You are a senior recruitment coordinator. Your task is to draft a polite, respectful, and professional rejection email.

    **CRITICAL INSTRUCTIONS:**
    1.  Analyze the Job Description to identify the **Job Title** and **Company Name**.
    2.  You MUST return a single, valid JSON object with two keys: "subject" and "body".
    3.  **"subject" key:** Format is "Update on Your Application for [Extracted Job Title] at [Extracted Company Name]".
    4.  **"body" key:** The email body must be empathetic and professional. It should:
        - Thank the candidate ({candidate_name}) for their interest.
        - State that while their profile is impressive, the team has decided to move forward with other candidates whose experience more closely matches the current requirements.
        - Encourage them to apply for future roles.
        - Wish them the best in their job search.
        - Sign off as "The [Extracted Company Name] Hiring Team".

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
        "job_description": job_description
    })

    email_data = clean_and_parse_json(response.content)

    if not email_data or "subject" not in email_data or "body" not in email_data:
        return {"drafted_email": {"subject": "Update on your application", "body": "Thank you for your interest. We have decided to move forward with other candidates at this time."}}

    return {"drafted_email": email_data}
