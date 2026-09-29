Project: RAX
Architecture version: 1.0
Reviewed: 2026-09-29
Platform: Windows desktop
Primary language: Python
Primary GUI: Tkinter
Architecture style: Local-first desktop application with command routing, skill execution, optional cloud services, and local persistence.

1. Architecture Overview

RAX is a Windows-first personal AI desktop assistant.

The supplied implementation is centered around a large Python application module (main_v4.py) that combines:

Tkinter user interface.

Voice input.

Speech recognition.

Text-to-speech.

Natural-language command routing.

Windows automation.

Browser automation.

WhatsApp automation.

Productivity tools.

Memory and task persistence.

Screen capture and OCR.

Agent Mode.

Code generation and remote code execution.

Optional OpenAI-powered chat.

System monitoring.

The current implementation is functionally broad but highly centralized.

The recommended target architecture separates these responsibilities into independent layers so that individual skills can be developed, tested and replaced without modifying the entire application.

2. Current Architecture

The current project is approximately:

                    +----------------------+
                    |      RAX GUI         |
                    |      Tkinter         |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Command Input Layer  |
                    | Voice / Text / GUI   |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Command Dispatcher   |
                    | main_v4.py           |
                    +----------+-----------+
                               |
          +--------------------+---------------------+
          |                    |                     |
          v                    v                     v
   Legacy Commands       RAX Pro Commands       AI / Lookup
          |                    |                     |
          +----------+---------+----------+----------+
                     |                    |
                     v                    v
             Windows/Desktop       External Services
             Automation            APIs / Web
                     |
                     v
             Local Data Files

The main implementation is intentionally monolithic because the project evolved by adding capabilities to the original assistant.

3. Target Architecture

The recommended architecture is:

+----------------------------------------------------------------+
|                         RAX Desktop UI                         |
|                                                                |
| HOME | AGENT | VISION | CODE | SKILLS | SYSTEM | PRO          |
+------------------------------+---------------------------------+
                               |
                               v
+----------------------------------------------------------------+
|                    Application Controller                      |
|                                                                |
| Lifecycle | UI State | Events | Session | Permissions          |
+------------------------------+---------------------------------+
                               |
                               v
+----------------------------------------------------------------+
|                     Interaction Layer                          |
|                                                                |
| Text Input | Voice Input | TTS | GUI Events | Wake Word        |
+------------------------------+---------------------------------+
                               |
                               v
+----------------------------------------------------------------+
|                    Intent / Command Layer                      |
|                                                                |
| Normalize -> Parse -> Resolve -> Authorize -> Execute          |
+------------------------------+---------------------------------+
                               |
              +----------------+----------------+
              |                |                |
              v                v                v
+------------------+  +------------------+  +------------------+
| Local Skills     |  | External Skills  |  | AI Services      |
|                  |  |                  |  |                  |
| Windows          |  | Browser          |  | OpenAI           |
| Files            |  | Weather          |  | Local LLM        |
| Memory           |  | Maps             |  | Judge0           |
| Tasks            |  | Shopping         |  | OCR              |
| Productivity     |  | WhatsApp         |  | Speech Service   |
| System           |  | YouTube          |  |                  |
| Vision           |  |                  |  |                  |
+--------+---------+  +--------+---------+  +--------+---------+
         |                     |                    |
         +---------------------+--------------------+
                               |
                               v
+----------------------------------------------------------------+
|                        Data Layer                              |
|                                                                |
| JSON | TXT | Logs | Screenshots | Generated Code | Config      |
+----------------------------------------------------------------+

4. Architectural Principles

4.1 Local-first

RAX should perform local operations locally.

Examples:

Opening applications.

Reading local system information.

Managing tasks.

Managing memory.

Taking screenshots.

Running local UI operations.

Cloud services should be used only when required.

4.2 Skill-based design

Every capability should eventually become an independent skill.

Example:

BrowserSkill
WhatsAppSkill
SystemSkill
MemorySkill
TaskSkill
VisionSkill
CodeSkill
WeatherSkill

A skill should expose:

name
description
commands
execute()
permissions

4.3 Explicit side effects

RAX should distinguish between:

Read-only

Examples:

CPU status.

Battery status.

Weather.

Current time.

Read memory.

Reversible actions

Examples:

Open an application.

Open a browser tab.

Start a timer.

External side effects

Examples:

Send WhatsApp message.

