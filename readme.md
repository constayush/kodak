# 🎙️ Kodak - Local AI Voice Assistant

Kodak is your always-listening local AI assistant built in Python.  
It works offline, understands Hinglish (Indian-accented English & Roman Hindi), and can control system tasks with voice commands — no cloud, no lag, pure speed.

> "Kodak, open YouTube!" — and boom. 💥

---

## 🧠 Features

- 🎤 Offline Voice Recognition (Vosk)
- 🧠 Hotword Detection ("Kodak", "Computer", etc.)
- 💬 Hinglish command understanding
- 🔊 Text-to-Speech Replies (Indian accent)
- 📁 File control, app launch, browser open
- 🧹 Clear temp, shutdown, kill process
- 📋 Clipboard reading, typing, etc.
- 🔌 Modular: Easily extend commands

---

## ⚙️ Installation

> Python 3.8 or above recommended.

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/kodak.git
cd kodak

2. Create virtual environment (optional but recommended)
bash
Copy
Edit
python -m venv venv
# On Windows
venv\Scripts\activate
# On Linux/Mac
source venv/bin/activate
3. Install dependencies
bash
Copy
Edit
pip install -r requirements.txt
4. Download Vosk Big Model (Offline STT)
Vosk needs a speech model to work offline.

Download the Vosk large English model from here:
🔗 https://alphacephei.com/vosk/models
(Recommended: vosk-model-en-us-0.42-gigaspeech)

After downloading, extract the folder and place it in your project directory.
Rename it to model or set the correct path in main.py:

python
Copy
Edit
model = Model("model")  # Make sure this folder exists
🚀 Run Kodak
bash
Copy
Edit
python main.py
You should hear it boot up and start listening. Try:

"Kodak open YouTube"
"Kodak shutdown"
"Computer clear temp"

📦 Dependencies
Main ones from requirements.txt:

vosk - Offline STT

sounddevice - Mic input

pyttsx3 - Text-to-speech

pyautogui - Control mouse/keyboard

pyperclip - Clipboard control

psutil - System process control

speedtest-cli, requests, feedparser - Lazy-loaded for internet actions

📌 Notes
Works completely offline (except web-based commands).

Add your own actions inside the commands dictionary.

You can modify wake words in the listen() function.

