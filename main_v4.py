import datetime
import json
import os
import platform
import re
import subprocess
import threading
import urllib.parse
import webbrowser
import base64
import ast
import operator as op
import socket
import time
import shutil
import sys
import ctypes
import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageTk

import requests
import speech_recognition as sr
import numpy as np
import sounddevice as sd


# ============================================================
# RAX - CONFIGURATION
# ============================================================

ASSISTANT_NAME = "RAX"
LANGUAGE = "en-IN"

# RAX multilingual speech support.
# Set ACTIVE_LANGUAGE to "auto" to try the configured languages, or select one
# explicitly with commands such as "language Hindi" / "भाषा हिंदी".
RAX_LANGUAGES = {
    "english": "en-IN",
    "hindi": "hi-IN",
    "bengali": "bn-IN",
    "maithili": "mai-IN",
    "bhojpuri": "bho-IN",
    "marathi": "mr-IN",
    "french": "fr-FR",
}
ACTIVE_LANGUAGE = "english"
LANGUAGE_MODE = "selected"
VOICE_RATE = 0
VOICE_VOLUME = 100

# "Open my PC" voice-password protection
PC_VOICE_PASSWORD = "140507"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NOTES_FILE = os.path.join(BASE_DIR, "rax_notes.txt")
ALARMS_FILE = os.path.join(BASE_DIR, "rax_alarms.json")
COMMAND_HISTORY_FILE = os.path.join(BASE_DIR, "rax_command_history.txt")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "RAX_Screenshots")
CODE_DIR = os.path.join(BASE_DIR, "RAX_Code")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
RAX_AI_MODEL = os.getenv("RAX_AI_MODEL", "gpt-5.6").strip()
JUDGE0_URLS = [
    "https://ce.judge0.com",
    "https://extra-ce.judge0.com",
]
LAST_COMMAND = None

# ============================================================
# RAX IDLE SLEEP / WAKE MODE
# ============================================================
IDLE_TIMEOUT_SECONDS = 60
SLEEP_MODE = False
LAST_ACTIVITY_TIME = time.monotonic()

# ============================================================
# RAX FRIEND / MOOD CONVERSATION
# ============================================================
FRIEND_CONVERSATION_ENABLED = True
FRIEND_STAGE = "mood"  # mood -> why -> day -> normal
FRIEND_GREETED = False

# ============================================================
# CHROME PROFILE / BROWSER CONTROL
# ============================================================
CHROME_USER_DATA_DIR = os.path.join(os.getenv("LOCALAPPDATA", ""), "Google", "Chrome", "User Data")
CHROME_SELECTED_PROFILE = None
CHROME_PROFILE_CHOICES = {}


# ============================================================
# RAX DESKTOP GUI - ULTIMATE EDITION
# ============================================================

GUI_ROOT = None
GUI_CHAT = None
GUI_STATUS = None
GUI_LISTEN_BUTTON = None
GUI_COMMAND_ENTRY = None
GUI_RAX_IMAGE = None
GUI_RAX_LABEL = None
GUI_IMAGE_PANEL = None
GUI_RAX_SOURCE_IMAGE = None
GUI_ANIMATION_JOB = None
GUI_ANIMATION_STEP = 0
GUI_STATE = "online"
GUI_RUNNING = False
GUI_WAVE_CANVAS = None
GUI_WAVE_PHASE = 0.0
GUI_SYSTEM_LABELS = {}
GUI_ACTIVITY = []
GUI_AGENT_RUNNING = False
GUI_AGENT_STATUS = None
GUI_TAB_CONTENT = None
GUI_TABS = {}
GUI_CURRENT_TAB = "HOME"
GUI_PRO_STATUS = None
POMODORO_RUNNING = False
POMODORO_END = 0
POMODORO_AFTER = None

SKILLS_FILE = os.path.join(BASE_DIR, "rax_skills.json")
ROUTINES_FILE = os.path.join(BASE_DIR, "rax_routines.json")


def gui_safe(callback):
    if GUI_ROOT is not None:
        try:
            GUI_ROOT.after(0, callback)
        except Exception:
            pass


def gui_log(sender, message):
    if GUI_CHAT is None:
        return
    message = str(message).strip()
    if not message:
        return
    GUI_ACTIVITY.append({"sender": sender, "message": message, "time": datetime.datetime.now().strftime("%H:%M:%S")})
    GUI_ACTIVITY[:] = GUI_ACTIVITY[-100:]
    def update():
        if GUI_CHAT is None:
            return
        GUI_CHAT.config(state="normal")
        tag = "rax" if sender == "RAX" else "user"
        GUI_CHAT.insert(tk.END, f"\n{sender.upper()}  ", tag)
        GUI_CHAT.insert(tk.END, message + "\n")
        GUI_CHAT.see(tk.END)
        GUI_CHAT.config(state="disabled")
    gui_safe(update)


def gui_set_state(state):
    global GUI_STATE
    GUI_STATE = state
    labels = {
        "online": ("● RAX ONLINE", "#00ff88"),
        "listening": ("● RAX IS LISTENING...", "#00eaff"),
        "thinking": ("● RAX IS THINKING...", "#b66cff"),
        "speaking": ("● RAX IS SPEAKING...", "#00eaff"),
        "agent": ("● RAX AGENT ACTIVE...", "#ffb347"),
        "vision": ("● RAX VISION ACTIVE...", "#ff4fd8"),
    }
    text_value, status_color = labels.get(state, labels["online"])
    def update():
        if GUI_STATUS is not None:
            GUI_STATUS.config(text=text_value, fg=status_color)
        if GUI_LISTEN_BUTTON is not None:
            GUI_LISTEN_BUTTON.config(text="🎙 LISTENING..." if state == "listening" else "🎙 LISTEN")
        if GUI_IMAGE_PANEL is not None:
            GUI_IMAGE_PANEL.config(highlightbackground=status_color,
                                   highlightthickness=3 if state in {"listening", "speaking", "thinking", "agent", "vision"} else 2)
    gui_safe(update)


def gui_status(text_value, status_color="#00ff88"):
    text_upper = str(text_value).upper()
    if "LISTENING" in text_upper:
        gui_set_state("listening")
    elif "SPEAKING" in text_upper:
        gui_set_state("speaking")
    elif "THINKING" in text_upper:
        gui_set_state("thinking")
    elif "VISION" in text_upper:
        gui_set_state("vision")
    else:
        gui_set_state("online")


def _blend_color(c1, c2, amount):
    a = max(0.0, min(1.0, amount))
    r1, g1, b1 = (int(c1[i:i+2], 16) for i in (1, 3, 5))
    r2, g2, b2 = (int(c2[i:i+2], 16) for i in (1, 3, 5))
    return f"#{int(r1+(r2-r1)*a):02x}{int(g1+(g2-g1)*a):02x}{int(b1+(b2-b1)*a):02x}"


def animate_rax():
    global GUI_RAX_IMAGE, GUI_ANIMATION_STEP, GUI_ANIMATION_JOB, GUI_WAVE_PHASE
    if GUI_ROOT is None:
        return
    GUI_ANIMATION_STEP = (GUI_ANIMATION_STEP + 1) % 120
    GUI_WAVE_PHASE += 0.32
    active = GUI_STATE in {"listening", "speaking", "thinking", "agent", "vision"}
    if GUI_RAX_LABEL is not None and GUI_RAX_SOURCE_IMAGE is not None:
        import math
        wave = (math.sin(GUI_ANIMATION_STEP * math.pi / 30) + 1) / 2
        scale = 0.985 + (0.03 * wave if active else 0.008 * wave)
        source = GUI_RAX_SOURCE_IMAGE
        w, h = max(1, int(source.width*scale)), max(1, int(source.height*scale))
        frame = source.resize((w, h), Image.Resampling.LANCZOS)
        if active:
            from PIL import ImageFilter
            pad = 26
            glow = Image.new("RGBA", (w+pad*2, h+pad*2), (0,0,0,0))
            mask = Image.new("L", (w,h), int(75+100*wave)).filter(ImageFilter.GaussianBlur(14))
            layer = Image.new("RGBA", (w,h), (0,220,255,0)); layer.putalpha(mask)
            glow.paste(layer,(pad,pad),layer)
            canvas=Image.new("RGBA",glow.size,(0,0,0,0)); canvas.alpha_composite(glow); canvas.alpha_composite(frame.convert("RGBA"),(pad,pad)); frame=canvas.convert("RGB")
        GUI_RAX_IMAGE=ImageTk.PhotoImage(frame); GUI_RAX_LABEL.config(image=GUI_RAX_IMAGE)
    if GUI_WAVE_CANVAS is not None:
        draw_waveform()
    GUI_ANIMATION_JOB = GUI_ROOT.after(45, animate_rax)


def draw_waveform():
    import math
    c = GUI_WAVE_CANVAS
    if c is None:
        return
    try:
        width = max(100, c.winfo_width()); height = max(50, c.winfo_height())
        c.delete("wave")
        active = GUI_STATE in {"listening", "speaking", "thinking", "agent", "vision"}
        amp = 5 if not active else (12 if GUI_STATE == "listening" else 18)
        points=[]
        for x in range(0, width, 7):
            y=height/2 + math.sin(x*0.045 + GUI_WAVE_PHASE)*amp + math.sin(x*0.018-GUI_WAVE_PHASE*0.7)*amp*0.45
            points += [x,y]
        c.create_line(*points, fill="#00eaff" if active else "#27434a", width=2, smooth=True, tags="wave")
        for x in range(0,width,35):
            c.create_oval(x-1,height/2-1,x+1,height/2+1,fill="#29434a",outline="",tags="wave")
    except Exception:
        pass


def _card(parent, title, subtitle="", accent="#00eaff"):
    f=tk.Frame(parent,bg="#0b1015",highlightthickness=1,highlightbackground="#1d3038")
    tk.Label(f,text=title,font=("Segoe UI",11,"bold"),fg=accent,bg="#0b1015").pack(anchor="w",padx=12,pady=(10,2))
    if subtitle:
        tk.Label(f,text=subtitle,font=("Segoe UI",8),fg="#7d8b92",bg="#0b1015",wraplength=280,justify="left").pack(anchor="w",padx=12,pady=(0,10))
    return f


def _load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path,"r",encoding="utf8") as f: return json.load(f)
    except Exception: pass
    return default


def _save_json(path, data):
    try:
        with open(path,"w",encoding="utf8") as f: json.dump(data,f,indent=2,ensure_ascii=False)
    except Exception as e: print("RAX save error:",e)


def system_snapshot():
    data={"CPU":"N/A","RAM":"N/A","Battery":"N/A","Disk":"N/A"}
    try:
        import psutil
        data["CPU"]=f"{psutil.cpu_percent(interval=0.15):.0f}%"
        data["RAM"]=f"{psutil.virtual_memory().percent:.0f}%"
        data["Disk"]=f"{psutil.disk_usage(os.path.abspath(os.sep)).percent:.0f}%"
        b=psutil.sensors_battery(); data["Battery"]=f"{b.percent:.0f}%" if b else "N/A"
    except Exception:
        pass
    return data


def update_system_dashboard():
    data=system_snapshot()
    for k,v in data.items():
        label=GUI_SYSTEM_LABELS.get(k)
        if label: label.config(text=v)
    if GUI_ROOT is not None: GUI_ROOT.after(1800,update_system_dashboard)


def gui_send_command(command=None):
    if command is None:
        if GUI_COMMAND_ENTRY is None: return
        command=GUI_COMMAND_ENTRY.get().strip(); GUI_COMMAND_ENTRY.delete(0,tk.END)
    command=str(command).strip()
    if not command: return
    gui_log("YOU",command)
    def worker():
        try:
            gui_set_state("thinking")
            should_continue=execute_command(command)
            if not should_continue and GUI_ROOT is not None: gui_safe(GUI_ROOT.destroy)
        except Exception as e:
            print("GUI command error:",e); speak("I encountered an error while processing that command.")
    threading.Thread(target=worker,daemon=True).start()


def gui_listen_once():
    def worker():
        gui_set_state("listening")
        try: command=listen(silent=False)
        except Exception as e: print("listen error",e); command=None
        if not command:
            gui_set_state("online"); return
        gui_log("YOU",command)
        gui_set_state("thinking")
        try:
            if not execute_command(command) and GUI_ROOT is not None: gui_safe(GUI_ROOT.destroy)
        except Exception as e:
            print("Voice command error:",e); speak("I encountered an error while processing that command.")
    threading.Thread(target=worker,daemon=True).start()


def gui_clear_chat():
    if GUI_CHAT:
        GUI_CHAT.config(state="normal"); GUI_CHAT.delete("1.0",tk.END); GUI_CHAT.config(state="disabled")


def vision_capture_and_analyze():
    def worker():
        global GUI_STATE
        gui_set_state("vision")
        try:
            os.makedirs(SCREENSHOTS_DIR,exist_ok=True)
            path=os.path.join(SCREENSHOTS_DIR,"rax_vision_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S")+".png")
            try:
                import pyautogui
                img=pyautogui.screenshot(); img.save(path)
            except ImportError:
                from PIL import ImageGrab
                img=ImageGrab.grab(); img.save(path)
            gui_log("RAX",f"Screen captured: {os.path.basename(path)}")
            # Optional OCR; the screenshot is always saved even if OCR is unavailable.
            text=""
            try:
                import pytesseract
                text=pytesseract.image_to_string(img).strip()
            except Exception:
                text=""
            if text:
                preview=" ".join(text.split())[:700]
                gui_log("RAX","Screen text detected: "+preview)
                speak("I captured your screen and detected text. I have shown a short preview in the console.")
            else:
                speak("I captured your screen. OCR is optional; install pytesseract and Tesseract OCR for text understanding.")
            gui_safe(lambda: show_vision_result(path,text))
        except Exception as e:
            print("Vision error:",e); speak("I could not analyze the screen.")
        finally: gui_set_state("online")
    threading.Thread(target=worker,daemon=True).start()


def show_vision_result(path,text):
    top=tk.Toplevel(GUI_ROOT); top.title("RAX Vision"); top.geometry("760x600"); top.configure(bg="#06090c")
    tk.Label(top,text="RAX VISION",font=("Segoe UI",22,"bold"),fg="#ff4fd8",bg="#06090c").pack(pady=12)
    try:
        img=Image.open(path); img.thumbnail((700,360),Image.Resampling.LANCZOS); ph=ImageTk.PhotoImage(img)
        lab=tk.Label(top,image=ph,bg="#06090c"); lab.image=ph; lab.pack()
    except Exception: pass
    box=scrolledtext.ScrolledText(top,bg="#0b1015",fg="#d7e5ea",insertbackground="white",font=("Consolas",10),height=9)
    box.pack(fill="both",expand=True,padx=16,pady=12); box.insert("1.0",text or "No OCR text detected. The screenshot was saved to:\n"+path); box.config(state="disabled")


def run_agent_sequence(commands):
    global GUI_AGENT_RUNNING
    if GUI_AGENT_RUNNING: return
    GUI_AGENT_RUNNING=True; gui_set_state("agent")
    def worker():
        try:
            total=len(commands)
            for i,cmd in enumerate(commands,1):
                if not GUI_RUNNING: break
                gui_log("RAX",f"AGENT {i}/{total}: {cmd}")
                gui_safe(lambda i=i,total=total: GUI_AGENT_STATUS.config(text=f"Running step {i}/{total}") if GUI_AGENT_STATUS else None)
                execute_command(cmd)
            gui_log("RAX","Agent task completed.")
            speak("Agent task completed.")
        except Exception as e:
            print("Agent error:",e); speak("The agent stopped because a step failed.")
        finally:
            GUI_AGENT_RUNNING=False; gui_set_state("online")
    threading.Thread(target=worker,daemon=True).start()


def open_agent_window():
    top=tk.Toplevel(GUI_ROOT); top.title("RAX Agent Mode"); top.geometry("650x520"); top.configure(bg="#06090c")
    tk.Label(top,text="RAX AGENT MODE",font=("Segoe UI",22,"bold"),fg="#ffb347",bg="#06090c").pack(pady=(18,4))
    tk.Label(top,text="Give RAX a sequence of safe existing commands. One command per line.",fg="#8a969c",bg="#06090c",font=("Segoe UI",9)).pack()
    box=scrolledtext.ScrolledText(top,bg="#0b1015",fg="#d7e5ea",insertbackground="white",font=("Consolas",11),height=16)
    box.pack(fill="both",expand=True,padx=18,pady=14)
    box.insert("1.0","open vscode\nopen chrome\nopen youtube")
    status=tk.Label(top,text="Ready",fg="#00ff88",bg="#06090c",font=("Segoe UI",9)); status.pack();
    def start():
        cmds=[x.strip() for x in box.get("1.0",tk.END).splitlines() if x.strip()]
        if cmds: run_agent_sequence(cmds); top.destroy()
    tk.Button(top,text="▶ RUN AGENT",command=start,bg="#ffb347",fg="#081016",font=("Segoe UI",10,"bold"),relief="flat",padx=20,pady=10).pack(pady=14)


def open_coding_lab(auto_voice=False):
    """Open the RAX Code Lab. Optionally start the voice coding interview."""
    top=tk.Toplevel(GUI_ROOT); top.title("RAX Code Lab - AI Online Compiler"); top.geometry("1000x760"); top.configure(bg="#06090c")
    tk.Label(top,text="RAX CODE LAB",font=("Segoe UI",24,"bold"),fg="#b66cff",bg="#06090c").pack(pady=(14,2))
    tk.Label(top,text="Choose any language supported by the connected online compiler, describe the problem, and RAX generates + runs it.",fg="#89979f",bg="#06090c",font=("Segoe UI",9)).pack()

    row=tk.Frame(top,bg="#06090c"); row.pack(fill="x",padx=18,pady=12)
    tk.Label(row,text="Language",fg="#c7d5da",bg="#06090c",font=("Segoe UI",10,"bold")).pack(side="left")
    lang=tk.StringVar(value="python")
    language_menu=tk.OptionMenu(row,lang,"python","javascript","java","c++","c","typescript","sql","go","rust","php","ruby","c#","kotlin","swift")
    language_menu.pack(side="left",padx=10)
    status=tk.Label(row,text="Ready",fg="#00ff88",bg="#06090c",font=("Segoe UI",9)); status.pack(side="left",padx=12)

    tk.Label(top,text="Coding request",fg="#c7d5da",bg="#06090c",font=("Segoe UI",10,"bold")).pack(anchor="w",padx=18)
    task=scrolledtext.ScrolledText(top,bg="#0b1015",fg="#d7e5ea",insertbackground="white",font=("Consolas",11),height=5)
    task.pack(fill="x",padx=18,pady=(5,10)); task.insert("1.0","Create a program that prints Hello World")

    result_box=scrolledtext.ScrolledText(top,bg="#070b0e",fg="#bfefff",insertbackground="white",font=("Consolas",10),height=27)
    result_box.pack(fill="both",expand=True,padx=18,pady=8)

    def set_status(text):
        gui_safe(lambda: status.config(text=text))

    def update_result(text):
        def ui():
            result_box.delete("1.0",tk.END)
            result_box.insert(tk.END,text)
            result_box.see("1.0")
        gui_safe(ui)

    def generate():
        t=task.get("1.0",tk.END).strip(); l=lang.get().strip()
        if not t:
            speak("Tell me what program you want me to create.")
            return
        set_status("Generating...")
        result_box.delete("1.0",tk.END); result_box.insert(tk.END,"RAX is generating your code...\\n")
        def worker():
            try:
                generated=request_ai_code(l,t)
                if not generated:
                    set_status("AI unavailable")
                    return
                set_status("Running online...")
                try:
                    result=run_code_online(l,generated["code"],generated.get("stdin",""))
                    text=format_code_lab_result(l,t,generated,result)
                    update_result(text)
                    set_status("Completed")
                    speak_code_result(result)
                except Exception as error:
                    path=save_generated_code(l,generated["code"])
                    text=("RAX CODE LAB\\n"+"="*80+"\\n"
                          f"Language: {l}\\nStatus: Online compiler unavailable\\nSaved: {path}\\n\\n"
                          "--- FULL CODE ---\\n"+generated["code"]+"\\n\\n"
                          "--- COMPILER ERROR ---\\n"+str(error))
                    update_result(text); set_status("Compiler unavailable")
                    speak("I generated the code and saved it, but the online compiler could not be reached.")
            except Exception as e:
                update_result("RAX Code Lab error:\\n"+str(e)); set_status("Error")
                speak("I could not complete the coding task. Check the Code Lab for details.")
        threading.Thread(target=worker,daemon=True).start()

    buttons=tk.Frame(top,bg="#06090c"); buttons.pack(fill="x",padx=18,pady=(2,12))
    tk.Button(buttons,text="⚡ GENERATE + RUN",command=generate,bg="#b66cff",fg="white",font=("Segoe UI",10,"bold"),relief="flat",padx=18,pady=9).pack(side="left")
    tk.Button(buttons,text="🎤 VOICE CODING",command=lambda: threading.Thread(target=programming_mode,daemon=True).start(),bg="#123b45",fg="#d7f9ff",font=("Segoe UI",10,"bold"),relief="flat",padx=18,pady=9).pack(side="left",padx=8)
    tk.Button(buttons,text="📂 OPEN CODE FOLDER",command=open_code_folder,bg="#101820",fg="#d7e5ea",font=("Segoe UI",10,"bold"),relief="flat",padx=18,pady=9).pack(side="left")

    if auto_voice:
        # Give Tkinter a moment to render the lab before the voice interview starts.
        GUI_ROOT.after(500, lambda: threading.Thread(target=programming_mode,daemon=True).start())


