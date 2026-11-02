import os
import argparse
from pathlib import Path
from dotenv import load_dotenv
from sarvamai import SarvamAI
from sarvamai.play import save

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("SARVAM_API_KEY")
if not api_key:
    raise ValueError("SARVAM_API_KEY is not set in .env")

client = SarvamAI(api_subscription_key=api_key)

# Curated Voice Personas with styles and languages
PERSONAS = {
    "epic_narrator": {"speaker": "shubh_en_audiobook", "lang": "en-IN", "name": "Shubh (Epic Audiobook)"},
    "docent_guide": {"speaker": "shubh_en_narration", "lang": "en-IN", "name": "Shubh (Museum Docent)"},
    "suspense_drama": {"speaker": "rustom_en_suspense", "lang": "en-IN", "name": "Rustom (Dramatic Suspense)"},
    "folklore_teller": {"speaker": "aditi_en_stories", "lang": "en-IN", "name": "Aditi (Folklore & Legends)"},
    "gentle_temple": {"speaker": "shubh_en_narration_gentle", "lang": "en-IN", "name": "Shubh (Sacred & Gentle)"},
    "hindi_documentary": {"speaker": "anand_hi_documentary", "lang": "hi-IN", "name": "Anand (Hindi Documentary)"},
    "hindi_dramatic": {"speaker": "shubh_hi_stories_dramatic", "lang": "hi-IN", "name": "Shubh (Hindi Dramatic Tales)"},
    "hindi_devotional": {"speaker": "ishita_hi_devotional", "lang": "hi-IN", "name": "Ishita (Hindi Devotional Lore)"},
    "hindi_character": {"speaker": "advait_hi_character", "lang": "hi-IN", "name": "Advait (Hindi Regal Ruler)"},
}

def generate_custom_audio(
    topic: str,
    persona_key: str = "epic_narrator",
    pace: float = 1.0,
    temperature: float = 0.6,
    language_code: str = None,
    output_filename: str = "custom_story.wav",
    skip_llm: bool = False
) -> dict:
    """
    Customizes and generates an audio track with specific voice persona,
    speech rate (pace), and emotional expressiveness (temperature).
    """
    persona = PERSONAS.get(persona_key, PERSONAS["epic_narrator"])
    target_lang = language_code or persona["lang"]
    speaker_id = persona["speaker"]

    print("==================================================")
    print("        CUSTOM AUDIO TRACK GENERATION             ")
    print("==================================================")
    print(f"Topic / Input: {topic[:60]}...")
    print(f"Persona: {persona['name']} ({speaker_id})")
    print(f"Language: {target_lang}")
    print(f"Pace: {pace}x (Speed)")
    print(f"Temperature: {temperature} (Expressiveness)")

    # Step 1: Script generation with Sarvam 105B (or use direct input)
    if skip_llm:
        script = topic
    else:
        print("\n[1/2] Drafting custom storytelling script with Sarvam 105B...")
        lang_prompt = "in Hindi" if target_lang.startswith("hi") else "in English"
        prompt = (
            f"You are a master heritage docent. Transform the following historical topic into an evocative, "
            f"dramatic audio tour script (approx 2 sentences, under 50 words) {lang_prompt}. "
            f"Output only the spoken words without any character labels.\n\n"
            f"Topic: {topic}"
        )
        response = client.chat.completions(
            model="sarvam-105b-conversations",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150,
        )
        script = response.choices[0].message.content.strip()

    print(f"\n--- Script ---\n\"{script}\"\n--------------")

    # Step 2: Custom voice synthesis with Bulbul v4 Flash
    print(f"\n[2/2] Synthesizing audio via Bulbul v4 Flash...")
    tts_response = client.text_to_speech.convert(
        text=script,
        language_code=target_lang,
        speaker=speaker_id,
        model="bulbul:v4-flash",
        pace=pace,
        temperature=temperature
    )

    save(tts_response, output_filename)
    file_size_kb = os.path.getsize(output_filename) / 1024
    print(f"Audio saved to: {output_filename} ({file_size_kb:.1f} KB)")

    return {
        "script": script,
        "audio_file": output_filename,
        "persona": persona["name"],
        "pace": pace,
        "temperature": temperature,
        "language": target_lang
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Customize Sarvam AI Audio Narration")
    parser.add_argument("--topic", type=str, default="The Ajanta Caves: Masterpieces of Buddhist religious art carved into rock cliffs.", help="Historical topic or text")
    parser.add_argument("--persona", type=str, default="epic_narrator", choices=list(PERSONAS.keys()), help="Voice persona")
    parser.add_argument("--pace", type=float, default=0.95, help="Speech pace (0.5 to 2.0)")
    parser.add_argument("--temp", type=float, default=0.7, help="Expressiveness temperature (0.01 to 1.0)")
    parser.add_argument("--lang", type=str, default=None, help="Language code (e.g. en-IN, hi-IN)")
    parser.add_argument("--out", type=str, default="custom_story.wav", help="Output file path")

    args = parser.parse_args()
    generate_custom_audio(
        topic=args.topic,
        persona_key=args.persona,
        pace=args.pace,
        temperature=args.temp,
        language_code=args.lang,
        output_filename=args.out
    )
