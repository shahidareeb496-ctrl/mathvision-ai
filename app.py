from flask import Flask, render_template, request, redirect, session, jsonify
from groq import Groq
import base64
import json
import os
import re
import requests
from datetime import date, datetime
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()
app = Flask(__name__)
app.secret_key = "mathvision-study-planner-secret-key-2026"


def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured")
    return Groq(api_key=api_key)


def ai_generate(prompt, temperature=0.7, image_bytes=None, filename=None):
    if image_bytes:
        try:
            client = get_groq_client()
            encoded = base64.b64encode(image_bytes).decode("ascii")
            payload = [{"type": "text", "text": prompt}]
            payload.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{encoded}"
                }
            })
            response = client.chat.completions.create(
                model="qwen/qwen3.6-27b",
                messages=[{"role": "user", "content": payload}],
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception:
            pass

    client = get_groq_client()
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature
    )
    return response.choices[0].message.content

def ai_json(prompt, temperature=0.7):
    text = ai_generate(prompt, temperature).strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if match:
            return json.loads(match.group(0))
        raise

def generate_schedule(name, exam_date, subjects_data):
    subjects_text = "\n".join([f"- {s['name']}: {s['topics']}" for s in subjects_data])
    prompt = f"""Create a day-by-day study schedule for a Matric (9th/10th grade) student named {name}, preparing for exams on {exam_date}.

Subjects and topics to cover:
{subjects_text}

Create a realistic daily plan starting from today, spreading topics across the available days before the exam date, mixing subjects sensibly, with lighter review days near the end.

Respond ONLY as JSON, no other text, in this exact format:
{{"days": [
    {{"day_label": "Day 1", "tasks": [
        {{"subject": "Math", "topic": "Quadratic Equations", "task": "Review formula and solve 10 practice problems"}}
    ]}}
]}}"""
    return ai_json(prompt)["days"]

def get_progress_by_subject(schedule, completed):
    totals = {}
    for d_idx, day in enumerate(schedule):
        for t_idx, task in enumerate(day["tasks"]):
            subj = task["subject"]
            totals.setdefault(subj, {"done": 0, "total": 0})
            totals[subj]["total"] += 1
            if completed.get(f"{d_idx}-{t_idx}"):
                totals[subj]["done"] += 1
    return totals

def get_current_day_index():
    start = session.get("start_date")
    if not start:
        return 0
    start_d = datetime.strptime(start, "%Y-%m-%d").date()
    return (date.today() - start_d).days

@app.route("/api/generate-schedule", methods=["POST"])
def api_generate_schedule():
    data = request.json
    name = data.get("name", "Student")
    exam_date = data.get("exam_date")
    subjects_data = data.get("subjects", [])

    schedule = generate_schedule(name, exam_date, subjects_data)
    session["name"] = name
    session["exam_date"] = exam_date
    session["schedule"] = schedule
    session["completed"] = {}
    session["start_date"] = date.today().isoformat()

    return jsonify({
        "name": name,
        "exam_date": exam_date,
        "schedule": schedule,
        "completed": {},
        "progress": get_progress_by_subject(schedule, {})
    })

@app.route("/api/plan", methods=["GET"])
def api_plan():
    if "schedule" not in session:
        return jsonify({"error": "No plan found"}), 404
    schedule = session["schedule"]
    completed = session.get("completed", {})
    return jsonify({
        "name": session["name"],
        "exam_date": session["exam_date"],
        "schedule": schedule,
        "completed": completed,
        "progress": get_progress_by_subject(schedule, completed),
        "current_day": get_current_day_index()
    })

@app.route("/api/toggle/<int:day_idx>/<int:task_idx>", methods=["POST"])
def api_toggle(day_idx, task_idx):
    completed = session.get("completed", {})
    key = f"{day_idx}-{task_idx}"
    completed[key] = not completed.get(key, False)
    session["completed"] = completed
    return jsonify({"completed": completed, "progress": get_progress_by_subject(session["schedule"], completed)})

@app.route("/api/priority", methods=["GET"])
def api_priority():
    if "schedule" not in session: return jsonify({"error": "No plan"}), 404
    schedule = session["schedule"]
    current_day = get_current_day_index()
    current_day = min(current_day, len(schedule) - 1) if schedule else 0
    today_tasks = schedule[current_day]["tasks"] if schedule else []

    tasks_text = "\n".join([f"- {t['subject']}: {t['topic']} — {t['task']}" for t in today_tasks])
    prompt = f"A Matric student has these tasks for today: {tasks_text}. If they only have time for ONE, what should they prioritize? 2-3 short sentences."
    priority_msg = ai_generate(prompt)
    return jsonify({"priority_message": priority_msg})

