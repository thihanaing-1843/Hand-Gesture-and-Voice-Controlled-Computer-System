##########################################################################################
#                                                                                        #
#                                                                                        #
#           HAND GESTURE AND VOICE CONTROLLED BASED CONTROLLED COMPUTER SYSTEM           #
#                                                                                        #
#                                                                                        #
##########################################################################################


# -------------------------------------------------- #

# -------------------------------------------------- #
# -------------------------------------------------- #

# @$%&        Short Program Description         ^%$@ #

# -------------------------------------------------- #

"""
Hand Gesture and Voice-Controlled Computer System

This program integrates computer vision-based hand gesture controls and real-time voice commands to provide a seamless interface for controlling a computer. 
Key functionalities include:
- Hand Gesture Control: Move the mouse pointer, perform clicks, and drag using hand movements detected via webcam.
- Voice Command Control: Execute system commands (e.g., opening apps, controlling volume, navigating browsers) via real-time speech recognition using AssemblyAI.
- Multitasking: Hand and voice controls run concurrently for enhanced usability.

Technologies: OpenCV, Mediapipe, PyAutoGUI, AssemblyAI API, and threading.

Note: Configured for Windows systems. Update application paths and API keys as required.

"""

# -------------------------------------------------- #
# -------------------------------------------------- #
# -------------------------------------------------- #

# @$%&       Required Libraries Importing       ^%$@ #

# -------------------------------------------------- #
# -------------------------------------------------- #
# -------------------------------------------------- #


# keyword and operating system control
import pyautogui
import os

# for the speech 
import threading
import time
import webbrowser
import pyaudio
import websockets
import base64
import json

# Training Model for Hand Traking Module
import HandTrackingModule as htm
import cv2
import numpy as np
import asyncio
import mediapipe as mp

# For the speech to text queue
from queue import Queue

# For the Web Application
import streamlit as st 



# -------------------------------------------------- #
# -------------------------------------------------- #
# -------------------------------------------------- #

# Assembly-AI API key 
auth_key = "aa833d9999f94692ab6082e4b31790f6"

# For the camera frame
FRAME_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# Initialize PyAudio
p = pyaudio.PyAudio()

# Start recording
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=FRAME_PER_BUFFER
)

# For speech to text translation URL
URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"

# Global control flag
running_event = threading.Event()

# Streamlit page configuration
st.title("Hand Tracking Mouse Control")
st.sidebar.header("Controls")

# Initialize control variables
start_app = st.sidebar.button("START", key="start_button")
stop_app = st.sidebar.button("STOP", key="stop_button")

# Sidebar settings
frameR = st.sidebar.slider("Frame Reduction", 50, 200, 100)  # Adjustable frame reduction
smoothening = st.sidebar.slider("Smoothening", 1, 10, 7)  # Adjustable smoothening factor

# Streamlit placeholder for video feed
frame_placeholder = st.empty()

# Placeholder for transcription output
transcription_placeholder = st.empty()

# Queue for passing data between threads
transcription_queue = Queue()

# Camera and Hand Tracking variables
wCam, hCam = 640, 480
cap = None  # Camera capture object
pTime = 0

# === Global Variables ===
selection_mode = False

# Global variable for scrolling control
scrolling = False


# Function to handle continuous scrolling
def continuous_scrolling(direction, step):
    global scrolling
    while scrolling:
        if direction == "up":
            pyautogui.scroll(step)
        elif direction == "down":
            pyautogui.scroll(-step)
        elif direction == "right":
            pyautogui.hscroll(step)
        elif direction == "left":
            pyautogui.hscroll(-step)
        time.sleep(0.1)  # Adjust delay for smoother scrolling

