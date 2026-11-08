
import re
import webbrowser

MEDIBRIDGE_URL = "https://medibrideg.netlify.app/"


def handle_medibridge_command(command, speak_fn=None):
    """Open the MediBridge website using RAX voice or text commands."""

    if not command:
        return False

    text = command.lower().strip()
    text = re.sub(r"[.!?,]+", " ", text)
    text = " ".join(text.split())
    text = re.sub(r"^rax\s+", "", text)

    open_commands = {
        "open medibridge",
        "open medi bridge",
        "launch medibridge",
        "start medibridge",
        "show medibridge",
        "open my medibridge project",
        "open healthcare project",
    }

    if text in open_commands:
        try:
            webbrowser.open_new_tab(MEDIBRIDGE_URL)

            message = "Opening MediBridge website"
            print("RAX:", message)

            if callable(speak_fn):
                speak_fn(message)

        except Exception as error:
            print("RAX: MediBridge opening error:", error)

        return True

    return False