Schedule an alarm.

Execute remote code.

Destructive/high-impact actions

Examples:

Delete files.

Shut down or sleep the computer.

Future account/payment operations.

The architecture should assign permissions and confirmation requirements accordingly.

4.4 UI must remain responsive

Tkinter uses a main event loop.

Long-running operations must not block it.

Operations such as:

Speech recognition.

Network requests.

OpenAI calls.

Judge0 execution.

OCR.

Browser automation.

should execute outside the UI thread when appropriate.

UI updates should return safely to the Tkinter event loop.

5. Layered Architecture

5.1 Presentation Layer

Responsible for displaying RAX.

Recommended components:

ui/
├── main_window.py
├── home_view.py
├── agent_view.py
├── vision_view.py
├── code_view.py
├── skills_view.py
├── system_view.py
├── pro_view.py
├── dialogs.py
└── components.py

Responsibilities

Render windows.

Render tabs.

Receive user input.

Show assistant responses.

Show execution state.

Display errors.

Display confirmation dialogs.

Must not

The UI should not directly contain:

HTTP logic.

File persistence logic.

Command parsing.

Password handling.

Browser automation.

6. Application Controller

The application controller owns the RAX runtime.

Recommended:

core/
├── app.py
├── state.py
├── events.py
└── lifecycle.py

Responsibilities:

Start application.

Initialize services.

Load configuration.

Load persistent data.

Register skills.

Manage shutdown.

Track current RAX state.

Example states:

IDLE
LISTENING
THINKING
EXECUTING
SPEAKING
AGENT_RUNNING
VISION_PROCESSING
ERROR
STOPPING

7. Interaction Layer

Recommended:

interaction/
├── voice_input.py
├── text_input.py
├── speech.py
├── tts.py
└── wake_word.py

Voice Input

Current implementation uses:

sounddevice

SpeechRecognition

microphone capture

external speech recognition

Flow:

Microphone
    |
    v
sounddevice
    |
    v
Audio Buffer
    |
    v
SpeechRecognition
    |
    v
Text

Text-to-Speech

Current RAX implementation uses Windows speech functionality.

Recommended abstraction:

class TTSProvider:
    def speak(self, text: str) -> None:
        ...

Possible providers:

Windows SAPI
pyttsx3
Cloud TTS
Local TTS

This allows the implementation to change without changing the command engine.

8. Language Layer

The current project supports several configured languages, including:

English

Hindi

Bengali

Maithili

Bhojpuri

Marathi

French

Recommended architecture:

language/
├── languages.py
├── normalizer.py
└── detector.py

Flow:

Recognized Speech
       |
       v
Language Detection
       |
       v
Text Normalization
       |
       v
Canonical Command

Example:

"Open Chrome"
"Chrome kholo"
"क्रोम खोलो"
        |
        v
OPEN_BROWSER

The command engine should operate on normalized intent rather than language-specific phrases wherever possible.

9. Command Processing Architecture

This is the central part of RAX.

Recommended flow:

Raw Input
   |
   v
Normalize
   |
   v
Language Resolution
   |
   v
Intent Detection
   |
   v
Skill Matching
   |
   v
Permission Check
   |
   +------ denied ------> Ask User
   |
   v
Skill Execution
   |
   v
Result Verification
   |
   v
Response Generator
   |
   +------> GUI
   |
   +------> TTS
   |
   +------> Activity Log

10. Command Router

Recommended:

core/
└── router.py

The router should not perform the action itself.

It should resolve:

User command
      |
      v
Intent
      |
      v
Skill

Example:

"open calculator"
      |
      v
intent = OPEN_APPLICATION
target = calculator
      |
      v
SystemSkill

Another example:

"send hello to Rahul on WhatsApp"
      |
      v
intent = SEND_MESSAGE
recipient = Rahul
message = hello
      |
      v
WhatsAppSkill
      |
      v
PermissionManager
      |
      v
Confirmation
      |
      v
Send

11. Skill Architecture

Recommended:

skills/
├── base.py
├── system.py
├── browser.py
├── whatsapp.py
├── files.py
├── memory.py
├── tasks.py
├── productivity.py
├── vision.py
├── coding.py
├── weather.py
├── shopping.py
└── routines.py

Base interface:

class Skill:
    name = ""
    description = ""
    permissions = []

    def can_handle(self, intent):
        ...

    def execute(self, context):
        ...