# Speech to text commands to perform actions
def perform_command(transcription):

    global scrolling

    global selection_mode

    transcription = transcription.strip()  # Remove leading/trailing whitespace
    print(f"Executing command: {transcription}")  # Debugging: Log the transcription

    # === "Type Here" Functionality ===
    # Normalize the transcription to lower case for easier comparison
    transcription = transcription.lower()

    # Check for "type here" or "type" in the transcription
    if "type here" in transcription or "type" in transcription:
        # Extract the portion of text after the last occurrence of "type here" or "type"
        if "type here" in transcription:
            text_to_type = transcription.split("type here")[-1].strip()
        else:
            text_to_type = transcription.split("type")[-1].strip()
        
        # Clean up the text to type (optional: remove multiple spaces, etc.)
        text_to_type = ' '.join(text_to_type.split())

        if text_to_type:
            # Ensure the browser is focused
            pyautogui.hotkey('ctrl', 'l')  # Focus on the browser's search/address bar
            time.sleep(0.5)

            # Debugging: Log the exact text being typed
            print(f"Typing text: {text_to_type}")

            # Use pyautogui to type the text
            pyautogui.typewrite(text_to_type)
            #pyautogui.press('enter')  # Optional: press enter after typing
        else:
            print("No valid text detected to type.")
    else:
        print("No command recognized for typing.")

    # === Browser Commands ===
    if "chrome" in transcription or "google" in transcription:
        webbrowser.open("https://www.google.com/")

    

    # === Activate Selection Mode ===
    if "select" in transcription:
        selection_mode = True
        pyautogui.keyDown('shift')  # Programmatically press Shift key
        print("Selection mode activated. Use hand gestures to select text.")

    # === Deactivate Selection Mode ===
    if "selecting" in transcription or "stop selecting" in transcription or "stop selection" in transcription or "close selecting" in transcription or "close selection" in transcription:
        selection_mode = False
        pyautogui.keyUp('shift')  # Programmatically release Shift key
        print("Selection mode deactivated.")

        # === Copy Command ===
    if "copy" in transcription:
        pyautogui.keyUp('shift')
        pyautogui.hotkey('ctrl', 'c')  # Simulate Ctrl + C
        print("Copied selected text.")

    # === Paste Command ===
    if "paste" in transcription or "pase" in transcription:
        pyautogui.hotkey('ctrl', 'v')  # Simulate Ctrl + V
        print("Pasted clipboard content.")


    elif "firefox" in transcription or "mozilla" in transcription:
        os.system(r'"C:\Program Files\Mozilla Firefox\firefox.exe"')
    elif "edge" in transcription or "microsoft" in transcription:
        os.system(r'start msedge')
    elif "new tab" in transcription or "new tap" in transcription:
        pyautogui.hotkey('ctrl', 't')


    # === Google Search Bar Commands ===
    elif any(keyword in transcription for keyword in ["search here", "type here", "type", "search"]):
        try:
            # Find the keyword used in the transcription
            for keyword in ["search here", "type here", "type", "search"]:
                if keyword in transcription:
                    # Extract text after the keyword
                    text_to_type = transcription.split(keyword, 1)[1].strip()
                    break
            else:
                text_to_type = ""

            # Validate the extracted text
            if text_to_type:
                # Focus on the browser's search/address bar
                pyautogui.hotkey('ctrl', 'l')  # Shortcut to focus on the address bar
                time.sleep(0.5)

                # Debugging: Print the text before typing
                print(f"Typing: {text_to_type}")

                # Use pyautogui to type the text
                pyautogui.typewrite(text_to_type)
            else:
                print("No valid text to type.")
        except Exception as e:
            print(f"Error in 'type here' command: {e}")


    # === Mouse Scrolling Commands ===
    elif "scroll" in transcription and "up" in transcription:
        if not scrolling:
            scrolling = True
            threading.Thread(target=continuous_scrolling, args=("up", 100), daemon=True).start()
            print("Scrolling up...")
    elif "scroll" in transcription and "down" in transcription:
        if not scrolling:
            scrolling = True
            threading.Thread(target=continuous_scrolling, args=("down", 100), daemon=True).start()
            print("Scrolling down...")
    elif "scroll" in transcription and "right" in transcription:
        if not scrolling:
            scrolling = True
            threading.Thread(target=continuous_scrolling, args=("right", 100), daemon=True).start()
            print("Scrolling right...")
    elif "scroll" in transcription and "left" in transcription:
        if not scrolling:
            scrolling = True
            threading.Thread(target=continuous_scrolling, args=("left", 100), daemon=True).start()
            print("Scrolling left...")
    elif "stop scrolling" in transcription or "scrolling" in transcription:
        scrolling = False
        print("Scrolling stopped.")

    # === File Explorer and System Apps Commands ===
    elif "explorer" in transcription or "file explorer" in transcription: 
        os.system("explorer")
    elif "downloads" in transcription or "download" in transcription:
        os.startfile(os.path.join(os.environ['USERPROFILE'], 'Downloads'))
    elif "documents" in transcription or "document" in transcription:
        os.startfile(os.path.join(os.environ['USERPROFILE'], 'Documents'))
    elif "pictures" in transcription or "picture" in transcription:
        os.startfile(os.path.join(os.environ['USERPROFILE'], 'Pictures'))

    # === Office Applications and Other Commands ===
    elif "notepad" in transcription:
        os.system("notepad")
    elif "calculator" in transcription:
        os.system("calc")
    elif "camera" in transcription:
        os.system("start microsoft.windows.camera:")
    elif "calendar" in transcription:
        os.system("start outlookcal:")
    elif "settings" in transcription:
        os.system("start ms-settings:")
    elif "task manager" in transcription:
        os.system("taskmgr")
    elif "control panel" in transcription:
        os.system("control")
    elif "command prompt" in transcription or "cmd" in transcription:
        os.system("cmd")
    elif "powerpoint" in transcription:
        os.system("start powerpnt")

     # === General PowerPoint Commands ===
    elif "open powerpoint" in transcription:
        os.system("start powerpnt")
        print("PowerPoint opened.")

    elif "new slide" in transcription:
        pyautogui.hotkey('ctrl', 'm')
        print("New slide added.")

    elif "save presentation" in transcription:
        pyautogui.hotkey('ctrl', 's')
        print("Presentation saved.")

    elif "close presentation" in transcription:
        pyautogui.hotkey('alt', 'f4')
        print("Presentation closed.")

    # === Slide Navigation Commands ===
    elif "next slide" in transcription:
        pyautogui.press('right')
        print("Moved to next slide.")

    elif "previous slide" in transcription:
        pyautogui.press('left')
        print("Moved to previous slide.")

    elif "go to slide" in transcription:
        slide_number = [int(s) for s in transcription.split() if s.isdigit()]
        if slide_number:
            pyautogui.typewrite(str(slide_number[0]))
            pyautogui.press('enter')
            print(f"Moved to slide {slide_number[0]}.")

    # === Presentation Mode Commands ===
    elif "start presentation" in transcription:
        pyautogui.press('f5')
        print("Presentation started.")

    elif "start from current slide" in transcription:
        pyautogui.hotkey('shift', 'f5')
        print("Slideshow started from current slide.")

    elif "stop presentation" in transcription:
        pyautogui.press('esc')
        print("Slideshow ended.")

    # === Text Formatting Commands ===
    elif "bold text" in transcription or "bold" and "text" in transcription or "make it bold" in transcription or "make bold" in transcription or "bold" in transcription:
        pyautogui.hotkey('ctrl', 'b')
        print("Bold applied to selected text.")

    elif "italicize text" in transcription:
        pyautogui.hotkey('ctrl', 'i')
        print("Italic applied to selected text.")

    elif "underline text" in transcription:
        pyautogui.hotkey('ctrl', 'u')
        print("Underline applied to selected text.")

    # === Other Commands ===
    elif "duplicate slide" in transcription:
        pyautogui.hotkey('ctrl', 'd')
        print("Current slide duplicated.")

    elif "delete slide" in transcription:
        pyautogui.hotkey('ctrl', 'delete')
        print("Current slide deleted.")

    elif "insert picture" in transcription:
        pyautogui.hotkey('alt', 'n', 'p')
        print("Insert picture dialog opened.")

    elif "insert text box" in transcription:
        pyautogui.hotkey('alt', 'n', 'x')
        print("Text box inserted.")


    elif "excel" in transcription:
        os.system("start excel")
    elif "word" in transcription:
        os.system("start winword")
    elif "teams" in transcription:
        os.system("start teams")
    elif "outlook" in transcription:
        os.system("start outlook")
    elif "paint" in transcription:
        os.system("mspaint")
    elif "wordpad" in transcription or "word pad" in transcription:
        os.system("write")
    elif "snipping tool" in transcription:
        os.system("snippingtool")
    elif "spotify" in transcription:
        os.system(r'"C:\Users\<YourUsername>\AppData\Roaming\Spotify\Spotify.exe"')  # Update path
    elif "vlc" in transcription or "vlc media player" in transcription:
        os.system(r'"C:\Program Files\VideoLAN\VLC\vlc.exe"')  # Update path
    elif "chrome" in transcription:
        os.system(r'"C:\Program Files\Google\Chrome\Application\chrome.exe"')
    elif "firefox" in transcription:
        os.system(r'"C:\Program Files\Mozilla Firefox\firefox.exe"')
    elif "microsoft edge" in transcription or "edge" in transcription:
        os.system("start msedge")
    elif "notion" in transcription:
        os.system(r'"C:\Users\<YourUsername>\AppData\Local\Programs\Notion\Notion.exe"')  # Update path
    elif "discord" in transcription:
        os.system(r'"C:\Users\<YourUsername>\AppData\Local\Discord\Update.exe --processStart Discord.exe"')  # Update path
    elif "zoom" in transcription:
        os.system(r'"C:\Users\<YourUsername>\AppData\Roaming\Zoom\bin\Zoom.exe"')  # Update path
    elif "spotify" in transcription:
        os.system(r'"C:\Users\<YourUsername>\AppData\Roaming\Spotify\Spotify.exe"')  # Update path
    elif "steam" in transcription:
        os.system(r'"C:\Program Files (x86)\Steam\steam.exe"')  # Update path
    elif "epic games" in transcription or "epic" in transcription or "game" in transcription or "games" in transcription:
        os.system(r'"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe"')  # Update path
    elif "adobe reader" in transcription or "pdf" in transcription:
        os.system(r'"C:\Program Files (x86)\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe"')  # Update path
    elif "adobe photoshop" in transcription or "photoshop" in transcription:
        os.system(r'"C:\Program Files\Adobe\Adobe Photoshop 2022\Photoshop.exe"')  # Update path
    elif "blender" in transcription:
        os.system(r'"C:\Program Files\Blender Foundation\Blender 3.3\blender.exe"')  # Update path
    elif "visual studio" in transcription:
        os.system(r'"C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\devenv.exe"')  # Update path
    elif "vs code" in transcription or "visual studio code" in transcription or "vs" in transcription or "Code" in transcription or "Visual" in transcription or "Studio" in transcription:
        os.system(r'"C:\Users\<YourUsername>\AppData\Local\Programs\Microsoft VS Code\Code.exe"')  # Update path
    elif "android" in transcription and "studio" in transcription or "android" in transcription:
        os.system(r'"C:\Program Files\Android\Android Studio\bin\studio64.exe"')  # Update path
    elif "intellij idea" in transcription or "intellij" in transcription:
        os.system(r'"C:\Program Files\JetBrains\IntelliJ IDEA 2023.2\bin\idea64.exe"')  # Update path
    elif "pycharm" in transcription:
        os.system(r'"C:\Program Files\JetBrains\PyCharm 2023.2\bin\pycharm64.exe"')  # Update path

    # === System Controls ===
    elif "shutdown" in transcription and "laptop" in transcription:
        os.system("shutdown /s /t 1")
    elif "restart" in transcription and "laptop" in transcription:
        os.system("shutdown /r /t 1")
    elif "lock" in transcription:
        os.system("rundll32.exe user32.dll,LockWorkStation")
    elif "sleep" in transcription and "laptop" in transcription:
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    elif "log off" in transcription or "sign out" in transcription and "laptop" in transcription:
        os.system("shutdown -l")

    # === Volume and Brightness Controls ===
    elif "volume up" in transcription or ("increase" in transcription and "volume" in transcription):
        for _ in range(10):  # Loop 10 times to increase the volume by 10 steps
            pyautogui.press("volumeup")
    elif "volume down" in transcription or ("reduce" in transcription and "volume" in transcription):
        for _ in range(10):  # Loop 10 times to decrease the volume by 10 steps
            pyautogui.press("volumedown")
    elif "mute" in transcription and "volume" in transcription:
        pyautogui.press("volumemute")

    # === Browser and Website Commands ===
    elif "youtube" in transcription:
        webbrowser.open("https://www.youtube.com")
        print("Opened YouTube.")
    elif "gmail" in transcription or "email" in transcription:
        webbrowser.open("https://mail.google.com")
        print("Opened Gmail.")
    elif "google drive" in transcription or "drive" in transcription:
        webbrowser.open("https://drive.google.com")
        print("Opened Google Drive.")
    elif "google maps" in transcription or "maps" in transcription:
        webbrowser.open("https://maps.google.com")
        print("Opened Google Maps.")
    elif "google docs" in transcription or "docs" in transcription:
        webbrowser.open("https://docs.google.com")
        print("Opened Google Docs.")
    elif "google sheets" in transcription or "sheets" in transcription:
        webbrowser.open("https://sheets.google.com")
        print("Opened Google Sheets.")
    elif "google slides" in transcription or "slides" in transcription:
        webbrowser.open("https://slides.google.com")
        print("Opened Google Slides.")
    elif "openai" in transcription or "chatgpt" in transcription or "open ai" in transcription:
        webbrowser.open("https://chat.openai.com")
        print("Opened OpenAI ChatGPT.")
    elif "linkedin" in transcription:
        webbrowser.open("https://www.linkedin.com")
        print("Opened LinkedIn.")
    elif "facebook" in transcription:
        webbrowser.open("https://www.facebook.com")
        print("Opened Facebook.")
    elif "twitter" in transcription or "x" in transcription:
        webbrowser.open("https://twitter.com")
        print("Opened Twitter.")
    elif "instagram" in transcription:
        webbrowser.open("https://www.instagram.com")
        print("Opened Instagram.")
    elif "reddit" in transcription:
        webbrowser.open("https://www.reddit.com")
        print("Opened Reddit.")
    elif "amazon" in transcription:
        webbrowser.open("https://www.amazon.com")
        print("Opened Amazon.")
    elif "flipkart" in transcription:
        webbrowser.open("https://www.flipkart.com")
        print("Opened Flipkart.")
    elif "alibaba" in transcription:
        webbrowser.open("https://www.alibaba.com")
        print("Opened Alibaba.")
    elif "noon" in transcription:
        webbrowser.open("https://www.noon.com")
        print("Opened Noon.")
    elif "e-bay" in transcription or "ebay" in transcription:
        webbrowser.open("https://www.ebay.com")
        print("Opened eBay.")
    elif "airbnb" in transcription:
        webbrowser.open("https://www.airbnb.com")
        print("Opened Airbnb.")
    elif "expedia" in transcription:
        webbrowser.open("https://www.expedia.com")
        print("Opened Expedia.")
    elif "imdb" in transcription:
        webbrowser.open("https://www.imdb.com")
        print("Opened IMDb.")
    elif "rotten tomatoes" in transcription:
        webbrowser.open("https://www.rottentomatoes.com")
        print("Opened Rotten Tomatoes.")
    elif "crunchyroll" in transcription or "anime" in transcription:
        webbrowser.open("https://www.crunchyroll.com")
        print("Opened Crunchyroll.")
    elif "netflix" in transcription or "movies" in transcription:
        webbrowser.open("https://www.netflix.com")
        print("Opened Netflix.")
    elif "spotify" in transcription or "music" in transcription:
        webbrowser.open("https://open.spotify.com")
        print("Opened Spotify.")
    elif "hulu" in transcription:
        webbrowser.open("https://www.hulu.com")
        print("Opened Hulu.")
    elif "disney plus" in transcription or "disney+" in transcription:
        webbrowser.open("https://www.disneyplus.com")
        print("Opened Disney+.")
    elif "prime video" in transcription or "amazon prime" in transcription:
        webbrowser.open("https://www.primevideo.com")
        print("Opened Prime Video.")
    elif "zoom" in transcription:
        webbrowser.open("https://zoom.us")
        print("Opened Zoom.")
    elif "microsoft teams" in transcription or "teams" in transcription:
        webbrowser.open("https://teams.microsoft.com")
        print("Opened Microsoft Teams.")
    elif "slack" in transcription:
        webbrowser.open("https://slack.com")
        print("Opened Slack.")
    elif "trello" in transcription:
        webbrowser.open("https://trello.com")
        print("Opened Trello.")
    elif "notion" in transcription:
        webbrowser.open("https://www.notion.so")
        print("Opened Notion.")
    elif "asana" in transcription:
        webbrowser.open("https://asana.com")
        print("Opened Asana.")
    elif "khan academy" in transcription:
        webbrowser.open("https://www.khanacademy.org")
        print("Opened Khan Academy.")
    elif "udemy" in transcription:
        webbrowser.open("https://www.udemy.com")
        print("Opened Udemy.")
    elif "coursera" in transcription or "moocs" in transcription:
        webbrowser.open("https://www.coursera.org")
        print("Opened Coursera.")
    elif "edx" in transcription:
        webbrowser.open("https://www.edx.org")
        print("Opened edX.")
    elif "medium" in transcription:
        webbrowser.open("https://medium.com")
        print("Opened Medium.")
    elif "quora" in transcription:
        webbrowser.open("https://www.quora.com")
        print("Opened Quora.")
    elif "stackoverflow" in transcription or "stack overflow" in transcription:
        webbrowser.open("https://stackoverflow.com")
        print("Opened Stack Overflow.")
    elif "github" in transcription or "git hub" in transcription:
        webbrowser.open("https://github.com")
        print("Opened GitHub.")
    elif "gitlab" in transcription:
        webbrowser.open("https://gitlab.com")
        print("Opened GitLab.")
    elif "bitbucket" in transcription:
        webbrowser.open("https://bitbucket.org")
        print("Opened Bitbucket.")
    elif "leetcode" in transcription:
        webbrowser.open("https://leetcode.com")
        print("Opened LeetCode.")
    elif "hackerrank" in transcription:
        webbrowser.open("https://www.hackerrank.com")
        print("Opened HackerRank.")
    elif "geeksforgeeks" in transcription or "gfg" in transcription:
        webbrowser.open("https://www.geeksforgeeks.org")
        print("Opened GeeksforGeeks.")
    elif "dev" in transcription or "dev.to" in transcription:
        webbrowser.open("https://dev.to")
        print("Opened Dev.to.")
    elif "kaggle" in transcription:
        webbrowser.open("https://www.kaggle.com")
        print("Opened Kaggle.")
    elif "datacamp" in transcription or "data camp" in transcription:
        webbrowser.open("https://www.datacamp.com")
        print("Opened DataCamp.")
    elif "power bi" in transcription:
        webbrowser.open("https://powerbi.microsoft.com")
        print("Opened Power BI.")
    elif "tableau" in transcription:
        webbrowser.open("https://www.tableau.com")
        print("Opened Tableau.")
    elif "behance" in transcription:
        webbrowser.open("https://www.behance.net")
        print("Opened Behance.")
    elif "dribbble" in transcription:
        webbrowser.open("https://dribbble.com")
        print("Opened Dribbble.")
    elif "zomato" in transcription:
        webbrowser.open("https://www.zomato.com")
        print("Opened Zomato.")
    elif "swiggy" in transcription:
        webbrowser.open("https://www.swiggy.com")
        print("Opened Swiggy.")
    elif "dominos" in transcription:
        webbrowser.open("https://www.dominos.com")
        print("Opened Domino's.")
    elif "the verge" in transcription:
        webbrowser.open("https://www.theverge.com")
        print("Opened The Verge.")
    elif "wired" in transcription:
        webbrowser.open("https://www.wired.com")
        print("Opened Wired.")
    elif "techcrunch" in transcription:
        webbrowser.open("https://techcrunch.com")
        print("Opened TechCrunch.")
    elif "indiegogo" in transcription:
        webbrowser.open("https://www.indiegogo.com")
        print("Opened Indiegogo.")
    elif "kickstarter" in transcription:
        webbrowser.open("https://www.kickstarter.com")
        print("Opened Kickstarter.")
    elif "edureka" in transcription:
        webbrowser.open("https://www.edureka.co")
        print("Opened Edureka.")
    elif "pluralsight" in transcription:
        webbrowser.open("https://www.pluralsight.com")
        print("Opened Pluralsight.")
    elif "byju's" in transcription or "byjus" in transcription:
        webbrowser.open("https://byjus.com")
        print("Opened Byju's.")
    elif "codecademy" in transcription or "codeacademy" in transcription:
        webbrowser.open("https://www.codecademy.com")
        print("Opened Codecademy.")
    elif "udacity" in transcription:
        webbrowser.open("https://www.udacity.com")
        print("Opened Udacity.")
    elif "pinterest" in transcription:
        webbrowser.open("https://www.pinterest.com")
        print("Opened Pinterest.")
    elif "twitch" in transcription:
        webbrowser.open("https://www.twitch.tv")
        print("Opened Twitch.")
    elif "wordpress" in transcription:
        webbrowser.open("https://wordpress.com")
        print("Opened WordPress.")
    elif "weebly" in transcription:
        webbrowser.open("https://www.weebly.com")
        print("Opened Weebly.")
    elif "wix" in transcription:
        webbrowser.open("https://www.wix.com")
        print("Opened Wix.")
    elif "google" in transcription:
        webbrowser.open("https://www.google.com")

    # === Social Media and Communication ===
    elif "reddit" in transcription:
        webbrowser.open("https://www.reddit.com")
        print("Opened Reddit.")
    elif "tiktok" in transcription:
        webbrowser.open("https://www.tiktok.com")
        print("Opened TikTok.")
    elif "snapchat" in transcription:
        webbrowser.open("https://www.snapchat.com")
        print("Opened Snapchat.")
    elif "threads" in transcription:
        webbrowser.open("https://www.threads.net")
        print("Opened Threads.")
    elif "messenger" in transcription:
        webbrowser.open("https://www.messenger.com")
        print("Opened Messenger.")

    # === E-commerce and Retail ===
    elif "shein" in transcription:
        webbrowser.open("https://www.shein.com")
        print("Opened Shein.")

    # === Entertainment and Streaming ===
    elif "disney plus" in transcription or "disney+" in transcription:
        webbrowser.open("https://www.disneyplus.com")
        print("Opened Disney+.")
    elif "imdb" in transcription:
        webbrowser.open("https://www.imdb.com")
        print("Opened IMDb.")

    # === Productivity and Tools ===
    elif "figma" in transcription:
        webbrowser.open("https://www.figma.com")
        print("Opened Figma.")

    # === News and Media ===
    elif "cnn" in transcription:
        webbrowser.open("https://www.cnn.com")
        print("Opened CNN.")
    elif "fox news" in transcription:
        webbrowser.open("https://www.foxnews.com")
        print("Opened Fox News.")
    elif "medium" in transcription:
        webbrowser.open("https://www.medium.com")
        print("Opened Medium.")

    # === Miscellaneous ===
    elif "weather" in transcription or "accuweather" in transcription:
        webbrowser.open("https://www.accuweather.com")
        print("Opened AccuWeather.")
    elif "coinmarketcap" in transcription:
        webbrowser.open("https://www.coinmarketcap.com")
        print("Opened CoinMarketCap.")
    elif "speedtest" in transcription:
        webbrowser.open("https://www.speedtest.net")
        print("Opened Speedtest.")
    elif "character ai" in transcription:
        webbrowser.open("https://character.ai")
        print("Opened Character AI.")
    elif "deepl" in transcription:
        webbrowser.open("https://www.deepl.com")
        print("Opened DeepL.")
    elif "nih" in transcription:
        webbrowser.open("https://www.nih.gov")
        print("Opened NIH.")

    # === Project Management Tools ===
    elif "trello" in transcription:
        webbrowser.open("https://trello.com")
        print("Opened Trello.")
    elif "asana" in transcription:
        webbrowser.open("https://asana.com")
        print("Opened Asana.")

    # === CRM Tools ===
    elif "hubspot" in transcription:
        webbrowser.open("https://www.hubspot.com")
        print("Opened HubSpot.")
    elif "salesforce" in transcription:
        webbrowser.open("https://www.salesforce.com")
        print("Opened Salesforce.")

    # === Communication Apps ===
    elif "slack" in transcription:
        webbrowser.open("https://slack.com")
        print("Opened Slack.")
    elif "microsoft teams" in transcription or "teams" in transcription:
        webbrowser.open("https://teams.microsoft.com")
        print("Opened Microsoft Teams.")

    # === Cloud Storage ===
    elif "google drive" in transcription or "drive" in transcription:
        webbrowser.open("https://drive.google.com")
        print("Opened Google Drive.")
    elif "dropbox" in transcription:
        webbrowser.open("https://www.dropbox.com")
        print("Opened Dropbox.")

    # === Collaborative Editing ===
    elif "google docs" in transcription or "docs" in transcription:
        webbrowser.open("https://docs.google.com")
        print("Opened Google Docs.")
    elif "office online" in transcription or "microsoft office online" in transcription:
        webbrowser.open("https://www.office.com")
        print("Opened Office Online.")

    # === Accounting Software ===
    elif "quickbooks" in transcription:
        webbrowser.open("https://quickbooks.intuit.com")
        print("Opened QuickBooks.")
    elif "xero" in transcription:
        webbrowser.open("https://www.xero.com")
        print("Opened Xero.")

    # === Social Media Management ===
    elif "hootsuite" in transcription:
        webbrowser.open("https://hootsuite.com")
        print("Opened Hootsuite.")
    elif "buffer" in transcription:
        webbrowser.open("https://buffer.com")
        print("Opened Buffer.")

    # === E-commerce Platforms ===
    elif "shopify" in transcription:
        webbrowser.open("https://www.shopify.com")
        print("Opened Shopify.")
    elif "woocommerce" in transcription:
        webbrowser.open("https://woocommerce.com")
        print("Opened WooCommerce.")

    # === Analytics Tools ===
    elif "google analytics" in transcription or "analytics" in transcription:
        webbrowser.open("https://analytics.google.com")
        print("Opened Google Analytics.")
    elif "mixpanel" in transcription:
        webbrowser.open("https://mixpanel.com")
        print("Opened Mixpanel.")

    # === Email Marketing ===
    elif "mailchimp" in transcription:
        webbrowser.open("https://mailchimp.com")
        print("Opened Mailchimp.")
    elif "constant contact" in transcription:
        webbrowser.open("https://www.constantcontact.com")
        print("Opened Constant Contact.")

    # === HR Management Systems ===
    elif "bamboohr" in transcription:
        webbrowser.open("https://www.bamboohr.com")
        print("Opened BambooHR.")
    elif "workday" in transcription:
        webbrowser.open("https://www.workday.com")
        print("Opened Workday.")

    # === Learning Management Systems ===
    elif "moodle" in transcription:
        webbrowser.open("https://moodle.com")
        print("Opened Moodle.")
    elif "talentlms" in transcription:
        webbrowser.open("https://www.talentlms.com")
        print("Opened TalentLMS.")

    # === Bug Tracking Software ===
    elif "jira" in transcription:
        webbrowser.open("https://www.atlassian.com/software/jira")
        print("Opened Jira.")
    elif "bugzilla" in transcription:
        webbrowser.open("https://www.bugzilla.org")
        print("Opened Bugzilla.")

    # === Video Conferencing ===
    elif "zoom" in transcription:
        webbrowser.open("https://zoom.us")
        print("Opened Zoom.")
    elif "microsoft teams" in transcription or "teams" in transcription:
        webbrowser.open("https://teams.microsoft.com")
        print("Opened Microsoft Teams.")

    # === Time Tracking ===
    elif "harvest" in transcription:
        webbrowser.open("https://www.getharvest.com")
        print("Opened Harvest.")
    elif "toggl" in transcription:
        webbrowser.open("https://www.toggl.com")
        print("Opened Toggl.")

    # === Appointment Scheduling ===
    elif "calendly" in transcription:
        webbrowser.open("https://calendly.com")
        print("Opened Calendly.")
    elif "doodle" in transcription:
        webbrowser.open("https://doodle.com")
        print("Opened Doodle.")

    # === Customer Support Tools ===
    elif "zendesk" in transcription:
        webbrowser.open("https://www.zendesk.com")
        print("Opened Zendesk.")
    elif "freshdesk" in transcription:
        webbrowser.open("https://freshdesk.com")
        print("Opened Freshdesk.")

    # === Code Repository ===
    elif "github" in transcription or "git hub" in transcription:
        webbrowser.open("https://github.com")
        print("Opened GitHub.")
    elif "bitbucket" in transcription:
        webbrowser.open("https://bitbucket.org")
        print("Opened Bitbucket.")

    # === Password Management ===
    elif "lastpass" in transcription:
        webbrowser.open("https://www.lastpass.com")
        print("Opened LastPass.")
    elif "1password" in transcription or "one password" in transcription:
        webbrowser.open("https://1password.com")
        print("Opened 1Password.")

    # === Survey and Feedback Apps ===
    elif "surveymonkey" in transcription:
        webbrowser.open("https://www.surveymonkey.com")
        print("Opened SurveyMonkey.")
    elif "typeform" in transcription:
        webbrowser.open("https://www.typeform.com")
        print("Opened Typeform.")

    # === Blogging Platforms ===
    elif "wordpress" in transcription:
        webbrowser.open("https://wordpress.com")
        print("Opened WordPress.")
    elif "livejournal" in transcription:
        webbrowser.open("https://www.livejournal.com")
        print("Opened LiveJournal.")
    elif "ghost" in transcription:
        webbrowser.open("https://ghost.org")
        print("Opened Ghost.")

    # === Forums ===
    elif "vanilla forums" in transcription or "vanilla" in transcription:
        webbrowser.open("https://vanillaforums.com")
        print("Opened Vanilla Forums.")
    elif "phpbb" in transcription:
        webbrowser.open("https://www.phpbb.com")
        print("Opened phpBB.")
    elif "fluxbb" in transcription:
        webbrowser.open("https://fluxbb.org")
        print("Opened FluxBB.")
    elif "discourse" in transcription:
        webbrowser.open("https://www.discourse.org")
        print("Opened Discourse.")
    elif "mybb" in transcription:
        webbrowser.open("https://mybb.com")
        print("Opened MyBB.")

    # === Distributed Social Networks ===
    elif "mastodon" in transcription:
        webbrowser.open("https://mastodon.social")
        print("Opened Mastodon.")
    elif "friendica" in transcription:
        webbrowser.open("https://friendi.ca")
        print("Opened Friendica.")
    elif "diaspora" in transcription:
        webbrowser.open("https://diasporafoundation.org")
        print("Opened Diaspora.")
    elif "gnusocial" in transcription:
        webbrowser.open("https://gnu.io/social")
        print("Opened GNU Social.")

    # === Social Bookmarking ===
    elif "scuttle" in transcription:
        webbrowser.open("https://scuttle.org")
        print("Opened Scuttle.")
    elif "meneame" in transcription:
        webbrowser.open("https://www.meneame.net")
        print("Opened Meneame.")

    # === File Sharing and Sync ===
    elif "nextcloud" in transcription:
        webbrowser.open("https://nextcloud.com")
        print("Opened Nextcloud.")
    elif "owncloud" in transcription:
        webbrowser.open("https://owncloud.com")
        print("Opened ownCloud.")
    elif "seafile" in transcription:
        webbrowser.open("https://www.seafile.com")
        print("Opened Seafile.")
    elif "ifolder" in transcription:
        webbrowser.open("https://www.ifolder.com")
        print("Opened iFolder.")

    # === Webmail ===
    elif "squirrelmail" in transcription:
        webbrowser.open("https://www.squirrelmail.org")
        print("Opened SquirrelMail.")
    elif "roundcube" in transcription:
        webbrowser.open("https://roundcube.net")
        print("Opened Roundcube.")
    elif "imp" in transcription:
        webbrowser.open("https://www.horde.org/imp")
        print("Opened IMP.")

    # === Online Office Suites ===
    elif "collabora online" in transcription:
        webbrowser.open("https://www.collaboraoffice.com")
        print("Opened Collabora Online.")
    elif "feng office" in transcription:
        webbrowser.open("https://www.fengoffice.com")
        print("Opened Feng Office.")
    elif "egroupware" in transcription:
        webbrowser.open("https://www.egroupware.org")
        print("Opened eGroupware.")
    elif "phpgroupware" in transcription:
        webbrowser.open("https://phpgroupware.org")
        print("Opened PHPGroupware.")
    elif "etherpad" in transcription:
        webbrowser.open("https://etherpad.org")
        print("Opened Etherpad.")

    # === Wikis ===
    elif "mediawiki" in transcription:
        webbrowser.open("https://www.mediawiki.org")
        print("Opened MediaWiki.")
    elif "dokuwiki" in transcription:
        webbrowser.open("https://www.dokuwiki.org")
        print("Opened DokuWiki.")
    elif "tiddlywiki" in transcription:
        webbrowser.open("https://tiddlywiki.com")
        print("Opened TiddlyWiki.")

    # === Mapping and Virtual Worlds ===
    elif "openstreetmap" in transcription:
        webbrowser.open("https://www.openstreetmap.org")
        print("Opened OpenStreetMap.")
    elif "opensimulator" in transcription:
        webbrowser.open("http://opensimulator.org")
        print("Opened OpenSimulator.")
    elif "opencroquet" in transcription:
        webbrowser.open("http://opencroquet.org")
        print("Opened OpenCroquet.")

    # === Password Management ===
    elif "bitwarden" in transcription:
        webbrowser.open("https://bitwarden.com")
        print("Opened Bitwarden.")
    elif "lastpass" in transcription:
        webbrowser.open("https://www.lastpass.com")
        print("Opened LastPass.")
    elif "1password" in transcription or "one password" in transcription:
        webbrowser.open("https://1password.com")
        print("Opened 1Password.")

    # === Video Streaming ===
    elif "peertube" in transcription:
        webbrowser.open("https://joinpeertube.org")
        print("Opened PeerTube.")
    elif "plumi" in transcription:
        webbrowser.open("https://plumi.org")
        print("Opened Plumi.")
    elif "openbroadcaster" in transcription:
        webbrowser.open("https://openbroadcaster.com")
        print("Opened OpenBroadcaster.")

    # === Surveys and Feedback ===
    elif "limesurvey" in transcription:
        webbrowser.open("https://www.limesurvey.org")
        print("Opened LimeSurvey.")
    elif "surveymonkey" in transcription:
        webbrowser.open("https://www.surveymonkey.com")
        print("Opened SurveyMonkey.")
    elif "typeform" in transcription:
        webbrowser.open("https://www.typeform.com")
        print("Opened Typeform.")

    # === Bibliographic Tools ===
    elif "citeseerx" in transcription:
        webbrowser.open("https://citeseerx.ist.psu.edu")
        print("Opened CiteSeerX.")

    # === Translation Tools ===
    elif "apertium" in transcription:
        webbrowser.open("https://www.apertium.org")
        print("Opened Apertium.")

    # === Music Streaming ===
    elif "libre fm" in transcription or "librefm" in transcription:
        webbrowser.open("https://libre.fm")
        print("Opened Libre.fm.")

    # === Time Tracking and Productivity ===
    elif "livetimer" in transcription:
        webbrowser.open("https://www.livetimer.com")
        print("Opened LiveTimer.")
    elif "tempo" in transcription:
        webbrowser.open("https://tempo.io")
        print("Opened Tempo.")
    elif "rescuetime" in transcription:
        webbrowser.open("https://www.rescuetime.com")
        print("Opened RescueTime.")
    elif "xpenser" in transcription:
        webbrowser.open("https://www.xpenser.com")
        print("Opened Xpenser.")
    elif "myhours" in transcription:
        webbrowser.open("https://www.myhours.com")
        print("Opened MyHours.")
    elif "tsheets" in transcription:
        webbrowser.open("https://www.tsheets.com")
        print("Opened TSheets.")

    # === File Sharing and Collaboration ===
    elif "nomadesk" in transcription:
        webbrowser.open("https://www.nomadesk.com")
        print("Opened NomaDesk.")
    elif "logmein" in transcription:
        webbrowser.open("https://www.logmein.com")
        print("Opened LogMeIn.")
    elif "mybloop" in transcription:
        webbrowser.open("https://www.mybloop.com")
        print("Opened MyBloop.")
    elif "zimbra" in transcription:
        webbrowser.open("https://www.zimbra.com")
        print("Opened Zimbra.")
    elif "nextcloud" in transcription:
        webbrowser.open("https://nextcloud.com")
        print("Opened Nextcloud.")
    elif "seafile" in transcription:
        webbrowser.open("https://www.seafile.com")
        print("Opened Seafile.")

    # === Project Management and Planning ===
    elif "wrike" in transcription:
        webbrowser.open("https://www.wrike.com")
        print("Opened Wrike.")
    elif "zoho" in transcription:
        webbrowser.open("https://www.zoho.com")
        print("Opened Zoho.")
    elif "trailfire" in transcription:
        webbrowser.open("https://www.trailfire.com")
        print("Opened Trailfire.")
    elif "teleport" in transcription:
        webbrowser.open("https://teleporthq.io")
        print("Opened Teleport.")
    elif "calendar hub" in transcription:
        webbrowser.open("https://www.calendarhub.com")
        print("Opened Calendar Hub.")
    elif "tripit" in transcription:
        webbrowser.open("https://www.tripit.com")
        print("Opened TripIt.")

    # === Video and Media Sharing ===
    elif "vimeo" in transcription:
        webbrowser.open("https://vimeo.com")
        print("Opened Vimeo.")
    elif "metacafe" in transcription:
        webbrowser.open("https://www.metacafe.com")
        print("Opened Metacafe.")
    elif "pandora" in transcription:
        webbrowser.open("https://www.pandora.com")
        print("Opened Pandora.")
    elif "dailymotion" in transcription:
        webbrowser.open("https://www.dailymotion.com")
        print("Opened Dailymotion.")
    elif "clipshack" in transcription:
        webbrowser.open("https://www.clipshack.com")
        print("Opened ClipShack.")
    elif "imeem" in transcription:
        webbrowser.open("https://www.imeem.com")
        print("Opened Imeem.")

    # === Social and Recommender Systems ===
    elif "vsocial" in transcription:
        webbrowser.open("https://www.vsocial.com")
        print("Opened vSocial.")
    elif "strands" in transcription:
        webbrowser.open("https://www.strands.com")
        print("Opened Strands.")
    elif "tall street" in transcription:
        webbrowser.open("https://www.tallstreet.com")
        print("Opened Tall Street.")
    elif "wink" in transcription:
        webbrowser.open("https://wink.com")
        print("Opened Wink People Search.")
    elif "ask" in transcription:
        webbrowser.open("https://www.ask.com")
        print("Opened Askeet.")

    # === AI and Automation Tools ===
    elif "chatgpt" in transcription or "openai" in transcription:
        webbrowser.open("https://chat.openai.com")
        print("Opened ChatGPT.")
    elif "tldr" in transcription:
        webbrowser.open("https://tldrthis.com")
        print("Opened TLDR This.")
    elif "hey friday" in transcription or "friday" in transcription:
        webbrowser.open("https://heyfriday.ai")
        print("Opened Hey Friday.")
    elif "sidekick" in transcription:
        webbrowser.open("https://www.runsidekick.com")
        print("Opened Sidekick.")

    # === Tools for Developers ===
    elif "foxit pdf mobile" in transcription:
        webbrowser.open("https://www.foxit.com/mobile-pdf")
        print("Opened Foxit PDF Mobile.")
    elif "extends class" in transcription or "extend" in transcription:
        webbrowser.open("https://extendsclass.com")
        print("Opened Extends Class.")
    elif "pull request" in transcription or "pull" in transcription or "request" in transcription:
        webbrowser.open("https://pullrequest.com")
        print("Opened Pull Request.")

    # === Entertainment and Travel ===
    elif "linkup" in transcription or "link" in transcription:
        webbrowser.open("https://www.linkup.com")
        print("Opened LinkUp.")
    elif "rawsugar" in transcription:
        webbrowser.open("https://rawsugar.com")
        print("Opened RawSugar.")
    elif "otavo" in transcription:
        webbrowser.open("https://otavo.com")
        print("Opened Otavo.")
    elif "camp fire usa" in transcription or "campfire usa" in transcription or "campfire, usa" in transcription:
        webbrowser.open("https://campfire.org")
        print("Opened Camp Fire USA.")

    # === Video and Media Creation/Sharing ===
    elif "jumpcut" in transcription or "jumb cut" in transcription or "jump tab" in transcription:
        webbrowser.open("https://www.jumpcut.com")
        print("Opened Jumpcut.")
    elif "revver" in transcription:
        webbrowser.open("https://www.revver.com")
        print("Opened Revver.")
    elif "vimeo" in transcription:
        webbrowser.open("https://vimeo.com")
        print("Opened Vimeo.")
    elif "metacafe" in transcription or "meta cave" in transcription:
        webbrowser.open("https://www.metacafe.com")
        print("Opened Metacafe.")
    elif "clipshack" in transcription:
        webbrowser.open("https://www.clipshack.com")
        print("Opened ClipShack.")
    elif "dailymotion" in transcription:
        webbrowser.open("https://www.dailymotion.com")
        print("Opened Dailymotion.")
    elif "imeem" in transcription:
        webbrowser.open("https://www.imeem.com")
        print("Opened Imeem.")

    # === Music Discovery and Streaming ===
    elif "musicovery" in transcription:
        webbrowser.open("https://musicovery.com")
        print("Opened Musicovery.")
    elif "ilike" in transcription:
        webbrowser.open("https://www.ilike.com")
        print("Opened iLike.")
    elif "pandora" in transcription:
        webbrowser.open("https://www.pandora.com")
        print("Opened Pandora.")

    # === Event and Task Management ===
    elif "eventful" in transcription:
        webbrowser.open("https://www.eventful.com")
        print("Opened Eventful.")
    elif "cogram" in transcription:
        webbrowser.open("https://www.cogram.com")
        print("Opened Cogram.")

    # === Social Bookmarking and Discovery ===
    elif "blummy" in transcription:
        webbrowser.open("https://www.blummy.com")
        print("Opened Blummy.")
    elif "trailfire" in transcription:
        webbrowser.open("https://www.trailfire.com")
        print("Opened Trailfire.")
    elif "blogmarks" in transcription:
        webbrowser.open("https://www.blogmarks.net")
        print("Opened BlogMarks.")
    elif "linkatopia" in transcription:
        webbrowser.open("https://www.linkatopia.com")
        print("Opened Linkatopia.")
    elif "tektag" in transcription:
        webbrowser.open("https://www.tektag.com")
        print("Opened TekTag.")
    elif "ma.gnolia" in transcription:
        webbrowser.open("https://www.ma.gnolia.com")
        print("Opened Ma.gnolia.")
    elif "diigo" in transcription:
        webbrowser.open("https://www.diigo.com")
        print("Opened Diigo.")

    # === AI Tools ===
    elif "tabnine" in transcription:
        webbrowser.open("https://www.tabnine.com")
        print("Opened Tabnine.")
    elif "browse ai" in transcription:
        webbrowser.open("https://www.browse.ai")
        print("Opened Browse AI.")
    elif "promptlayer" in transcription:
        webbrowser.open("https://promptlayer.com")
        print("Opened PromptLayer.")
    elif "nuclia" in transcription:
        webbrowser.open("https://www.nuclia.com")
        print("Opened Nuclia.")
    elif "axiom ai" in transcription:
        webbrowser.open("https://www.axiom.ai")
        print("Opened Axiom AI.")
    elif "riku ai" in transcription:
        webbrowser.open("https://riku.ai")
        print("Opened Riku AI.")
    elif "robovision" in transcription:
        webbrowser.open("https://www.robovision.ai")
        print("Opened Robovision.")
    elif "seek ai" in transcription:
        webbrowser.open("https://www.seek.ai")
        print("Opened Seek AI.")

    # === Development and Code Collaboration ===
    elif "replit" in transcription:
        webbrowser.open("https://replit.com")
        print("Opened Replit.")
    elif "dotnetkicks" in transcription:
        webbrowser.open("https://www.dotnetkicks.com")
        print("Opened DotNetKicks.")
    elif "message dance" in transcription:
        webbrowser.open("https://www.messagedance.com")
        print("Opened MessageDance.")

    # === Networking and Messaging ===
    elif "ebuddy" in transcription:
        webbrowser.open("https://www.ebuddy.com")
        print("Opened eBuddy.")
    elif "fring" in transcription:
        webbrowser.open("https://www.fring.com")
        print("Opened Fring.")
    elif "trillian" in transcription:
        webbrowser.open("https://www.trillian.im")
        print("Opened Trillian.")

    # === Data Management and Tracking ===
    elif "zoto" in transcription:
        webbrowser.open("https://www.zoto.com")
        print("Opened Zoto.")
    elif "eventful" in transcription:
        webbrowser.open("https://www.eventful.com")
        print("Opened Eventful.")
    elif "networthiq" in transcription:
        webbrowser.open("https://www.networthiq.com")
        print("Opened NetworthIQ.")

    # === Bonus Apps ===
    elif "cligs" in transcription:
        webbrowser.open("https://www.cligs.com")
        print("Opened Cligs.")
    elif "joopz" in transcription:
        webbrowser.open("https://www.joopz.com")
        print("Opened Joopz.")
    elif "jajah" in transcription:
        webbrowser.open("https://www.jajah.com")
        print("Opened JAJAH.")

    # === New Social Media and Communication ===
    elif "live" in transcription:
        webbrowser.open("https://www.live.com")
        print("Opened Live.")
    elif "t.me" in transcription or "telegram link" in transcription:
        webbrowser.open("https://t.me")
        print("Opened Telegram Link.")
    elif "pixiv" in transcription:
        webbrowser.open("https://www.pixiv.net")
        print("Opened Pixiv.")
    elif "vk" in transcription or "vkontakte" in transcription:
        webbrowser.open("https://www.vk.com")
        print("Opened VKontakte.")
    elif "x" in transcription or "x dot com" in transcription:
        webbrowser.open("https://www.x.com")
        print("Opened X.")

    # === New E-commerce and Retail ===
    elif "amazon japan" in transcription or "amazon.co.jp" in transcription:
        webbrowser.open("https://www.amazon.co.jp")
        print("Opened Amazon Japan.")
    elif "amazon india" in transcription or "amazon.in" in transcription:
        webbrowser.open("https://www.amazon.in")
        print("Opened Amazon India.")
    elif "rakuten" in transcription:
        webbrowser.open("https://www.rakuten.co.jp")
        print("Opened Rakuten.")
    elif "temu" in transcription:
        webbrowser.open("https://www.temu.com")
        print("Opened Temu.")
    elif "etsy" in transcription:
        webbrowser.open("https://www.etsy.com")
        print("Opened Etsy.")

    # === Entertainment and Streaming ===
    elif "hanime" in transcription or "hanime.tv" in transcription:
        webbrowser.open("https://www.hanime.tv")
        print("Opened Hanime.")
    elif "animeflv" in transcription:
        webbrowser.open("https://www.animeflv.net")
        print("Opened AnimeFLV.")
    elif "animesuge" in transcription:
        webbrowser.open("https://www.animesuge.to")
        print("Opened AnimeSuge.")
    elif "roblox" in transcription:
        webbrowser.open("https://www.roblox.com")
        print("Opened Roblox.")
    elif "steampowered" in transcription or "steam" in transcription:
        webbrowser.open("https://www.steampowered.com")
        print("Opened Steam.")

    # === Productivity and Tools ===
    elif "archive of our own" in transcription or "ao3" in transcription:
        webbrowser.open("https://www.archiveofourown.org")
        print("Opened Archive of Our Own (AO3).")
    elif "sharepoint" in transcription:
        webbrowser.open("https://www.sharepoint.com")
        print("Opened SharePoint.")
    elif "adjust" in transcription:
        webbrowser.open("https://www.adjust.com")
        print("Opened Adjust.")

    # === News and Media ===
    elif "marca" in transcription:
        webbrowser.open("https://www.marca.com")
        print("Opened Marca.")
    elif "as.com" in transcription:
        webbrowser.open("https://www.as.com")
        print("Opened AS.")
    elif "nytimes" in transcription or "new york times" in transcription:
        webbrowser.open("https://www.nytimes.com")
        print("Opened The New York Times.")
    elif "the guardian" in transcription:
        webbrowser.open("https://www.theguardian.com")
        print("Opened The Guardian.")

    # === File Sharing and Shortening ===
    elif "mediafire" in transcription:
        webbrowser.open("https://www.mediafire.com")
        print("Opened MediaFire.")
    elif "goo.gl" in transcription:
        webbrowser.open("https://www.goo.gl")
        print("Opened Goo.gl.")
    elif "page link" in transcription:
        webbrowser.open("https://www.page.link")
        print("Opened Page.link.")
    elif "app link" in transcription:
        webbrowser.open("https://www.app.link")
        print("Opened App.link.")

    # === Entertainment and Fandom ===
    elif "fandom" in transcription:
        webbrowser.open("https://www.fandom.com")
        print("Opened Fandom.")
    elif "fanfiction" in transcription:
        webbrowser.open("https://www.fanfiction.net")
        print("Opened FanFiction.")

    # === Manga and Anime ===
    elif "syosetu" in transcription:
        webbrowser.open("https://www.syosetu.com")
        print("Opened Syosetu.")
    elif "mangadex" in transcription:
        webbrowser.open("https://www.mangadex.org")
        print("Opened MangaDex.")
    elif "mangago" in transcription:
        webbrowser.open("https://www.mangago.me")
        print("Opened MangaGo.")
    elif "mangakakalot" in transcription:
        webbrowser.open("https://www.mangakakalot.com")
        print("Opened MangaKakalot.")

    # === Miscellaneous ===
    elif "apple" in transcription:
        webbrowser.open("https://www.apple.com")
        print("Opened Apple.")
    elif "noodlemagazine" in transcription:
        webbrowser.open("https://www.noodlemagazine.com")
        print("Opened NoodleMagazine.")
    elif "dzen" in transcription:
        webbrowser.open("https://www.dzen.ru")
        print("Opened Dzen.")
    elif "fmoviesz" in transcription:
        webbrowser.open("https://www.fmoviesz.to")
        print("Opened FMovies.")
    elif "ign" in transcription:
        webbrowser.open("https://www.ign.com")
        print("Opened IGN.")
    elif "bit.ly" in transcription:
        webbrowser.open("https://www.bit.ly")
        print("Opened Bit.ly.")




    # === Window and Display Controls ===
    elif "maximize" in transcription and "window" in transcription or "maximize" in transcription and "windows" in transcription:
        pyautogui.hotkey("alt", "space")
        time.sleep(0.2)
        pyautogui.press("x")
    elif "minimize" in transcription and "the window" in transcription or "minimize" in transcription and "windows" in transcription:
        pyautogui.hotkey("alt", "space")
        time.sleep(0.2)
        pyautogui.press("n")
    elif "close" in transcription and "window" in transcription or "close" in transcription and "windows" in transcription:
        pyautogui.hotkey("alt", "f4")

    # === Desktop and Display Controls ===
    elif "new" in transcription and "desktop" in transcription or "new" and "desktops" in transcription:
        pyautogui.hotkey("win", "ctrl", "d")
    elif "switch" in transcription and "desktop" in transcription or "switch" and "desktops" in transcription:
        pyautogui.hotkey("win", "ctrl", "right")
    elif "close" in transcription and "desktop" in transcription or "close" and "desktops" in transcription:
        pyautogui.hotkey("win", "ctrl", "f4")

     # === Function Keys Commands ===
    elif "press f1" in transcription:
        pyautogui.press('f1')
    elif "press f2" in transcription:
        pyautogui.press('f2')
    elif "press f3" in transcription:
        pyautogui.press('f3')
    elif "press f4" in transcription:
        pyautogui.press('f4')
    elif "press f5" in transcription:
        pyautogui.press('f5')
    elif "press f6" in transcription:
        pyautogui.press('f6')
    elif "press f7" in transcription:
        pyautogui.press('f7')
    elif "press f8" in transcription:
        pyautogui.press('f8')
    elif "press f9" in transcription:
        pyautogui.press('f9')
    elif "press f10" in transcription:
        pyautogui.press('f10')
    elif "press f11" in transcription:
        pyautogui.press('f11')
    elif "press f12" in transcription:
        pyautogui.press('f12')

    # === Mouse Actions ===
    elif "double" in transcription and "click" in transcription: 
        pyautogui.click(clicks=2, interval=0.25)
    elif "click" in transcription:
        pyautogui.click()
    elif "right" in transcription and "click" in transcription:
        pyautogui.click(button="right")

    # === Ending the Program ===
    elif "end the program" in transcription or "stop" in transcription and "program" in transcription:
        print("Program ending")
        os._exit(0)

    # Example: Debugging in Sidebar
    #st.sidebar.write(f"Executed command: {transcription}")
    