def format_code_lab_result(language, task, generated, result):
    code = generated.get("code", "")
    explanation = generated.get("explanation", "")
    stdout = (result.get("stdout") or "").rstrip()
    stderr = (result.get("stderr") or "").rstrip()
    compile_output = (result.get("compile_output") or "").rstrip()
    message = (result.get("message") or "").rstrip()
    status = (result.get("status") or {}).get("description", "Unknown")
    path = save_generated_code(language, code)
    parts = [
        "RAX CODE LAB", "="*80,
        f"Task: {task}", f"Language: {language}",
        f"Compiler: {result.get('judge_language', 'Judge0')}",
        f"Status: {status}", f"Saved: {path}",
        "", "--- FULL CODE ---", code,
        "", "--- OUTPUT ---", stdout if stdout else "(no standard output)",
    ]
    if compile_output: parts += ["", "--- COMPILER OUTPUT ---", compile_output]
    if stderr: parts += ["", "--- ERROR OUTPUT ---", stderr]
    if message: parts += ["", "--- MESSAGE ---", message]
    if explanation: parts += ["", "--- RAX EXPLANATION ---", explanation]
    return "\\n".join(parts)


def speak_code_result(result):
    status = (result.get("status") or {}).get("description", "Unknown")
    stdout = re.sub(r"\\s+", " ", (result.get("stdout") or "")).strip()
    if status.lower() == "accepted":
        if stdout:
            speak(f"The program ran successfully. The output is: {stdout[:350]}")
        else:
            speak("The program compiled and ran successfully. I showed the full code and result in Code Lab.")
    else:
        details = (result.get("compile_output") or result.get("stderr") or result.get("message") or "").strip()
        speak(f"The online compiler returned {status}. I showed the full result in Code Lab." + (f" The error is {details[:220]}" if details else ""))


def open_skills_window():
    skills=_load_json(SKILLS_FILE,{"WhatsApp":"WhatsApp automation","Coding":"AI coding","Vision":"Screen capture and OCR","Windows":"Desktop controls","Search":"Web and YouTube search","Notes":"Notes and reminders","Alarms":"Alarm manager","Shopping":"Amazon, Flipkart, Meesho, Shopsy"})
    top=tk.Toplevel(GUI_ROOT); top.title("RAX Skills"); top.geometry("620x560"); top.configure(bg="#06090c")
    tk.Label(top,text="RAX SKILLS",font=("Segoe UI",22,"bold"),fg="#00eaff",bg="#06090c").pack(pady=18)
    for name,desc in skills.items():
        f=tk.Frame(top,bg="#0b1015",highlightthickness=1,highlightbackground="#1d3038"); f.pack(fill="x",padx=18,pady=4)
        tk.Label(f,text="✓ "+name,fg="#00ff88",bg="#0b1015",font=("Segoe UI",10,"bold"),width=18,anchor="w").pack(side="left",padx=10,pady=10)
        tk.Label(f,text=desc,fg="#9aa9af",bg="#0b1015",font=("Segoe UI",9),anchor="w").pack(side="left",fill="x")


def open_routines_window():
    routines=_load_json(ROUTINES_FILE,{"Coding Mode":["open vscode","open chrome"],"Morning Mode":["open youtube"],"Study Mode":["open vscode"]})
    top=tk.Toplevel(GUI_ROOT); top.title("RAX Routines"); top.geometry("700x600"); top.configure(bg="#06090c")
    tk.Label(top,text="CUSTOM ROUTINES",font=("Segoe UI",22,"bold"),fg="#00ff88",bg="#06090c").pack(pady=16)
    listbox=tk.Listbox(top,bg="#0b1015",fg="#d7e5ea",selectbackground="#123b45",font=("Segoe UI",10),height=12)
    listbox.pack(fill="both",expand=True,padx=18,pady=10)
    def refresh():
        listbox.delete(0,tk.END)
        for n in routines: listbox.insert(tk.END,n)
    refresh()
    controls=tk.Frame(top,bg="#06090c"); controls.pack(fill="x",padx=18,pady=12)
    def run_selected():
        sel=listbox.curselection()
        if sel: run_agent_sequence(routines[list(routines.keys())[sel[0]]])
    def add():
        editor=tk.Toplevel(top); editor.title("New RAX Routine"); editor.geometry("560x420"); editor.configure(bg="#06090c")
        tk.Label(editor,text="Routine name",fg="#d7e5ea",bg="#06090c").pack(anchor="w",padx=16,pady=(16,4))
        name=tk.Entry(editor,bg="#0b1015",fg="white",insertbackground="white"); name.pack(fill="x",padx=16)
        tk.Label(editor,text="Commands (one per line)",fg="#d7e5ea",bg="#06090c").pack(anchor="w",padx=16,pady=(12,4))
        b=scrolledtext.ScrolledText(editor,bg="#0b1015",fg="white",insertbackground="white",height=12); b.pack(fill="both",expand=True,padx=16)
        def save():
            n=name.get().strip(); cmds=[x.strip() for x in b.get("1.0",tk.END).splitlines() if x.strip()]
            if n and cmds: routines[n]=cmds; _save_json(ROUTINES_FILE,routines); refresh(); editor.destroy()
        tk.Button(editor,text="SAVE ROUTINE",command=save,bg="#00ff88",fg="#06100b",relief="flat",font=("Segoe UI",10,"bold"),padx=15,pady=8).pack(pady=12)
    tk.Button(controls,text="▶ RUN",command=run_selected,bg="#00ff88",fg="#06100b",relief="flat",padx=18,pady=8).pack(side="left",padx=4)
    tk.Button(controls,text="＋ NEW",command=add,bg="#14242b",fg="#00eaff",relief="flat",padx=18,pady=8).pack(side="left",padx=4)


def switch_tab(name):
    global GUI_CURRENT_TAB
    GUI_CURRENT_TAB=name
    for n,b in GUI_TABS.items():
        b.config(fg="#00eaff" if n==name else "#718087",bg="#101820" if n==name else "#090e12")
    for child in GUI_TAB_CONTENT.winfo_children(): child.destroy()
    if name=="HOME": build_home_tab(GUI_TAB_CONTENT)
    elif name=="AGENT": build_agent_tab(GUI_TAB_CONTENT)
    elif name=="VISION": build_vision_tab(GUI_TAB_CONTENT)
    elif name=="CODE": build_code_tab(GUI_TAB_CONTENT)
    elif name=="SKILLS": build_skills_tab(GUI_TAB_CONTENT)
    elif name=="SYSTEM": build_system_tab(GUI_TAB_CONTENT)
    elif name=="PRO": build_pro_tab(GUI_TAB_CONTENT)


def build_home_tab(parent):
    global GUI_CHAT,GUI_COMMAND_ENTRY,GUI_LISTEN_BUTTON,GUI_WAVE_CANVAS
    top=tk.Frame(parent,bg="#06090c"); top.pack(fill="both",expand=True)
    left=tk.Frame(top,bg="#080d12",width=360,highlightthickness=1,highlightbackground="#12323b"); left.pack(side="left",fill="y",padx=(0,8)); left.pack_propagate(False)
    tk.Label(left,text="RAX",font=("Segoe UI",30,"bold"),fg="#00eaff",bg="#080d12").pack(pady=(12,0))
    tk.Label(left,text="INTELLIGENT AI DESKTOP ASSISTANT",font=("Segoe UI",8,"bold"),fg="#6f7f86",bg="#080d12").pack(pady=(0,8))
    global GUI_IMAGE_PANEL,GUI_RAX_LABEL,GUI_RAX_SOURCE_IMAGE,GUI_RAX_IMAGE
    GUI_IMAGE_PANEL=tk.Frame(left,bg="#000000",highlightthickness=2,highlightbackground="#00eaff"); GUI_IMAGE_PANEL.pack(fill="both",expand=True,padx=18,pady=7)
    image_path=os.path.join(BASE_DIR,"rax.jpg")
    try:
        image=Image.open(image_path).convert("RGB"); image.thumbnail((330,520),Image.Resampling.LANCZOS); GUI_RAX_SOURCE_IMAGE=image.copy(); GUI_RAX_IMAGE=ImageTk.PhotoImage(image)
        GUI_RAX_LABEL=tk.Label(GUI_IMAGE_PANEL,image=GUI_RAX_IMAGE,bg="#000000"); GUI_RAX_LABEL.pack(expand=True)
    except Exception:
        tk.Label(GUI_IMAGE_PANEL,text="RAX IMAGE NOT FOUND\nPlace rax.jpg beside this file",fg="#00eaff",bg="#000000",font=("Segoe UI",13,"bold")).pack(expand=True)
    GUI_STATUS=tk.Label(left,text="● RAX ONLINE",fg="#00ff88",bg="#080d12",font=("Segoe UI",9,"bold")); GUI_STATUS.pack(pady=(3,7))
    GUI_WAVE_CANVAS=tk.Canvas(left,height=55,bg="#05080b",highlightthickness=0); GUI_WAVE_CANVAS.pack(fill="x",padx=18,pady=(0,12))
    right=tk.Frame(top,bg="#06090c"); right.pack(side="right",fill="both",expand=True)
    header=tk.Frame(right,bg="#06090c"); header.pack(fill="x")
    tk.Label(header,text="COMMAND CONSOLE",font=("Segoe UI",18,"bold"),fg="#dbe9ed",bg="#06090c").pack(side="left")
    tk.Label(header,text="LOCAL • PRIVATE • ACTION-READY",font=("Segoe UI",8,"bold"),fg="#00ff88",bg="#06090c").pack(side="right",pady=8)
    GUI_CHAT=scrolledtext.ScrolledText(right,bg="#090f14",fg="#b8cbd1",insertbackground="white",font=("Segoe UI",10),height=16,wrap="word",bd=0)
    GUI_CHAT.pack(fill="both",expand=True,pady=(10,8)); GUI_CHAT.tag_config("rax",foreground="#00eaff",font=("Segoe UI",10,"bold")); GUI_CHAT.tag_config("user",foreground="#b66cff",font=("Segoe UI",10,"bold")); GUI_CHAT.config(state="disabled")
    entry_frame=tk.Frame(right,bg="#0b1116",highlightthickness=1,highlightbackground="#1d3038"); entry_frame.pack(fill="x",pady=(0,8))
    GUI_COMMAND_ENTRY=tk.Entry(entry_frame,bg="#0b1116",fg="white",insertbackground="#00eaff",font=("Segoe UI",11),bd=0); GUI_COMMAND_ENTRY.pack(side="left",fill="x",expand=True,padx=12,pady=13); GUI_COMMAND_ENTRY.bind("<Return>",lambda e:gui_send_command())
    tk.Button(entry_frame,text="SEND",command=gui_send_command,bg="#00eaff",fg="#061014",relief="flat",font=("Segoe UI",9,"bold"),padx=18,pady=8).pack(side="right",padx=5)
    buttons=tk.Frame(right,bg="#06090c"); buttons.pack(fill="x")
    GUI_LISTEN_BUTTON=tk.Button(buttons,text="🎙 LISTEN",command=gui_listen_once,bg="#10232b",fg="#00eaff",relief="flat",font=("Segoe UI",9,"bold"),padx=14,pady=9); GUI_LISTEN_BUTTON.pack(side="left",padx=(0,5))
    for text,cmd in [("⚡ AGENT",open_agent_window),("👁 VISION",vision_capture_and_analyze),("</> CODE",open_coding_lab),("☰ SKILLS",open_skills_window),("⟳ CLEAR",gui_clear_chat)]:
        tk.Button(buttons,text=text,command=cmd,bg="#0d151b",fg="#b8cbd1",relief="flat",font=("Segoe UI",8,"bold"),padx=10,pady=9).pack(side="left",padx=3)


def build_agent_tab(parent):
    tk.Label(parent,text="RAX AGENT MODE",font=("Segoe UI",24,"bold"),fg="#ffb347",bg="#06090c").pack(anchor="w",pady=(8,3))
    tk.Label(parent,text="Turn multiple RAX commands into one autonomous workflow.",fg="#84939a",bg="#06090c").pack(anchor="w")
    f=_card(parent,"QUICK AGENTS","Ready-made workflows using your existing RAX command engine.","#ffb347"); f.pack(fill="x",pady=18)
    for name,cmds in [("Coding Workspace",["open vscode","open chrome"]),("Research Setup",["open chrome","open google"]),("Media Setup",["open chrome","open youtube"]),("Developer + Terminal",["open vscode","open file explorer"])]:
        tk.Button(f,text=name,command=lambda c=cmds:run_agent_sequence(c),bg="#101a20",fg="#d7e5ea",relief="flat",font=("Segoe UI",9,"bold"),padx=12,pady=8).pack(side="left",padx=5,pady=12)
    GUI_AGENT_STATUS=tk.Label(parent,text="Agent ready",fg="#00ff88",bg="#06090c",font=("Segoe UI",10)); GUI_AGENT_STATUS.pack(anchor="w")
    tk.Button(parent,text="＋ CREATE CUSTOM AGENT",command=open_agent_window,bg="#ffb347",fg="#081016",relief="flat",font=("Segoe UI",10,"bold"),padx=16,pady=10).pack(anchor="w",pady=14)


def build_vision_tab(parent):
    tk.Label(parent,text="COMPUTER VISION",font=("Segoe UI",24,"bold"),fg="#ff4fd8",bg="#06090c").pack(anchor="w",pady=(8,3))
    tk.Label(parent,text="Capture the desktop, preview it, and optionally extract visible text with OCR.",fg="#84939a",bg="#06090c").pack(anchor="w")
    f=_card(parent,"SCREEN UNDERSTANDING","The screenshot is saved locally in RAX_Screenshots. OCR is optional.","#ff4fd8"); f.pack(fill="x",pady=20)
    tk.Button(f,text="👁 CAPTURE & ANALYZE SCREEN",command=vision_capture_and_analyze,bg="#ff4fd8",fg="#100613",relief="flat",font=("Segoe UI",11,"bold"),padx=20,pady=12).pack(padx=15,pady=15)
    tk.Label(parent,text="Optional OCR setup:\n  python -m pip install pytesseract\n  Install Tesseract OCR separately on Windows for text extraction.",fg="#84939a",bg="#06090c",justify="left",font=("Consolas",9)).pack(anchor="w")


def build_code_tab(parent):
    tk.Label(parent,text="RAX CODE LAB",font=("Segoe UI",24,"bold"),fg="#b66cff",bg="#06090c").pack(anchor="w",pady=(8,3))
    tk.Label(parent,text="Generate, save and run code through the programming engine already inside RAX.",fg="#84939a",bg="#06090c").pack(anchor="w")
    tk.Button(parent,text="OPEN FULL CODE LAB",command=open_coding_lab,bg="#b66cff",fg="white",relief="flat",font=("Segoe UI",11,"bold"),padx=20,pady=12).pack(anchor="w",pady=20)
    f=_card(parent,"VOICE CODING","Try commands such as: 'start coding', 'write Python code to ...', or 'open code folder'.","#b66cff"); f.pack(fill="x")


def build_skills_tab(parent):
    tk.Label(parent,text="RAX SKILLS + ROUTINES",font=("Segoe UI",24,"bold"),fg="#00eaff",bg="#06090c").pack(anchor="w",pady=(8,3))
    tk.Label(parent,text="Organize what RAX can do and create repeatable workflows.",fg="#84939a",bg="#06090c").pack(anchor="w")
    row=tk.Frame(parent,bg="#06090c"); row.pack(fill="x",pady=20)
    tk.Button(row,text="☰ VIEW SKILLS",command=open_skills_window,bg="#10232b",fg="#00eaff",relief="flat",font=("Segoe UI",10,"bold"),padx=18,pady=11).pack(side="left",padx=(0,8))
    tk.Button(row,text="⟳ CUSTOM ROUTINES",command=open_routines_window,bg="#10232b",fg="#00ff88",relief="flat",font=("Segoe UI",10,"bold"),padx=18,pady=11).pack(side="left")


def build_system_tab(parent):
    tk.Label(parent,text="COMPUTER / SYSTEM DASHBOARD",font=("Segoe UI",24,"bold"),fg="#00ff88",bg="#06090c").pack(anchor="w",pady=(8,3))
    tk.Label(parent,text="Live local system telemetry and common controls.",fg="#84939a",bg="#06090c").pack(anchor="w")
    grid=tk.Frame(parent,bg="#06090c"); grid.pack(fill="x",pady=20)
    for i,(name,desc) in enumerate([("CPU","Processor usage"),("RAM","Memory usage"),("Battery","Battery level"),("Disk","System disk")]):
        f=_card(grid,name,desc,"#00ff88"); f.grid(row=0,column=i,sticky="nsew",padx=4); grid.grid_columnconfigure(i,weight=1)
        val=tk.Label(f,text="--",font=("Segoe UI",22,"bold"),fg="#d7e5ea",bg="#0b1015"); val.pack(anchor="w",padx=12,pady=(0,12)); GUI_SYSTEM_LABELS[name]=val
    controls=_card(parent,"WINDOWS CONTROLS","These buttons call the same RAX desktop functions used by voice commands.","#00eaff"); controls.pack(fill="x",pady=10)
    actions=[("🔒 LOCK PC","lock my pc"),("📁 FILES","open file explorer"),("📝 NOTEPAD","open notepad"),("🧮 CALCULATOR","open calculator"),("💻 VS CODE","open vscode"),("🌐 BROWSER","open google")]
    for label,cmd in actions: tk.Button(controls,text=label,command=lambda c=cmd:gui_send_command(c),bg="#101a20",fg="#b8cbd1",relief="flat",font=("Segoe UI",9,"bold"),padx=10,pady=8).pack(side="left",padx=3,pady=12)
    update_system_dashboard()