@app.route("/api/coach", methods=["GET"])
def api_coach():
    if "schedule" not in session: return jsonify({"error": "No plan"}), 404
    schedule = session["schedule"]
    completed = session.get("completed", {})
    progress = get_progress_by_subject(schedule, completed)
    total_done = sum(p["done"] for p in progress.values())
    total_tasks = sum(p["total"] for p in progress.values())

    prompt = f"Coach Matric student {session['name']}. Progress: {total_done}/{total_tasks}. Short encouraging check-in (2-3 sentences)."
    coach_msg = ai_generate(prompt)
    return jsonify({"coach_message": coach_msg})

@app.route("/api/catchup", methods=["GET"])
def api_catchup():
    if "schedule" not in session: return jsonify({"error": "No plan"}), 404
    schedule = session["schedule"]
    completed = session.get("completed", {})
    current_day = get_current_day_index()

    missed_tasks = []
    for d_idx in range(min(current_day, len(schedule))):
        for t_idx, task in enumerate(schedule[d_idx]["tasks"]):
            if not completed.get(f"{d_idx}-{t_idx}"):
                missed_tasks.append(task)

    remaining_days = schedule[current_day:]
    if not missed_tasks or not remaining_days:
        return jsonify({"schedule": schedule, "message": "Nothing to catch up!"})

    missed_text = "\n".join([f"- {t['subject']}: {t['topic']} — {t['task']}" for t in missed_tasks])
    prompt = f"Missed: {missed_text}. Remaining: {json.dumps(remaining_days)}. Redistribute missed tasks into remaining days. Respond ONLY JSON."
    new_remaining = ai_json(prompt, temperature=0)["days"]
    updated_schedule = schedule[:current_day] + new_remaining
    session["schedule"] = updated_schedule
    return jsonify({"schedule": updated_schedule})

@app.route("/api/ask", methods=["POST"])
def api_ask():
    question = request.json.get("question", "")
    prompt = f"Tutor helping Matric student. Question: '{question}'. Short answer under 100 words."
    answer = ai_generate(prompt)
    return jsonify({"answer": answer})