# Function to send and receive data from the WebSocket
async def send_receive():
    global transcription_queue
    async with websockets.connect(
        URL,
        extra_headers=(("Authorization", auth_key),),
        ping_interval=5,
        ping_timeout=20
    ) as _ws:
        print("Connected to WebSocket")

        session_begins = await _ws.recv()
        print("Session begins:", session_begins)

        async def send():
            while running_event.is_set():
                try:
                    data = stream.read(FRAME_PER_BUFFER)
                    data = base64.b64encode(data).decode("utf-8")
                    json_data = json.dumps({"audio_data": str(data)})

                    await _ws.send(json_data)
                except websockets.exceptions.ConnectionClosedError:
                    print("Connection closed during send")
                    break
                except Exception as e:
                    print("Error in send:", e)
                    break
                await asyncio.sleep(0.01)

        async def receive():
            accumulated_text = ""  # Accumulate the text during speech
            last_received_time = time.time()  # Track the last time text was received
            pause_threshold = 1.0  # Time in seconds to consider a pause in speech

            while running_event.is_set():
                try:
                    result_str = await _ws.recv()
                    current_text = json.loads(result_str).get('text', '').strip()

                    # Process only when new text arrives
                    if current_text:
                        print(f"New transcription chunk: {current_text}")
                        accumulated_text = current_text
                        last_received_time = time.time()

                    # Check if there’s a pause and process the accumulated text
                    if time.time() - last_received_time > pause_threshold and accumulated_text:
                        print(f"Final transcription after pause: {accumulated_text}")
                        transcription_queue.put(accumulated_text)  # Add transcription to the queue
                        accumulated_text = ""  # Reset after processing
                except websockets.exceptions.ConnectionClosedError:
                    print("Connection closed during receive")
                    break
                except Exception as e:
                    print("Error in receive:", e)
                    break

        await asyncio.gather(send(), receive())

