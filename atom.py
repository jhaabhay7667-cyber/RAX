
import re
import webbrowser

ATOM_URL = "https://silly-cobbler-149c98.netlify.app/"


def handle_atom_command(command, speak_fn=None):
    """Open Atom using RAX voice or text commands."""

    if not command:
        return False

    text = command.lower().strip()
    text = re.sub(r"[.!?,]+", " ", text)
    text = " ".join(text.split())
    text = re.sub(r"^rax\s+", "", text)

    open_commands = {
        "open atom",
        "launch atom",
        "start atom",
        "show atom",
        "open my atom project",
    }

    if text in open_commands:
        try:
            webbrowser.open_new_tab(ATOM_URL)

            message = "Opening Atom project"
            print("RAX:", message)

            if callable(speak_fn):
                speak_fn(message)

        except Exception as error:
            print("RAX: Atom opening error:", error)

        return True

    return False