@app.route("/api/vision-chat", methods=["POST"])
def api_vision_chat():
    data = request.json
    image_base64 = data.get("image_base64")
    question = data.get("question", "")

    image_bytes = None
    if image_base64:
        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception:
            return jsonify({"error": "Invalid image encoding"}), 400

    prompt = f"Act as a patient study tutor for a Matric student. Explain or answer questions about the content: '{question}'."

    try:
        if image_bytes:
            # Re-using ai_generate logic but explicitly calling the vision model if bytes present
            answer = ai_generate(prompt, image_bytes=image_bytes)
        else:
            answer = ai_generate(prompt)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.json
    message = data.get("message", "")
    image_base64 = data.get("image_base64")
    history = data.get("history", []) # Array of {role, content}

    # System context from session
    schedule = session.get("schedule", [])
    completed = session.get("completed", {})
    name = session.get("name", "Student")

    system_prompt = f"You are a friendly, encouraging AI study tutor and planner for a Matric student named {name}. "
    if schedule:
        system_prompt += f"Their current study plan is: {json.dumps(schedule)}. "
        system_prompt += f"Completed tasks: {json.dumps(completed)}. "
    system_prompt += "Help them with doubts, priorities, motivation, or planning. Keep responses concise and practical."

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)

    if not message and not image_base64:
        return jsonify({"error": "No message or image provided"}), 400

    image_bytes = None
    if image_base64:
        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception:
            return jsonify({"error": "Invalid image encoding"}), 400

    try:
        client = get_groq_client()
        if image_bytes:
            encoded = base64.b64encode(image_bytes).decode("ascii")
            content = [{"type": "text", "text": message}] if message else []
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{encoded}"}
            })
            # Multimodal messages should have a specific structure
            # We replace the last user message or add a new one with image
            messages.append({"role": "user", "content": content})
            response = client.chat.completions.create(
                model="qwen/qwen3.6-27b",
                messages=messages,
                temperature=0.7
            )
        else:
            if message:
                messages.append({"role": "user", "content": message})
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                temperature=0.7
            )

        answer = response.choices[0].message.content
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/compare-answer", methods=["POST"])
def api_compare_answer():
    data = request.json
    student_image_base64 = data.get("student_image_base64")
    topper_image_base64 = data.get("topper_image_base64") # Or topper_id if server-side
    subject = data.get("subject", "")
    topic = data.get("topic", "")

    if not student_image_base64 or not topper_image_base64:
        return jsonify({"error": "Missing student or topper image"}), 400

    try:
        client = get_groq_client()
        content = [{
            "type": "text",
            "text": f"Compare this student answer with the topper reference for {subject} - {topic}. Identify differences in structure, completeness, clarity, and presentation. Give specific, actionable improvement suggestions."
        }]

        # Add student image
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{student_image_base64}"}
        })

        # Add topper image
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{topper_image_base64}"}
        })

        response = client.chat.completions.create(
            model="qwen/qwen3.6-27b",
            messages=[{"role": "user", "content": content}],
            temperature=0.7
        )

        answer = response.choices[0].message.content
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/syllabus-lookup", methods=["POST"])
def api_syllabus_lookup():
    data = request.json
    class_level = data.get("class_level", "10th")
    subject = data.get("subject", "")
    chapter = data.get("chapter", "")

    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return jsonify({"error": "TAVILY_API_KEY not configured"}), 500

    query = f"current Punjab Board PCTB textbook syllabus topics for {class_level} {subject} chapter {chapter}"

    try:
        # Call Tavily API
        tavily_url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": True
        }
        t_response = requests.post(tavily_url, json=payload)
        t_data = t_response.json()

        search_context = t_data.get("answer", "")
        if not search_context:
            search_context = "\n".join([r.get("content", "") for r in t_data.get("results", [])])

        # Summarize with GPT
        prompt = f"""Based on these search results about the syllabus for {class_level} {subject} - {chapter}:
{search_context}

Provide a concise summary of the key topics, subtopics, and any important formulas or concepts covered in this chapter.
Format it as a clean list of topics separated by commas or newlines, suitable for study planning."""

        summary = ai_generate(prompt)
        return jsonify({"topics": summary})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form.get("name", "Student")
        exam_date = request.form.get("exam_date")
        subject_names = request.form.getlist("subject_name")
        subject_topics = request.form.getlist("subject_topics")
        subjects_data = [{"name": n, "topics": t} for n, t in zip(subject_names, subject_topics) if n.strip()]

        schedule = generate_schedule(name, exam_date, subjects_data)
        session["name"] = name
        session["exam_date"] = exam_date
        session["schedule"] = schedule
        session["completed"] = {}
        session["start_date"] = date.today().isoformat()
        return redirect("/plan")

    return render_template("form.html")

@app.route("/plan")
def plan():
    if "schedule" not in session:
        return redirect("/")
    schedule = session["schedule"]
    completed = session.get("completed", {})
    progress = get_progress_by_subject(schedule, completed)
    current_day = get_current_day_index()
    return render_template("plan.html", name=session["name"], exam_date=session["exam_date"],
                            schedule=schedule, completed=completed, progress=progress,
                            current_day=current_day, tutor_answer=None, priority_msg=None, coach_msg=None)

@app.route("/toggle/<int:day_idx>/<int:task_idx>")
def toggle(day_idx, task_idx):
    completed = session.get("completed", {})
    key = f"{day_idx}-{task_idx}"
    completed[key] = not completed.get(key, False)
    session["completed"] = completed
    return redirect("/plan")

@app.route("/coach")
def coach():
    schedule = session["schedule"]
    completed = session.get("completed", {})
    progress = get_progress_by_subject(schedule, completed)
    current_day = get_current_day_index()
    total_done = sum(p["done"] for p in progress.values())
    total_tasks = sum(p["total"] for p in progress.values())
    days_left = max(len(schedule) - current_day, 0)

    prompt = f"""You are an encouraging study coach for a Matric student named {session['name']}.
They have completed {total_done} out of {total_tasks} total study tasks so far, with about {days_left} days left until their exam.
Write a short, warm, genuinely personalized check-in message (2-3 sentences) — celebrate real progress if they're doing well, or gently motivate without guilt if they're behind. Do not be generic. Under 60 words."""
    coach_msg = ai_generate(prompt)

    return render_template("plan.html", name=session["name"], exam_date=session["exam_date"],
                            schedule=schedule, completed=completed, progress=progress,
                            current_day=current_day, tutor_answer=None, priority_msg=None, coach_msg=coach_msg)

