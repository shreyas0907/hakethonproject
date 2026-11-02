import os
import json
from pathlib import Path
from dotenv import load_dotenv
from sarvamai import SarvamAI
from sarvamai.play import save

# Load environment
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("SARVAM_API_KEY")
if not api_key:
    raise ValueError("SARVAM_API_KEY is not set. Please add it to your .env file.")

client = SarvamAI(api_subscription_key=api_key)

# Curated Heritage Persona Catalog for Bulbul v4 Flash
HERITAGE_PERSONAS = {
    "english": {
        "museum_docent": {
            "speaker": "shubh_en_narration",
            "description": "Refined, authoritative museum tour guide",
            "lang": "en-IN"
        },
        "dramatic_epic": {
            "speaker": "shubh_en_audiobook",
            "description": "Deep, immersive audiobook narrator for epic battles and empires",
            "lang": "en-IN"
        },
        "suspense_chronicler": {
            "speaker": "rustom_en_suspense",
            "description": "Tense, atmospheric voice for historical mysteries and lost cities",
            "lang": "en-IN"
        },
        "folklore_teller": {
            "speaker": "aditi_en_stories",
            "description": "Warm, captivating storyteller for legends and cultural lore",
            "lang": "en-IN"
        }
    },
    "hindi": {
        "documentary_historian": {
            "speaker": "anand_hi_documentary",
            "description": "Authoritative documentary voice for archaeological insights",
            "lang": "hi-IN"
        },
        "dramatic_bard": {
            "speaker": "shubh_hi_stories_dramatic",
            "description": "Expressive dramatic narrator for royalty and historic clashes",
            "lang": "hi-IN"
        },
        "temple_sacred_lore": {
            "speaker": "ishita_hi_devotional",
            "description": "Serene, respectful voice for sacred architecture and mythology",
            "lang": "hi-IN"
        },
        "historical_character": {
            "speaker": "advait_hi_character",
            "description": "Regal, commanding character voice for historical rulers",
            "lang": "hi-IN"
        }
    }
}

def generate_multi_persona_scene(historical_event: str, language: str = "en") -> dict:
    """
    Uses Sarvam 105B to generate a dialogue between a Museum Docent and a Historical Figure.
    """
    print(f"\n[1/3] Generating multi-character historical scene using Sarvam 105B...")
    
    system_prompt = (
        "You are a master historical playwright and museum audio experience designer. "
        "Create a short, dramatic two-part audio clip based on the historical event. "
        "Part 1: The Docent / Narrator setting the scene (max 30 words). "
        "Part 2: The Historical Character speaking in first person (max 30 words). "
        "Respond ONLY in valid JSON format with keys 'narrator_dialogue', 'character_name', and 'character_dialogue'."
    )
    
    user_prompt = f"Historical Topic: {historical_event}\nLanguage: {language}"
    
    response = client.chat.completions(
        model="sarvam-105b-conversations",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=250,
    )
    
    raw_content = response.choices[0].message.content.strip()
    
    # Clean possible markdown fence from JSON
    if raw_content.startswith("```"):
        raw_content = raw_content.split("```")[1]
        if raw_content.startswith("json"):
            raw_content = raw_content[4:]
        raw_content = raw_content.strip()
        
    try:
        scene_data = json.loads(raw_content)
    except Exception:
        # Fallback if raw text returned
        scene_data = {
            "narrator_dialogue": "Before us stands the iron bastion of Mewar, where honor was defended above all else.",
            "character_name": "Maharana Pratap",
            "character_dialogue": "Let these hills bear witness: freedom is not granted by emperors, it is earned with every breath."
        }
        
    return scene_data

def synthesize_persona_voice(text: str, speaker_id: str, lang_code: str, output_file: str):
    """Synthesizes speech using a specific Bulbul v4 Flash persona."""
    print(f"  -> Synthesizing [{speaker_id}] voice for: \"{text[:45]}...\"")
    res = client.text_to_speech.convert(
        text=text,
        language_code=lang_code,
        model="bulbul:v4-flash",
        speaker=speaker_id
    )
    save(res, output_file)
    size_kb = os.path.getsize(output_file) / 1024
    print(f"     Saved {output_file} ({size_kb:.1f} KB)")

def run_persona_experience():
    print("=======================================================")
    print("      HERITAGE MULTI-PERSONA VOICE STUDIO             ")
    print("=======================================================")
    
    historical_topic = (
        "The Battle of Haldighati (1576) - Maharana Pratap stands with Chetak in the Aravalli hills."
    )
    print(f"\nHistorical Context:\n{historical_topic}")
    
    # 1. Generate scene script
    scene = generate_multi_persona_scene(historical_topic, language="en")
    print("\n--- Generated Dramatic Script ---")
    print(f"Docent: \"{scene.get('narrator_dialogue')}\"")
    print(f"{scene.get('character_name')}: \"{scene.get('character_dialogue')}\"")
    print("---------------------------------")
    
    # 2. Synthesize Narrator with 'shubh_en_audiobook'
    narrator_voice = HERITAGE_PERSONAS["english"]["dramatic_epic"]["speaker"]
    synthesize_persona_voice(
        text=scene["narrator_dialogue"],
        speaker_id=narrator_voice,
        lang_code="en-IN",
        output_file="scene_narrator.wav"
    )
    
    # 3. Synthesize Character with 'rustom_en_suspense'
    character_voice = HERITAGE_PERSONAS["english"]["suspense_chronicler"]["speaker"]
    synthesize_persona_voice(
        text=scene["character_dialogue"],
        speaker_id=character_voice,
        lang_code="en-IN",
        output_file="scene_character.wav"
    )
    
    print("\n[3/3] Complete! Created 2 distinct persona audio tracks:")
    print("  1. scene_narrator.wav (Narrator Voice: Shubh Audiobook)")
    print(f"  2. scene_character.wav ({scene.get('character_name')} Voice: Rustom Dramatic)")

if __name__ == "__main__":
    run_persona_experience()
