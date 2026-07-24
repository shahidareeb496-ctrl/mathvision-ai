from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template, request, redirect

from groq import Groq
import json
import random
import os
app = Flask(__name__)
import os
client = Groq(api_key=os.environ.get("Enter your groq key"))

CHAPTERS = {
    "complex-numbers": {
        "title": "Complex Numbers", "grade": "10th", "unit": "",
        "problem": "An electrical engineer is analyzing an AC circuit with impedance Z = 3 + 4i ohms. What is the magnitude of this impedance?",
        "formula": "z = a + bi   |   |z| = √(a² + b²)",
        "profession": "electrical engineer",
        "diagram": """<svg viewBox="0 0 200 200" style="width:100%; max-width:200px; display:block; margin:0 auto;">
            <line x1="20" y1="100" x2="180" y2="100" stroke="#888" stroke-width="2"/>
            <line x1="100" y1="180" x2="100" y2="20" stroke="#888" stroke-width="2"/>
            <line x1="100" y1="100" x2="160" y2="40" stroke="#2563eb" stroke-width="3"/>
            <circle cx="160" cy="40" r="5" fill="#f97316"/>
            <text x="165" y="35" font-size="12" fill="#333">3+4i</text>
        </svg>"""
    },
    "quadratic-equations": {
        "title": "Quadratic Equations and Inequalities", "grade": "10th", "unit": "",
        "problem": "A ball is thrown upward. Its height in meters is given by h = -5t² + 20t, where t is time in seconds. When does the ball hit the ground again?",
        "formula": "ax² + bx + c = 0   |   x = [-b ± √(b²-4ac)] ÷ 2a",
        "profession": "sports engineer",
        "diagram": """<svg viewBox="0 0 220 140" style="width:100%;">
            <line x1="20" y1="120" x2="200" y2="120" stroke="#888" stroke-width="2"/>
            <path d="M30,120 Q110,20 190,120" fill="none" stroke="#f97316" stroke-width="4"/>
            <circle cx="30" cy="120" r="4" fill="#2563eb"/>
            <circle cx="190" cy="120" r="4" fill="#2563eb"/>
            <text x="10" y="135" font-size="11" fill="#333">throw</text>
            <text x="160" y="135" font-size="11" fill="#333">lands</text>
        </svg>"""
    },
    "matrices": {
        "title": "Matrices and Determinants", "grade": "10th", "unit": "",
        "problem": "A graphics engineer needs to rotate a game character's position (3, 2) by 90° using a transformation matrix. What are the new coordinates?",
        "formula": "[a b; c d] × [x, y] = [ax+by, cx+dy]   |   det = ad − bc",
        "profession": "computer graphics engineer",
        "diagram": """<svg viewBox="0 0 200 200" style="width:100%; max-width:200px; display:block; margin:0 auto;">
            <line x1="20" y1="100" x2="180" y2="100" stroke="#888" stroke-width="2"/>
            <line x1="100" y1="180" x2="100" y2="20" stroke="#888" stroke-width="2"/>
            <circle cx="150" cy="70" r="5" fill="#2563eb"/>
            <circle cx="70" cy="50" r="5" fill="#f97316"/>
            <path d="M150,70 A60,60 0 0,1 70,50" fill="none" stroke="#7c3aed" stroke-width="2" stroke-dasharray="4,4"/>
        </svg>"""
    },
    "functions-graphs": {
        "title": "Functions and Graphs", "grade": "10th", "unit": "",
        "problem": "A company's monthly revenue is modeled as R(x) = 500x + 2000, where x is the number of products sold. How much revenue is made from selling 150 products?",
        "formula": "y = f(x)",
        "profession": "business analyst",
        "diagram": """<svg viewBox="0 0 220 140" style="width:100%;">
            <line x1="20" y1="120" x2="200" y2="120" stroke="#888" stroke-width="2"/>
            <line x1="20" y1="120" x2="20" y2="20" stroke="#888" stroke-width="2"/>
            <line x1="20" y1="110" x2="190" y2="30" stroke="#2563eb" stroke-width="4"/>
        </svg>"""
    },
    "algebraic-fractions": {
        "title": "Algebraic Fractions", "grade": "10th", "unit": "",
        "problem": "Two workers can complete a job alone in 4 hours and 6 hours respectively. Working together, how long will it take them to finish the job?",
        "formula": "1/a + 1/b = 1/t",
        "profession": "mechanical engineer",
        "diagram": """<svg viewBox="0 0 220 100" style="width:100%;">
            <rect x="20" y="30" width="70" height="30" fill="#2563eb" rx="6"/>
            <rect x="110" y="30" width="90" height="30" fill="#f97316" rx="6"/>
            <text x="35" y="50" font-size="12" fill="white">4 hrs</text>
            <text x="140" y="50" font-size="12" fill="white">6 hrs</text>
        </svg>"""
    },
    "vectors": {
        "title": "Vectors in Plane", "grade": "10th", "unit": "",
        "problem": "A ship sails 30 km east then 40 km north. Using vectors, what is the ship's straight-line displacement from its starting point?",
        "formula": "|v| = √(x² + y²)",
        "profession": "game developer",
        "diagram": """<svg viewBox="0 0 220 180" style="width:100%;">
            <line x1="20" y1="160" x2="200" y2="160" stroke="#888" stroke-width="2"/>
            <line x1="20" y1="160" x2="20" y2="20" stroke="#888" stroke-width="2"/>
            <line x1="20" y1="160" x2="150" y2="160" stroke="#2563eb" stroke-width="4"/>
            <line x1="150" y1="160" x2="150" y2="50" stroke="#2563eb" stroke-width="4"/>
            <line x1="20" y1="160" x2="150" y2="50" stroke="#f97316" stroke-width="3" stroke-dasharray="5,5"/>
        </svg>"""
    },
    "trigonometry": {
        "title": "Trigonometry", "grade": "10th", "unit": "",
        "problem": "A surveyor stands 50 meters from a building and measures the angle to the top as 30°. How tall is the building?",
        "formula": "tan(θ) = Opposite ÷ Adjacent",
        "profession": "surveyor",
        "diagram": """<svg viewBox="0 0 300 220" style="width:100%;">
            <line x1="40" y1="200" x2="40" y2="40" stroke="#2563eb" stroke-width="4"/>
            <line x1="40" y1="200" x2="220" y2="200" stroke="#2563eb" stroke-width="4"/>
            <line x1="40" y1="40" x2="220" y2="200" stroke="#f97316" stroke-width="4"/>
            <text x="10" y="120" font-size="16" fill="#333">h = ?</text>
            <text x="110" y="220" font-size="16" fill="#333">50 m</text>
            <text x="150" y="150" font-size="14" fill="#f97316">30°</text>
        </svg>"""
    },
    "chords-arcs": {
        "title": "Chords and Arcs of a Circle", "grade": "10th", "unit": "",
        "problem": "A civil engineer is designing a circular road curve. If a chord of the curve is 24 meters long and the radius is 20 meters, what is the perpendicular distance from the center to the chord?",
        "formula": "d = √(r² − (c/2)²)",
        "profession": "road engineer",
        "diagram": """<svg viewBox="0 0 200 200" style="width:100%; max-width:180px; display:block; margin:0 auto;">
            <circle cx="100" cy="100" r="80" fill="none" stroke="#888" stroke-width="2"/>
            <line x1="40" y1="130" x2="160" y2="130" stroke="#2563eb" stroke-width="4"/>
            <line x1="100" y1="100" x2="100" y2="130" stroke="#f97316" stroke-width="3" stroke-dasharray="4,4"/>
        </svg>"""
    },
    "tangent-angles": {
        "title": "Tangent and Angles of a Circle", "grade": "10th", "unit": "",
        "problem": "A mechanical engineer is designing two connected gears. If a tangent line touches a gear at one point, what is the angle between the tangent and the radius at that point?",
        "formula": "Tangent ⊥ Radius (angle = 90°)",
        "profession": "mechanical engineer",
        "diagram": """<svg viewBox="0 0 200 200" style="width:100%; max-width:180px; display:block; margin:0 auto;">
            <circle cx="100" cy="100" r="60" fill="none" stroke="#888" stroke-width="2"/>
            <line x1="100" y1="100" x2="160" y2="100" stroke="#f97316" stroke-width="3"/>
            <line x1="160" y1="60" x2="160" y2="140" stroke="#2563eb" stroke-width="4"/>
        </svg>"""
    },
    "practical-geometry": {
        "title": "Practical Geometry of Circles", "grade": "10th", "unit": "",
        "problem": "A civil engineer needs to construct a circular roundabout using only a compass and straightedge, given three fixed boundary points. How can the center of the circle be found?",
        "formula": "Center = intersection of perpendicular bisectors",
        "profession": "civil engineer",
        "diagram": """<svg viewBox="0 0 200 200" style="width:100%; max-width:180px; display:block; margin:0 auto;">
            <circle cx="100" cy="100" r="4" fill="#f97316"/>
            <circle cx="60" cy="150" r="4" fill="#2563eb"/>
            <circle cx="150" cy="140" r="4" fill="#2563eb"/>
            <circle cx="120" cy="50" r="4" fill="#2563eb"/>
            <circle cx="100" cy="100" r="70" fill="none" stroke="#888" stroke-dasharray="4,4"/>
        </svg>"""
    },
    "information-handling": {
        "title": "Information Handling", "grade": "10th", "unit": "",
        "problem": "A student scored 65, 70, 80, 85, and 90 on five tests. What is the average score, and how spread out are the scores?",
        "formula": "Mean = (Σx) ÷ n",
        "profession": "data analyst",
        "diagram": """<svg viewBox="0 0 220 140" style="width:100%;">
            <line x1="20" y1="120" x2="200" y2="120" stroke="#888" stroke-width="2"/>
            <rect x="30" y="80" width="20" height="40" fill="#2563eb"/>
            <rect x="60" y="60" width="20" height="60" fill="#2563eb"/>
            <rect x="90" y="40" width="20" height="80" fill="#2563eb"/>
            <rect x="120" y="30" width="20" height="90" fill="#f97316"/>
            <rect x="150" y="20" width="20" height="100" fill="#f97316"/>
        </svg>"""
    },
    "probability": {
        "title": "Probability", "grade": "10th", "unit": "",
        "problem": "A machine learning model correctly diagnoses a disease 9 out of 10 times based on its training data. What is the probability it is correct on a new patient?",
        "formula": "P(E) = favorable outcomes ÷ total outcomes",
        "profession": "machine learning engineer",
        "diagram": """<svg viewBox="0 0 200 200" style="width:100%; max-width:180px; display:block; margin:0 auto;">
            <circle cx="100" cy="100" r="80" fill="#e5e7eb" stroke="#888" stroke-width="2"/>
            <path d="M100,100 L100,20 A80,80 0 0,1 176,68 Z" fill="#2563eb"/>
            <text x="100" y="105" font-size="18" text-anchor="middle" fill="#333">90%</text>
        </svg>"""
    }
}
PERSONAS = {
    "default": "a 15-year-old student",
    "kid": "an 8-year-old, using very simple words and fun comparisons",
    "gamer": "a teenager who loves video games, using gaming analogies make correct matches with gaming",
    "football": "a teenager who loves football, using sports analogies make correct matches with football",
    "chef": "a teenager interested in cooking, using kitchen/recipe analogies make correct matches with cooking and recipes if possible",
    "mechanic": "a teenager interested in cars and mechanics, using mechanical analogies make correct matches with cars and mechanics if possible",
    "artist": "a teenager interested in art, using drawing/painting analogies make correct matches with art and drawing if possible",

} 
def ai_generate(prompt):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def get_explanation(chapter_id, lang, persona="default"):
    data = CHAPTERS[chapter_id]
    lang_instruction = "Respond entirely in Urdu." if lang == "ur" else ""
    audience = PERSONAS.get(persona,    ["default"])
    prompt = f"""You are an experienced {data['profession']}, acting as a friendly tutor for {audience}.
The student is looking at this problem: "{data['problem']}"

Explain the idea behind solving this in really simple, everyday language suited to that audience.
Include:
1. Why someone in your profession actually runs into this kind of problem in real life
2. A step-by-step walkthrough of solving THIS problem
3. One extra simple example from your work to reinforce the idea

Keep it warm, encouraging, and under 180 words. {lang_instruction}"""
    return ai_generate(prompt)