def build_rax_gui():
    global GUI_ROOT,GUI_TAB_CONTENT,GUI_TABS,GUI_RUNNING
    root=tk.Tk(); GUI_ROOT=root; GUI_RUNNING=True
    root.title("RAX — Intelligent AI Desktop Assistant")
    root.geometry("1280x820"); root.minsize(980,680); root.configure(bg="#04070a")
    root.protocol("WM_DELETE_WINDOW",lambda:root.destroy())
    header=tk.Frame(root,bg="#070b0f",height=60); header.pack(fill="x"); header.pack_propagate(False)
    tk.Label(header,text="◉  RAX",font=("Segoe UI",22,"bold"),fg="#00eaff",bg="#070b0f").pack(side="left",padx=20)
    tk.Label(header,text="YOUR AI DESKTOP COMMAND CENTER",font=("Segoe UI",8,"bold"),fg="#68777e",bg="#070b0f").pack(side="left")
    tk.Label(header,text="● LOCAL CORE",font=("Segoe UI",8,"bold"),fg="#00ff88",bg="#070b0f").pack(side="right",padx=20)
    nav=tk.Frame(root,bg="#090e12",height=42); nav.pack(fill="x"); nav.pack_propagate(False)
    GUI_TABS={}
    for name in ["HOME","AGENT","VISION","CODE","SKILLS","SYSTEM","PRO"]:
        b=tk.Button(nav,text=name,command=lambda n=name:switch_tab(n),bg="#101820" if name=="HOME" else "#090e12",fg="#00eaff" if name=="HOME" else "#718087",relief="flat",bd=0,font=("Segoe UI",8,"bold"),padx=16,pady=7); b.pack(side="left",padx=2,pady=4); GUI_TABS[name]=b
    GUI_TAB_CONTENT=tk.Frame(root,bg="#06090c"); GUI_TAB_CONTENT.pack(fill="both",expand=True,padx=12,pady=12)
    switch_tab("HOME")
    root.after(100,animate_rax)
    root.after(300,update_system_dashboard)
    return root


# ============================================================
# END ULTIMATE GUI
# ============================================================

# ============================================================
# RAX MULTILINGUAL LANGUAGE ENGINE
# ============================================================

LANGUAGE_NAMES = {
    "english": "English",
    "hindi": "Hindi",
    "bengali": "Bengali",
    "maithili": "Maithili",
    "bhojpuri": "Bhojpuri",
    "marathi": "Marathi",
    "french": "French",
}


def normalize_language_name(value):
    value = str(value or "").strip().lower()
    aliases = {
        "en": "english", "eng": "english", "english": "english",
        "hi": "hindi", "hin": "hindi", "hindi": "hindi", "हिंदी": "hindi",
        "bn": "bengali", "bangla": "bengali", "bengali": "bengali", "বাংলা": "bengali",
        "mai": "maithili", "maithili": "maithili", "मैथिली": "maithili",
        "bho": "bhojpuri", "bhojpuri": "bhojpuri", "भोजपुरी": "bhojpuri",
        "mr": "marathi", "marathi": "marathi", "मराठी": "marathi",
        "fr": "french", "french": "french", "français": "french", "francais": "french",
    }
    return aliases.get(value)


def set_rax_language(name):
    global ACTIVE_LANGUAGE, LANGUAGE_MODE, LANGUAGE
    key = normalize_language_name(name)
    if not key or key not in RAX_LANGUAGES:
        speak("I support English, Hindi, Bengali, Maithili, Bhojpuri, Marathi, French, and Gujarati.")
        return True
    ACTIVE_LANGUAGE = key
    LANGUAGE = RAX_LANGUAGES[key]
    LANGUAGE_MODE = "selected"
    speak(f"Okay Abhay, I will listen in {LANGUAGE_NAMES[key]}.")
    return True


def show_languages():
    names = ", ".join(LANGUAGE_NAMES.values())
    speak(f"I can understand these languages: {names}. You can say language Hindi, language Bengali, or language English.")
    return True


def multilingual_text(texts):
    """Return the response for the active language, with English fallback."""
    if isinstance(texts, str):
        return texts
    return texts.get(ACTIVE_LANGUAGE) or texts.get("english") or next(iter(texts.values()))


def _friend_mood_type(command):
    c = command.lower().strip()
    positive = {
        "good", "fine", "great", "amazing", "excellent", "happy", "awesome",
        "well", "okay", "ok", "nice", "बहुत अच्छा", "अच्छा", "ठीक", "ठीक हूं",
        "ভালো", "ঠিক আছি", "ठीक छी", "नीक", "बढ़िया", "छान", "bien", "bon",
    }
    negative = {
        "bad", "worse", "worst", "stressful", "stressed", "sad", "upset",
        "angry", "tired", "worried", "anxious", "not good", "terrible",
        "बुरा", "खराब", "परेशान", "तनाव", "तनाव में", "दुखी", "गुस्सा",
        "খারাপ", "চাপ", "দুঃখিত", "মন খারাপ", "तनावग्रस्त",
        "खराब छै", "परेशान छी", "दुःखी", "stress",
        "mauvais", "triste", "stressé", "fatigué",
    }
    if any(x in c for x in negative):
        return "negative"
    if any(x in c for x in positive):
        return "positive"
    return None


# ============================================================
# WINDOWS TEXT TO SPEECH
# ============================================================

def speak(text):
    """Speak text using Windows built-in Speech engine."""
    text = str(text).strip()

    if not text:
        return

    print(f"\n{ASSISTANT_NAME}: {text}")
    gui_log("RAX", text)
    gui_set_state("speaking")

    encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")

    powershell_script = f"""
Add-Type -AssemblyName System.Speech
$bytes = [Convert]::FromBase64String('{encoded}')
$message = [System.Text.Encoding]::UTF8.GetString($bytes)

$voice = New-Object System.Speech.Synthesis.SpeechSynthesizer
$voice.Rate = {VOICE_RATE}
$voice.Volume = {VOICE_VOLUME}
$voice.Speak($message)
$voice.Dispose()
"""

    try:
        subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                powershell_script,
            ],
            check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception as error:
        print("Text-to-speech error:", error)
    finally:
        if GUI_RUNNING:
            gui_set_state("online")


# ============================================================
# SPEECH RECOGNITION
# ============================================================

recognizer = sr.Recognizer()
MICROPHONE_INDEX = None


def find_microphone():
    """Find a usable microphone without requiring PyAudio."""
    global MICROPHONE_INDEX

    try:
        devices = sd.query_devices()
        input_devices = []

        print("\nAvailable microphones:")
        for index, device in enumerate(devices):
            if device.get("max_input_channels", 0) > 0:
                input_devices.append(index)
                print(f"{index}: {device['name']}")

        if not input_devices:
            print("RAX: No microphone was found.")
            return False

        preferred_words = ["microphone", "mic", "headset", "input", "array"]

        for index in input_devices:
            name = devices[index]["name"]
            if any(word in name.lower() for word in preferred_words):
                MICROPHONE_INDEX = index
                print(f"\nRAX: Selected microphone {index}: {name}")
                return True

        default_input = sd.default.device[0]
        if default_input is not None and default_input in input_devices:
            MICROPHONE_INDEX = default_input
        else:
            MICROPHONE_INDEX = input_devices[0]

        print(
            f"\nRAX: Using microphone {MICROPHONE_INDEX}: "
            f"{devices[MICROPHONE_INDEX]['name']}"
        )
        return True

    except Exception as error:
        print("Microphone error:", error)
        return False


def listen(silent=False):
    """Record microphone audio and recognize speech in RAX's selected language."""
    global ACTIVE_LANGUAGE, LANGUAGE
    try:
        gui_status("● RAX IS LISTENING...", "#00eaff")
        sample_rate = 16000
        max_seconds = 8

        print("\nListening...")
        print("Speak now...")

        audio = sd.rec(
            int(max_seconds * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
            device=MICROPHONE_INDEX,
            blocking=True,
        )

        audio_bytes = np.asarray(audio, dtype=np.int16).tobytes()
        audio_data = sr.AudioData(audio_bytes, sample_rate, 2)

        print("Recognizing...")

        languages_to_try = []
        if LANGUAGE_MODE == "selected":
            languages_to_try = [LANGUAGE]
        else:
            languages_to_try = list(RAX_LANGUAGES.values())

        command = None
        last_error = None
        for lang in languages_to_try:
            try:
                candidate = recognizer.recognize_google(audio_data, language=lang)
                if candidate and candidate.strip():
                    command = candidate.strip()
                    print(f"Recognized ({lang}): {command}")
                    if LANGUAGE_MODE == "auto":
                        # Keep the detected language for the next turn.
                        for name, code in RAX_LANGUAGES.items():
                            if code == lang:
                                ACTIVE_LANGUAGE = name
                                LANGUAGE = code
                                break
                    break
            except sr.UnknownValueError as error:
                last_error = error
                continue
            except sr.RequestError as error:
                last_error = error
                break

        if command is None:
            if isinstance(last_error, sr.RequestError):
                if not silent:
                    speak("Speech recognition is currently unavailable.")
            elif not silent:
                speak("Sorry, I could not understand that.")
            return ""

        print(f"You: {command}")
        gui_status("● RAX ONLINE", "#00ff88")
        return command.lower().strip()

    except Exception as error:
        print("Microphone error:", error)
        if not silent:
            speak("There is a microphone problem.")
        return None


# ============================================================
# LOCAL KNOWLEDGE
# ============================================================

KNOWLEDGE = {
    "html": "HTML stands for HyperText Markup Language. It creates the structure of web pages.",
    "css": "CSS stands for Cascading Style Sheets. It controls the design, layout, colors, fonts, and appearance of web pages.",
    "javascript": "JavaScript is a programming language used to make websites interactive. It can also be used for servers and applications.",
    "python": "Python is a high-level programming language popular for automation, web development, data science, artificial intelligence, and machine learning.",
    "java": "Java is a high-level, object-oriented programming language used for applications, enterprise software, Android development, and many other systems.",
    "c": "C is a general-purpose programming language known for speed, efficiency, and low-level memory control.",
    "c++": "C plus plus is a general-purpose programming language that supports object-oriented programming and is widely used in software, games, and systems.",
    "programming": "Programming is the process of writing instructions that tell a computer how to perform tasks.",
    "frontend": "Frontend development focuses on the part of a website that users see and interact with. HTML, CSS, JavaScript, and React are common frontend technologies.",
    "backend": "Backend development handles server-side logic, databases, authentication, APIs, and application services.",
    "full stack": "Full stack development means working with both frontend and backend parts of an application.",
    "web development": "Web development is the process of creating websites and web applications. HTML, CSS, and JavaScript are common technologies.",
    "react": "React is a JavaScript library used to build reusable user interfaces, especially for web applications.",
    "node js": "Node.js is a JavaScript runtime that allows JavaScript to run outside a web browser, commonly on servers.",
    "api": "An API is an Application Programming Interface. It allows different software systems to communicate with each other.",
    "json": "JSON stands for JavaScript Object Notation. It is a lightweight format commonly used to exchange structured data.",
    "database": "A database is an organized collection of information that can be stored, managed, searched, and retrieved efficiently.",
    "sql": "SQL stands for Structured Query Language. It is used to create, read, update, and manage data in relational databases.",
    "github": "GitHub is a platform where developers can store, manage, and collaborate on software projects using Git.",
    "git": "Git is a version control system used to track changes in code and collaborate on software projects.",
    "artificial intelligence": "Artificial intelligence is a field of computer science focused on building systems that can perform tasks that normally require human intelligence.",
    "ai": "AI stands for artificial intelligence. It enables computer systems to perform tasks such as understanding language, recognizing patterns, and making decisions.",
    "machine learning": "Machine learning is a branch of artificial intelligence where computers learn patterns from data and use those patterns to make predictions or decisions.",
    "deep learning": "Deep learning is a type of machine learning that uses multi-layer neural networks to learn complex patterns.",
    "algorithm": "An algorithm is a step-by-step procedure used to solve a problem or complete a task.",
    "data structure": "A data structure is a way of organizing and storing data so it can be accessed and modified efficiently.",
    "oop": "Object-oriented programming is a programming approach based on objects and concepts such as classes, objects, inheritance, encapsulation, abstraction, and polymorphism.",
    "operating system": "An operating system manages computer hardware and provides services for applications. Windows, Linux, and macOS are examples.",
    "computer": "A computer is an electronic device that processes data according to instructions provided by software.",
    "software": "Software is a collection of programs and instructions that tell a computer what to do.",
    "hardware": "Hardware refers to the physical components of a computer, such as the processor, memory, storage, keyboard, and monitor.",
    "cybersecurity": "Cybersecurity is the practice of protecting computers, networks, applications, and data from unauthorized access and other digital threats.",
    "cloud computing": "Cloud computing provides computing resources such as storage, servers, and databases over the internet.",
}


def clean_question(command):
    question = command.lower().strip()

    phrases = [
        "hey rax", "hi rax", "hello rax", "okay rax", "ok rax",
        "rax", "what is", "what are", "who is", "what does",
        "tell me about", "tell me", "explain", "define",
        "can you explain", "please explain"
    ]

    for phrase in phrases:
        question = question.replace(phrase, "")

    return question.strip(" ?.!,")


def local_answer(command):
    question = clean_question(command)

    if question in KNOWLEDGE:
        return KNOWLEDGE[question]

    for topic, answer in KNOWLEDGE.items():
        if topic in question:
            return answer

    return None


# ============================================================
# SAFE CALCULATOR
# ============================================================

OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}


def safe_calculate(expression):
    """Safely calculate basic arithmetic without eval()."""
    expression = expression.replace("x", "*").replace("X", "*")
    expression = expression.replace("^", "**")

    def calculate(node):
        if isinstance(node, ast.Expression):
            return calculate(node.body)

        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value

        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            left = calculate(node.left)
            right = calculate(node.right)

            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError("Power is too large.")

            return OPERATORS[type(node.op)](left, right)

        if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
            return OPERATORS[type(node.op)](calculate(node.operand))

        raise ValueError("Unsupported expression.")

    tree = ast.parse(expression, mode="eval")
    return calculate(tree)


# ============================================================
# WEB / WIKIPEDIA
# ============================================================

def wikipedia_answer(command):
    try:
        question = clean_question(command)

        if not question:
            return None

        url = (
            "https://en.wikipedia.org/api/rest_v1/"
            f"page/summary/{urllib.parse.quote(question)}"
        )

        response = requests.get(
            url,
            timeout=7,
            headers={"User-Agent": "RAX-Desktop-Assistant/2.0"}
        )

        if response.status_code != 200:
            return None

        data = response.json()
        answer = data.get("extract")

        if not answer:
            return None

        if len(answer) > 650:
            answer = answer[:650]
            last_space = answer.rfind(" ")
            if last_space > 0:
                answer = answer[:last_space]
            answer += "."

        return answer

    except Exception as error:
        print("Wikipedia error:", error)
        return None


def google_search(query):
    if not query:
        speak("What should I search for?")
        return

    speak(f"Searching Google for {query}.")
    webbrowser.open(
        "https://www.google.com/search?q="
        + urllib.parse.quote_plus(query)
    )


def youtube_search(query):
    if not query:
        speak("What should I search for on YouTube?")
        return

    speak(f"Searching YouTube for {query}.")
    webbrowser.open(
        "https://www.youtube.com/results?search_query="
        + urllib.parse.quote_plus(query)
    )


# ============================================================
# WEATHER
# ============================================================

def get_weather(city):
    city = city.strip()

    if not city:
        speak("Please say a city. For example, weather in Kolkata.")
        return

    try:
        url = (
            f"https://wttr.in/{urllib.parse.quote(city)}"
            "?format=j1"
        )

        response = requests.get(
            url,
            timeout=8,
            headers={"User-Agent": "RAX-Desktop-Assistant/2.0"}
        )

        if response.status_code != 200:
            speak("I could not get the weather right now.")
            return

        data = response.json()
        current = data["current_condition"][0]

        temperature = current["temp_C"]
        feels = current["FeelsLikeC"]
        description = current["weatherDesc"][0]["value"]
        humidity = current["humidity"]

        speak(
            f"The current weather in {city} is {description}. "
            f"The temperature is {temperature} degrees Celsius, "
            f"it feels like {feels} degrees, and humidity is {humidity} percent."
        )

    except Exception as error:
        print("Weather error:", error)
        speak("Sorry, I could not get the weather.")


# ============================================================
# BATTERY / SYSTEM INFO
# ============================================================

def get_battery():
    try:
        command = (
            "Get-CimInstance Win32_Battery | "
            "Select-Object -ExpandProperty EstimatedChargeRemaining"
        )

        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            timeout=5
        )

        value = result.stdout.strip()

        if value:
            speak(f"Your battery level is {value} percent.")
        else:
            speak("I could not detect a battery on this computer.")

    except Exception as error:
        print("Battery error:", error)
        speak("I could not check the battery.")


def system_info():
    try:
        computer = platform.node() or "your computer"
        system = platform.system()
        version = platform.release()
        processor = platform.processor() or "unknown processor"
        cores = os.cpu_count() or 1

        speak(
            f"You are using {system} {version}. "
            f"The computer name is {computer}. "
            f"The processor is {processor}. "
            f"I detected {cores} logical processor cores."
        )

    except Exception as error:
        print("System info error:", error)
        speak("I could not read the system information.")


# ============================================================
# NOTES
# ============================================================

def add_note(note):
    note = note.strip()

    if not note:
        speak("What would you like me to write down?")
        return

    timestamp = datetime.datetime.now().strftime("%d %B %Y, %I:%M %p")

    try:
        with open(NOTES_FILE, "a", encoding="utf-8") as file:
            file.write(f"[{timestamp}] {note}\n")

        speak("I saved that note.")

    except Exception as error:
        print("Note error:", error)
        speak("I could not save the note.")


def read_notes():
    try:
        if not os.path.exists(NOTES_FILE):
            speak("You do not have any saved notes.")
            return

        with open(NOTES_FILE, "r", encoding="utf-8") as file:
            notes = file.read().strip()

        if not notes:
            speak("You do not have any saved notes.")
            return

        print("\n--- RAX NOTES ---")
        print(notes)

        # Speak only the latest few notes to keep the response manageable.
        lines = notes.splitlines()[-5:]
        spoken = " ".join(lines)

        if len(spoken) > 650:
            spoken = spoken[-650:]

        speak("Here are your latest notes. " + spoken)

    except Exception as error:
        print("Read notes error:", error)
        speak("I could not read your notes.")


def clear_notes():
    try:
        with open(NOTES_FILE, "w", encoding="utf-8") as file:
            file.write("")

        speak("Your notes have been cleared.")

    except Exception as error:
        print("Clear notes error:", error)
        speak("I could not clear your notes.")


# ============================================================
# REMINDERS
# ============================================================

def reminder_callback(message):
    speak(f"Reminder. {message}")


def create_reminder(minutes, message):
    if minutes <= 0:
        speak("The reminder time must be greater than zero.")
        return

    speak(f"Okay. I will remind you in {minutes} minutes.")

    timer = threading.Timer(
        minutes * 60,
        reminder_callback,
        args=(message,)
    )

    timer.daemon = True
    timer.start()


def parse_reminder(command):
    pattern = (
        r"remind me in\s+(\d+(?:\.\d+)?)\s*"
        r"(second|seconds|minute|minutes|hour|hours)\s+to\s+(.+)"
    )

    match = re.search(pattern, command, re.IGNORECASE)

    if not match:
        return False

    amount = float(match.group(1))
    unit = match.group(2).lower()
    message = match.group(3).strip()

    if "hour" in unit:
        minutes = amount * 60
    elif "second" in unit:
        minutes = amount / 60
    else:
        minutes = amount

    create_reminder(minutes, message)
    return True