@app.route("/priority")
def priority():
    schedule = session["schedule"]
    completed = session.get("completed", {})
    current_day = get_current_day_index()
    current_day = min(current_day, len(schedule) - 1) if schedule else 0
    today_tasks = schedule[current_day]["tasks"] if schedule else []
    days_left = max(len(schedule) - current_day, 0)

    tasks_text = "\n".join([f"- {t['subject']}: {t['topic']} — {t['task']}" for t in today_tasks])
    prompt = f"""A Matric student has these study tasks planned for today, with {days_left} days left until their exam:
{tasks_text}

If they only have time for ONE thing today, which single task should they prioritize and why? Answer in 2-3 short sentences, practical and specific."""
    priority_msg = ai_generate(prompt)

    progress = get_progress_by_subject(schedule, completed)
    return render_template("plan.html", name=session["name"], exam_date=session["exam_date"],
                            schedule=schedule, completed=completed, progress=progress,
                            current_day=current_day, tutor_answer=None, priority_msg=priority_msg, coach_msg=None)

@app.route("/catchup")
def catchup():
    schedule = session["schedule"]
    completed = session.get("completed", {})
    current_day = get_current_day_index()

    missed_tasks = []
    for d_idx in range(min(current_day, len(schedule))):
        for t_idx, task in enumerate(schedule[d_idx]["tasks"]):
            if not completed.get(f"{d_idx}-{t_idx}"):
                missed_tasks.append(task)

    remaining_days = schedule[current_day:]
    if not missed_tasks or not remaining_days:
        return redirect("/plan")

    missed_text = "\n".join([f"- {t['subject']}: {t['topic']} — {t['task']}" for t in missed_tasks])
    remaining_text = json.dumps(remaining_days)

    prompt = f"""A student fell behind on these study tasks:
{missed_text}

Here is their existing remaining schedule (JSON): {remaining_text}

Redistribute the missed tasks sensibly into the remaining days, alongside the existing tasks, without overloading any single day too much. Keep day_label values the same as given.

Respond ONLY as JSON, no other text, in this exact format:
{{"days": [{{"day_label": "...", "tasks": [{{"subject": "...", "topic": "...", "task": "..."}}]}}]}}"""
    new_remaining = ai_json(prompt, temperature=0)["days"]

    updated_schedule = schedule[:current_day] + new_remaining
    session["schedule"] = updated_schedule
    return redirect("/plan")

@app.route("/ask", methods=["POST"])
def ask():
    question = request.form.get("question", "")
    prompt = f"You are a friendly, encouraging study tutor helping a Matric student. They asked: '{question}'. Answer clearly and simply, under 100 words."
    try:
        answer = ai_generate(prompt)
    except Exception:
        answer = "I’m unable to answer right now, but you can still upload a photo and I’ll help explain it once the AI service is available."
    schedule = session.get("schedule", [])
    completed = session.get("completed", {})
    progress = get_progress_by_subject(schedule, completed)
    current_day = get_current_day_index()
    return render_template("plan.html", name=session.get("name"), exam_date=session.get("exam_date"),
                            schedule=schedule, completed=completed, progress=progress,
                            current_day=current_day, tutor_answer=answer, priority_msg=None, coach_msg=None,
                            photo_answer=None)

@app.route("/ask-photo", methods=["POST"])
def ask_photo():
    question = request.form.get("question", "")
    image_file = request.files.get("image")

    if image_file and image_file.filename:
        filename = secure_filename(image_file.filename)
        image_bytes = image_file.read()
        image_text = f"[User uploaded image: {filename}, size={len(image_bytes)} bytes]"
    else:
        image_text = "[No image uploaded]"

    prompt = f"""You are a supportive study tutor. A student uploaded a photo of a math or science solution and asked: '{question}'.
The image reference is: {image_text}.
Explain the work in a clear, step-by-step way as if you are teaching the student. If the image shows a worked solution, describe the method, the spaces, and the reasoning in a simple, encouraging way. Keep it under 180 words and mention the key steps clearly."""
    try:
        photo_answer = ai_generate(prompt, image_bytes=image_bytes if image_file and image_file.filename else None, filename=filename if image_file and image_file.filename else None)
    except Exception:
        photo_answer = "I can help explain your photo, but the AI service is not available right now. Please try again shortly."

    schedule = session.get("schedule", [])
    completed = session.get("completed", {})
    progress = get_progress_by_subject(schedule, completed)
    current_day = get_current_day_index()
    return render_template("plan.html", name=session.get("name"), exam_date=session.get("exam_date"),
                            schedule=schedule, completed=completed, progress=progress,
                            current_day=current_day, tutor_answer=None, priority_msg=None, coach_msg=None,
                            photo_answer=photo_answer)

@app.route("/reset")
def reset():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")