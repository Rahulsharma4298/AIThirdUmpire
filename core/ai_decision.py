from google import genai
from google.genai import types
import os
from PIL import Image
import cv2
import json
import numpy as np
import time

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=api_key)

def ask_gemini_decision(frames: list[tuple[int, np.ndarray]]) -> dict:
    """
    Given a sequence of frames, convert them to PIL images and pass to Gemini
    with a strong prompt to determine run-out status.
    Frames param is a list of (frame_index, numpy_image).
    """
    client = get_gemini_client()
    
    pil_images = []
    frame_indices = []
    for idx, f in frames:
        # Convert BGR (OpenCV) to RGB (PIL)
        rgb_frame = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
        pil_images.append(Image.fromarray(rgb_frame))
        frame_indices.append(idx)
        
    n = len(pil_images)
    prompt = f"""
    You are an expert cricket Third Umpire making an official run-out decision.
    You are reviewing {n} sequential video frames of a potential run-out or stumping.

    STEP 1 — SCAN ALL FRAMES AND IDENTIFY:
      a) The STUMPS: 3 vertical wooden posts at the end of the pitch.
      b) The BAILS: 2 small horizontal pieces resting on top of the stumps.
      c) The POPPING CREASE: the white painted line on the ground in front of the stumps.
      d) The BATSMAN'S BAT: focus on the bottom tip of the bat closest to the ground.

    STEP 2 — FIND THE DISMISSAL FRAME:
      Scan the frames in order and find the FIRST frame where the bails are fully airborne
      or separated from the stumps. If using LED/glowing stumps, it is the frame they illuminate.
      Note which frame number (1 through {n}) this is.

    STEP 3 — CHECK BAT POSITION AT THAT EXACT MOMENT:
      In the dismissal frame identified above:
      - Is the bat tip physically touching the ground BEHIND the popping crease? → NOT OUT
      - Is the bat tip in the air, exactly on the line, or short of the crease?   → OUT

    DECISION RULES (apply in order):
      1. If the bat is grounded behind or on the crease at the moment of bail dislodgement → NOT OUT
      2. If the bat is clearly short of the crease or in the air at that moment → OUT
      3. If you CANNOT clearly see the crease, the bat tip, or the bails in any of the frames → INCONCLUSIVE

    Output your answer as valid JSON with this exact structure:
    {{
      "reasoning": "Frame-by-frame description of what you observe (crease position, bat tip, bails, dismissal frame). Be specific.",
      "decision": "OUT" | "NOT OUT" | "INCONCLUSIVE"
    }}
    """
    
    contents = pil_images + [prompt]
    
    # Send to Gemini
    response = client.models.generate_content(
        model='gemini-3.1-flash-lite',
        contents=contents,
        config=types.GenerateContentConfig(
            temperature=0.1, # keep it deterministic
            response_mime_type="application/json"
        )
    )
    
    return json.loads(response.text)

def find_event_timestamp_with_ai(video_path: str) -> float:
    """
    Uses Gemini File API to intelligently find the exact timestamp of the stump hit.
    """
    client = get_gemini_client()
    
    # Upload the video file
    video_file = client.files.upload(file=video_path)
    
    # Wait for processing
    while video_file.state.name == "PROCESSING":
        time.sleep(2)
        video_file = client.files.get(name=video_file.name)
        
    if video_file.state.name == "FAILED":
        raise ValueError("Gemini failed to process the video.")
        
    prompt = """
    You are an expert cricket video analyst. Watch this video carefully from start to finish.

    YOUR TASK: Identify the EXACT timestamp (in seconds) of a run-out or stumping attempt.

    WHAT TO LOOK FOR:
      1. A fielder throwing the ball at the stumps, OR breaking the stumps with the ball in hand.
      2. The bails (two small horizontal pieces on top of the stumps) becoming airborne or separating.
      3. If the stumps have LED lights — look for the moment the stumps ILLUMINATE (light up).
      4. Report the timestamp of BAIL DISLODGEMENT — not the throw, not the catch.

    RULES:
      - If the event is clearly visible, return the precise timestamp as a decimal (e.g. 4.73).
      - If there are multiple events, report the one closest to the batsman's crease.
      - If you are NOT 100% certain you can see the bails coming off, return null. Do NOT guess.

    Respond ONLY with this JSON:
    {{"timestamp_seconds": 3.45}}   ← float, or null if no event found
    """
    
    response = client.models.generate_content(
        model='gemini-3.1-flash-lite',
        contents=[video_file, prompt],
        config=types.GenerateContentConfig(
            temperature=0.0,  # deterministic — no creativity needed
            response_mime_type="application/json"
        )
    )
    
    # Clean up the file from Gemini storage
    client.files.delete(name=video_file.name)
    
    result = json.loads(response.text)
    return result.get('timestamp_seconds', 0.0)
