from src.utils.email_sender import send_email

def send_email_node(state):
    """
    This is the final agent node. It now correctly retrieves the candidate's name
    from the screening_results to create a complete and accurate final status message.
    This prevents bugs in the backend log and ensures a clean data structure is
    available for the frontend.

    Args:
        state (AgentState): The current state of the graph.

    Returns:
        dict: A dictionary containing the final status of the operation.
    """
    print("---NODE: SENDING FINAL STRUCTURED EMAIL---")

    drafted_email_data = state.get("drafted_email", {})
    screening_results = state.get("screening_results", {})
    
    candidate_email = screening_results.get("candidateEmail")
 
    candidate_name = screening_results.get("candidateName")

    email_subject = drafted_email_data.get("subject", "Update on your application")
    email_body = drafted_email_data.get("body", "")

    if not email_body or not candidate_email or candidate_email == "N/A":
        print("---STATUS: Missing email content or recipient. Skipping email send.---")
        return {"final_status": "Error: Missing critical data, email not sent."}

    try:
        send_email(
            to_address=candidate_email,
            subject=email_subject,
            body_html=email_body
        )
        final_status = f"Success: Email sent to {candidate_name} at {candidate_email}."
        print(f"---STATUS: {final_status}---")

    except Exception as e:
        final_status = f"Error: Failed to send email to {candidate_name}. Details: {e}"
        print(f"---STATUS: {final_status}---")

    return {"final_status": final_status}

