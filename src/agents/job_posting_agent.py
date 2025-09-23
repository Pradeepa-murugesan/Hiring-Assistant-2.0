from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

def generate_jd_from_notes(notes: str) -> str:
    """
    Uses an LLM to expand brief notes into a full, professional job description
    with clean formatting, suitable for direct use without markdown.

    Args:
        notes: Raw text notes from the user about the job requirements.

    Returns:
        A well-formatted and clean job description string.
    """
    print("---AGENT: GENERATING CLEANLY FORMATTED JOB DESCRIPTION---")

    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.5)

    prompt_template = """
    You are an expert HR copywriter for a top technology company.
    Your mission is to take the following rough notes and transform them into a complete, professional, and engaging job description.

    **CRITICAL FORMATTING INSTRUCTIONS:**
    1.  **NO MARKDOWN:** Do NOT use any markdown characters like '#' or '**'. The output must be clean, plain text.
    2.  **STRUCTURE:** Create clear sections with titles in ALL CAPS followed by a new line. The required sections are: JOB TITLE, JOB SUMMARY, KEY RESPONSIBILITIES, and REQUIRED QUALIFICATIONS.
    3.  **BULLET POINTS:** Use a hyphen (-) followed by a space for bullet points under the "KEY RESPONSIBILITIES" and "REQUIRED QUALIFICATIONS" sections.
    4.  **SPACING:** Use a double line break to create clear visual separation between each section.
    5.  **TONE:** Adopt a professional and welcoming tone that will attract top talent. Intelligently elaborate on the provided notes.

    **EXAMPLE OUTPUT FORMAT:**
    JOB TITLE
    Machine Learning Intern

    JOB SUMMARY
    We are seeking a highly motivated and talented Machine Learning Intern...

    KEY RESPONSIBILITIES
    - Assist in the design, development, and implementation...
    - Collect, clean, and prepare large datasets...

    REQUIRED QUALIFICATIONS
    - Currently pursuing a Bachelor's or Master's degree...
    - Strong understanding of machine learning concepts...

    **Rough Notes from Hiring Manager:**
    "{notes}"

    **Generated Job Description (MUST follow the format above):**
    """
    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = prompt | llm
    response = chain.invoke({"notes": notes})
    return response.content

