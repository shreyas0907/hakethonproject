import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sarvamai import SarvamAI
from sarvamai.play import save

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("SARVAM_API_KEY")
if not api_key:
    raise ValueError("SARVAM_API_KEY is not set. Please add it to your .env file.")

client = SarvamAI(api_subscription_key=api_key)

def generate_heritage_story(historical_topic_or_excerpt: str, language: str = "en-IN") -> str:
    """
    Uses Sarvam 105B to transform raw historical notes/excerpts
    into an evocative, dramatic audio tour narration script.
    """
    print(f"\n[1/2] Generating storytelling script with Sarvam 105B...")
    
    prompt = f"""You are a master Heritage Storyteller and Museum Docent.
Transform the following historical notes or manuscript excerpt into an evocative, immersive audio narration script (approx 2-3 sentences, engaging and spoken-word friendly, under 60 words so it stays under TTS limits).
Do NOT include stage directions like '[Sound effect]' or character headers like 'Narrator:'. Return only the spoken words.

Topic / Manuscript Excerpt:
{historical_topic_or_excerpt}
"""
    
    response = client.chat.completions(
        model="sarvam-105b-conversations",
        messages=[
            {"role": "system", "content": "You are a master cultural historian and heritage audio tour docent."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=250,
    )
    
    script = response.choices[0].message.content.strip()
    return script

def narrate_story(script_text: str, output_path: str = "heritage_story.wav", language_code: str = "en-IN"):
    """
    Uses Bulbul v4 Flash (Sarvam AI's latest TTS) to synthesize natural,
    expressive audio narration.
    """
    print(f"\n[2/2] Synthesizing voice narration using Bulbul v4 Flash...")
    
    # Bulbul v4 Flash converts text to speech with high naturalness
    tts_response = client.text_to_speech.convert(
        text=script_text,
        language_code=language_code,
        model="bulbul:v4-flash",
    )
    
    save(tts_response, output_path)
    file_size_kb = os.path.getsize(output_path) / 1024
    print(f"Audio narration saved successfully to: {output_path} ({file_size_kb:.1f} KB)")

def main():
    # Sample historical manuscript excerpt: The Stone Chariot of Hampi (Vijayanagara Empire)
    sample_excerpt = (
        "In the heart of Hampi lies the Vittala Temple, renowned for its iconic Stone Chariot. "
        "Built in the 16th century during the reign of Emperor Krishnadevaraya of Vijayanagara, "
        "it is dedicated to Garuda, the vahana of Lord Vishnu. The chariot was carved from granite blocks "
        "with wheels that once turned freely, symbolizing an empire where celestial art and architectural genius met."
    )
    
    print("==========================================")
    print("      HERITAGE STORYTELLING AGENT         ")
    print("==========================================")
    print(f"\nSource Historical Excerpt:\n\"{sample_excerpt}\"")
    
    # 1. Transform excerpt to audio script using sarvam-105b
    script = generate_heritage_story(sample_excerpt, language="en-IN")
    print("\n--- Generated Audio Tour Script ---")
    print(f"\"{script}\"")
    print("-----------------------------------")
    
    # 2. Convert script to natural voice with Bulbul v4 Flash
    output_audio = "heritage_story.wav"
    narrate_story(script, output_path=output_audio, language_code="en-IN")
    
    print("\nStorytelling generation complete!")

if __name__ == "__main__":
    main()
