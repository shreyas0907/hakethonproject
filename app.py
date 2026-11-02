import os
import time
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from sarvamai import SarvamAI
from sarvamai.play import save

app = Flask(__name__, static_folder=".")

# Load API key
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("SARVAM_API_KEY")
if not api_key:
    raise ValueError("SARVAM_API_KEY is not set in .env")

client = SarvamAI(api_subscription_key=api_key)

PERSONAS = {
    "epic_narrator": {"speaker": "shubh_en_audiobook", "lang": "en-IN", "name": "Shubh (Epic Audiobook)"},
    "docent_guide": {"speaker": "shubh_en_narration", "lang": "en-IN", "name": "Shubh (Museum Docent)"},
    "suspense_drama": {"speaker": "rustom_en_suspense", "lang": "en-IN", "name": "Rustom (Dramatic Suspense)"},
    "folklore_teller": {"speaker": "aditi_en_stories", "lang": "en-IN", "name": "Aditi (Folklore Stories)"},
    "gentle_temple": {"speaker": "shubh_en_narration_gentle", "lang": "en-IN", "name": "Shubh (Sacred & Gentle)"},
    "hindi_documentary": {"speaker": "anand_hi_documentary", "lang": "hi-IN", "name": "Anand (Hindi Documentary)"},
    "hindi_dramatic": {"speaker": "shubh_hi_stories_dramatic", "lang": "hi-IN", "name": "Shubh (Hindi Dramatic)"},
    "hindi_devotional": {"speaker": "ishita_hi_devotional", "lang": "hi-IN", "name": "Ishita (Hindi Devotional)"},
    "hindi_character": {"speaker": "advait_hi_character", "lang": "hi-IN", "name": "Advait (Hindi Regal Ruler)"},
}

@app.route("/")
def index():
    return send_from_directory(".", "player.html")

@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(".", filename)

@app.route("/api/generate", methods=["POST"])
def generate_track():
    data = request.json or {}
    topic = data.get("topic", "Ancient Temple of India")
    persona_key = data.get("persona", "epic_narrator")
    pace = float(data.get("pace", 1.0))
    temperature = float(data.get("temperature", 0.6))
    custom_script = data.get("custom_script", "").strip()
    
    persona = PERSONAS.get(persona_key, PERSONAS["epic_narrator"])
    target_lang = persona["lang"]
    speaker_id = persona["speaker"]

    # Generate or use custom script
    if custom_script:
        script = custom_script
    else:
        lang_prompt = "in Hindi" if target_lang.startswith("hi") else "in English"
        prompt = (
            f"You are a master cultural docent and heritage storyteller. "
            f"Transform this historical topic into an evocative, dramatic 2-sentence audio narration {lang_prompt} "
            f"(under 45 words, suitable for voice synthesis). Output ONLY the spoken words.\n\n"
            f"Topic: {topic}"
        )
        llm_res = client.chat.completions(
            model="sarvam-105b-conversations",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150,
        )
        script = llm_res.choices[0].message.content.strip()

    # Generate audio
    timestamp = int(time.time())
    output_filename = f"custom_track_{timestamp}.wav"
    
    tts_res = client.text_to_speech.convert(
        text=script,
        language_code=target_lang,
        model="bulbul:v4-flash",
        speaker=speaker_id,
        pace=pace,
        temperature=temperature
    )
    save(tts_res, output_filename)

    return jsonify({
        "success": True,
        "title": topic[:40] if topic else "Custom Heritage Track",
        "script": script,
        "file": output_filename,
        "persona": persona["name"],
        "pace": pace,
        "temperature": temperature,
        "language": target_lang
    })

if __name__ == "__main__":
    app.run(port=5050, debug=False)