# ============================================================
# OPEN APPS / WEBSITES
# ============================================================

def open_url(name, url):
    speak(f"Okay, I am opening {name}.")
    webbrowser.open(url)


def open_calculator():
    speak("Okay, I am opening Calculator.")
    try:
        subprocess.Popen("calc.exe")
    except Exception:
        speak("I could not open Calculator.")


def open_notepad():
    speak("Okay, I am opening Notepad.")
    try:
        subprocess.Popen("notepad.exe")
    except Exception:
        speak("I could not open Notepad.")


def open_camera():
    speak("Okay, I am opening Camera.")
    try:
        os.system("start microsoft.windows.camera:")
    except Exception:
        speak("I could not open Camera.")


def open_file_explorer():
    speak("Okay, I am opening File Explorer.")
    try:
        subprocess.Popen("explorer.exe")
    except Exception:
        speak("I could not open File Explorer.")


def open_vscode():
    speak("Okay, I am opening Visual Studio Code.")
    try:
        subprocess.Popen("code")
    except Exception:
        speak("I could not open Visual Studio Code.")


def open_downloads():
    speak("Okay, I am opening Downloads.")
    try:
        os.startfile(os.path.join(os.path.expanduser("~"), "Downloads"))
    except Exception:
        speak("I could not open Downloads.")


def open_documents():
    speak("Okay, I am opening Documents.")
    try:
        os.startfile(os.path.join(os.path.expanduser("~"), "Documents"))
    except Exception:
        speak("I could not open Documents.")


# ============================================================
# VOICE PASSWORD - OPEN MY PC
# ============================================================

def open_my_pc_with_password():
    """Ask for the configured voice password, then open This PC."""
    speak("Tell password.")

    password = listen()
    if password is None:
        speak("I could not access the microphone.")
        return

    if not password:
        speak("No password was heard. Access denied.")
        return

    # Normalize common speech-recognition variations.
    normalized = password.lower().strip()
    normalized = normalized.replace(" ", "").replace("-", "")

    # Accept spoken number words as well as digits.
    number_words = {
        "zero": "0", "oh": "0", "one": "1", "two": "2",
        "three": "3", "four": "4", "five": "5", "six": "6",
        "seven": "7", "eight": "8", "nine": "9"
    }

    words = password.lower().replace("-", " ").split()
    if words and all(word in number_words for word in words):
        normalized = "".join(number_words[word] for word in words)

    if normalized == PC_VOICE_PASSWORD:
        speak("Password correct. Opening your PC.")
        try:
            subprocess.Popen("explorer.exe shell:MyComputerFolder")
        except Exception as error:
            print("Open My PC error:", error)
            speak("I could not open your PC.")
    else:
        speak("Incorrect password. Access denied.")


# ============================================================
# WINDOWS POWER CONTROLS / APP CONTROL
# ============================================================

APP_PROCESSES = {
    "chrome": ["chrome.exe"],
    "google chrome": ["chrome.exe"],
    "edge": ["msedge.exe"],
    "microsoft edge": ["msedge.exe"],
    "firefox": ["firefox.exe"],
    "notepad": ["notepad.exe"],
    "calculator": ["CalculatorApp.exe", "Calculator.exe"],
    "spotify": ["Spotify.exe"],
    "discord": ["Discord.exe"],
    "whatsapp": ["WhatsApp.exe"],
    "telegram": ["Telegram.exe"],
    "vscode": ["Code.exe"],
    "visual studio code": ["Code.exe"],
}


def lock_pc():
    try:
        speak("Locking your PC now.")
        result = subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], timeout=5)
        if result.returncode != 0:
            speak("I could not lock the PC.")
    except Exception as error:
        print("Lock PC error:", error)
        speak("I could not lock the PC.")


def sleep_pc():
    try:
        speak("Putting your PC to sleep.")
        subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception as error:
        print("Sleep error:", error)
        speak("I could not put the PC to sleep.")


def close_app(app_name):
    key = app_name.lower().strip()
    processes = APP_PROCESSES.get(key)
    if not processes:
        speak("That application is not on my safe close list.")
        return
    closed_any = False
    for process in processes:
        try:
            result = subprocess.run(["taskkill", "/IM", process], capture_output=True, text=True, timeout=8)
            if result.returncode == 0:
                closed_any = True
        except Exception as error:
            print(f"Close {process} error:", error)
    if closed_any:
        speak(f"I closed {app_name}.")
    else:
        speak(f"{app_name} does not appear to be running.")


def close_current_browser_tab():
    # Only sends Ctrl+W when the active window title looks like a browser.
    ps = (
        'Add-Type -AssemblyName Microsoft.VisualBasic; '
        '$title = (Get-Process | Where-Object {$_.MainWindowHandle -eq (Get-Process -Id $PID).MainWindowHandle} | Select-Object -ExpandProperty MainWindowTitle); '
        'if ($title -match "Chrome|Microsoft Edge|Firefox|Brave|Opera") { '
        '$shell = New-Object -ComObject WScript.Shell; $shell.SendKeys("^w"); exit 0 } else { exit 2 }'
    )
    try:
        result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            speak("I closed the current browser tab.")
        else:
            speak("The active window does not appear to be a supported browser.")
    except Exception as error:
        print("Browser tab error:", error)
        speak("I could not close the current browser tab.")


# ============================================================
# WINDOWS ALARMS
# ============================================================

def load_alarms():
    try:
        if not os.path.exists(ALARMS_FILE):
            return []
        with open(ALARMS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except Exception as error:
        print("Alarm file error:", error)
        return []


def save_alarms(alarms):
    with open(ALARMS_FILE, "w", encoding="utf-8") as file:
        json.dump(alarms, file, indent=2, ensure_ascii=False)


def write_alarm_script(message, script_path):
    encoded = base64.b64encode(message.encode("utf-8")).decode("ascii")
    script = (
        "Add-Type -AssemblyName System.Speech\n"
        f"$bytes = [Convert]::FromBase64String('{encoded}')\n"
        "$message = [System.Text.Encoding]::UTF8.GetString($bytes)\n"
        "$voice = New-Object System.Speech.Synthesis.SpeechSynthesizer\n"
        "$voice.Rate = 0\n"
        "$voice.Volume = 100\n"
        "$voice.Speak($message)\n"
        "$voice.Dispose()\n"
        "Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue\n"
    )
    with open(script_path, "w", encoding="utf-8") as file:
        file.write(script)


def set_alarm(hour, minute, ampm, label="your alarm"):
    ampm = ampm.upper()
    if ampm not in {"AM", "PM"} or not (1 <= hour <= 12) or not (0 <= minute <= 59):
        speak("Please give a valid time such as 7:30 PM.")
        return False

    hour24 = hour % 12 + (12 if ampm == "PM" else 0)
    now = datetime.datetime.now()
    alarm_dt = now.replace(hour=hour24, minute=minute, second=0, microsecond=0)
    if alarm_dt <= now:
        alarm_dt += datetime.timedelta(days=1)

    label = label.strip() or "your alarm"
    message = f"Alarm. {label}. It is {alarm_dt.strftime('%I:%M %p')}."

    task_name = "RAX_Alarm_" + alarm_dt.strftime("%Y%m%d_%H%M%S") + "_" + str(int(datetime.datetime.now().timestamp()))
    script_path = os.path.join(BASE_DIR, task_name + ".ps1")
    write_alarm_script(message, script_path)
    task_command = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{script_path}"'

    try:
        result = subprocess.run(
            ["schtasks.exe", "/Create", "/TN", task_name, "/SC", "ONCE", "/SD", alarm_dt.strftime("%m/%d/%Y"), "/ST", alarm_dt.strftime("%H:%M"), "/TR", task_command, "/F", "/Z"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            print("Alarm scheduler error:", result.stdout, result.stderr)
            speak("Windows could not create the alarm. Please try again.")
            return False

        alarms = load_alarms()
        alarms.append({"task": task_name, "datetime": alarm_dt.isoformat(), "label": label})
        save_alarms(alarms)
        if alarm_dt.date() == now.date():
            speak(f"Alarm set for {alarm_dt.strftime('%I:%M %p')}.")
        else:
            speak(f"That time has passed, so I set the alarm for tomorrow at {alarm_dt.strftime('%I:%M %p')}.")
        return True
    except Exception as error:
        print("Set alarm error:", error)
        speak("I could not set the alarm.")
        return False


def parse_alarm(command):
    text = command.lower()
    text = text.replace("a.m.", "am").replace("p.m.", "pm").replace("a.m", "am").replace("p.m", "pm")
    text = re.sub(r"\s+", " ", text).strip()
    pattern = re.compile(
        r"(?:set\s+(?:an?\s+)?alarm|set\s+alarm|wake\s+me(?:\s+up)?)"
        r"\s+(?:for\s+|at\s+)?"
        r"(\d{1,2})(?:\s*[:.]\s*(\d{2}))?\s*(am|pm)"
        r"(?:\s+(?:to|for)\s+(.+))?$",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if not match:
        return False
    set_alarm(int(match.group(1)), int(match.group(2) or 0), match.group(3).upper(), (match.group(4) or "your alarm").strip())
    return True


def show_alarms():
    alarms = load_alarms()
    now = datetime.datetime.now()
    active = []
    for alarm in alarms:
        try:
            if datetime.datetime.fromisoformat(alarm["datetime"]) > now:
                active.append(alarm)
        except Exception:
            pass
    save_alarms(active)
    if not active:
        speak("You have no active alarms.")
        return
    print("\n--- RAX ALARMS ---")
    for index, alarm in enumerate(active, 1):
        dt = datetime.datetime.fromisoformat(alarm["datetime"])
        print(f"{index}. {dt.strftime('%d %B %Y, %I:%M %p')} - {alarm['label']}")
    spoken = "; ".join(f"alarm {i}, {datetime.datetime.fromisoformat(a['datetime']).strftime('%I:%M %p')} for {a['label']}" for i, a in enumerate(active, 1))
    speak("Your active alarms are: " + spoken)


def cancel_all_alarms():
    alarms = load_alarms()
    if not alarms:
        speak("There are no active alarms to cancel.")
        return
    cancelled = 0
    for alarm in alarms:
        try:
            result = subprocess.run(["schtasks.exe", "/Delete", "/TN", alarm["task"], "/F"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                cancelled += 1
        except Exception as error:
            print("Cancel alarm error:", error)
    save_alarms([])
    speak(f"I cancelled {cancelled} alarm{'s' if cancelled != 1 else ''}.")


def cancel_alarm(number):
    alarms = load_alarms()
    try:
        index = int(number) - 1
        alarm = alarms[index]
    except (ValueError, IndexError):
        speak("I could not find that alarm number.")
        return
    try:
        result = subprocess.run(["schtasks.exe", "/Delete", "/TN", alarm["task"], "/F"], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            speak("I could not cancel that alarm.")
            return
    except Exception as error:
        print("Cancel alarm error:", error)
        speak("I could not cancel that alarm.")
        return
    alarms.pop(index)
    save_alarms(alarms)
    speak("Alarm cancelled.")


# ============================================================
# JOKES
# ============================================================

JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "Why did the computer go to the doctor? Because it had a virus.",
    "Why was the JavaScript developer sad? Because they did not know how to express themselves.",
]


def tell_joke():
    import random
    speak(random.choice(JOKES))



# ============================================================
# EXTRA DESKTOP UTILITIES
# ============================================================

def log_command(command):
    """Save commands locally so the user can review recent RAX activity."""
    try:
        timestamp = datetime.datetime.now().strftime("%d %B %Y, %I:%M:%S %p")
        with open(COMMAND_HISTORY_FILE, "a", encoding="utf-8") as file:
            file.write(f"[{timestamp}] {command}\n")
    except Exception as error:
        print("Command history error:", error)


def show_command_history(limit=10):
    try:
        if not os.path.exists(COMMAND_HISTORY_FILE):
            speak("There is no command history yet.")
            return
        with open(COMMAND_HISTORY_FILE, "r", encoding="utf-8") as file:
            lines = [line.strip() for line in file if line.strip()]
        if not lines:
            speak("There is no command history yet.")
            return
        recent = lines[-limit:]
        print("\n--- RAX COMMAND HISTORY ---")
        for line in recent:
            print(line)
        speak(f"I displayed your latest {len(recent)} commands in the terminal.")
    except Exception as error:
        print("History error:", error)
        speak("I could not read the command history.")


def clear_command_history():
    try:
        with open(COMMAND_HISTORY_FILE, "w", encoding="utf-8") as file:
            file.write("")
        speak("Command history cleared.")
    except Exception as error:
        print("Clear history error:", error)
        speak("I could not clear the command history.")


def take_screenshot():
    """Capture the primary screen using built-in Windows .NET libraries."""
    try:
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        filename = datetime.datetime.now().strftime("RAX_%Y%m%d_%H%M%S.png")
        path = os.path.join(SCREENSHOTS_DIR, filename)
        encoded = base64.b64encode(path.encode("utf-8")).decode("ascii")
        ps = (
            "Add-Type -AssemblyName System.Windows.Forms\n"
            "Add-Type -AssemblyName System.Drawing\n"
            f"$bytes = [Convert]::FromBase64String('{encoded}')\n"
            "$path = [System.Text.Encoding]::UTF8.GetString($bytes)\n"
            "$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds\n"
            "$bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height\n"
            "$graphics = [System.Drawing.Graphics]::FromImage($bitmap)\n"
            "$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)\n"
            "$bitmap.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)\n"
            "$graphics.Dispose()\n"
            "$bitmap.Dispose()\n"
        )
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and os.path.exists(path):
            speak("Screenshot taken and saved in the RAX Screenshots folder.")
            print("Screenshot:", path)
        else:
            print("Screenshot error:", result.stderr)
            speak("I could not take a screenshot.")
    except Exception as error:
        print("Screenshot error:", error)
        speak("I could not take a screenshot.")


def open_screenshots_folder():
    try:
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        speak("Okay, I am opening your RAX Screenshots folder.")
        os.startfile(SCREENSHOTS_DIR)
    except Exception as error:
        print("Open screenshots error:", error)
        speak("I could not open the screenshots folder.")


def _press_volume_key(vk_code, presses=1):
    ps = (
        '$sig = @"\n'
        '[DllImport("user32.dll")]\n'
        'public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);\n'
        '"@; '
        '$type = Add-Type -MemberDefinition $sig -Name NativeMethods -Namespace RAX -PassThru; '
        f'1..{max(1, int(presses))} | ForEach-Object {{ '
        f'$type::keybd_event({vk_code},0,0,[UIntPtr]::Zero); '
        f'$type::keybd_event({vk_code},0,2,[UIntPtr]::Zero); Start-Sleep -Milliseconds 60 }}'
    )
    return subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", ps],
        capture_output=True, text=True, timeout=8
    )


def volume_up(presses=5):
    try:
        _press_volume_key(0xAF, presses)
        speak("Volume increased.")
    except Exception as error:
        print("Volume error:", error)
        speak("I could not increase the volume.")


def volume_down(presses=5):
    try:
        _press_volume_key(0xAE, presses)
        speak("Volume decreased.")
    except Exception as error:
        print("Volume error:", error)
        speak("I could not decrease the volume.")


def toggle_mute():
    try:
        _press_volume_key(0xAD, 1)
        speak("I toggled system mute.")
    except Exception as error:
        print("Mute error:", error)
        speak("I could not change mute.")


def set_brightness(level):
    """Set the built-in Windows display brightness from 0 to 100 percent."""
    try:
        level = max(0, min(100, int(level)))
        ps = (
            f'$level = [byte]{level}; '
            '$methods = Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods -ErrorAction Stop; '
            'if (-not $methods) { exit 2 }; '
            '$methods | ForEach-Object { '
            'Invoke-CimMethod -InputObject $_ -MethodName WmiSetBrightness '
            '-Arguments @{Timeout=[uint32]1; Brightness=$level} -ErrorAction Stop | Out-Null }'
        )
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            speak(f"Brightness set to {level} percent.")
            return True

        print("Brightness error:", result.stderr.strip() or result.stdout.strip())
        speak("I could not change the brightness. This control normally works with a laptop built-in display.")
        return False
    except Exception as error:
        print("Brightness error:", error)
        speak("I could not change the brightness.")
        return False


def parse_brightness(command):
    """Recognize commands such as 'brightness 50%' or 'set brightness to 20 percent'."""
    text = command.lower().strip()

    if text in {"full brightness", "maximum brightness", "max brightness"}:
        set_brightness(100)
        return True

    if text in {"minimum brightness", "min brightness"}:
        set_brightness(0)
        return True

    match = re.search(
        r"(?:set\s+)?(?:screen\s+|display\s+)?brightness(?:\s+(?:to|at))?\s+(\d{1,3})(?:\s*%|\s+percent)?$",
        text,
        re.IGNORECASE,
    )
    if not match:
        return False

    level = int(match.group(1))
    if not 0 <= level <= 100:
        speak("Brightness must be between 0 and 100 percent.")
        return True

    set_brightness(level)
    return True


def internet_status():
    try:
        sock = socket.create_connection(("1.1.1.1", 53), timeout=3)
        sock.close()
        speak("Your internet connection is working.")
    except OSError:
        speak("I could not reach the internet. Your connection may be offline.")


def get_local_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        speak(f"Your local IP address is {ip.replace('.', ' dot ')}.")
        print("Local IP address:", ip)
    except Exception as error:
        print("IP error:", error)
        speak("I could not determine your local IP address.")


def open_task_manager():
    speak("Okay, I am opening Task Manager.")
    try:
        subprocess.Popen("taskmgr.exe")
    except Exception:
        speak("I could not open Task Manager.")


def open_windows_settings():
    speak("Okay, I am opening Windows Settings.")
    try:
        os.system("start ms-settings:")
    except Exception:
        speak("I could not open Windows Settings.")


def open_control_panel():
    speak("Okay, I am opening Control Panel.")
    try:
        subprocess.Popen("control.exe")
    except Exception:
        speak("I could not open Control Panel.")


def read_clipboard():
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
            capture_output=True, text=True, timeout=5
        )
        text = result.stdout.strip()
        if not text:
            speak("Your clipboard is empty or does not contain readable text.")
            return
        print("\n--- CLIPBOARD ---\n" + text)
        spoken = text if len(text) <= 400 else text[:400] + "..."
        speak("Your clipboard says: " + spoken)
    except Exception as error:
        print("Clipboard error:", error)
        speak("I could not read the clipboard.")


def copy_to_clipboard(text):
    text = text.strip()
    if not text:
        speak("Please tell me what to copy.")
        return
    try:
        encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
        ps = (
            f"$bytes=[Convert]::FromBase64String('{encoded}'); "
            "$text=[System.Text.Encoding]::UTF8.GetString($bytes); "
            "Set-Clipboard -Value $text"
        )
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", ps],
            timeout=5, check=True
        )
        speak("Copied to clipboard.")
    except Exception as error:
        print("Clipboard error:", error)
        speak("I could not copy that text.")


def timer_callback(message):
    speak(f"Timer finished. {message}")


def create_timer(seconds, message="Your timer is complete"):
    if seconds <= 0:
        speak("The timer duration must be greater than zero.")
        return
    timer = threading.Timer(seconds, timer_callback, args=(message,))
    timer.daemon = True
    timer.start()
    if seconds < 60:
        speak(f"Timer set for {int(seconds)} seconds.")
    elif seconds < 3600:
        speak(f"Timer set for {round(seconds / 60, 2)} minutes.")
    else:
        speak(f"Timer set for {round(seconds / 3600, 2)} hours.")


def parse_timer(command):
    pattern = r"(?:set\s+(?:a\s+)?timer(?:\s+for)?|timer)\s+(\d+(?:\.\d+)?)\s*(second|seconds|minute|minutes|hour|hours)(?:\s+(?:for|to)\s+(.+))?$"
    match = re.search(pattern, command, re.IGNORECASE)
    if not match:
        return False
    amount = float(match.group(1))
    unit = match.group(2).lower()
    message = (match.group(3) or "Your timer is complete").strip()
    if "hour" in unit:
        seconds = amount * 3600
    elif "minute" in unit:
        seconds = amount * 60
    else:
        seconds = amount
    create_timer(seconds, message)
    return True


def maps_search(place):
    place = place.strip()
    if not place:
        speak("What place should I find on Google Maps?")
        return
    speak(f"Opening Google Maps for {place}.")
    webbrowser.open(
        "https://www.google.com/maps/search/?api=1&query="
        + urllib.parse.quote_plus(place)
    )


# ============================================================
# AI PROGRAMMING + ONLINE COMPILER
# ============================================================

CODE_EXTENSIONS = {
    "python": ".py",
    "c": ".c",
    "c++": ".cpp",
    "cpp": ".cpp",
    "java": ".java",
    "javascript": ".js",
    "js": ".js",
    "typescript": ".ts",
    "sql": ".sql",
    "go": ".go",
    "rust": ".rs",
    "php": ".php",
    "ruby": ".rb",
    "c#": ".cs",
    "kotlin": ".kt",
    "swift": ".swift",
}

LANGUAGE_ALIASES = {
    "python": ["python"],
    "c": ["c (", "c ", "gnu c"],
    "c++": ["c++", "cpp"],
    "cpp": ["c++", "cpp"],
    "java": ["java (", "java "],
    "javascript": ["javascript", "node.js", "nodejs"],
    "js": ["javascript", "node.js", "nodejs"],
    "typescript": ["typescript"],
    "sql": ["sql", "sqlite"],
    "go": ["go (", "golang"],
    "rust": ["rust"],
    "php": ["php"],
    "ruby": ["ruby"],
    "c#": ["c#", "c sharp"],
    "kotlin": ["kotlin"],
    "swift": ["swift"],
}


def extract_openai_text(data):
    """Extract assistant text from a Responses API JSON object."""
    pieces = []
    for item in data.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                pieces.append(content["text"])
    return "\n".join(pieces).strip()


def request_ai_code(language, task):
    """Ask the AI coding model for one self-contained program in JSON form."""
    if not OPENAI_API_KEY:
        speak("AI coding is not configured yet. Please set the OPENAI API key in your terminal first.")
        print("\nSet it in PowerShell with:")
        print('$env:OPENAI_API_KEY="YOUR_KEY_HERE"')
        return None

    prompt = f"""
You are the coding engine inside a Windows voice assistant named RAX.
Create a correct, self-contained {language} solution for this request:

{task}

Rules:
- Return ONLY valid JSON. No markdown fences and no extra text.
- JSON keys must be: language, code, stdin, explanation.
- language must be exactly: {language}
- code must be complete and directly runnable.
- stdin must be a string. Use an empty string if no input is needed.
- explanation must be short, maximum 3 sentences.
- Prefer deterministic examples so the online compiler can show useful output immediately.
- For SQL, make the code self-contained by including CREATE TABLE and sample INSERT statements when tables are needed.
- Do not use network access, GUI access, files outside the program, or destructive system operations.
""".strip()

    try:
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": RAX_AI_MODEL,
                "input": prompt,
            },
            timeout=90,
        )
        if response.status_code >= 400:
            print("AI API error:", response.status_code, response.text[:800])
            speak("The AI coding service returned an error. Check the terminal for details.")
            return None

        raw = extract_openai_text(response.json()).strip()
        if not raw:
            speak("The AI did not return code.")
            return None

        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
            raw = re.sub(r"\s*```$", "", raw)

        result = json.loads(raw)
        code = str(result.get("code", "")).strip()
        if not code:
            raise ValueError("AI response did not contain code.")
        result["language"] = str(result.get("language") or language).strip().lower()
        result["stdin"] = str(result.get("stdin") or "")
        result["explanation"] = str(result.get("explanation") or "")
        return result
    except json.JSONDecodeError as error:
        print("AI JSON error:", error)
        print("Raw AI response:", raw[:2000] if 'raw' in locals() else '')
        speak("The AI returned code in an unexpected format. Please try again.")
        return None
    except Exception as error:
        print("AI coding error:", error)
        speak("I could not contact the AI coding service.")
        return None


def get_judge0_languages(base_url):
    response = requests.get(base_url + "/languages/", timeout=15)
    response.raise_for_status()
    return response.json()


def choose_judge0_language(languages, requested):
    requested = requested.lower().strip()
    aliases = LANGUAGE_ALIASES.get(requested, [requested])

    # Prefer newer/higher language IDs when several versions match.
    matches = []
    for item in languages:
        name = str(item.get("name", "")).lower()
        if any(alias in name for alias in aliases):
            matches.append(item)

    if not matches:
        return None
    return sorted(matches, key=lambda x: int(x.get("id", 0)), reverse=True)[0]


def run_code_online(language, code, stdin=""):
    """Compile/run code on Judge0 and return its result."""
    last_error = None
    for base_url in JUDGE0_URLS:
        try:
            languages = get_judge0_languages(base_url)
            selected = choose_judge0_language(languages, language)
            if not selected:
                continue

            create = requests.post(
                base_url + "/submissions?base64_encoded=false&wait=false",
                headers={"Content-Type": "application/json"},
                json={
                    "source_code": code,
                    "language_id": selected["id"],
                    "stdin": stdin,
                },
                timeout=20,
            )
            create.raise_for_status()
            token = create.json().get("token")
            if not token:
                raise RuntimeError("Judge0 did not return a submission token.")

            for _ in range(35):
                time.sleep(0.6)
                result_response = requests.get(
                    base_url + f"/submissions/{token}?base64_encoded=false&fields=stdout,stderr,compile_output,message,status,time,memory",
                    timeout=15,
                )
                result_response.raise_for_status()
                result = result_response.json()
                status_id = int((result.get("status") or {}).get("id", 0))
                if status_id not in {1, 2}:
                    result["judge_language"] = selected.get("name", language)
                    result["judge_url"] = base_url
                    return result

            raise TimeoutError("Online compiler did not finish in time.")
        except Exception as error:
            last_error = error
            print(f"Judge0 error at {base_url}:", error)

    if last_error:
        raise last_error
    raise RuntimeError(f"No online compiler language was found for {language}.")


def save_generated_code(language, code):
    os.makedirs(CODE_DIR, exist_ok=True)
    safe_language = language.lower().strip()
    extension = CODE_EXTENSIONS.get(safe_language, ".txt")
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(CODE_DIR, f"rax_{safe_language.replace('+', 'p').replace('#', 'sharp')}_{stamp}{extension}")
    with open(path, "w", encoding="utf-8") as file:
        file.write(code)
    return path


def show_code_result(language, task, generated, result):
    code = generated["code"]
    explanation = generated.get("explanation", "")
    stdout = (result.get("stdout") or "").rstrip()
    stderr = (result.get("stderr") or "").rstrip()
    compile_output = (result.get("compile_output") or "").rstrip()
    message = (result.get("message") or "").rstrip()
    status = (result.get("status") or {}).get("description", "Unknown")

    path = save_generated_code(language, code)

    print("\n" + "=" * 70)
    print("RAX PROGRAMMING ASSISTANT")
    print("=" * 70)
    print("Task:", task)
    print("Language:", language)
    print("Compiler:", result.get("judge_language", "Judge0"))
    print("Saved:", path)
    print("\n--- CODE ---")
    print(code)
    print("\n--- STATUS ---")
    print(status)
    if stdout:
        print("\n--- OUTPUT ---")
        print(stdout)
    if compile_output:
        print("\n--- COMPILER OUTPUT ---")
        print(compile_output)
    if stderr:
        print("\n--- ERROR OUTPUT ---")
        print(stderr)
    if message:
        print("\n--- MESSAGE ---")
        print(message)
    if explanation:
        print("\n--- EXPLANATION ---")
        print(explanation)
    print("=" * 70)

    if status.lower() == "accepted":
        if stdout:
            spoken_output = re.sub(r"\s+", " ", stdout)[:300]
            speak(f"The program ran successfully. The output is: {spoken_output}")
        else:
            speak("The program compiled and ran successfully. The code and result are shown in the terminal.")
    else:
        speak(f"The online compiler returned {status}. I showed the details in the terminal.")


def run_programming_task(language, task):
    """Shared coding pipeline used by voice mode and Code Lab."""
    language = language.lower().strip()
    task = task.strip()
    if not task:
        speak("Tell me what program you want me to create.")
        return None

    speak(f"Okay. I will write the {language} code and run it using the online compiler.")
    generated = request_ai_code(language, task)
    if not generated:
        return None

    print("\nRAX generated the code. Sending it to the online compiler...")
    try:
        result = run_code_online(language, generated["code"], generated.get("stdin", ""))
        show_code_result(language, task, generated, result)
        if GUI_ROOT is not None:
            # Find an existing Code Lab window and update its result area if present.
            try:
                for child in GUI_ROOT.winfo_children():
                    if str(child.title()).startswith("RAX Code Lab"):
                        widgets = [w for w in child.winfo_children() if isinstance(w, scrolledtext.ScrolledText)]
                        if widgets:
                            widgets[-1].delete("1.0", tk.END)
                            widgets[-1].insert(tk.END, format_code_lab_result(language, task, generated, result))
                            widgets[-1].see("1.0")
                        break
            except Exception as ui_error:
                print("Code Lab UI update error:", ui_error)
        return result
    except Exception as error:
        print("Online compiler error:", error)
        path = save_generated_code(language, generated["code"])
        print("\n--- GENERATED CODE ---")
        print(generated["code"])
        print("\nSaved:", path)
        speak("I created the code, but the online compiler is unavailable. I saved the code and showed it in the terminal.")
        return None


def programming_task(language, task):
    return run_programming_task(language, task)


def programming_mode():
    """Voice-first Code Lab flow: ask language, then task, then generate + run."""
    speak("Code Lab is ready. What programming language do you want to use? I can use any language available on the connected online compiler.")
    language = listen()
    if not language:
        speak("I did not hear the programming language.")
        return

    language = language.lower().strip()
    spoken_aliases = {
        "c plus plus": "c++", "cplusplus": "c++", "cpp": "c++",
        "java script": "javascript", "type script": "typescript",
        "c sharp": "c#", "golang": "go", "sequel": "sql",
        "dot net": "c#", "c sharp dot net": "c#",
    }
    language = spoken_aliases.get(language, language)

    # Validate against the live Judge0 language list when possible. This makes
    # Code Lab dynamic instead of being limited to RAX's original 14 languages.
    try:
        languages = get_judge0_languages(JUDGE0_URLS[0])
        selected = choose_judge0_language(languages, language)
        if selected:
            compiler_name = selected.get("name", language)
            language = compiler_name.split("(", 1)[0].strip()
            speak(f"Great. I found {compiler_name} online. What should I build or solve in {language}?")
        else:
            speak(f"I heard {language}. I could not verify that language on the online compiler, but I can still try to generate it. What should I build or solve?")
    except Exception:
        speak(f"I heard {language}. What should I build or solve in that language?")

    task = listen()
    if not task:
        speak("I did not hear the coding question.")
        return
    run_programming_task(language, task)


def open_code_folder():
    os.makedirs(CODE_DIR, exist_ok=True)
    speak("Opening your RAX code folder.")
    try:
        os.startfile(CODE_DIR)
    except Exception as error:
        print("Open code folder error:", error)
        speak("I could not open the code folder.")



# ============================================================
# WHATSAPP - WINDOWS DESKTOP APP + MESSAGE CONFIRMATION
# ============================================================

WHATSAPP_DRIVER = None
WHATSAPP_CURRENT_CONTACT = None
WHATSAPP_OPENED = False
WHATSAPP_PROFILE_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", BASE_DIR),
    "RAX_WhatsApp_Profile"
)


