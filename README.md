# 🏏 AI 3rd Umpire

A next-generation, autonomous AI Third Umpire application built with Streamlit, OpenCV, and the Google Gemini Multimodal API.

The AI 3rd Umpire is designed to process raw cricket video footage, autonomously scrub through the video to find the exact millisecond the bails are dislodged, and use strict ICC-style reasoning to declare a batsman **OUT** or **NOT OUT**.

## ✨ Features

- **Autonomous Event Detection:** Drop in a video and the system uses `gemini-3.1-flash-lite` native video understanding to instantly jump to the exact moment the stumps are broken.
- **Frame-by-Frame Scrubbing:** Configurable evidence gathering allows you to grab surrounding frames (e.g., 2 frames before, the event frame, and 2 frames after) with custom step intervals.
- **Multimodal Decision Engine:** The AI acts as an umpire, analyzing the popping crease, bat tip, and bails across sequential frames to issue a binding, highly-accurate decision.
- **Broadcasting-Grade UI:** A stunning, premium Streamlit interface featuring dark-mode styling, glassmorphism, gradient typography, and TV-style animated decision graphics.

## 🚀 Getting Started

### Prerequisites

You need Python 3.9+ installed on your machine. You will also need a Google Gemini API Key.

### Installation

1. **Clone the repository** (or download the files).
2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. **Install the dependencies**:
   ```bash
   pip install streamlit opencv-python pillow python-dotenv google-genai numpy
   ```
4. **Set up your API Key**:
   Create a `.env` file in the root directory and add your Google Gemini API key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

### Running the App

Start the Streamlit development server:
```bash
streamlit run app.py
```

## 🧠 How it Works

1. **Video Upload:** The user uploads a `.mp4`, `.avi`, or `.mov` cricket clip.
2. **AI Smart Detection:** The Gemini Video API processes the entire video temporally, identifying the specific millisecond the bails separate from the stumps.
3. **Evidence Extraction:** OpenCV slices the video and extracts high-resolution frames around that exact timestamp.
4. **Deliberation:** The sequential frames are fed to the Gemini multimodal vision model, which applies strict physical rules (bat tip vs. popping crease) to determine if the batsman made their ground.
5. **Verdict:** The UI triggers a cinematic broadcast graphic displaying the final decision (OUT, NOT OUT, or INCONCLUSIVE) along with the umpire's step-by-step reasoning.

## 🛠 Tech Stack

- **Frontend UI:** Streamlit with custom CSS injections
- **Video Processing:** OpenCV (`cv2`)
- **AI Brain:** `google-genai` SDK (`gemini-3.1-flash-lite`)
- **Image Handling:** Pillow (`PIL`), Numpy
