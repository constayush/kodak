import os
import sys
import json
import queue
import threading
import time
import datetime
import subprocess
import webbrowser
import sounddevice as sd
import pyautogui
import ctypes
import random
import pyperclip
import shutil
import psutil
import re
import pyttsx3
from vosk import Model, KaldiRecognizer


# Lazy imports (used only when needed)
def lazy_imports():
    global requests, feedparser, speedtest
    import requests
    import feedparser
    import speedtest


model = Model("model-big")
q = queue.Queue()
stop_lock = threading.Lock()
stop_speaking = False


# -- Audio Input Setup --
def callback(indata, frames, t, status):
    if status:
        print("🔴 Audio error:", status)
        speak("Audio error occurred", "en")
    q.put(bytes(indata))


# -- Web Browser Setup --
brave_path = os.path.join(
    os.getenv("PROGRAMFILES", "C:\\Program Files"),
    "BraveSoftware\\Brave-Browser\\Application\\brave.exe"
)

try:
    webbrowser.register('brave', None, webbrowser.BackgroundBrowser(brave_path))
    web = webbrowser.get('brave')
except Exception as e:
    print(f"⚠️ Browser setup failed: {e}")
    speak("Browser setup failed", "en")


# -- TTS Setup (pyttsx3) --
try:
    tts = pyttsx3.init()
    tts.setProperty('rate', 180)
except Exception as e:
    print(f"⚠️ TTS initialization failed: {e}")
    sys.exit(1)


def speak(text, lang="en"):
    global stop_speaking
    with stop_lock:
        if stop_speaking:
            return
        stop_speaking = False
    print(f"🔊 [{lang.upper()}] {text}")
    try:
        tts.say(text)
        tts.runAndWait()
    except Exception as e:
        print(f"⚠️ TTS error: {e}")


def detect_input_lang(text):
    return "en"


def open_url(url, name, lang):
    try:
        web.open(url)
        speak(f"Opened {name}.", lang)
    except Exception as e:
        speak(f"Failed to open {name}. Error: {str(e)}", lang)


# -- Dictionary-based Command Mapping --
command_map = {
    "notepad": {
        "action": lambda: subprocess.Popen(["notepad"]),
        "response": "Opened Notepad."
    },
    "calculator": {
        "action": lambda: subprocess.Popen(["calc"]),
        "response": "Opened Calculator."
    },
    "paint": {
        "action": lambda: subprocess.Popen(["mspaint"]),
        "response": "Opened Paint."
    },
    "spotify": {
        "action": lambda: subprocess.Popen([os.path.expandvars(r"%APPDATA%\\Spotify\\Spotify.exe")]),
        "response": "Spotify launched."
    },
    "vs code": {
        "action": lambda: subprocess.Popen(["code"]),
        "response": "VS Code launched."
    },
    "terminal": {
        "action": lambda: subprocess.Popen(["cmd"]),
        "response": "Opened Terminal."
    },
    "control panel": {
        "action": lambda: subprocess.Popen(["control"]),
        "response": "Control Panel opened."
    },
    "photos": {
        "action": lambda: os.system("start microsoft.windows.photos:"),
        "response": "Photos opened."
    },
    "youtube": {
        "action": lambda: open_url("https://www.youtube.com", "YouTube", "en"),
        "response": None
    },
    "google": {
        "action": lambda: open_url("https://www.google.com", "Google", "en"),
        "response": None
    },
    "instagram": {
        "action": lambda: open_url("https://www.instagram.com", "Instagram", "en"),
        "response": None
    },
    "whatsapp": {
        "action": lambda: open_url("https://web.whatsapp.com", "WhatsApp", "en"),
        "response": None
    },
    "chatgpt": {
        "action": lambda: open_url("https://chat.openai.com", "ChatGPT", "en"),
        "response": None
    },
    "github": {
        "action": lambda: open_url("https://github.com", "GitHub", "en"),
        "response": None
    },
    "private tab": {
        "action": lambda: subprocess.Popen([brave_path, "--incognito"]),
        "response": "Private tab opened."
    },
    "tor tab": {
        "action": lambda: subprocess.Popen([brave_path, "--tor"]),
        "response": "Tor tab opened."
    },
    "clipboard": {
        "action": lambda: speak(f"Clipboard contains: {pyperclip.paste()}", "en"),
        "response": None
    },
    "volume up": {
        "action": lambda: pyautogui.press("volumeup"),
        "response": "Volume increased."
    },
    "volume down": {
        "action": lambda: pyautogui.press("volumedown"),
        "response": "Volume decreased."
    },
    "mute": {
        "action": lambda: pyautogui.press("volumemute"),
        "response": "Muted."
    },
    "sleep": {
        "action": lambda: ctypes.windll.powrprof.SetSuspendState(False, True, True),
        "response": "System sleeping."
    },
    "hibernate": {
        "action": lambda: ctypes.windll.powrprof.SetSuspendState(True, True, True),
        "response": "System hibernating."
    },
    "lock": {
        "action": lambda: ctypes.windll.user32.LockWorkStation(),
        "response": "System locked."
    },
    "battery": {
        "action": lambda: speak(
            f"Battery at {psutil.sensors_battery().percent} percent"
            if psutil.sensors_battery()
            else "Battery status not found."
        ),
        "response": None
    },
  "clear temp": {
    "action": lambda: shutil.rmtree(
        os.path.join(os.getenv("WINDIR", "C:\\Windows"), "Temp")
    ),
    "response": "Temporary files cleared."
},

    "time": {
        "action": lambda: speak(datetime.datetime.now().strftime("%I:%M %p")),
        "response": None
    },
    "date": {
        "action": lambda: speak(datetime.datetime.now().strftime("%d %B %Y")),
        "response": None
    },
    "screenshot": {
        "action": lambda: save_screenshot(),
        "response": None
    },
    "news": {
        "action": lambda: read_news(),
        "response": None
    },
    "speed test": {
        "action": lambda: run_speedtest(),
        "response": None
    },
    "clean junk": {
        "action": lambda: clean_junk(),
        "response": "Cleaning junk files."
    },
    "shutdown": {
        "action": lambda: shutdown_kodak(),
        "response": "Shutting down. Goodbye 👋"
    },
    "close": {
        "action": lambda: shutdown_kodak(),
        "response": "Closing Kodak. See you later."
    },
    "exit": {
        "action": lambda: shutdown_kodak(),
        "response": "Kodak is going offline."
    },
    "bye": {
        "action": lambda: shutdown_kodak(),
        "response": "Kodak is going offline."
    },
    "goodbye": {
        "action": lambda: shutdown_kodak(),
        "response": "Kodak is going offline."
    },
    "restart": {
        "action": lambda: os.system("shutdown /r /t 1"),
        "response": "Restarting system."
    },
    "kill": {
    "action": lambda text: kill_process(text),
    "response": None
    },

    "system info": {
        "action": lambda: system_info(),
        "response": None
    },
    "launch": {
        "action": lambda text: open_app(text),
        "response": None
    },
    "schedule shutdown": {
        "action": lambda text: schedule_shutdown(text),
        "response": None
    },
}