# Start the application when the START button is pressed
if start_app:
    running_event.set()
    threading.Thread(target=lambda: asyncio.run(send_receive()), daemon=True).start()

    # Initialize the camera for hand tracking
    cap = cv2.VideoCapture(0)
    detector = htm.handDetector(maxHands=1)
    wScr, hScr = pyautogui.size()
    plocX, plocY = 0, 0
    clocX, clocY = 0, 0
    last_transcription_time = time.time()
    DEBOUNCE_DELAY = 0.5  # Debounce delay for processing transcriptions
    transcription_text = ""

    while running_event.is_set():
        # Check if the STOP button is pressed
        if stop_app:
            st.write("Application Stopped!")
            running_event.clear()
            break

        # Read camera frame
        success, img = cap.read()
        if not success:
            st.warning("Failed to access the camera.")
            break

        # Process hand landmarks
        img = detector.findHands(img)
        lmList, bbox = detector.findPosition(img)
        
        if len(lmList) != 0:
            x1, y1 = lmList[8][1:]  # Index finger tip
            x2, y2 = lmList[12][1:]  # Middle finger tip

            # Check which fingers are up
            fingers = detector.fingersUp()

            # Draw rectangle for frame reduction
            cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR), (255, 0, 255), 2)

            # Moving mode
            if fingers[1] == 1 and fingers[2] == 0:  # Only index finger is up
                x3 = np.interp(x1, (frameR, wCam - frameR), (0, wScr))
                y3 = np.interp(y1, (frameR, hCam - frameR), (0, hScr))

                # Smoothen values
                clocX = plocX + (x3 - plocX) / smoothening
                clocY = plocY + (y3 - plocY) / smoothening

                # Move mouse
                pyautogui.moveTo(wScr - clocX, clocY)
                cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
                plocX, plocY = clocX, clocY

            # Selection mode: Index and middle fingers up
            elif fingers[1] == 1 and fingers[2] == 1 and selection_mode:
                x3 = np.interp(x1, (frameR, wCam - frameR), (0, wScr))
                y3 = np.interp(y1, (frameR, hCam - frameR), (0, hScr))

                # Smoothen values
                clocX = plocX + (x3 - plocX) / smoothening
                clocY = plocY + (y3 - plocY) / smoothening

                # Move mouse
                pyautogui.moveTo(wScr - clocX, clocY)
                cv2.circle(img, (x1, y1), 15, (0, 255, 0), cv2.FILLED)  # Green circle for selection mode
                
                # Start dragging if it's the first move in selection mode
                if not pyautogui.mouseDown():
                    pyautogui.mouseDown()

                plocX, plocY = clocX, clocY

            # Stop dragging: No fingers up
            elif all(f == 0 for f in fingers) and selection_mode:
                pyautogui.mouseUp()

        # Calculate and display frame rate
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime
        cv2.putText(img, str(int(fps)), (20, 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)

        # Display camera feed in Streamlit
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        frame_placeholder.image(img, channels="RGB")

        # Continuously update the transcription output from the queue
        current_time = time.time()
        if not transcription_queue.empty() and (current_time - last_transcription_time > DEBOUNCE_DELAY):
            transcription = transcription_queue.get()
            print(f"Received transcription: {transcription}")

            # Update transcription display
            transcription_text += transcription + "\n"
            if len(transcription_text) > 500:
                transcription_text = transcription_text[-500:]  # Keep only the last 500 characters

            transcription_placeholder.text_area(
                "Real-Time Transcription",
                transcription_text,
                height=300,
            )

            # Execute the command based on the transcription
            perform_command(transcription)
            last_transcription_time = current_time

# Cleanup when the application is stopped
if cap is not None:
    cap.release()
    cv2.destroyAllWindows()
    if running_event.is_set():
        running_event.clear()
        st.sidebar.write("Application stopped.")