def _pyautogui_import():
    try:
        import pyautogui
        return pyautogui
    except ImportError:
        return None


def _activate_whatsapp_window():
    """Bring the installed WhatsApp Windows app to the foreground."""
    try:
        import ctypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        SW_RESTORE = 9

        found = {"hwnd": None}

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        def enum_callback(hwnd, lparam):
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value.lower()
            if "whatsapp" in title:
                found["hwnd"] = hwnd
                return False
            return True

        user32.EnumWindows(enum_callback, 0)
        hwnd = found["hwnd"]
        if not hwnd:
            return None

        user32.ShowWindow(hwnd, SW_RESTORE)
        try:
            user32.SetForegroundWindow(hwnd)
        except Exception:
            pass
        time.sleep(0.5)
        return hwnd
    except Exception as error:
        print("WhatsApp activation error:", repr(error))
        return None


def _whatsapp_window_rect():
    """Return (left, top, right, bottom) for the WhatsApp window."""
    try:
        import ctypes
        from ctypes import wintypes
        hwnd = _activate_whatsapp_window()
        if not hwnd:
            return None
        rect = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return rect.left, rect.top, rect.right, rect.bottom
    except Exception as error:
        print("WhatsApp window rectangle error:", repr(error))
        return None


def open_whatsapp_app():
    """Open the already-installed Windows WhatsApp application."""
    global WHATSAPP_OPENED
    try:
        os.startfile("whatsapp:")
        WHATSAPP_OPENED = True
        time.sleep(3)
        _activate_whatsapp_window()
        speak("WhatsApp is open, boss. Tell me the contact name.")
        return True
    except Exception as error:
        print("WhatsApp app launch error:", repr(error))
        return False