This provides a common contract for every capability.

12. System Skill

The System Skill owns Windows operations.

Responsibilities:

Open applications
Close applications
Lock PC
Sleep PC
Open Settings
Open Control Panel
Open File Explorer
Task Manager
Clipboard
System telemetry
Network diagnostics
Brightness

Dependencies may include:

subprocess

os

ctypes

psutil

PowerShell

Windows commands

The system skill should isolate Windows-specific implementation details from the rest of RAX.

13. Browser Skill

The Browser Skill owns browser automation.

Current implementation is strongly oriented toward Google Chrome.

Responsibilities:

Open Chrome
Select profile
Open new tab
Search Google
Search YouTube
Open ChatGPT
Open websites
Type into browser
Close browser tab

Recommended adapter:

browser/
├── base.py
├── chrome.py
└── profiles.py

Future browser providers could include:

Chrome
Edge
Firefox

14. WhatsApp Skill

The WhatsApp Skill controls WhatsApp Desktop.

Architecture:

WhatsApp Command
      |
      v
Contact Resolver
      |
      v
WhatsApp UI Controller
      |
      v
Draft Message
      |
      v
Permission Manager
      |
      v
User Confirmation
      |
      v
Send
      |
      v
Result Verification

Important rule:

No confirmation
      ↓
No message send

The skill should not bypass the confirmation mechanism.

Because current automation relies on UI behavior, changes in WhatsApp Desktop may break the automation.

15. Vision Architecture

Recommended:

vision/
├── capture.py
├── ocr.py
├── analyzer.py
└── models.py

Flow:

Desktop
   |
   v
Screenshot Capture
   |
   +------> Save Image
   |
   v
OCR
   |
   v
Extracted Text
   |
   v
Optional AI Analysis

Current technologies include:

pyautogui

Pillow/ImageGrab

pytesseract

Tesseract OCR

OCR should remain optional.

16. Code Lab Architecture

Recommended:

coding/
├── generator.py
├── languages.py
├── executor.py
├── judge0.py
└── storage.py

Flow:

Programming Request
       |
       v
Code Generator
       |
       v
Generated Source
       |
       +------> Save Locally
       |
       v
Language Resolver
       |
       v
Judge0 Adapter
       |
       v
Remote Execution
       |
       v
Execution Result
       |
       +------> Console
       +------> GUI

Security boundary:

User Code
   |
   v
UNTRUSTED
   |
   v
Remote Sandbox / Execution Service

RAX should never assume generated code is safe.

17. AI Service Architecture

AI services should be behind provider interfaces.

Recommended:

services/ai/
├── base.py
├── openai_provider.py
├── local_provider.py
└── manager.py

Interface:

class AIProvider:
    def generate(self, prompt, context=None):
        ...

Provider selection:

AI Manager
   |
   +---- OpenAI
   |
   +---- Local LLM
   |
   +---- Future provider

This prevents the rest of RAX from depending directly on OpenAI-specific APIs.

18. Weather Service

Current weather flow:

Weather Command
      |
      v
Location
      |
      v
wttr.in
      |
      v
Weather Data
      |
      v
Response

Recommended adapter:

services/weather.py

Future weather providers can be added without changing command routing.

19. Storage Architecture

Current persistence uses local JSON/TXT files.

Recommended:

storage/
├── memory.py
├── tasks.py
├── notes.py
├── alarms.py
├── history.py
├── focus.py
├── routines.py
└── repository.py

Data flow:

Skill
  |
  v
Repository
  |
  v
JSON/TXT

The skill should not manually manipulate file formats throughout the codebase.

20. Memory Architecture

Current memory:

rax_memory.json

Recommended model:

{
  "id": "memory-id",
  "text": "remembered information",
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "tags": []
}

Operations:

create
list
search
update
delete
clear
export

21. Task Architecture

Current task storage:

rax_todos.json

Recommended model:

{
  "id": 1,
  "title": "Study Python",
  "created_at": "timestamp",
  "completed": false,
  "completed_at": null
}

Operations:

add
list
complete
reopen
delete
clear_completed

22. Agent Mode Architecture

Agent Mode executes multiple RAX commands sequentially.

Current flow:

Agent Input
     |
     v
Split Into Steps
     |
     v
Step 1 -> Router -> Skill
     |
     v
Step 2 -> Router -> Skill
     |
     v