def schedule_shutdown(text):
    try:
        mins = int(re.search(r"\d+", text).group())
        os.system(f"shutdown /s /t {mins * 60}")
        speak(f"Shutting down in {mins} minutes")
    except:
        speak("Invalid time format. Example: 'schedule shutdown 30'")


def clean_junk():
    if is_admin():
        os.system("cleanmgr /sagerun:1")
    else:
        speak("Please run as administrator to clean junk files.")


def load_app_config():
    try:
        with open("config.json", "r") as f:
            return json.load(f).get("apps", {})
    except:
        return {}


def open_app(text):
    """Open an application dynamically from config.json with error handling."""
    try:
        # Extract app name more reliably (handles phrases like "please open spotify")
        app_name = re.sub(r'^.*\bopen\b', '', text, flags=re.IGNORECASE).strip()
        if not app_name:
            speak("Please specify an app to open.")
            return

        apps = load_app_config()
        
        # Fuzzy matching for app names (e.g., "vs code" -> "vscode")
        matches = [
            (name, score) 
            for name in apps.keys() 
            if (score := fuzz.ratio(app_name.lower(), name.lower())) > 60
        ]
        
        if matches:
            best_match = max(matches, key=lambda x: x[1])[0]
            app_path = apps[best_match]
            
            # Expand environment variables (e.g., %APPDATA%)
            expanded_path = os.path.expandvars(app_path)
            
            if os.path.exists(expanded_path):
                # Use shell=True only for paths with spaces
                subprocess.Popen(f'"{expanded_path}"', shell=True)
                speak(f"Opening {best_match}")
            else:
                speak(f"Error: Path not found - {expanded_path}")
        else:
            speak(f"No configured app matches '{app_name}'. Try saying 'launch chrome' or similar.")
            
    except Exception as e:
        speak(f"Failed to open app: {str(e)}")
        print(f"🔥 open_app() error: {e}")


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_speedtest():
    lazy_imports()
    try:
        st = speedtest.Speedtest()
        down = round(st.download() / 1_000_000, 2)
        up = round(st.upload() / 1_000_000, 2)
        speak(f"Download speed: {down} Mbps. Upload speed: {up} Mbps")
    except Exception as e:
        speak(f"Speed test failed: {str(e)}")


def kill_process(text):
    proc = text.split("kill")[-1].strip()
    try:
        os.system(f"taskkill /f /im {proc}.exe")
        speak(f"Killed {proc}")
    except Exception as e:
        speak(f"Failed to kill {proc}: {str(e)}")


def system_info():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    speak(f"CPU: {cpu}%, RAM: {ram}%")


def save_screenshot():
    try:
        folder = os.path.join(os.path.expanduser("~"), "Pictures", "VoiceScreenshots")
        os.makedirs(folder, exist_ok=True)
        filename = datetime.datetime.now().strftime("screenshot_%Y%m%d_%H%M%S.png")
        path = os.path.join(folder, filename)
        pyautogui.screenshot(path)
        speak(f"Screenshot saved at {path}")
    except Exception as e:
        speak(f"Failed to save screenshot: {str(e)}")