def get_derivation(chapter_id, lang):
    data = CHAPTERS[chapter_id]
    lang_instruction = "Respond entirely in Urdu." if lang == "ur" else ""
    prompt = f"""Explain, in simple terms for a 15-year-old, WHERE the formula for {data['title']} ({data['formula']}) actually comes from and WHY it works — not just that it exists.
Keep it intuitive, use a small visual or logical mental model if possible, under 130 words. {lang_instruction}"""
    return ai_generate(prompt)

def get_curiosity(chapter_id, lang):
    data = CHAPTERS[chapter_id]
    lang_instruction = "Respond entirely in Urdu." if lang == "ur" else ""
    prompt = f"""A 15-year-old just learned about {data['title']}. Answer ONE surprising, genuinely curious "but WHY does this work / why is this true" question about this topic — something that makes them go "whoa, I never thought about that." Keep it fascinating but simple, under 110 words. {lang_instruction}"""
    return ai_generate(prompt)

def get_careers(chapter_id, lang):
    data = CHAPTERS[chapter_id]
    lang_instruction = "Write it in Urdu." if lang == "ur" else "Write it in English."
    prompt = f"""List 4 different real careers/professions (not just {data['profession']}) that actually use {data['title']} in their daily work.
{lang_instruction}
Respond ONLY as JSON, no other text, in this exact format:
{{"careers": [{{"job": "...", "use": "one short sentence on how they use it"}}, ...]}}"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9
    )
    text = response.choices[0].message.content.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(text)["careers"]

def get_future_me(chapter_id, lang):
    data = CHAPTERS[chapter_id]
    lang_instruction = "Respond entirely in Urdu." if lang == "ur" else ""
    prompt = f"""Write a short, vivid, second-person scene (2-3 sentences) imagining the student at age 25 working in a career that uses {data['title']} in a meaningful, high-stakes, or exciting way. Start with "Imagine you're 25...". Keep it inspiring and concrete. {lang_instruction}"""
    return ai_generate(prompt)

def generate_quiz(chapter_id, lang):
    topic = CHAPTERS[chapter_id]["title"]
    lang_instruction = "Write it in Urdu." if lang == "ur" else "Write it in English."
    variations = [
        "Use different numbers than a typical textbook example, and make it a real-life scenario, like the student is facing it in hiswork or hobby.",
        "Make it a word problem set in a completely different real-life scenario related to this topic ask the question by making it a life scenario of student.",
        "Change the numbers and context completely from any previous version.",
        "Create a fresh scenario with new numbers — avoid repeating common examples."
    ]
    variation_instruction = random.choice(variations)
    prompt = f"""Create ONE new multiple-choice practice question about {topic}.
{variation_instruction}
{lang_instruction}
Respond ONLY as JSON, no other text, in this exact format:
{{"question": "...", "options": ["...", "...", "..."], "correct_index": 0}}"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=1.0
    )
    text = response.choices[0].message.content.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(text)