def close_whatsapp_app():
    """Close the installed WhatsApp Windows application."""
    global WHATSAPP_OPENED, WHATSAPP_CURRENT_CONTACT
    try:
        closed = False
        # First try to close the active WhatsApp window gracefully.
        try:
            hwnd = _activate_whatsapp_window()
            if hwnd:
                import ctypes
                WM_CLOSE = 0x0010
                ctypes.windll.user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
                time.sleep(1.2)
                closed = True
        except Exception as error:
            print("WhatsApp graceful close error:", repr(error))

        # Fallback: terminate only the WhatsApp executable.
        try:
            result = subprocess.run(
                ["taskkill", "/F", "/IM", "WhatsApp.exe", "/T"],
                capture_output=True, text=True, timeout=5,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0:
                closed = True
        except Exception as error:
            print("WhatsApp taskkill error:", repr(error))

        WHATSAPP_OPENED = False
        WHATSAPP_CURRENT_CONTACT = None

        if closed:
            speak("Okay boss, WhatsApp is closed.")
            return True

        speak("Boss, WhatsApp is already closed.")
        return True
    except Exception as error:
        print("WhatsApp close error:", repr(error))
        speak("Boss, I could not close WhatsApp.")
        return True

def _find_whatsapp_window_pyautogui():
    pa = _pyautogui_import()
    if pa is None:
        return None
    try:
        pa.hotkey("win", "s")
        time.sleep(1)
        pa.write("WhatsApp", interval=0.03)
        time.sleep(1)
        pa.press("enter")
        time.sleep(3)
        _activate_whatsapp_window()
        return pa
    except Exception as error:
        print("WhatsApp Windows search error:", repr(error))
        return None


def open_whatsapp_desktop_chat(contact):
    """Open a saved contact in the user's existing Windows WhatsApp app."""
    global WHATSAPP_CURRENT_CONTACT, WHATSAPP_OPENED

    contact = re.sub(r"\s+", " ", str(contact or "")).strip()
    if not contact:
        return False

    pa = _pyautogui_import()
    if pa is None:
        speak("Boss, I need PyAutoGUI for Windows WhatsApp control. Please install it with pip.")
        return False

    try:
        if not WHATSAPP_OPENED:
            try:
                os.startfile("whatsapp:")
            except Exception as error:
                print("whatsapp: protocol launch failed:", repr(error))
                if _find_whatsapp_window_pyautogui() is None:
                    return False
            WHATSAPP_OPENED = True
            time.sleep(3)
        else:
            _activate_whatsapp_window()

        _activate_whatsapp_window()
        print(f"RAX WhatsApp desktop: opening contact -> {contact}")

        # WhatsApp Desktop shortcut for starting a new chat.
        pa.hotkey("ctrl", "alt", "n")
        time.sleep(1.2)
        pa.hotkey("ctrl", "a")
        pa.write(contact, interval=0.05)
        time.sleep(1.8)

        # Search result selection.
        pa.press("down")
        time.sleep(0.35)
        pa.press("enter")
        time.sleep(1.2)
        pa.press("enter")
        time.sleep(1.2)

        _activate_whatsapp_window()
        WHATSAPP_CURRENT_CONTACT = contact
        speak(f"Okay boss, {contact} chat is open.")
        speak("When you want to write, say type message.")
        return True

    except Exception as error:
        print("WhatsApp desktop chat error:", repr(error))
        speak(f"Boss, I could not open {contact} chat.")
        return False


def open_whatsapp_chat(contact):
    """Open contact in Windows WhatsApp. Chrome is kept only as a last resort."""
    return open_whatsapp_desktop_chat(contact)


def _focus_whatsapp_message_box(pa):
    """Focus the message composer in the active WhatsApp window."""
    _activate_whatsapp_window()
    rect = _whatsapp_window_rect()

    if rect:
        left, top, right, bottom = rect
        width = max(300, right - left)
        height = max(300, bottom - top)

        # The composer is near the bottom of the chat pane. Start around
        # 60% of the window width and 92% of its height.
        x = int(left + width * 0.62)
        y = int(top + height * 0.92)
        pa.click(x, y)
        time.sleep(0.4)
        return True

    # Safe fallback for a maximized WhatsApp window.
    screen_w, screen_h = pa.size()
    pa.click(int(screen_w * 0.62), int(screen_h * 0.92))
    time.sleep(0.4)
    return True


def type_whatsapp_message(message, replace=False):
    pa = _pyautogui_import()
    if pa is None:
        return False

    message = str(message or "").strip()
    if not message:
        return False

    try:
        _focus_whatsapp_message_box(pa)

        if replace:
            pa.hotkey("ctrl", "a")
            time.sleep(0.1)
            pa.press("backspace")

        pa.write(message, interval=0.025)
        time.sleep(0.4)
        return True
    except Exception as error:
        print("WhatsApp typing error:", repr(error))
        return False


def clear_whatsapp_draft():
    pa = _pyautogui_import()
    if pa is None:
        return False
    try:
        _focus_whatsapp_message_box(pa)
        pa.hotkey("ctrl", "a")
        pa.press("backspace")
        return True
    except Exception as error:
        print("WhatsApp clear draft error:", repr(error))
        return False


def send_whatsapp_draft():
    pa = _pyautogui_import()
    if pa is None:
        return False
    try:
        _focus_whatsapp_message_box(pa)
        pa.press("enter")
        time.sleep(0.8)
        speak("Yes boss, the message has been sent.")
        return True
    except Exception as error:
        print("WhatsApp send error:", repr(error))
        speak("Boss, I could not send the message.")
        return False


def whatsapp_message_flow(contact=None):
    """Type a message into the current WhatsApp chat and confirm before sending."""
    global WHATSAPP_CURRENT_CONTACT

    contact = contact or WHATSAPP_CURRENT_CONTACT
    if not contact:
        speak("Boss, no WhatsApp chat is selected. Say open WhatsApp and then open the contact chat.")
        return True

    # The chat is already open. Do not reopen it.
    _activate_whatsapp_window()
    speak("Yes boss, tell me the message.")

    message = listen()
    if not message:
        speak("Boss, I did not hear the message.")
        return True

    if not type_whatsapp_message(message):
        speak("Boss, I could not type the message in the chat.")
        return True

    speak(f"Boss, I typed: {message}. Please confirm. Should I send this message?")

    while True:
        answer = listen()
        if not answer:
            continue

        answer = answer.lower().strip()

        if answer in {
            "yes", "yeah", "yep", "send", "send it",
            "yes send", "okay send", "ok send", "send message",
            "yes send it", "yes please"
        }:
            send_whatsapp_draft()
            return True

        if answer in {
            "no", "no send", "cancel", "do not send",
            "don't send", "do not send it", "don't send it"
        }:
            clear_whatsapp_draft()
            speak("Okay boss, I will not send that message.")
            return True

        if any(word in answer for word in {"change", "edit", "replace", "correct"}):
            speak("Yes boss, tell me the new message.")
            new_message = listen()
            if not new_message:
                speak("Boss, I did not hear the new message.")
                continue

            if type_whatsapp_message(new_message, replace=True):
                speak(f"Boss, I changed it to: {new_message}. Should I send this message?")
            else:
                speak("Boss, I could not replace the message.")
            continue

        speak("Boss, please say yes to send, change this to edit it, or cancel.")


def whatsapp_call(contact):
    if not open_whatsapp_chat(contact):
        return True
    pa = _pyautogui_import()
    if pa is None:
        return True
    try:
        _activate_whatsapp_window()
        for _ in range(8):
            pa.press("tab")
            time.sleep(0.15)
        pa.press("enter")
        speak(f"Okay boss, I tried to call {contact} on WhatsApp.")
        return True
    except Exception as error:
        print("WhatsApp call error:", repr(error))
        speak("I could not start the WhatsApp call.")
        return True


def _extract_whatsapp_contact(text):
    text = re.sub(r"\s+", " ", text.strip())
    text = re.sub(r"\s+(?:chat|contact)$", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"^(?:my|the|saved)\s+contact\s+", "", text, flags=re.IGNORECASE)
    return text.strip(" .,!?:;\"'")


def parse_whatsapp_command(command):
    """Support opening a contact, then separately typing a message."""
    global WHATSAPP_OPENED, WHATSAPP_CURRENT_CONTACT

    text = re.sub(r"\s+", " ", str(command or "").lower().strip())
    print(f"RAX WhatsApp parser input: {text}")

    # Open WhatsApp only.
    if text in {"open whatsapp", "whatsapp", "open whatsapp web", "open my whatsapp"}:
        if open_whatsapp_app():
            return True
        speak("Boss, I could not open the Windows WhatsApp app.")
        return True

    # Close WhatsApp.
    if text in {
        "close whatsapp", "exit whatsapp", "quit whatsapp",
        "close my whatsapp", "close the whatsapp", "shutdown whatsapp"
    }:
        return close_whatsapp_app()

    # Ask RAX to open a different/another chat, then listen for the name.
    if text in {
        "open another chat", "open another whatsapp chat",
        "open a different chat", "open a new chat",
        "switch chat", "switch whatsapp chat", "change chat"
    }:
        if not WHATSAPP_OPENED:
            if not open_whatsapp_app():
                speak("Boss, I could not open WhatsApp.")
                return True
        speak("Yes boss, tell me the contact name.")
        contact_answer = listen()
        if not contact_answer:
            speak("Boss, I did not hear the contact name.")
            return True
        contact = _extract_whatsapp_contact(contact_answer)
        if not contact:
            speak("Boss, I could not understand the contact name.")
            return True
        return open_whatsapp_chat(contact)

    # Separate message command AFTER a chat has been opened.
    if text in {
        "type message", "type a message", "write message", "write a message",
        "send a message", "type my message", "write my message",
        "message", "compose message"
    }:
        if WHATSAPP_CURRENT_CONTACT:
            return whatsapp_message_flow(WHATSAPP_CURRENT_CONTACT)
        speak("Boss, open a WhatsApp contact chat first.")
        return True

    # Call command.
    for pattern in [
        r"^call (.+?) on whatsapp$",
        r"^whatsapp call (.+)$",
        r"^open whatsapp and call (.+)$",
    ]:
        m = re.match(pattern, text)
        if m:
            return whatsapp_call(_extract_whatsapp_contact(m.group(1)))

    # Explicit switch/open a different contact chat.
    for pattern in [
        r"^(?:switch|change) (?:to|chat to) (.+?)(?: chat)?$",
        r"^open another chat (?:with|for) (.+)$",
    ]:
        m = re.match(pattern, text)
        if m:
            contact = _extract_whatsapp_contact(m.group(1))
            if contact and contact not in {"whatsapp", "chat", "anyone", "someone", "another"}:
                return open_whatsapp_chat(contact)

    # One-step open-chat command.
    for pattern in [
        r"^open whatsapp and open (.+?) chat$",
        r"^open whatsapp and (.+?) chat$",
        r"^open (.+?) chat on whatsapp$",
        r"^whatsapp (.+?) chat$",
        r"^open (.+?) chat$",
        r"^open whatsapp chat (.+)$",
    ]:
        m = re.match(pattern, text)
        if m:
            contact = _extract_whatsapp_contact(m.group(1))
            if contact and contact not in {"whatsapp", "my", "the", "anyone", "someone"}:
                if not WHATSAPP_OPENED:
                    open_whatsapp_app()
                return open_whatsapp_chat(contact)

    # If WhatsApp is already open, support: "open Aman" or "go to Aman".
    if WHATSAPP_OPENED:
        m = re.match(r"^(?:open|go to|show)(?: the)? (.+?)(?: chat)?$", text)
        if m:
            contact = _extract_whatsapp_contact(m.group(1))
            if contact and contact not in {"whatsapp", "chat", "anyone", "someone"}:
                return open_whatsapp_chat(contact)

    return False


# ============================================================
# SHOPPING SEARCH
# ============================================================

SHOPPING_SITES = {
    "amazon": "https://www.amazon.in/s?k={query}",
    "flipkart": "https://www.flipkart.com/search?q={query}",
    "meesho": "https://www.meesho.com/search?q={query}",
    "shopsy": "https://www.shopsy.in/search?q={query}",
}


def shopping_search(site, product):
    site = site.lower().strip()
    product = product.strip()
    if site not in SHOPPING_SITES:
        speak("I do not know that shopping website yet.")
        return True
    home_urls = {
        "amazon": "https://www.amazon.in/",
        "flipkart": "https://www.flipkart.com/",
        "meesho": "https://www.meesho.com/",
        "shopsy": "https://www.shopsy.in/",
    }
    if not product:
        speak(f"Okay boss, I am opening {site}.")
        webbrowser.open(home_urls[site])
        return True
    url = SHOPPING_SITES[site].format(query=urllib.parse.quote_plus(product))
    speak(f"Okay boss, I am searching {product} on {site}.")
    webbrowser.open(url)
    speak("Boss, the product has been searched.")
    return True


def parse_shopping_command(command):
    text = command.lower().strip()
    site_patterns = {
        "amazon": ["amazon", "amazon india"],
        "flipkart": ["flipkart"],
        "meesho": ["meesho"],
        "shopsy": ["shopsy"],
    }
    for site, names in site_patterns.items():
        for name in names:
            escaped = re.escape(name)
            patterns = [
                rf"(?:open\s+)?{escaped}\s+(?:and\s+)?(?:search|find|look\s+for|show\s+me)\s+(.+)$",
                rf"(?:search|find|look\s+for|show\s+me)\s+(.+?)\s+(?:on|in|at)\s+{escaped}$",
                rf"{escaped}\s+(?:search|find)\s+(.+)$",
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match and match.group(1).strip():
                    return shopping_search(site, match.group(1).strip())
            if text in {f"open {name}", name}:
                return shopping_search(site, "")
    return False


# ============================================================
# COMMAND HANDLER
# ============================================================


# ============================================================
# RAX PRO 2.0 FEATURES
# ============================================================

PRO_MEMORY_FILE = os.path.join(BASE_DIR, "rax_memory.json")
TODO_FILE = os.path.join(BASE_DIR, "rax_todos.json")
FOCUS_FILE = os.path.join(BASE_DIR, "rax_focus.json")
PRO_LOG_FILE = os.path.join(BASE_DIR, "rax_pro_activity.log")


def _pro_json(path, default):
    try:
        if not os.path.exists(path):
            _save_json(path, default)
            return default
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception:
        return default


def _pro_log(action, detail=""):
    try:
        with open(PRO_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {action} {detail}\n")
    except Exception:
        pass


def remember_fact(text):
    text = re.sub(r"^(?:remember|remember that|save this)\s*", "", text, flags=re.I).strip()
    if not text:
        speak("Tell me what you want me to remember.")
        return
    memory = _pro_json(PRO_MEMORY_FILE, [])
    memory.append({"text": text, "time": datetime.datetime.now().isoformat(timespec="seconds")})
    _save_json(PRO_MEMORY_FILE, memory[-200:])
    _pro_log("MEMORY", text)
    speak("I will remember that.")


def show_memory():
    memory = _pro_json(PRO_MEMORY_FILE, [])
    if not memory:
        speak("My memory is empty.")
        return
    lines = [f"{i}. {item.get('text','')}" for i, item in enumerate(memory[-10:], 1)]
    text = "Here are my latest memories. " + "; ".join(lines)
    speak(text[:1800])


def clear_memory():
    _save_json(PRO_MEMORY_FILE, [])
    _pro_log("MEMORY_CLEAR")
    speak("My saved memory has been cleared.")


def add_todo(text):
    text = re.sub(r"^(?:add|create|make)\s+(?:a\s+)?(?:todo|to-do|task)\s*[:,-]?\s*", "", text, flags=re.I).strip()
    if not text:
        speak("Tell me the task you want to add.")
        return
    todos = _pro_json(TODO_FILE, [])
    todos.append({"task": text, "done": False, "created": datetime.datetime.now().isoformat(timespec="seconds")})
    _save_json(TODO_FILE, todos)
    _pro_log("TODO_ADD", text)
    speak(f"Added to your task list: {text}")


def list_todos():
    todos = _pro_json(TODO_FILE, [])
    pending = [x for x in todos if not x.get("done")]
    if not pending:
        speak("You have no pending tasks.")
        return
    lines = [f"{i+1}. {x.get('task','')}" for i, x in enumerate(pending[:12])]
    speak("Your pending tasks are: " + "; ".join(lines))


def complete_todo(number):
    todos = _pro_json(TODO_FILE, [])
    pending_indexes = [i for i, x in enumerate(todos) if not x.get("done")]
    try:
        n = int(number) - 1
        if n < 0 or n >= len(pending_indexes):
            raise ValueError
        idx = pending_indexes[n]
        todos[idx]["done"] = True
        todos[idx]["completed"] = datetime.datetime.now().isoformat(timespec="seconds")
        _save_json(TODO_FILE, todos)
        speak(f"Completed task {number}.")
    except Exception:
        speak("I could not find that task number.")


def clear_completed_todos():
    todos = _pro_json(TODO_FILE, [])
    todos = [x for x in todos if not x.get("done")]
    _save_json(TODO_FILE, todos)
    speak("Completed tasks were cleared.")


def start_pomodoro(minutes=25):
    global POMODORO_RUNNING, POMODORO_END, POMODORO_AFTER
    try:
        minutes = max(1, min(180, int(minutes)))
    except Exception:
        minutes = 25
    if POMODORO_AFTER:
        try:
            GUI_ROOT.after_cancel(POMODORO_AFTER)
        except Exception:
            pass
    POMODORO_RUNNING = True
    POMODORO_END = time.monotonic() + minutes * 60
    _pro_log("POMODORO_START", f"{minutes}m")
    speak(f"Focus session started for {minutes} minutes.")
    _pomodoro_tick()


def _pomodoro_tick():
    global POMODORO_RUNNING, POMODORO_AFTER
    if not POMODORO_RUNNING:
        return
    remaining = int(max(0, POMODORO_END - time.monotonic()))
    if remaining <= 0:
        POMODORO_RUNNING = False
        speak("Focus session complete. Time for a short break.")
        return
    if GUI_ROOT is not None:
        POMODORO_AFTER = GUI_ROOT.after(1000, _pomodoro_tick)
    else:
        threading.Timer(1, _pomodoro_tick).start()


def stop_pomodoro():
    global POMODORO_RUNNING, POMODORO_AFTER
    POMODORO_RUNNING = False
    if GUI_ROOT is not None and POMODORO_AFTER:
        try:
            GUI_ROOT.after_cancel(POMODORO_AFTER)
        except Exception:
            pass
    POMODORO_AFTER = None
    speak("Focus session stopped.")


def pomodoro_status():
    if not POMODORO_RUNNING:
        speak("No focus session is running.")
        return
    sec = int(max(0, POMODORO_END - time.monotonic()))
    speak(f"Focus session has {sec // 60} minutes and {sec % 60} seconds remaining.")


def system_report():
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage(os.path.abspath(os.sep))
        net = psutil.net_io_counters()
        battery = psutil.sensors_battery()
        bat = f", battery {battery.percent:.0f} percent" if battery else ""
        text = (f"System report: CPU {cpu:.0f} percent, RAM {ram.percent:.0f} percent, "
                f"disk {disk.percent:.0f} percent, network sent {net.bytes_sent // (1024*1024)} megabytes, "
                f"received {net.bytes_recv // (1024*1024)} megabytes{bat}.")
        speak(text)
    except Exception as e:
        speak("I could not read the full system report. " + str(e)[:120])


def network_test():
    import urllib.request
    try:
        start = time.perf_counter()
        with urllib.request.urlopen("https://www.google.com/generate_204", timeout=5) as r:
            r.read(1)
        ms = (time.perf_counter() - start) * 1000
        speak(f"Internet connection is working. Response time is about {ms:.0f} milliseconds.")
    except Exception:
        speak("The internet connection test failed or timed out.")


def find_files(pattern, folder=None, limit=20):
    pattern = pattern.strip().strip('"').strip("'")
    if not pattern:
        speak("Tell me a file name to find.")
        return
    folder = folder or os.path.expanduser("~")
    matches = []
    try:
        for root, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if d not in {"AppData", "node_modules", ".git", "__pycache__"}]
            for name in files:
                if pattern.lower() in name.lower():
                    matches.append(os.path.join(root, name))
                    if len(matches) >= limit:
                        break
            if len(matches) >= limit:
                break
    except Exception:
        pass
    if not matches:
        speak(f"I could not find a file matching {pattern}.")
        return
    text = "I found " + str(len(matches)) + " files. " + "; ".join(matches[:8])
    gui_log("RAX", text)
    speak(text[:1600])


def open_path(path):
    path = os.path.expandvars(os.path.expanduser(path.strip().strip('"')))
    if not os.path.exists(path):
        speak("That file or folder does not exist.")
        return
    try:
        os.startfile(path) if hasattr(os, "startfile") else subprocess.Popen(["xdg-open", path])
        speak("Opening it now.")
    except Exception as e:
        speak("I could not open that path. " + str(e)[:100])


def create_project_folder(name):
    name = re.sub(r'[<>:"/|?*\\]', "", name).strip()
    if not name:
        speak("Please give the project a name.")
        return
    path = os.path.join(os.path.expanduser("~/Desktop"), name)
    try:
        os.makedirs(os.path.join(path, "src"), exist_ok=True)
        os.makedirs(os.path.join(path, "assets"), exist_ok=True)
        os.makedirs(os.path.join(path, "docs"), exist_ok=True)
        with open(os.path.join(path, "README.md"), "w", encoding="utf-8") as f:
            f.write(f"# {name}\n\nCreated by RAX.\n")
        _pro_log("PROJECT_CREATE", path)
        speak(f"Project folder {name} was created on your desktop.")
        open_path(path)
    except Exception as e:
        speak("I could not create the project. " + str(e)[:120])


def show_pro_help():
    speak("RAX Pro adds memory, tasks, focus sessions, system reports, internet tests, file search, project creation, AI chat, and a Pro dashboard. Try remember this, add task study Python, start pomodoro, system report, find file, create project, or ask AI followed by your question.")


def ai_chat(prompt):
    """Optional OpenAI-powered conversational layer. Uses OPENAI_API_KEY only from environment."""
    prompt = prompt.strip()
    if not prompt:
        speak("What would you like to ask me?")
        return
    if not OPENAI_API_KEY:
        speak("AI chat is not configured yet. Set the OPENAI_API_KEY environment variable, then restart RAX.")
        return
    try:
        url = "https://api.openai.com/v1/responses"
        payload = {
            "model": RAX_AI_MODEL,
            "input": [
                {"role": "system", "content": "You are RAX, a concise and helpful desktop AI assistant. Give practical answers. Do not claim to have performed an action unless RAX actually performed it."},
                {"role": "user", "content": prompt},
            ],
        }
        response = requests.post(url, headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}, json=payload, timeout=45)
        response.raise_for_status()
        data = response.json()
        answer = data.get("output_text", "")
        if not answer:
            parts = []
            for item in data.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        parts.append(content.get("text", ""))
            answer = " ".join(parts)
        answer = answer.strip() or "I received an empty response."
        gui_log("RAX", answer)
        speak(answer[:2500])
    except Exception as e:
        speak("AI chat failed. " + str(e)[:160])


def build_pro_tab(parent):
    global GUI_PRO_STATUS
    tk.Label(parent, text="RAX PRO COMMAND CENTER", font=("Segoe UI", 24, "bold"), fg="#b66cff", bg="#06090c").pack(anchor="w", pady=(8, 3))
    tk.Label(parent, text="Memory • Tasks • Focus • AI • File tools • Diagnostics", fg="#84939a", bg="#06090c").pack(anchor="w")
    status = _card(parent, "PRO STATUS", "Your advanced local productivity layer.", "#b66cff")
    status.pack(fill="x", pady=15)
    GUI_PRO_STATUS = tk.Label(status, text="Ready", fg="#d7e5ea", bg="#0b1015", font=("Segoe UI", 11, "bold"))
    GUI_PRO_STATUS.pack(anchor="w", padx=12, pady=(0, 12))

    groups = [
        ("🧠 MEMORY", [("Remember", lambda: gui_send_command("remember " + (GUI_COMMAND_ENTRY.get().strip() if GUI_COMMAND_ENTRY else ""))), ("Show memory", lambda: gui_send_command("show memory")), ("Clear memory", lambda: gui_send_command("clear memory"))]),
        ("✅ PRODUCTIVITY", [("List tasks", lambda: gui_send_command("list tasks")), ("Focus 25m", lambda: gui_send_command("start pomodoro 25 minutes")), ("Stop focus", lambda: gui_send_command("stop pomodoro"))]),
        ("🛠 TOOLS", [("System report", lambda: gui_send_command("system report")), ("Internet test", lambda: gui_send_command("test internet")), ("Pro help", show_pro_help)]),
    ]
    for title, buttons in groups:
        card = _card(parent, title, "Quick controls", "#00eaff")
        card.pack(fill="x", pady=6)
        for label, fn in buttons:
            tk.Button(card, text=label, command=fn, bg="#101a20", fg="#d7e5ea", relief="flat", font=("Segoe UI", 9, "bold"), padx=12, pady=8).pack(side="left", padx=4, pady=10)

    ai = _card(parent, "🤖 AI CHAT", "Optional cloud AI. Requires OPENAI_API_KEY in your environment.", "#00ff88")
    ai.pack(fill="x", pady=8)
    entry = tk.Entry(ai, bg="#070b0e", fg="white", insertbackground="white", relief="flat", font=("Segoe UI", 10))
    entry.pack(side="left", fill="x", expand=True, padx=10, pady=12)
    tk.Button(ai, text="ASK RAX AI", command=lambda: ai_chat(entry.get()), bg="#00ff88", fg="#06100b", relief="flat", font=("Segoe UI", 9, "bold"), padx=14, pady=8).pack(side="right", padx=8)


def execute_command_legacy(command):
    global LAST_COMMAND, SLEEP_MODE, LAST_ACTIVITY_TIME

    if not command:
        return True

    command = command.lower().strip()

    # ------------------------------------------------------------
    # WAKE RAX FROM SLEEP
    # ------------------------------------------------------------
    if SLEEP_MODE:
        wake_commands = {
            "ok",
            "okay",
            "ok rax",
            "okay rax",
            "wake up",
            "wake up rax",
            "rax wake up",
            "rax wakeup",
            "i am back",
            "rax i am back",
        }

        if command in wake_commands or "wake up rax" in command:
            SLEEP_MODE = False
            LAST_ACTIVITY_TIME = time.monotonic()
            log_command(command)
            speak("Hi Abhay, how are you?")
            return True

        # Ignore other words while RAX is sleeping.
        return True

    log_command(command)
    LAST_ACTIVITY_TIME = time.monotonic()

    # WhatsApp contact chat / message / call automation
    if parse_whatsapp_command(command):
        return True

    # Shopping websites and product search
    if parse_shopping_command(command):
        return True

    if command in {"repeat last command", "repeat my last command", "do that again"}:
        if not LAST_COMMAND:
            speak("There is no previous command to repeat yet.")
            return True
        previous = LAST_COMMAND
        speak("Repeating your previous command.")
        return execute_command(previous)

    LAST_COMMAND = command

    # AI Programming Mode
    if command in {
        "programming mode", "start programming", "start coding",
        "coding mode", "open programming mode", "code for me"
    }:
        programming_mode()
        return True

    if command in {"open code folder", "open my code folder", "show generated code"}:
        open_code_folder()
        return True

    direct_code = re.match(
        r"^(?:write|create|make|generate)\s+(?:a\s+)?(python|c\+\+|cpp|c|java|javascript|java script|typescript|type script|sql|go|golang|rust|php|ruby|c#|c sharp|kotlin|swift)\s+(?:code|program)?\s*(?:to|for|that)?\s*(.+)$",
        command,
        re.IGNORECASE,
    )
    if direct_code:
        lang = direct_code.group(1).lower().strip()
        aliases = {
            "cpp": "c++", "java script": "javascript",
            "type script": "typescript", "golang": "go", "c sharp": "c#"
        }
        lang = aliases.get(lang, lang)
        programming_task(lang, direct_code.group(2))
        return True

    # Screenshots
    if command in {"take a screenshot", "take screenshot", "screenshot", "capture screen"}:
        take_screenshot()
        return True

    if command in {"open screenshots", "open screenshot folder", "open screenshots folder"}:
        open_screenshots_folder()
        return True

    # Volume
    if command in {"volume up", "increase volume", "raise volume", "turn volume up"}:
        volume_up()
        return True

    if command in {"volume down", "decrease volume", "lower volume", "turn volume down"}:
        volume_down()
        return True

    if command in {"mute", "mute volume", "mute sound", "unmute", "unmute volume", "toggle mute"}:
        toggle_mute()
        return True

    # Brightness
    if "brightness" in command:
        if parse_brightness(command):
            return True
        speak("Tell me a brightness level from 0 to 100 percent. For example, brightness 50 percent.")
        return True

    # Connectivity
    if command in {"check internet", "internet status", "am i online", "is internet working"}:
        internet_status()
        return True

    if command in {"what is my ip", "my ip address", "local ip", "local ip address"}:
        get_local_ip()
        return True

    # Windows tools
    if command in {"open task manager", "task manager"}:
        open_task_manager()
        return True

    if command in {"open settings", "open windows settings", "windows settings"}:
        open_windows_settings()
        return True

    if command in {"open control panel", "control panel"}:
        open_control_panel()
        return True

    # Clipboard
    if command in {"read clipboard", "what is in my clipboard", "show clipboard"}:
        read_clipboard()
        return True

    if command.startswith("copy "):
        copy_to_clipboard(command[5:])
        return True

    # Timers
    if command.startswith("set timer") or command.startswith("set a timer") or command.startswith("timer "):
        if parse_timer(command):
            return True
        speak("I could not understand the timer. Try saying set a timer for 5 minutes.")
        return True

    # Maps
    if command.startswith("find on maps "):
        maps_search(command.replace("find on maps ", "", 1))
        return True

    if command.startswith("open maps for "):
        maps_search(command.replace("open maps for ", "", 1))
        return True

    # Command history
    if command in {"show command history", "show my command history", "command history"}:
        show_command_history()
        return True

    if command in {"clear command history", "delete command history"}:
        clear_command_history()
        return True

    # Windows controls MUST run before local knowledge. Otherwise "lock my PC"
    # can accidentally match the knowledge entry for the letter C.
    if any(x in command for x in ["lock my pc", "lock my computer", "lock the pc", "lock computer"]):
        lock_pc()
        return True

    if any(x in command for x in ["put my pc to sleep", "put computer to sleep", "sleep my pc", "sleep computer"]):
        sleep_pc()
        return True

    if any(x in command for x in ["close this tab", "close current tab", "close the current tab"]):
        close_current_browser_tab()
        return True

    close_patterns = {
        "google chrome": "google chrome", "chrome": "chrome",
        "microsoft edge": "microsoft edge", "edge": "edge",
        "firefox": "firefox", "notepad": "notepad", "calculator": "calculator",
        "spotify": "spotify", "discord": "discord", "whatsapp": "whatsapp",
        "telegram": "telegram", "visual studio code": "visual studio code",
        "vs code": "vscode"
    }
    if command.startswith("close ") or command.startswith("quit "):
        target = re.sub(r"^(?:close|quit)\s+", "", command).strip()
        if target in {"youtube", "youtube app"}:
            speak("YouTube runs inside your browser. Say close current tab, close Chrome, or close Edge.")
            return True
        if target in close_patterns:
            close_app(close_patterns[target])
            return True

    if command in {"close all apps", "close all applications", "close my apps"}:
        speak("I will close the supported apps that are currently running.")
        for key in ["chrome", "edge", "firefox", "notepad", "calculator", "spotify", "discord", "whatsapp", "telegram", "vscode"]:
            close_app(key)
        return True

    # Alarms
    if command in {"show my alarms", "show alarms", "list my alarms", "list alarms"}:
        show_alarms()
        return True

    if command in {"cancel all alarms", "delete all alarms", "remove all alarms"}:
        cancel_all_alarms()
        return True

    cancel_match = re.fullmatch(r"(?:cancel|delete|remove)\s+alarm\s+(\d+)", command)
    if cancel_match:
        cancel_alarm(cancel_match.group(1))
        return True

    if any(x in command for x in ["set alarm", "set an alarm", "wake me at", "wake me up at"]):
        if parse_alarm(command):
            return True
        speak("I could not understand the alarm time. Please say set alarm for 10 PM, or wake me at 6:30 AM.")
        return True

    # Greetings
    if command in {"hello", "hi", "hey"} or any(
        phrase in command for phrase in ["hello rax", "hi rax", "hey rax"]
    ):
        friend_greeting()
        return True

    # Identity
    if "who are you" in command or "what are you" in command:
        speak("I am RAX, your personal desktop voice assistant.")
        return True

    # How are you
    if "how are you" in command:
        speak("I am doing great and ready to help.")
        return True

    # Help
    if command in {"help", "what can you do", "what can you do for me"}:
        speak(
            "I can answer programming questions, open applications and websites, "
            "search Google and YouTube, check weather, tell the time and date, "
            "calculate expressions, check battery, read system information, "
            "save notes, read notes, create reminders, tell jokes, take screenshots, "
            "control volume, check internet and IP address, use timers, read or copy clipboard text, "
            "open Windows tools, search Google Maps, and show command history."
        )
        return True

    # Time
    if (
        "what time is it" in command
        or "current time" in command
        or command == "time"
    ):
        now = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The current time is {now}.")
        return True

    # Date
    if (
        "what is today's date" in command
        or "what is the date" in command
        or command == "date"
    ):
        today = datetime.datetime.now().strftime("%d %B %Y")
        speak(f"Today's date is {today}.")
        return True

    # Weather
    if command.startswith("weather in "):
        get_weather(command.replace("weather in ", "", 1))
        return True

    if command.startswith("what is the weather in "):
        get_weather(command.replace("what is the weather in ", "", 1))
        return True

    if command in {"weather", "check weather"}:
        speak("Please say the city. For example, weather in Kolkata.")
        return True

    # Battery
    if "battery" in command:
        get_battery()
        return True

    # System information
    if (
        "system information" in command
        or "system info" in command
        or "computer information" in command
    ):
        system_info()
        return True

    # Calculator
    calc_match = re.match(
        r"^(?:calculate|what is)\s+(.+)$",
        command
    )

    if calc_match:
        expression = calc_match.group(1).strip()

        # Avoid treating normal knowledge questions as calculations.
        if any(char.isdigit() for char in expression) and any(
            symbol in expression for symbol in "+-*/xX%^"
        ):
            try:
                result = safe_calculate(expression)
                speak(f"The answer is {result}.")
                return True
            except Exception:
                pass

    # Notes
    if command.startswith("take a note "):
        add_note(command.replace("take a note ", "", 1))
        return True

    if command.startswith("note "):
        add_note(command.replace("note ", "", 1))
        return True

    if command in {"read my notes", "read notes", "show my notes"}:
        read_notes()
        return True

    if command in {"clear my notes", "clear notes"}:
        clear_notes()
        return True

    # Reminders
    if command.startswith("remind me in "):
        if parse_reminder(command):
            return True

        speak(
            "I could not understand the reminder. "
            "Try saying, remind me in 10 minutes to study."
        )
        return True

    # Jokes
    if "tell me a joke" in command or command == "joke":
        tell_joke()
        return True

    # Websites
    if "open youtube" in command:
        open_url("YouTube", "https://www.youtube.com")
        return True

    if "open google" in command:
        open_url("Google", "https://www.google.com")
        return True


    if "open linkedin" in command:
        open_url("LinkedIn", "https://www.linkedin.com")
        return True

    if "open instagram" in command:
        open_url("Instagram", "https://www.instagram.com")
        return True

    if "open chatgpt" in command:
        open_url("ChatGPT", "https://chatgpt.com")
        return True

    # Open My PC with voice password
    if command in {
        "open my pc",
        "open my computer",
        "open this pc",
        "open the pc",
        "open computer",
    }:
        open_my_pc_with_password()
        return True

    # Apps
    if "open calculator" in command or command == "calculator":
        open_calculator()
        return True

    if "open notepad" in command or "open notes app" in command:
        open_notepad()
        return True

    if "open camera" in command:
        open_camera()
        return True

    if "open file explorer" in command or "open explorer" in command:
        open_file_explorer()
        return True

    if "open vs code" in command or "open visual studio code" in command:
        open_vscode()
        return True

    if "open downloads" in command:
        open_downloads()
        return True

    if "open documents" in command:
        open_documents()
        return True

    # YouTube search
    if command.startswith("search youtube for "):
        youtube_search(command.replace("search youtube for ", "", 1))
        return True

    if command.startswith("youtube "):
        youtube_search(command.replace("youtube ", "", 1))
        return True

    # Google search
    if command.startswith("search for "):
        google_search(command.replace("search for ", "", 1))
        return True

    if command.startswith("search "):
        google_search(command.replace("search ", "", 1))
        return True

    # Exit
    if command in {"stop", "exit", "quit", "goodbye"} or "shutdown rax" in command:
        speak("Goodbye. RAX is shutting down.")
        return False

    # Local knowledge
    answer = local_answer(command)

    if answer:
        speak(answer)
        return True

    # Wikipedia fallback
    speak("I do not have that in my local knowledge. Let me look for a short answer.")

    answer = wikipedia_answer(command)

    if answer:
        speak(answer)
    else:
        speak("Sorry, I could not find a useful answer.")

    return True


# ============================================================
# MAIN - RAX GUI
# ============================================================


def _normalize_friend_text(text):
    return re.sub(r"[^a-z0-9\s\u0900-\u097F\u0980-\u09FF]", "", text.lower().strip())


def friend_greeting():
    """Start RAX's friendly check-in conversation in the active language."""
    global FRIEND_STAGE, FRIEND_GREETED
    FRIEND_STAGE = "mood"
    FRIEND_GREETED = True
    speak(multilingual_text({
        "english": "Hi Abhay, how are you today? You can tell me anything: good, fine, bad, stressed, or whatever you feel.",
        "hindi": "हाय अभय, आज तुम कैसे हो? जो भी महसूस कर रहे हो, मुझे बता सकते हो। अच्छा, ठीक, बुरा या तनाव में—कुछ भी।",
        "bengali": "হাই অভয়, আজ তুমি কেমন আছো? তুমি যা অনুভব করছো আমাকে বলতে পারো। ভালো, ঠিক, খারাপ বা স্ট্রেস—যাই হোক।",
        "maithili": "हाय अभय, आइ अहाँ कोना छी? जे किछु महसूस करैत छी, हमरा कहि सकैत छी। नीक, ठीक, खराब वा तनाव—जे किछु।",
        "bhojpuri": "हाय अभय, आज तू कइसन बाड़ऽ? जवन महसूस करताड़, हमरा बता सकताड़। बढ़िया, ठीक, खराब चाहे तनाव—कुछुओ।",
        "marathi": "हाय अभय, आज तू कसा आहेस? तुला जे काही वाटतंय ते मला सांगू शकतोस. चांगलं, ठीक, वाईट किंवा तणावात—काहीही.",
        "french": "Salut Abhay, comment vas-tu aujourd'hui ? Tu peux me dire ce que tu ressens : bien, mal, stressé ou autre chose.",
        "gujarati": "હાય અભય, આજે તમે કેમ છો? તમને જે કંઈ લાગે છે તે મને કહી શકો છો—સારું, ઠીક, ખરાબ કે તણાવમાં.",
    }))


def _friend_mood_type(text):
    t = _normalize_friend_text(text)
    negative = {
        "bad", "worse", "worst", "stressful", "stressed", "sad", "upset",
        "angry", "tired", "exhausted", "depressed", "not good", "not fine",
        "terrible", "horrible", "awful", "low", "anxious", "worried", "rough",
        "बुरा", "खराब", "परेशान", "तनाव", "तनाव में", "दुखी", "गुस्सा", "थका",
        "খারাপ", "চাপ", "দুঃখিত", "মন খারাপ",
        "खराब छै", "परेशान छी", "दुःखी",
        "mauvais", "triste", "stressé", "fatigué",
    }
    positive = {
        "good", "fine", "great", "excellent", "awesome", "amazing", "happy",
        "okay", "ok", "well", "pretty good", "very good", "fantastic", "nice",
        "अच्छा", "ठीक", "ठीक हूं", "बहुत अच्छा", "बढ़िया", "खुश",
        "ভালো", "ঠিক", "ভাল", "বেশ ভালো",
        "नीक", "ठीक छी", "अच्छा छी",
        "छान", "चांगला",
        "bien", "bon", "bonne", "heureux", "heureuse",
    }
    if t in negative or any(k in t for k in negative):
        return "negative"
    if t in positive or any(k in t for k in positive):
        return "positive"
    return None


def friend_conversation(command):
    """Handle friend-style check-in while preserving normal RAX commands."""
    global FRIEND_STAGE
    if not FRIEND_CONVERSATION_ENABLED or not FRIEND_GREETED:
        return False

    # Never swallow an obvious desktop/browser command while RAX is in a
    # friendly follow-up stage.
    if re.match(r"^(open|search|type|play|take|lock|sleep|close|set|show|list|add|create|start|stop|find|ask|remember|delete|clear|run|launch|switch|language)\b", command.lower().strip()):
        return False

    mood = _friend_mood_type(command)
    if FRIEND_STAGE == "mood":
        if mood == "negative":
            FRIEND_STAGE = "why"
            speak(multilingual_text({
                "english": "Oh Abhay, I am here with you. What happened? Kya hua? You can tell me.",
                "hindi": "ओह अभय, मैं तुम्हारे साथ हूँ। क्या हुआ? तुम मुझे बता सकते हो।",
                "bengali": "ওহ অভয়, আমি তোমার সাথে আছি। কী হয়েছে? তুমি আমাকে বলতে পারো।",
                "maithili": "ओह अभय, हम अहाँक संग छी। की भेल? अहाँ हमरा कहि सकैत छी।",
                "bhojpuri": "अरे अभय, हम तोहरा साथ बानी। का भइल? तू हमरा बता सकताड़।",
                "marathi": "अरे अभय, मी तुझ्यासोबत आहे. काय झालं? तू मला सांगू शकतोस.",
                "french": "Oh Abhay, je suis là avec toi. Qu'est-ce qui s'est passé ? Tu peux me le dire.",
            }))
            return True
        if mood == "positive":
            FRIEND_STAGE = "day"
            speak(multilingual_text({
                "english": "Good, Abhay. I am glad to hear that. How was your day going? What's happening today?",
                "hindi": "अच्छा अभय। यह सुनकर मुझे अच्छा लगा। तुम्हारा दिन कैसा चल रहा है? आज क्या हो रहा है?",
                "bengali": "ভালো অভয়। শুনে আমার ভালো লাগলো। তোমার দিন কেমন যাচ্ছে? আজ কী হচ্ছে?",
                "maithili": "नीक अभय। ई सुनि हमरा खुशी भेल। अहाँक दिन कोना चलि रहल अछि? आइ की भ' रहल अछि?",
                "bhojpuri": "बढ़िया अभय। ई सुन के अच्छा लागल। तोहार दिन कइसन जा रहल बा? आज का हो रहल बा?",
                "marathi": "छान अभय. हे ऐकून मला आनंद झाला. तुझा दिवस कसा चालला आहे? आज काय चाललंय?",
                "french": "Super Abhay. Je suis content de l'entendre. Comment se passe ta journée ? Qu'est-ce qui se passe aujourd'hui ?",
            }))
            return True
        return False

    if FRIEND_STAGE == "why":
        FRIEND_STAGE = "day"
        speak(multilingual_text({
            "english": "I understand. Thanks for telling me. How is your day going? What's happening today?",
            "hindi": "मैं समझता हूँ। मुझे बताने के लिए धन्यवाद। तुम्हारा दिन कैसा चल रहा है? आज क्या हो रहा है?",
            "bengali": "আমি বুঝতে পারছি। আমাকে বলার জন্য ধন্যবাদ। তোমার দিন কেমন যাচ্ছে? আজ কী হচ্ছে?",
            "maithili": "हम बुझि रहल छी। हमरा बतौने लेल धन्यवाद। अहाँक दिन कोना चलि रहल अछि? आइ की भ' रहल अछि?",
            "bhojpuri": "हम समझतानी। हमरा बतावे खातिर धन्यवाद। तोहार दिन कइसन जा रहल बा? आज का हो रहल बा?",
            "marathi": "मला समजलं. मला सांगितल्याबद्दल धन्यवाद. तुझा दिवस कसा चालला आहे? आज काय चाललंय?",
            "french": "Je comprends. Merci de me l'avoir dit. Comment se passe ta journée ? Qu'est-ce qui se passe aujourd'hui ?",
        }))
        return True

    if FRIEND_STAGE == "day":
        FRIEND_STAGE = "normal"
        speak(multilingual_text({
            "english": "I am listening, Abhay. Tell me anything you want. What would you like me to do next?",
            "hindi": "मैं सुन रहा हूँ अभय। जो मन करे बताओ। अब मैं तुम्हारे लिए क्या करूँ?",
            "bengali": "আমি শুনছি অভয়। যা বলতে চাও বলো। এখন আমি তোমার জন্য কী করব?",
            "maithili": "हम सुनि रहल छी अभय। जे कहय चाही कहू। आब हम अहाँ लेल की करी?",
            "bhojpuri": "हम सुनतानी अभय। जे मन करे बतावा। अब हम का करी?",
            "marathi": "मी ऐकतोय अभय. तुला जे सांगायचं आहे ते सांग. आता मी तुझ्यासाठी काय करू?",
            "french": "Je t'écoute, Abhay. Dis-moi ce que tu veux. Que veux-tu que je fasse maintenant ?",
        }))
        return True

    return False

def _chrome_executable():
    candidates = [
        os.path.join(os.getenv("PROGRAMFILES", ""), "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.getenv("PROGRAMFILES(X86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.getenv("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe"),
    ]
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return None


def _chrome_profiles():
    """Return Chrome profiles using the friendly names stored by Chrome."""
    profiles = []
    if not os.path.isdir(CHROME_USER_DATA_DIR):
        return profiles
    local_state = os.path.join(CHROME_USER_DATA_DIR, "Local State")
    try:
        data = _pro_json(local_state, {}) if os.path.isfile(local_state) else {}
        info = data.get("profile", {}).get("info_cache", {})
        for directory, meta in info.items():
            name = str(meta.get("name") or directory).strip()
            profiles.append((name, directory))
    except Exception as error:
        print("Chrome profile read error:", error)

    if not profiles:
        for directory in ["Default"] + [f"Profile {i}" for i in range(1, 20)]:
            if os.path.isdir(os.path.join(CHROME_USER_DATA_DIR, directory)):
                profiles.append((directory, directory))
    return profiles


def _ask_chrome_profile(action="open Chrome"):
    global CHROME_SELECTED_PROFILE
    profiles = _chrome_profiles()
    if not profiles:
        speak("I could not find any Chrome profiles on this PC. Please open Chrome once and sign in first.")
        return None

    if len(profiles) == 1:
        CHROME_SELECTED_PROFILE = profiles[0][1]
        speak(f"Opening Chrome profile {profiles[0][0]}.")
        return CHROME_SELECTED_PROFILE

    CHROME_PROFILE_CHOICES.clear()
    for i, (name, directory) in enumerate(profiles, 1):
        CHROME_PROFILE_CHOICES[str(i)] = directory
        CHROME_PROFILE_CHOICES[name.lower()] = directory

    names = ", ".join(f"{i}: {name}" for i, (name, _) in enumerate(profiles, 1))
    speak(f"Which Chrome profile should I use, Abhay? {names}. Say the name or say the number.")
    answer = listen()
    if not answer:
        speak("I did not hear the Chrome profile name.")
        return None
    a = answer.lower().strip()
    selected = CHROME_PROFILE_CHOICES.get(a)
    if selected is None:
        for name, directory in profiles:
            if name.lower() in a or a in name.lower():
                selected = directory
                break
    if selected is None and a.isdigit():
        idx = int(a) - 1
        if 0 <= idx < len(profiles):
            selected = profiles[idx][1]
    if selected is None:
        speak("I could not match that Chrome profile. Please say the profile name again.")
        return None
    CHROME_SELECTED_PROFILE = selected
    return selected


def open_chrome_profile(url=None, ask_profile=True, new_tab=False):
    """Open the real installed Google Chrome, optionally with a selected profile."""
    chrome = _chrome_executable()
    if not chrome:
        speak("I could not find Google Chrome. Please make sure Chrome is installed.")
        return False
    profile = CHROME_SELECTED_PROFILE
    if ask_profile or not profile:
        profile = _ask_chrome_profile()
    if not profile:
        return False
    args = [chrome, f"--profile-directory={profile}"]
    if new_tab:
        args.append("--new-tab")
    if url:
        args.append(url)
    try:
        subprocess.Popen(args)
        return True
    except Exception as error:
        print("Chrome open error:", error)
        speak("I could not open Chrome.")
        return False


def chrome_search(query, ask_profile=False):
    query = query.strip()
    if not query:
        speak("What should I search for?")
        return True
    url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
    if open_chrome_profile(url, ask_profile=ask_profile):
        speak(f"Searching Chrome for {query}.")
    return True


def chrome_new_tab_search(query, ask_profile=True):
    query = query.strip()
    if not query:
        speak("What should I search for in the new tab?")
        return True
    url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
    if open_chrome_profile(url, ask_profile=ask_profile, new_tab=True):
        speak(f"Opening a new Chrome tab and searching for {query}.")
    return True


def chrome_type_text(text):
    """Type into the currently focused Chrome page using PyAutoGUI."""
    try:
        import pyautogui
        pyautogui.write(text, interval=0.01)
        speak("Done. I typed that in Chrome.")
    except Exception as error:
        print("Chrome type error:", error)
        speak("I could not type into Chrome. Please click the text box first.")
    return True


def _find_youtube_app_shortcut():
    """Find the installed YouTube desktop/PWA shortcut created by Chrome.

    This is intentionally checked before any normal browser URL is opened.
    A Chrome-installed YouTube PWA shortcut contains the exact Chrome profile
    and app-id chosen when the app was installed, so launching the .lnk opens
    the downloaded YouTube app directly without showing the Chrome profile
    chooser.
    """
    roots = []
    appdata = os.getenv("APPDATA", "")
    programdata = os.getenv("PROGRAMDATA", "")
    userprofile = os.getenv("USERPROFILE", "")
    if appdata:
        roots.append(os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs"))
    if programdata:
        roots.append(os.path.join(programdata, "Microsoft", "Windows", "Start Menu", "Programs"))
    if userprofile:
        roots.append(os.path.join(userprofile, "Desktop"))

    candidates = []
    for root in roots:
        if not os.path.isdir(root):
            continue
        try:
            for current, dirs, files in os.walk(root):
                # Keep this search small and focused on shortcuts.
                dirs[:] = [d for d in dirs if d.lower() not in {"node_modules", ".git"}]
                for filename in files:
                    if not filename.lower().endswith(".lnk"):
                        continue
                    if "youtube" in filename.lower():
                        candidates.append(os.path.join(current, filename))
        except Exception as error:
            print("YouTube shortcut search error:", error)

    # Prefer an exact YouTube shortcut name.
    candidates.sort(key=lambda x: (0 if os.path.splitext(os.path.basename(x))[0].strip().lower() == "youtube" else 1, x.lower()))
    return candidates[0] if candidates else None


def open_installed_youtube():
    """Open the user's installed YouTube PWA/app directly, without asking for Chrome profile."""
    shortcut = _find_youtube_app_shortcut()
    if shortcut:
        try:
            os.startfile(shortcut)
            speak("Opening your installed YouTube app.")
            return True
        except Exception as error:
            print("YouTube app launch error:", error)

    # Fallback: open YouTube directly in the browser, but NEVER ask which
    # Chrome profile. This keeps 'open youtube' a one-step command even if
    # the shortcut was moved/deleted.
    try:
        os.startfile("https://www.youtube.com")
        speak("I could not find the installed YouTube shortcut, so I opened YouTube directly.")
        return True
    except Exception:
        try:
            webbrowser.open("https://www.youtube.com")
            speak("Opening YouTube directly.")
            return True
        except Exception as error:
            print("YouTube fallback error:", error)
            speak("I could not open YouTube.")
            return False


def youtube_command(action, query=None):
    """Control YouTube. 'open youtube' launches the installed YouTube app directly."""
    if action == "open":
        return open_installed_youtube()
    if action == "search":
        query = (query or "").strip()
        if not query:
            speak("What should I search for on YouTube?")
            return True
        # If a Chrome profile has already been selected, reuse it. Otherwise
        # ask once because this is a browser-search command, not the installed app.
        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)
        if open_chrome_profile(url, ask_profile=(CHROME_SELECTED_PROFILE is None)):
            speak(f"Searching YouTube for {query}.")
        return True
    if action == "play":
        query = (query or "").strip()
        if not query:
            speak("What should I play on YouTube?")
            return True
        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)
        if open_chrome_profile(url, ask_profile=(CHROME_SELECTED_PROFILE is None)):
            speak(f"Opening YouTube and searching for {query}.")
        return True
    return False


def multilingual_command_alias(raw):
    """Map common spoken commands in supported languages to RAX's English command syntax."""
    original = str(raw or "").strip()
    c = original.lower().strip()

    # Language selection commands.
    lang_patterns = [
        (r"^(?:language|speak|switch to|use)\s+(.+)$", None),
        (r"^(?:भाषा|भाषा बदलो)\s*(.+)$", None),
        (r"^(?:भाषा|भाषा बदल)\s+(.+)$", None),
        (r"^(?:ভাষা|ভাষা বদলাও)\s+(.+)$", None),
        (r"^(?:भाषा|भाषा बदलू)\s+(.+)$", None),
    ]
    for pattern, _ in lang_patterns:
        m = re.match(pattern, c, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            key = normalize_language_name(candidate)
            if key:
                set_rax_language(key)
                return "__HANDLED__"

    aliases = {
        # Hindi
        "क्रोम खोलो": "open chrome",
        "गूगल क्रोम खोलो": "open chrome",
        "यूट्यूब खोलो": "open youtube",
        "यूट्यूब चलाओ": "open youtube",
        "नया टैब खोलो": "open new tab",
        "चैटजीपीटी खोजो": "search chatgpt",
        "क्रोम में चैटजीपीटी खोजो": "search on chrome chatgpt",
        "क्रोम में खोजो": "search on chrome ",
        "स्क्रीनशॉट लो": "take screenshot",
        "आवाज़ बढ़ाओ": "volume up",
        "आवाज़ कम करो": "volume down",
        # Bengali
        "ক্রোম খোলো": "open chrome",
        "ইউটিউব খোলো": "open youtube",
        "নতুন ট্যাব খোলো": "open new tab",
        "চ্যাটজিপিটি খোঁজো": "search chatgpt",
        "স্ক্রিনশট নাও": "take screenshot",
        # Maithili / Bhojpuri common phrases
        "क्रोम खोलू": "open chrome",
        "यूट्यूब खोलू": "open youtube",
        "क्रोम खोल": "open chrome",
        "यूट्यूब खोल": "open youtube",
        "नया टैब खोल": "open new tab",
        # Marathi
        "क्रोम उघड": "open chrome",
        "क्रोम उघडा": "open chrome",
        "यूट्यूब उघड": "open youtube",
        "यूट्यूब उघडा": "open youtube",
        "नवीन टॅब उघडा": "open new tab",
        # French
        "ouvre chrome": "open chrome",
        "ouvrir chrome": "open chrome",
        "ouvre youtube": "open youtube",
        "ouvrir youtube": "open youtube",
        "nouvel onglet": "open new tab",
        "nouvel onglet et recherche": "open new tab and search ",
    }

    if c in aliases:
        return aliases[c]

    # Natural Hindi/Bengali command prefixes.
    replacements = [
        ("क्रोम में खोजो ", "search on chrome "),
        ("क्रोम पर खोजो ", "search on chrome "),
        ("यूट्यूब पर खोजो ", "search youtube for "),
        ("यूट्यूब पर ", "search youtube for "),
        ("नया टैब और खोजो ", "open new tab and search "),
        ("নতুন ট্যাব এবং খোঁজো ", "open new tab and search "),
        ("ইউটিউবে খোঁজো ", "search youtube for "),
        ("क्रोम में टाइप करो ", "type in chrome "),
        ("ক্রোমে টাইপ করো ", "type in chrome "),
        ("क्रोम में चैटजीपीटी में टाइप करो ", "type in chrome "),
        ("याद रखो ", "remember "),
        ("टास्क जोड़ो ", "add task "),
    ]
    for source, target in replacements:
        if c.startswith(source):
            return target + original[len(source):].strip()

    return original


def execute_command(command):
    """RAX Pro dispatcher. New features run first; all original RAX commands remain available."""
    if not command:
        return True
    raw = command.strip()
    normalized = multilingual_command_alias(raw)
    if normalized == "__HANDLED__":
        return True
    raw = normalized
    c = raw.lower()

    # Friend-style mood-in
    if friend_conversation(raw):
        return True

    # Voice-first Code Lab.
    if c in {"open code lab", "open coding lab", "start code lab", "start coding lab", "coding lab", "code lab"}:
        open_coding_lab(auto_voice=True)
        return True
    if c in {"programming mode", "start programming mode", "start coding"}:
        open_coding_lab(auto_voice=True)
        return True

    # Chrome / YouTube control: always use installed Google Chrome, never Edge.
    if c in {"open chrome", "open google chrome", "start chrome"}:
        open_chrome_profile(ask_profile=True)
        return True
    if c in {"open second chrome", "open another chrome", "open chrome again"}:
        open_chrome_profile(ask_profile=True)
        return True
    if c.startswith("open chrome and search "):
        return chrome_search(raw[len("open chrome and search "):], ask_profile=True)
    if c.startswith("open chrome search "):
        return chrome_search(raw[len("open chrome search "):], ask_profile=True)
    if c.startswith("search on chrome "):
        return chrome_search(raw[len("search on chrome "):], ask_profile=False)
    if c.startswith("search chrome for "):
        return chrome_search(raw[len("search chrome for "):], ask_profile=False)
    if c.startswith("open new tab and search "):
        return chrome_new_tab_search(raw[len("open new tab and search "):], ask_profile=True)
    if c.startswith("new tab and search "):
        return chrome_new_tab_search(raw[len("new tab and search "):], ask_profile=False)
    if c.startswith("type in chrome "):
        return chrome_type_text(raw[len("type in chrome "):])
    if c.startswith("type ") and " in chatgpt" in c:
        text = re.split(r"\s+in chatgpt", raw, maxsplit=1, flags=re.IGNORECASE)[0][5:].strip()
        return chrome_type_text(text)

    if c in {"search chatgpt", "search for chatgpt", "open chatgpt"}:
        return chrome_search("ChatGPT", ask_profile=False)

    if c in {"open new tab", "new chrome tab", "open a new tab"}:
        return open_chrome_profile(new_tab=True, ask_profile=False)

    # YouTube commands through Chrome, not Microsoft Edge.
    if c in {"open youtube", "start youtube", "launch youtube"}:
        return youtube_command("open")
    if c.startswith("search youtube for "):
        return youtube_command("search", raw[len("search youtube for "):])
    if c.startswith("search youtube "):
        return youtube_command("search", raw[len("search youtube "):])
    if c.startswith("play on youtube "):
        return youtube_command("play", raw[len("play on youtube "):])
    if c.startswith("play youtube "):
        return youtube_command("play", raw[len("play youtube "):])

    # Memory
    if c.startswith("remember ") or c.startswith("remember that ") or c.startswith("save this "):
        remember_fact(raw); return True
    if c in {"show memory", "show my memory", "what do you remember", "read memory"}:
        show_memory(); return True
    if c in {"clear memory", "forget everything", "delete memory"}:
        clear_memory(); return True

    # Tasks
    if c.startswith(("add task ", "add todo ", "add to-do ", "create task ", "create todo ", "make a task ")):
        add_todo(raw); return True
    if c in {"list tasks", "show tasks", "show my tasks", "todo list", "to do list", "show todo"}:
        list_todos(); return True
    m = re.fullmatch(r"(?:complete|finish|done)(?: task| todo)?\s*(\d+)", c)
    if m:
        complete_todo(m.group(1)); return True
    if c in {"clear completed tasks", "clear completed todos"}:
        clear_completed_todos(); return True

    # Focus / Pomodoro
    m = re.search(r"(?:start|begin) (?:a )?(?:pomodoro|focus|focus session)(?: for)?\s*(\d+)?\s*(?:minutes?|mins?)?", c)
    if m and ("pomodoro" in c or "focus" in c):
        start_pomodoro(int(m.group(1) or 25)); return True
    if c in {"start pomodoro", "start focus", "focus mode", "start focus mode"}:
        start_pomodoro(25); return True
    if c in {"stop pomodoro", "stop focus", "end focus", "stop focus mode"}:
        stop_pomodoro(); return True
    if c in {"pomodoro status", "focus status", "how much focus time is left"}:
        pomodoro_status(); return True

    # Diagnostics
    if c in {"system report", "full system report", "diagnose my pc", "pc report"}:
        system_report(); return True
    if c in {"test internet", "test my internet", "internet speed test", "network test"}:
        network_test(); return True

    # File tools
    if c.startswith("find file "):
        find_files(raw[10:].strip()); return True
    if c.startswith("search file "):
        find_files(raw[12:].strip()); return True
    if c.startswith("open path "):
        open_path(raw[10:].strip()); return True
    if c.startswith("create project "):
        create_project_folder(raw[15:].strip()); return True

    # AI chat
    if c.startswith("ask ai "):
        ai_chat(raw[7:].strip()); return True
    if c.startswith("ask rax ai "):
        ai_chat(raw[11:].strip()); return True
    if c.startswith("ai chat "):
        ai_chat(raw[8:].strip()); return True

    if c in {"pro help", "rax pro help", "advanced help"}:
        show_pro_help(); return True

    return execute_command_legacy(raw)

def run_rax_voice_loop():
    """Run the continuous RAX microphone loop in a background thread."""
    global SLEEP_MODE, LAST_ACTIVITY_TIME, GUI_RUNNING
    try:
        if not find_microphone():
            gui_log("RAX", "I could not find a microphone. You can still use typed commands.")
            gui_set_state("online")
            return

        LAST_ACTIVITY_TIME = time.monotonic()
        time.sleep(0.8)
        friend_greeting()

        while GUI_RUNNING:
            command = listen(silent=SLEEP_MODE)
            if command is None:
                gui_log("RAX", "I cannot access your microphone.")
                gui_set_state("online")
                break

            if SLEEP_MODE:
                if command:
                    gui_set_state("thinking")
                    try:
                        should_continue = execute_command(command)
                    except Exception as error:
                        print("Voice loop command error:", error)
                        should_continue = True
                    if not should_continue:
                        GUI_RUNNING = False
                        break
                continue

            if not command:
                idle_seconds = time.monotonic() - LAST_ACTIVITY_TIME
                if idle_seconds >= IDLE_TIMEOUT_SECONDS:
                    SLEEP_MODE = True
                    gui_log("RAX", "No command for 20 seconds. Entering sleep mode.")
                    speak("I am going to sleep. When you want me, say okay and I will wake up.")
                continue

            LAST_ACTIVITY_TIME = time.monotonic()
            gui_log("YOU", command)
            gui_set_state("thinking")
            try:
                should_continue = execute_command(command)
            except Exception as error:
                print("Voice loop command error:", error)
                speak("I encountered an error while processing that command.")
                should_continue = True

            if not should_continue:
                GUI_RUNNING = False
                break

    except Exception as error:
        print("RAX voice loop stopped:", error)
        gui_set_state("online")
        gui_log("RAX", "Voice mode stopped. You can continue using typed commands.")


def main():
    global GUI_RUNNING

    GUI_RUNNING = True

    root = build_rax_gui()

    # Start the original microphone/voice loop without freezing Tkinter.
    threading.Thread(
        target=run_rax_voice_loop,
        daemon=True
    ).start()

    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        GUI_RUNNING = False
        print("\nRAX stopped.")