def run_command(text):
    lazy_imports()
    try:
        for keyword, info in command_map.items():
            if keyword in text:
                info["action"]()
                if info["response"]: 
                    speak(info["response"])
                return
        
        if "remember" in text:
            content = text.split("remember")[-1].strip()
            remember(content, "en")
        elif "remind" in text:
            recall_memory("en")
        elif "find file" in text:
            keyword = text.split("file")[-1].strip()
            for root, dirs, files in os.walk(os.path.expanduser("~")):
                for f in files:
                    if keyword.lower() in f.lower():
                        speak(f"Found {f}")
                        return
            speak("No file found.")
        elif "search" in text:
            q = text.split("search")[-1].strip().replace(" ", "+")
            open_url(f"https://www.google.com/search?q={q}", f"Search results for {q}", "en")
        elif "define" in text or "meaning of" in text:
            word = text.replace("define", "").replace("meaning of", "").strip()
            speak(fetch_definition(word))
        elif "joke" in text:
            speak(random.choice(fetch_jokes()))
        else:
            speak("Sorry, command not recognized.")
    except Exception as e:
        speak(f"Command failed: {str(e)}")


def fetch_definition(word):
    lazy_imports()
    try:
        r = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
        if r.ok:
            return r.json()[0]['meanings'][0]['definitions'][0]['definition']
        return "Definition not found."
    except Exception as e:
        return f"Failed to fetch definition: {str(e)}"


def fetch_jokes():
    lazy_imports()
    try:
        r = requests.get("https://official-joke-api.appspot.com/jokes/programming/ten")
        return [j['setup'] + " ... " + j['punchline'] for j in r.json()] if r.ok else ["No joke found."]
    except Exception as e:
        return [f"Joke fetch failed: {str(e)}"]


def read_news():
    lazy_imports()
    with stop_lock:
        if stop_speaking: 
            return
    try:
        feed = feedparser.parse("https://news.google.com/rss")
        for entry in feed.entries[:5]:
            with stop_lock:
                if stop_speaking: 
                    break
            speak(entry.title)
    except Exception as e:
        speak(f"Failed to fetch news: {str(e)}")


MEMORY_FILE = "memory.json"


def load_memory():
    if not os.path.exists(MEMORY_FILE): 
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        speak(f"Memory load failed: {str(e)}")
        return []


def save_memory(mem_list):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(mem_list, f, indent=2, ensure_ascii=False)
    except Exception as e:
        speak(f"Memory save failed: {str(e)}")


def remember(text, lang):
    mem = load_memory()
    mem.append({"timestamp": str(datetime.datetime.now()), "note": text})
    save_memory(mem)
    speak("Remembered.", lang)


def recall_memory(lang):
    mem = load_memory()
    if not mem: 
        speak("No memories found.", lang)
    else:
        speak("Here are your latest memories:", lang)
        for item in mem[-5:]: 
            speak(item['note'], lang)


def clear_command_queue():
    while not q.empty():
        try: 
            q.get_nowait()
        except queue.Empty: 
            break


def shutdown_kodak():
    speak("Shutting down. Goodbye 👋", "en")
    sd.stop()  # Release audio resources
    sys.exit()


def listen():
    global stop_speaking
    wake_words = [
        "kodak", "codak", "codac", "codec", "kodac", "kodaak", "kodack",
        "koduck", "koduk", "kodik", "coduck", "coduk",
        "kordak", "korduc", "kordick",
        "kudak", "cudak", "kodik", "kuduk",
        "go duck", "go deck", "go dac",
        "computer", "komputer", "komputar", "compooter", "comp",
        "yo kodak", "ok kodak", "hello kodak", "hey kodak", "coretec"
    ]
    wake_pattern = re.compile(r"|".join(wake_words), re.IGNORECASE)

    rec = KaldiRecognizer(model, 16000)
    try:
        with sd.RawInputStream(
            samplerate=16000,
            blocksize=4000,
            dtype='int16',
            channels=1,
            callback=callback
        ):
            speak("Kodak is online 🚀", "en")
            while True:
                try:
                    data = q.get(timeout=7)
                    if rec.AcceptWaveform(data):
                        full_text = json.loads(rec.Result()).get("text", "")
                        if not full_text.strip(): 
                            continue
                        print("🗣️ Input:", full_text)

                        if any(kw in full_text.lower() for kw in ["stop", "bas", "enough"]):
                            with stop_lock:
                                stop_speaking = True
                            continue

                        if wake_pattern.search(full_text.lower()):
                            clear_command_queue()
                            command = wake_pattern.sub("", full_text).strip()
                            
                            run_command(command)
                except queue.Empty:
                    continue
    except Exception as e:
        speak(f"Audio error: {str(e)}", "en")
        sys.exit(1)


if __name__ == "__main__":
    listen()