def base_render(chapter_id, lang, **overrides):
    data = CHAPTERS[chapter_id]
    context = dict(chapter=data, chapter_id=chapter_id, ai_message=None, derivation=None,
                   curiosity=None, careers=None, future_me=None,
                   tutor_answer=None, quiz_result=None, quiz=None,
                   quiz_solution=None, lang=lang, waiting_next=False)
    context.update(overrides)
    return render_template("index.html", **context)

@app.route("/")
def home():
    return render_template("home.html", chapters=CHAPTERS)

@app.route("/chapter/<chapter_id>")
def chapter(chapter_id):
    lang = request.args.get("lang", "en")
    quiz = generate_quiz(chapter_id, lang)
    return base_render(chapter_id, lang, quiz=quiz)

@app.route("/explain/<chapter_id>")
def explain(chapter_id):
    lang = request.args.get("lang", "en")
    persona = request.args.get("persona", "default")
    quiz = generate_quiz(chapter_id, lang)
    ai_message = get_explanation(chapter_id, lang, persona)
    return base_render(chapter_id, lang, quiz=quiz, ai_message=ai_message)

@app.route("/derive/<chapter_id>")
def derive(chapter_id):
    lang = request.args.get("lang", "en")
    quiz = generate_quiz(chapter_id, lang)
    derivation = get_derivation(chapter_id, lang)
    return base_render(chapter_id, lang, quiz=quiz, derivation=derivation)

