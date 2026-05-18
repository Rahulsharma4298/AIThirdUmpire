import os
import argparse
from dotenv import load_dotenv
from core.video_tools import VideoTools
from core.ai_decision import ask_gemini_decision
import json

def run_umpire(video_path: str):
    load_dotenv()
    
    print(f"Loading video: {video_path}")
    vt = VideoTools(video_path)
    
    try:
        print("Finding event frame (stump hit)...")
        # In a real scenario, you'd specify a tighter range where the action happens
        # For MVP, we scan a generic subset or the whole thing
        # Here we just scan the first 100 frames to save time if no range provided
        event_idx = vt.find_event_frame(diff_threshold=30)
        print(f"Event detected around frame: {event_idx}")
        
        print("Extracting critical frames around the event...")
        frames = vt.get_frame_range(event_idx, before=2, after=2)
        print(f"Extracted {len(frames)} frames for Gemini analysis.")
        
        print("Consulting the AI Third Umpire (Gemini)...")
        result = ask_gemini_decision(frames)
        
        print("\n=== AI THIRD UMPIRE DECISION ===")
        print(f"Decision: {result.get('decision')}")
        print(f"Reasoning: {result.get('reasoning')}")
        print("================================")
        
    finally:
        vt.release()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI 3rd Umpire - Run out detection")
    parser.add_argument("video", type=str, help="Path to the cricket video (mp4, avi, etc.)")
    args = parser.parse_args()
    
    run_umpire(args.video)