Step 3 -> Router -> Skill

Recommended target:

User Goal
   |
   v
Planner
   |
   v
Plan
   |
   v
Permission Check
   |
   v
User Preview
   |
   v
Executor
   |
   +---- Step Result
   |
   +---- Retry
   |
   +---- Stop
   |
   v
Final Summary

The planner should not directly execute OS operations.

23. Permission Architecture

Recommended:

security/
├── permissions.py
├── confirmations.py
├── secrets.py
└── audit.py

Example permission levels:

READ_ONLY
LOCAL_ACTION
EXTERNAL_ACTION
SENSITIVE_ACTION
DESTRUCTIVE_ACTION

Example:

Action

Permission

CPU status

READ_ONLY

Weather

READ_ONLY

Open Calculator

LOCAL_ACTION

Screenshot

LOCAL_ACTION

WhatsApp draft

EXTERNAL_ACTION

Send WhatsApp

SENSITIVE_ACTION

Sleep PC

SENSITIVE_ACTION

Delete file

DESTRUCTIVE_ACTION

Execute remote code

EXTERNAL_ACTION

24. Configuration Architecture

Configuration should not be hard-coded inside main_v4.py.

Recommended:

config/
├── settings.py
├── defaults.json
└── loader.py

Environment variables:

OPENAI_API_KEY
RAX_AI_MODEL
RAX_DEFAULT_LANGUAGE
RAX_TTS_RATE
RAX_TTS_VOLUME
JUDGE0_ENDPOINT

Example:

.env
.env.example

.env must never be committed.

25. Threading and Concurrency

Tkinter requires careful thread handling.

Recommended architecture:

Main Tkinter Thread
        |
        +---- UI Events
        |
        +---- Queue
                |
                v
        Worker Thread(s)
                |
        +-------+--------+
        |       |        |
     Voice    Network   OCR
        |       |        |
        +-------+--------+
                |
                v
        Result Queue
                |
                v
        Main Tkinter Thread

The worker should never directly manipulate Tkinter widgets.

26. Event System

A lightweight event system is recommended.

Example events:

COMMAND_RECEIVED
COMMAND_STARTED
COMMAND_COMPLETED
COMMAND_FAILED
VOICE_STARTED
VOICE_STOPPED
TTS_STARTED
TTS_FINISHED
AGENT_STARTED
AGENT_STEP_STARTED
AGENT_STEP_COMPLETED
VISION_CAPTURED
CODE_GENERATED
SYSTEM_STATE_CHANGED

This allows the GUI to react to application state without tightly coupling the UI to every skill.

27. Logging Architecture

Recommended:

logging/
├── logger.py
├── filters.py
└── audit.py

Log categories:

INFO
WARNING
ERROR
AUDIT
DEBUG

Logs should contain:

Timestamp.

Event type.

Skill.

Result.

Error details where safe.

Logs should not contain:

API keys.

Passwords.

Authentication tokens.

Private clipboard contents.

Unnecessary private message content.

28. External Service Boundaries

RAX currently interacts with several external services.

                         Internet
                            |
       +--------------------+-------------------+
       |                    |                   |
       v                    v                   v
Speech Recognition       Weather             OpenAI
       |                    |                   |
       +--------------------+-------------------+
                            |
                            v
                         RAX Core
                            |
                            v
                         Judge0

Each external integration should have:

Timeout.

Exception handling.

Clear unavailable state.

Retry policy where appropriate.

User-visible failure message.

29. Browser / Desktop Automation Boundary

The automation layer should isolate OS-specific operations.

Generic Skill
     |
     v
Automation Interface
     |
     +---- Windows Adapter
     |
     +---- Chrome Adapter
     |
     +---- WhatsApp Adapter

The command router should never directly call:

pyautogui.click(...)
subprocess.Popen(...)

Instead:

system_skill.open_application(...)

This makes the code testable and maintainable.

30. Data Flow — Voice Command

Example:

User speaks:
"Open YouTube"
       |
       v
Microphone
       |
       v
Speech Recognition
       |
       v
"open youtube"
       |
       v
Language Normalizer
       |
       v
Command Router
       |
       v
Browser Skill
       |
       v
Chrome Adapter
       |
       v
YouTube
       |
       v
Result
       |
       +------> GUI
       |
       +------> TTS
       |
       +------> Activity Log

31. Data Flow — WhatsApp Message