@app.route("/curiosity/<chapter_id>")
def curiosity(chapter_id):
    lang = request.args.get("lang", "en")
    quiz = generate_quiz(chapter_id, lang)
    curiosity_text = get_curiosity(chapter_id, lang)
    return base_render(chapter_id, lang, quiz=quiz, curiosity=curiosity_text)

@app.route("/careers/<chapter_id>")
def careers(chapter_id):
    lang = request.args.get("lang", "en")
    quiz = generate_quiz(chapter_id, lang)
    careers_list = get_careers(chapter_id, lang)
    return base_render(chapter_id, lang, quiz=quiz, careers=careers_list)

@app.route("/future/<chapter_id>")
def future(chapter_id):
    lang = request.args.get("lang", "en")
    quiz = generate_quiz(chapter_id, lang)
    future_text = get_future_me(chapter_id, lang)
    return base_render(chapter_id, lang, quiz=quiz, future_me=future_text)

@app.route("/quiz/<chapter_id>", methods=["POST"])
def quiz_check(chapter_id):
    lang = request.args.get("lang", "en")
    selected = request.form.get("answer")
    question_text = request.form.get("question_text")
    correct = int(request.form.get("correct_index"))

    if selected is None:
        quiz = generate_quiz(chapter_id, lang)
        return base_render(chapter_id, lang, quiz=quiz, quiz_result="⚠️ Please select an answer first.")

    selected = int(selected)
    if selected == correct:
        quiz_result = "✅ Correct! Well done."
    else:
        prompt = f"""A student got this question wrong: '{question_text}'.
First, in ONE short sentence, name the specific misconception or mistake type (e.g. "You mixed up the formula for X with Y" or "You forgot to take the square root at the end").
Then briefly explain the correct reasoning in under 50 more words. {'Respond in Urdu.' if lang == 'ur' else ''}"""
        quiz_result = f"❌ {ai_generate(prompt)}"

    return base_render(chapter_id, lang, quiz_result=quiz_result, waiting_next=True)

