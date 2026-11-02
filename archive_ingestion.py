import os
import time
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

class HeritageArchiveIngestor:
    """
    Ingests and processes raw heritage material:
    - Oral audio archives (Saaras v4)
    - Historical manuscript documents/scans (Sarvam Vision Doc AI)
    """
    def __init__(self, sarvam_client: SarvamAI):
        self.client = sarvam_client

    def ingest_oral_audio(
        self,
        audio_file_path: str,
        mode: str = "transcribe",
        language_code: str = "unknown"
    ) -> dict:
        """
        Transcribes oral histories, elder interviews, or audio field recordings using Saaras v4.
        Modes:
          - 'transcribe': Native script and language
          - 'translate': Directly translates Indic spoken audio into English
          - 'codemix': Handles mixed speech (e.g., Hinglish)
        """
        print(f"\n[STT Ingestion] Processing oral audio: {audio_file_path}")
        print(f"  -> Model: Saaras v4 | Mode: {mode} | Language: {language_code}")

        with open(audio_file_path, "rb") as f:
            response = self.client.speech_to_text.transcribe(
                file=f,
                model="saaras:v4",
                mode=mode,
                language_code=language_code
            )

        result = {
            "transcript": response.transcript,
            "detected_language": getattr(response, "language_code", language_code),
            "request_id": response.request_id
        }
        print(f"  -> Transcription complete!")
        print(f"     \"{result['transcript']}\"")
        return result

    def ingest_manuscript_document(
        self,
        document_path: str,
        language: str = "hi-IN"
    ) -> str:
        """
        Parses scanned manuscripts or PDF documents using Sarvam Vision 2.1 (Doc AI).
        Extracts clean text / Markdown preserving layout.
        """
        print(f"\n[Doc AI Ingestion] Processing manuscript document: {document_path}")
        print(f"  -> Model: Sarvam Vision 2.1 | Language: {language}")

        with open(document_path, "rb") as f:
            job = self.client.doc_ai.parse(
                file=[f],
                language=language
            )

        job_id = job.job_id
        print(f"  -> Parse Job initiated (Job ID: {job_id}). Polling for results...")

        # Poll status
        for _ in range(30):
            status_res = self.client.doc_ai.get_status(job_id=job_id)
            state = getattr(status_res, "status", None) or getattr(status_res, "state", "processing")
            if state in ["completed", "done", "partially_completed"]:
                print(f"  -> Job completed successfully!")
                break
            time.sleep(2)

        results = self.client.doc_ai.get_results(job_id=job_id)
        return results

    def transform_archive_to_narration(
        self,
        raw_text: str,
        output_audio: str = "archive_story_narration.wav",
        speaker: str = "shubh_en_audiobook"
    ):
        """
        Takes raw archived text or transcript, enhances it into a dramatic story script with Sarvam 105B,
        and generates audio narration using Bulbul v4 Flash.
        """
        print(f"\n[Transformation] Converting archive transcript into narrative audio...")
        
        prompt = (
            "You are a master museum docent and heritage storyteller. "
            "Convert this raw archival record into an evocative, dramatic 2-sentence story narration (under 50 words) "
            "suitable for a museum audio guide. Output only the spoken words.\n\n"
            f"Archival Record: {raw_text}"
        )

        llm_res = self.client.chat.completions(
            model="sarvam-105b-conversations",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150,
        )
        script = llm_res.choices[0].message.content.strip()
        print(f"\n--- Produced Narrative Script ---\n\"{script}\"\n---------------------------------")

        print(f"Synthesizing with Bulbul v4 Flash [{speaker}]...")
        tts_res = self.client.text_to_speech.convert(
            text=script,
            language_code="en-IN",
            model="bulbul:v4-flash",
            speaker=speaker
        )
        save(tts_res, output_audio)
        size_kb = os.path.getsize(output_audio) / 1024
        print(f"Story narration saved to: {output_audio} ({size_kb:.1f} KB)")
        return script, output_audio

def main():
    ingestor = HeritageArchiveIngestor(client)

    print("==========================================================")
    print("      HERITAGE ARCHIVE INGESTION & NARRATION PIPELINE     ")
    print("==========================================================")

    # Demonstration with an oral archive audio track
    sample_audio = Path(__file__).parent / "scene_narrator.wav"
    if sample_audio.exists():
        # 1. Ingest oral archive using Saaras v4
        result = ingestor.ingest_oral_audio(
            audio_file_path=str(sample_audio),
            mode="transcribe",
            language_code="en-IN"
        )

        # 2. Transform the ingested archive into a produced historical narration
        ingestor.transform_archive_to_narration(
            raw_text=result["transcript"],
            output_audio="archive_story_narration.wav",
            speaker="shubh_en_audiobook"
        )
    else:
        print(f"Audio file not found: {sample_audio}")

if __name__ == "__main__":
    main()