User:
"Message Rahul saying hello"
             |
             v
       Command Router
             |
             v
       WhatsApp Skill
             |
             v
       Contact Resolver
             |
             v
        Draft Message
             |
             v
      Permission Manager
             |
             v
       User Confirmation
          /        \
       Cancel      Confirm
         |            |
         v            v
       Stop          Send
                       |
                       v
                 Verify Result
                       |
                       v
                   Response

32. Data Flow — Code Lab

User Problem
     |
     v
Code Lab
     |
     v
AI Provider
     |
     v
Generated Code
     |
     +------> Save to RAX_Code
     |
     v
Language Resolver
     |
     v
Judge0
     |
     v
Compiler / Runtime
     |
     v
Output / Error
     |
     v
Code Lab UI

33. Data Flow — Vision

User presses Capture
          |
          v
Screenshot Engine
          |
          v
Desktop Image
          |
          +------> Save
          |
          v
Optional OCR
          |
          v
Extracted Text
          |
          v
Vision Result

34. Data Flow — Agent Mode

User Goal
   |
   v
Agent Parser
   |
   v
Command List
   |
   v
+------------------+
| Step 1            |
| Router -> Skill   |
+------------------+
        |
        v
+------------------+
| Step 2            |
| Router -> Skill   |
+------------------+
        |
        v
+------------------+
| Step N            |
| Router -> Skill   |
+------------------+
        |
        v
Final Result

Target architecture adds:

Plan
  |
  v
Risk Analysis
  |
  v
Permission
  |
  v
Execution

35. Startup Sequence

Recommended startup sequence:

Application Start
      |
      v
Load Configuration
      |
      v
Initialize Logger
      |
      v
Initialize Storage
      |
      v
Load Memory / Tasks / Settings
      |
      v
Initialize Services
      |
      v
Register Skills
      |
      v
Create Tkinter Window
      |
      v
Start System Monitoring
      |
      v
Ready

The application should fail gracefully if an optional service cannot initialize.

36. Shutdown Sequence

User exits RAX
      |
      v
Stop Voice Listener
      |
      v
Stop Agent
      |
      v
Cancel UI Timers
      |
      v
Flush Logs
      |
      v
Save Required State
      |
      v
Destroy Tkinter Window
      |
      v
Exit

37. Recommended Repository Structure

The supplied archive is currently more monolithic. The recommended production structure is:

RAX/
│
├── app.py
├── README.md
├── PRD.md
├── ARCHITECTURE.md
├── requirements.txt
├── .gitignore
├── .env.example
│
├── assets/
│   └── rax.jpg
│
├── config/
│   ├── defaults.json
│   ├── settings.py
│   └── loader.py
│
├── core/
│   ├── app.py
│   ├── router.py
│   ├── state.py
│   ├── events.py
│   └── permissions.py
│
├── ui/
│   ├── main_window.py
│   ├── home.py
│   ├── agent.py
│   ├── vision.py
│   ├── code.py
│   ├── skills.py
│   ├── system.py
│   ├── pro.py
│   └── dialogs.py
│
├── interaction/
│   ├── voice_input.py
│   ├── speech.py
│   ├── tts.py
│   └── language.py
│
├── skills/
│   ├── base.py
│   ├── system.py
│   ├── browser.py
│   ├── whatsapp.py
│   ├── files.py
│   ├── memory.py
│   ├── tasks.py
│   ├── productivity.py
│   ├── vision.py
│   ├── coding.py
│   ├── weather.py
│   ├── shopping.py
│   └── routines.py
│
├── services/
│   ├── ai/
│   │   ├── base.py
│   │   ├── openai.py
│   │   └── local.py
│   ├── weather.py
│   ├── judge0.py
│   └── ocr.py
│
├── automation/
│   ├── windows.py
│   ├── chrome.py
│   └── whatsapp.py
│
├── storage/
│   ├── repository.py
│   ├── memory.py
│   ├── tasks.py
│   ├── notes.py
│   ├── alarms.py
│   ├── history.py
│   └── routines.py
│
├── data/
│   └── .gitkeep
│
├── screenshots/
│   └── .gitkeep
│
├── generated/
│   └── code/
│
└── tests/
    ├── test_router.py
    ├── test_memory.py
    ├── test_tasks.py
    ├── test_parsers.py
    └── test_permissions.py

38. Dependency Direction

The target architecture should follow this dependency direction:

UI
 |
 v
Core
 |
 v
Skills
 |
 +------> Services
 |
 +------> Automation
 |
 +------> Storage

Lower layers should not import higher layers.

For example:

storage -> should NOT import ui
automation -> should NOT import ui
skills -> should NOT manipulate Tkinter widgets directly

Instead, skills return structured results.

Example:

SkillResult(
    success=True,
    message="VS Code opened",
    data={}
)

The UI then decides how to display it.

39. Structured Result Model

A common result object is recommended:

@dataclass
class SkillResult:
    success: bool
    message: str
    data: dict | None = None
    error: str | None = None
    requires_confirmation: bool = False

Example:

SkillResult
success = True
message = "WhatsApp draft is ready."
requires_confirmation = True

This avoids every skill inventing its own response format.

40. Command Context

Commands should carry structured context.

Example:

CommandContext(
    raw_text="send hello to Rahul",
    normalized_text="send hello to rahul",
    language="en",
    source="voice",
    user_id=None,
    session_id="...",
    metadata={}
)

This makes future logging, analytics and AI integration easier.

41. Security Boundaries

The architecture should treat these as security boundaries:

                TRUSTED
                   |
        +----------+----------+
        |                     |
    Local Core            Local Storage
        |
        v
    Skill Layer
        |
   +----+----+
   |         |
   v         v
Browser    WhatsApp
   |         |
   +----+----+
        |
        v
     External
     Side Effect

Before crossing an external side-effect boundary, RAX should check permissions.

42. Privacy Architecture

The default data policy should be:

Local command
     |
     v
Stay local

Only commands that explicitly require an external service should send data externally.

Examples:

Weather

Location query → weather provider.

Speech

Audio → configured speech-recognition service.

OpenAI

User prompt → OpenAI only when cloud AI is invoked.

Judge0

Code → remote execution service only when the user requests execution.

Vision

Screenshot → remains local unless the user explicitly invokes external vision analysis.

43. Error Isolation

Each skill should isolate failures.

Example:

WhatsApp Failure
      |
      v
WhatsAppSkill catches error
      |
      v
SkillResult(success=False)
      |
      v
Router
      |
      v
GUI + TTS

The entire RAX process should not crash because WhatsApp is unavailable.

44. Testing Architecture

Recommended test layers:

             End-to-End
                 |
        +--------+--------+
        |                 |
   Integration         GUI Tests
        |
        v
      Unit

Unit tests

Test:

Parsers.

Normalizers.

Memory.

Tasks.

Permission logic.

Time parsing.

Integration tests

Test:

Router + skills.

Storage + skills.

AI service adapters.

Weather adapter.

End-to-end

Test:

Voice → command → action.

Agent → multi-step action.

WhatsApp → confirmation → send.

Code Lab → generation → execution.

45. Observability

Recommended metrics:

command_count
command_success_count
command_failure_count
voice_recognition_failures
skill_execution_time
external_api_failures
agent_step_failures
application_crashes

The system should not store sensitive user content merely to produce metrics.

46. Deployment Architecture

RAX is currently designed for a local Windows machine.

Recommended deployment:

Windows PC
   |
   +-- Python Runtime
   |
   +-- RAX Application
   |
   +-- Local Data
   |
   +-- Optional Browser
   |
   +-- Optional WhatsApp Desktop
   |
   +-- Optional Tesseract
   |
   +-- Internet
        |
        +-- Speech Recognition
        +-- Weather
        +-- OpenAI
        +-- Judge0

Future distribution may package RAX as a Windows executable.

Possible future packaging:

RAX.exe
assets/
config/
data/

47. Environment Separation

Recommended environments:

Development
Testing
Production

Configuration should change by environment.

Never use production secrets during automated tests.

48. Source-Control Requirements

The following should generally NOT be committed:

.venv/
venv/
__pycache__/
*.pyc
.env
Chrome profiles
WhatsApp profiles
runtime logs
private screenshots
generated personal data
local credentials

The supplied archive contains a large virtual environment and browser/WhatsApp runtime data. These should be excluded from the source repository.

49. Migration Plan From Current Architecture

The current monolithic application should be migrated gradually.

Step 1

Create:

core/
ui/
skills/
services/
storage/
automation/

Step 2

Move storage functions first.

Step 3

Move system commands.

Step 4

Move browser commands.

Step 5

Move WhatsApp commands.