@app.route("/solve/<chapter_id>", methods=["POST"])
def solve_quiz(chapter_id):
    lang = request.args.get("lang", "en")
    data = CHAPTERS[chapter_id]
    question_text = request.form.get("question_text")
    lang_instruction = "Respond entirely in Urdu." if lang == "ur" else ""
    prompt = f"""You are an experienced {data['profession']}, helping a 15-year-old student who is stuck on this practice question:
"{question_text}"

Structure your response in this exact format, with a blank line between each part:

Scene: (2-3 sentences putting the student INSIDE the situation, as if they are the {data['profession']} facing this right now)

Step 1: (what to notice first)

Step 2: (which formula applies and why)

Step 3: (the actual calculation, written clearly)

Answer: (the final answer, stated plainly)

Keep each part short and simple. Use actual line breaks between sections exactly as shown above. {lang_instruction}"""
    quiz_solution = ai_generate(prompt)
    quiz = {"question": question_text, "options": None, "correct_index": None}
    return base_render(chapter_id, lang, quiz=quiz, quiz_solution=quiz_solution)

@app.route("/next/<chapter_id>")
def next_quiz(chapter_id):
    lang = request.args.get("lang", "en")
    quiz = generate_quiz(chapter_id, lang)
    return base_render(chapter_id, lang, quiz=quiz)

@app.route("/ask", methods=["POST"])
def ask():
    question = request.form["question"]
    chapter_id = request.args.get("chapter_id", "trigonometry")
    lang = request.args.get("lang", "en")
    data = CHAPTERS[chapter_id]
    quiz = generate_quiz(chapter_id, lang)
    prompt = f"You are an experienced {data['profession']} tutoring a 15-year-old about {data['title']}. They asked: '{question}'. Answer simply, under 80 words. {'Respond in Urdu.' if lang == 'ur' else ''}"
    tutor_answer = ai_generate(prompt)
    return base_render(chapter_id, lang, quiz=quiz, tutor_answer=tutor_answer)

if __name__ == "__main__":
    app.run(host="0.0.0.0")
