import os
import sys
import uuid
import smtplib
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from email.mime.text import MIMEText

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, List, Dict
import operator

project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.pdf_parser import parse_pdf_from_path
from src.agents.job_posting_agent import generate_jd_from_notes
from src.agents.resume_screening_agent import screen_resume_node
from src.agents.candidate_communication_agent import draft_email_node, refine_email_with_feedback
from src.agents.rejection_email_agent import draft_rejection_node

load_dotenv()
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def send_email_node(state):
    drafted_email = state.get("drafted_email", {})
    recipient_email = state.get("screening_results", {}).get("candidateEmail")

    if not drafted_email or not recipient_email or "subject" not in drafted_email:
        return {"final_status": "Failed: Missing email subject, content, or recipient."}
    
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not all([smtp_server, smtp_port, smtp_user, smtp_password]):
        print("ERROR: Missing SMTP configuration in .env file.")
        return {"final_status": "Failed: SMTP configuration is missing."}

    try:
        msg = MIMEText(drafted_email["body"], 'html')
        msg['Subject'] = drafted_email["subject"]
        msg['From'] = smtp_user
        msg['To'] = recipient_email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            print(f"Email successfully sent to {recipient_email}")
            return {"final_status": "Email Sent Successfully"}
    except Exception as e:
        print(f"ERROR: Failed to send email. {e}")
        return {"final_status": f"Failed to send email: {e}"}

class AgentState(TypedDict):
    job_description: str
    resume_content: str
    screening_results: dict
    drafted_email: Dict[str, str]
    final_status: str
    messages: Annotated[List[str], operator.add]

workflow = StateGraph(AgentState)
workflow.add_node("resume_screener", screen_resume_node)
workflow.add_node("invitation_drafter", draft_email_node)
workflow.add_node("rejection_drafter", draft_rejection_node)
workflow.add_node("email_sender", send_email_node)
workflow.set_entry_point("resume_screener")

def route_after_screening(state):
    match_score = state.get("screening_results", {}).get("matchScore", 0)
    return "invitation_drafter" if match_score >= 70 else "rejection_drafter"

workflow.add_conditional_edges("resume_screener", route_after_screening, {"invitation_drafter": "invitation_drafter", "rejection_drafter": "rejection_drafter"})
workflow.add_edge('invitation_drafter', 'email_sender')
workflow.add_edge('rejection_drafter', 'email_sender')
workflow.add_edge('email_sender', END)

checkpointer = MemorySaver()
recruitment_graph = workflow.compile(checkpointer=checkpointer, interrupt_before=["email_sender"])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_jd', methods=['POST'])
def generate_jd():
    data = request.get_json()
    notes = data.get('notes')
    if not notes:
        return jsonify({"error": "No notes were provided."}), 400
    try:
        generated_jd = generate_jd_from_notes(notes)
        return jsonify({"job_description": generated_jd})
    except Exception as e:
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/process', methods=['POST'])
def process():
    job_description_text = request.form.get('job_description_text')
    resume_files = request.files.getlist('resumes')
    if not job_description_text or not resume_files:
        return jsonify({"error": "Missing job description or resumes."}), 400
    all_results = []
    for resume_file in resume_files:
        if not resume_file.filename: continue
        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{resume_file.filename}")
        resume_file.save(resume_path)
        try:
            resume_text = parse_pdf_from_path(resume_path)
            thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}
            initial_state = {"job_description": job_description_text, "resume_content": resume_text}
            final_state = recruitment_graph.invoke(initial_state, config)
            is_paused = "final_status" not in final_state
            all_results.append({"filename": resume_file.filename, "thread_id": thread_id, "is_paused": is_paused, "state": final_state})
        except Exception as e:
            all_results.append({"filename": resume_file.filename, "error": str(e)})
        finally:
            os.remove(resume_path)
    return jsonify(all_results)

@app.route("/resume", methods=["POST"])
def resume_workflow():
    data = request.get_json()
    thread_id = data.get('thread_id')
    decision = data.get('decision')
    if not thread_id or not decision:
        return jsonify({"error": "thread_id and decision are required"}), 400
    config = {"configurable": {"thread_id": thread_id}}

    if decision == "approve":
        try:
            final_state = recruitment_graph.invoke(None, config)
            return jsonify({"filename": "N/A", "thread_id": thread_id, "is_paused": False, "state": final_state})
        except Exception as e:
            return jsonify({"error": f"Failed to resume workflow: {e}"}), 500

    elif decision == "refine":
        feedback = data.get("feedback")
        if not feedback: return jsonify({"error": "Feedback is required"}), 400
        try:
            current_state = recruitment_graph.get_state(config).values
            refined_body = refine_email_with_feedback(current_state['drafted_email']['body'], feedback)
            current_state['drafted_email']['body'] = refined_body
            recruitment_graph.update_state(config, current_state)
            return jsonify({"filename": "N/A", "thread_id": thread_id, "is_paused": True, "state": current_state})
        except Exception as e:
            return jsonify({"error": f"Failed to refine email: {e}"}), 500

    elif decision == "reject":
        state_values = recruitment_graph.get_state(config).values if recruitment_graph.get_state(config) else {}
        state_values['final_status'] = "Process Rejected by User"
        return jsonify({"filename": "N/A", "thread_id": thread_id, "is_paused": False, "state": state_values})

    elif decision == "manual_edit_and_send":
        edited_email_body = data.get("edited_email")
        if not edited_email_body: return jsonify({"error": "Edited email is required"}), 400
        
      
        current_state = recruitment_graph.get_state(config).values
        
        current_state['drafted_email']['body'] = edited_email_body
        
        recruitment_graph.update_state(config, current_state)
        
        final_state = recruitment_graph.invoke(None, config)
        return jsonify({"filename": "N/A", "thread_id": thread_id, "is_paused": False, "state": final_state})
    else:
        return jsonify({"error": "Invalid decision"}), 400

if __name__ == '__main__':
    app.run(port=5001, debug=True)

