
import re
import webbrowser

SHASAPP_URL = "https://sha-sapp.netlify.app/"


def handle_shasapp_command(command, speak_fn=None):
    """Open Sha'sapp using RAX voice or text commands."""

    if not command:
        return False

    text = command.lower().strip()
    text = re.sub(r"[.!?,]+", " ", text)
    text = " ".join(text.split())
    text = re.sub(r"^rax\s+", "", text)

    open_commands = {
        "open shasapp",
        "open sha'sapp",
        "open sha sapp",
        "open sha app",
        "launch shasapp",
        "start shasapp",
        "show shasapp",
        "open messaging app",
        "open my messaging app",
    }

    if text in open_commands:
        try:
            webbrowser.open_new_tab(SHASAPP_URL)

            message = "Opening Sha'sapp"
            print("RAX:", message)

            if callable(speak_fn):
                speak_fn(message)

        except Exception as error:
            print("RAX: Sha'sapp opening error:", error)

        return True

    return False