Step 6

Move productivity commands.

Step 7

Move Vision.

Step 8

Move Code Lab.

Step 9

Move AI services.

Step 10

Reduce main_v4.py to application initialization and compatibility routing.

50. Compatibility Strategy

During migration, the old command system should continue to work.

Recommended:

New Router
    |
    +---- New Skill
    |
    +---- Legacy Adapter
              |
              v
        Existing main_v4

This allows one feature to be migrated at a time without rewriting RAX completely.

51. Architectural Risks

Risk 1 — Monolithic source file

Large centralized code increases:

Regression risk.

Debugging difficulty.

Merge conflicts.

Testing complexity.

Mitigation

Incremental modularization.

Risk 2 — UI automation

Browser and WhatsApp UI changes can break commands.

Mitigation

Use official APIs where available and isolate automation adapters.

Risk 3 — External APIs

Speech, weather, OpenAI and Judge0 may become unavailable.

Mitigation

Timeouts, fallbacks and clear failure states.

Risk 4 — Blocking operations

Voice and network operations can freeze Tkinter.

Mitigation

Worker threads and result queues.

Risk 5 — Secrets

Hard-coded credentials can compromise accounts.

Mitigation

Environment variables and secure OS credential storage.

Risk 6 — Untrusted code

Generated code may be unsafe.

Mitigation

Remote sandboxing, explicit execution, timeouts and data isolation.

52. Architecture Decision Records

ADR-001 — Tkinter

Decision: Continue using Tkinter for the current desktop UI.

Reason: It is already integrated into the supplied implementation and provides a lightweight native Python desktop GUI.

Future: UI technology can be reconsidered after the core architecture is modularized.

ADR-002 — Local-first

Decision: Keep core desktop and productivity features local.

Reason: Reduces network dependency and improves privacy.

ADR-003 — Skill-based command execution

Decision: Route commands to independent skills.

Reason: Allows features to evolve independently and simplifies testing.

ADR-004 — Confirmation for external side effects

Decision: Require explicit confirmation before sensitive actions.

Reason: Prevents accidental external actions such as sending messages.

ADR-005 — Provider abstraction

Decision: Wrap AI, weather, speech and execution services behind adapters.

Reason: Prevents vendor lock-in and allows local alternatives.

53. Reference Runtime Flow

The complete target runtime is:

                  USER
                   |
            +------+------+
            |             |
          VOICE          TEXT
            |             |
            v             v
       Speech Input   Text Input
            |             |
            +------+------+
                   |
                   v
             Normalizer
                   |
                   v
             Intent Router
                   |
                   v
           Permission Check
                   |
          +--------+--------+
          |                 |
       Allowed          Confirmation
          |                 |
          |             User confirms
          |                 |
          +--------+--------+
                   |
                   v
               Skill
                   |
        +----------+----------+
        |          |          |
      Local      External     AI
        |          |          |
        +----------+----------+
                   |
                   v
            Result Verifier
                   |
          +--------+--------+
          |        |        |
         GUI      TTS      Log

54. Final Architecture Direction

RAX should evolve from its current:

Large monolithic Python application

toward:

Modular local-first AI agent

with:

UI
 ↓
Application Controller
 ↓
Interaction Layer
 ↓
Intent Router
 ↓
Permission Manager
 ↓
Skills
 ↓
Service / Automation Adapters
 ↓
Storage

The most important architectural objective is separation of concerns without breaking the existing RAX functionality.

The existing main_v4.py should therefore be treated as the reference implementation during migration, while new modules gradually take ownership of individual capabilities.

55. Architecture Success Criteria

The architecture is successful when:

A new skill can be added without editing the entire application.

UI code does not contain business logic.

Skills can be unit-tested without starting Tkinter.

External services can be replaced through adapters.

Local features work without cloud AI.

Sensitive actions pass through permission checks.

Voice/network operations do not freeze the GUI.

Storage can be changed from JSON/TXT to SQLite without rewriting skills.

Agent Mode can execute existing skills through the same router.

Failures in one skill do not crash RAX.

User data remains local unless external processing is explicitly requested.

The application can eventually be packaged as a standalone Windows application.

56. One-Line Architecture Definition

RAX is a Windows-first, local-first personal AI desktop agent using a Tkinter presentation layer, centralized command routing, modular skills, permission-aware automation, provider-based external services, and local persistent storage.