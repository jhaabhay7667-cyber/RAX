
import re
import webbrowser

from smart_home_bridge import queue_device_command

SMART_HOME_URL = "https://venerable-tapioca-7a11ed.netlify.app/"


def handle_smart_home_command(command, speak_fn=None):

    if not command:
        return False

    text = command.lower().strip()
    text = re.sub(r"[.!?,]+", " ", text)
    text = " ".join(text.split())
    text = re.sub(r"^rax\s+", "", text)

    def respond(message):
        print("RAX:", message)
        if callable(speak_fn):
            speak_fn(message)

    open_commands = {
        "open home",
        "open smart home",
        "open jha smart home",
        "start smart home",
        "launch smart home",
        "show smart home",
        "home dashboard",
        "open my home",
    }

    if text in open_commands:
        webbrowser.open_new_tab(SMART_HOME_URL)
        respond("Opening JHA Smart Home")
        return True

    patterns = [
        (r"(turn on|switch on|lights on|light on)\s*(all\s*)?(lights?|light)?",
         "light", "on"),
        (r"(turn off|switch off|lights off|light off)\s*(all\s*)?(lights?|light)?",
         "light", "off"),
        (r"(turn on|switch on|fan on)\s*(the\s*)?fan?",
         "fan", "on"),
        (r"(turn off|switch off|fan off)\s*(the\s*)?fan?",
         "fan", "off"),
        (r"(open|unlock)\s*(the\s*)?gate",
         "gate", "on"),
        (r"(close|lock)\s*(the\s*)?gate",
         "gate", "off"),
    ]

    for pattern, device, action in patterns:
        if re.search(pattern, text):
            if queue_device_command(device, action):
                labels = {
                    "light": "Lights",
                    "fan": "Fan",
                    "gate": "Gate"
                }

                state = "ON" if action == "on" else "OFF"
                respond(
                    f"{labels[device]} {state} command sent "
                    "to the website simulation"
                )
                return True

    return False
