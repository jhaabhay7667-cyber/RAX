Document type: Product Requirements Document
Product: RAX
Version: 1.0 — based on the supplied RAX project archive
Platform: Windows desktop
Primary implementation: Python + Tkinter
Product status: Working prototype / advanced personal desktop assistant
Last reviewed: 2026-09-29

1. Product Overview

RAX is a Windows-first personal AI desktop assistant designed to let a user control common computer tasks through natural-language voice commands or typed commands from a desktop GUI.

The current implementation combines:

A graphical desktop command center built with Tkinter.

Microphone input and speech recognition.

Windows text-to-speech.

Multilingual speech-command support.

Local command routing for desktop actions.

Browser and website automation.

WhatsApp Windows desktop automation with message confirmation.

Screen capture and optional OCR.

An AI-powered Code Lab using an external AI API and Judge0-compatible online execution.

Local memory, tasks, focus/Pomodoro, notes, reminders, alarms and command history.

Windows system monitoring and controls.

Optional cloud AI chat.

An extensible command dispatcher that preserves the original RAX command set while adding newer RAX Pro capabilities.

RAX is currently implemented as a local desktop application rather than a web application or cloud-hosted SaaS product.

2. Product Vision

Create a personal desktop assistant that can understand what the user says, decide which supported action is required, execute that action on the user's Windows computer, and report the result through both the GUI and voice.

The intended experience is:

Speak or type → RAX understands → RAX performs a supported action → RAX reports the result.

The long-term direction is to evolve RAX from a command-based assistant into a reliable personal desktop agent while keeping the user in control of sensitive or irreversible actions.

3. Problem Statement

Users repeatedly perform small desktop operations that require multiple clicks or context switching, such as:

Opening applications.

Searching the web.

Opening a specific Chrome profile.

Searching YouTube.

Sending a WhatsApp message.

Checking system status.

Setting reminders and alarms.

Taking screenshots.

Searching files.

Creating project folders.

Generating and testing code.

Checking weather or battery state.

Managing tasks and focus sessions.

RAX aims to reduce this friction by providing one natural-language interface for these operations.

The product should also support a conversational interaction model so the assistant feels useful beyond isolated commands.

4. Goals

4.1 Primary goals

Provide reliable voice and typed command interaction.

Execute common Windows desktop actions from natural-language commands.

Provide a clear visual command-center interface.

Support multilingual speech commands.

Provide safe confirmation for sensitive communication actions such as WhatsApp message sending.

Provide a local productivity layer for memory, tasks and focus sessions.

Provide an integrated programming workflow for generating and executing code.

Provide screen capture and optional OCR capabilities.

Provide useful browser, search, weather and system integrations.

Keep the core assistant functional even when optional cloud AI features are unavailable.

4.2 Secondary goals

Make commands easy to discover.

Preserve command history for troubleshooting.

Provide visible system status.

Allow repeatable multi-step workflows through Agent Mode.

Keep user data primarily on the local computer.

Make the architecture extensible for future skills and routines.

5. Non-Goals

The current product is not intended to be:

A fully autonomous unrestricted computer-control agent.

A replacement for a professional cybersecurity product.

A cloud multi-user SaaS platform.

A guaranteed human-level conversational AI.

A medical, legal or financial decision-making system.

A fully offline speech-recognition platform.

A universal automation engine capable of safely operating every Windows application.

A production-grade enterprise device-management system.

6. Target User

Primary user

A technically interested individual who wants a personal AI assistant for Windows.

Typical use cases include:

College/student productivity.

Programming and development.

Web research.

Desktop automation.

Personal reminders.

Communication assistance.

Quick system checks.

Repetitive desktop workflows.

User characteristics

The user is expected to be comfortable installing Python packages, configuring Windows software, and granting local application permissions when required.

7. User Experience Principles

7.1 Voice first, but never voice only

Voice is a primary interaction method, but every important feature should remain accessible through typed commands or GUI controls where practical.

7.2 Visible state

RAX should clearly communicate whether it is:

Online.

Listening.

Thinking.

Speaking.

Running an agent.

Using vision.

7.3 User confirmation for consequential actions

Actions that can send messages, delete data, or cause irreversible changes should require explicit confirmation.

7.4 Local-first behavior

Local capabilities should work without a cloud AI API whenever possible.

7.5 Graceful failure

If a dependency, microphone, browser, OCR engine, network service, or optional AI API is unavailable, RAX should explain the limitation instead of silently claiming success.

8. Core Functional Requirements

FR-01 — Desktop GUI

RAX shall provide a desktop GUI built with Tkinter.

The current interface includes these main tabs:

HOME

AGENT

VISION

CODE

SKILLS

SYSTEM

PRO

HOME

The Home screen provides:

RAX identity and image.

Animated assistant visual.

Online/listening/thinking/speaking state.

Voice waveform.

Conversation console.

Text command entry.

Listen control.

Command execution.

SYSTEM

The System tab provides live telemetry for:

CPU.

RAM.

Battery.

Disk.

It also exposes common Windows actions.

PRO

The Pro tab exposes:

Memory.

Productivity/tasks.

Focus/Pomodoro.

Diagnostics.

File tools.

Optional AI chat.

FR-02 — Voice Input

RAX shall capture microphone audio and convert speech to text.

Current implementation:

Uses sounddevice for recording.

Uses SpeechRecognition for recognition.

Uses Google's speech-recognition service through the SpeechRecognition package.

Uses a configurable recognition language.

Supports selected-language and auto-language modes.

The current audio capture is configured around a 16 kHz microphone stream with a short listening window.

Failure behavior

RAX should report:

Microphone unavailable.

Speech recognition unavailable.

Speech not understood.

It should not treat an unrecognized command as a successful action.

FR-03 — Text-to-Speech

RAX shall provide spoken responses.

The main application uses Windows speech functionality through its local TTS implementation.

A separate test_voice.py utility in the supplied project tests pyttsx3/SAPI5 voice output.

The product should eventually standardize on one clearly documented TTS implementation rather than maintaining separate experimental voice paths.

FR-04 — Multilingual Support

The current project defines speech recognition support for:

English

Hindi

Bengali

Maithili

Bhojpuri

Marathi

French

The product shall allow the user to change the active language through commands such as:

language Hindi

Equivalent localized language commands.

An auto-language mode may try configured recognition languages and retain the detected language for subsequent turns.

Future requirement

Language support should be moved into a configuration file rather than being hard-coded into the main source file.

9. Command and Automation Requirements

FR-05 — Command Dispatcher

RAX shall route a natural-language command to the appropriate skill.

The current architecture uses:

Multilingual command normalization.

Friend/conversation handling.

RAX Pro command routing.

Legacy command routing.

Local knowledge and external lookup fallback.

The dispatcher must return a success/continue signal so RAX can determine whether to remain active or shut down.

FR-06 — Desktop Application Control

RAX shall support opening common Windows applications, including:

Calculator.

Notepad.

Camera.

File Explorer.

Visual Studio Code.

Downloads.

Documents.

Task Manager.

Windows Settings.

Control Panel.

RAX can also close supported applications.

Supported close targets include common applications such as Chrome, Edge, Firefox, Notepad, Calculator, Spotify, Discord, WhatsApp, Telegram and VS Code, subject to Windows installation and permissions.

FR-07 — Windows Power Controls

RAX shall support desktop controls including:

Lock PC.

Put PC to sleep.

Close current browser tab.

Close supported applications.

Open My PC.

Opening My PC currently uses a voice-password protection mechanism.

Security requirement

The current password mechanism must not remain as a hard-coded secret in production.

Future implementation should:

Move secrets out of source code.

Store credentials securely.

Never log passwords.

Rate-limit failed attempts.

Provide a secure reset mechanism.

Avoid speaking secrets aloud.

FR-08 — Browser Control

RAX shall support browser actions.

The current implementation is specifically designed around installed Google Chrome.

Capabilities include:

Open Chrome.

Select a Chrome profile.

Open a new tab.

Search Google.

Type text into Chrome.

Open/search ChatGPT.

Search YouTube.

Play/search YouTube content.

Chrome profile selection reads profile information from the local Chrome profile configuration.

Future requirement

Browser automation should be isolated behind a browser adapter so Chrome-specific behavior does not dominate the core command engine.

FR-09 — Website Shortcuts

RAX shall support opening commonly used websites including:

YouTube.

Google.

LinkedIn.

Instagram.

ChatGPT.

FR-10 — Web Search and Knowledge

RAX shall support:

Google search.

Wikipedia-style short knowledge lookup.

Weather lookup.

Google Maps search.

Weather is currently retrieved through wttr.in.

The assistant must clearly distinguish between:

Local knowledge.

External web information.

AI-generated information.

10. Communication Automation

FR-11 — WhatsApp Desktop Integration

RAX shall interact with the installed Windows WhatsApp application.

Current capabilities include:

Open WhatsApp.

Find/open a contact chat.

Type a message.

Replace/edit a drafted message.

Confirm before sending.

Cancel a message.

Attempt WhatsApp calls.

Close WhatsApp.

Mandatory confirmation

The message flow is intentionally confirmation-based:

User selects/open a contact.

RAX asks for the message.

RAX types the message.

RAX reads/confirms the drafted message.

User says an affirmative confirmation.

RAX sends it.

If the user says cancel, the draft is cleared.

If the user requests a change, RAX asks for the replacement text and repeats confirmation.

Reliability requirement

UI-coordinate automation is inherently fragile. A future version should prefer official APIs or accessibility/UI automation interfaces where available.

11. Productivity Requirements

FR-12 — Notes

RAX shall support:

Add a note.

Read notes.

Clear notes.

Notes are intended to be stored locally.

The current code defines a notes file path, although the supplied archive does not contain an initial notes file.

FR-13 — Reminders

RAX shall support natural-language reminders such as:

remind me in 10 minutes to study

Supported units include:

Seconds.

Minutes.

Hours.

The reminder should result in a local callback/notification behavior.

FR-14 — Timers

RAX shall support timers using seconds, minutes and hours.

The timer may contain a completion message.

FR-15 — Alarms

RAX shall support scheduled alarms.

The current Windows implementation uses:

PowerShell.

Windows Task Scheduler.

Generated PowerShell alarm scripts.

A local JSON alarm record.

Alarm behavior must be clearly reported when scheduling succeeds or fails.

FR-16 — Tasks / To-Do

RAX Pro shall support:

Add task.

List pending tasks.

Complete task by number.

Clear completed tasks.

Task records include creation timestamps and completion state.

FR-17 — Memory

RAX Pro shall support:

Remember a fact.

Show recent memory.

Clear memory.

Memory is currently stored in a local JSON file.

The current implementation limits saved memory to the latest 200 entries.

Privacy requirement

Memory must be user-controlled and locally inspectable.

Future versions should provide:

Individual memory deletion.

Search.

Editing.

Export/import.

Clear-all confirmation.

FR-18 — Pomodoro / Focus Mode

RAX Pro shall support configurable focus sessions.

Default behavior:

25-minute focus session.

Start.

Stop.

Status.

Completion announcement.

The implementation uses Tkinter callbacks or a background timer when appropriate.

12. System and Utility Requirements

FR-19 — System Monitoring

RAX shall expose:

CPU usage.

RAM usage.

Disk usage.

Battery level.

Network transfer information in the Pro system report.

The GUI shall refresh system telemetry periodically.

FR-20 — Network Diagnostics

RAX shall support:

Internet connectivity test.

Local IP lookup.

Network test/report.

Connectivity testing currently uses a network socket to determine whether the internet is reachable.

FR-21 — Clipboard

RAX shall support:

Read clipboard text.

Copy text to clipboard.

Clipboard content should be handled carefully because it may contain passwords, tokens or private information.

Future versions should avoid unnecessary logging of clipboard content.

FR-22 — Screenshot Capture

RAX shall support desktop screenshot capture.

Screenshots are stored in the RAX_Screenshots directory with timestamp-based names.

The current project already contains historical screenshots.

13. Computer Vision Requirements

FR-23 — Vision Capture

The Vision tab shall allow the user to:

Capture the current screen.

Save the image locally.

Preview the screenshot.

Optionally extract visible text using OCR.

The current implementation attempts to use:

pyautogui for screenshot capture.

Pillow's ImageGrab as a fallback.

pytesseract for OCR when installed.

Current limitation

OCR is optional and requires Tesseract OCR to be installed separately on Windows.

Future direction

Vision should evolve from OCR-only screen inspection into structured screen understanding, with explicit user control over what information may be interpreted or acted upon.

14. RAX Agent Mode

FR-24 — Multi-Step Agent Workflows

Agent Mode shall allow the user to execute a sequence of existing RAX commands.

Example workflow:

open vscode
open chrome
open youtube

The current implementation:

Accepts one command per line.

Executes commands sequentially.

Shows step progress.

Logs each step.

Speaks completion.

Stops reporting success if an execution error occurs.

Safety requirement

Agent Mode should only execute commands already supported by RAX unless the user explicitly enables an advanced automation capability.

Future versions should support:

Preview before execution.

Step-by-step confirmation for sensitive commands.

Cancel/stop button.

Per-step result status.

Retry.

Undo where technically possible.

15. RAX Code Lab

FR-25 — AI Programming Assistant

RAX Code Lab shall allow the user to describe a programming problem and request generated code.

The current Code Lab supports a broad language list including:

Python

JavaScript

Java

C

C++

TypeScript

SQL

Go

Rust

PHP

Ruby

C#

Kotlin

Swift

The implementation can dynamically query a Judge0-compatible compiler endpoint to identify available languages.

FR-26 — Code Generation

Code generation currently uses an optional OpenAI API configuration.

The application reads:

OPENAI_API_KEY from an environment variable.

RAX_AI_MODEL from an environment variable, with a configured default.

The product must never require an API key to use basic local desktop functions.

FR-27 — Online Code Execution

Generated code may be sent to a Judge0-compatible online execution service.

The current configuration contains multiple Judge0-compatible endpoint options.

The workflow is:

Receive programming request.

Generate code.

Determine compiler/language.

Send code to online compiler.

Receive execution result.

Show output/error.

Save generated code if execution cannot be completed.

Security requirement

Generated code must be treated as untrusted input.

Future versions should:

Clearly identify remote execution.

Avoid sending secrets or private files.

Sanitize inputs.

Provide an execution timeout.

Show compiler/runtime errors.

Provide a local-only mode where practical.

16. Shopping Search

FR-28 — Shopping Search

RAX supports product searches on configured shopping sites.

Current supported sites include:

Amazon India.

Flipkart.

Meesho.

Shopsy.

The current feature opens search URLs in the browser rather than directly purchasing products.

Product safety requirement

RAX must not autonomously place orders or make payments without explicit user interaction and confirmation.

17. Conversational Personality

FR-29 — Friendly Conversation

RAX includes a friend-style check-in flow.

The current conversation can:

Greet the user.

Ask how the user is feeling.

Recognize broad positive/negative mood phrases.

Ask a follow-up question.

Return to normal command handling.

The feature should remain optional and should not prevent ordinary commands from being executed.

Future requirement

The assistant should avoid presenting itself as a human or making unsupported claims about emotional understanding.

18. AI Chat

FR-30 — Optional Cloud AI Chat

RAX Pro includes optional AI chat.

The current implementation:

Uses the OpenAI Responses API.

Reads the API key from an environment variable.

Sends a system instruction describing RAX as a concise desktop assistant.

Displays the response in the RAX console.

Speaks the response.

If no API key is configured, RAX should explain that cloud AI chat is not configured.

19. Data and Storage

The current project uses local files for persistent data.

Expected data files include:

File

Purpose

rax_memory.json

Saved user memory

rax_todos.json

Tasks/to-dos

rax_pro_activity.log

Pro feature activity log

rax_command_history.txt

Command history

rax_notes.txt

Notes

rax_alarms.json

Scheduled alarm metadata

rax_focus.json

Focus-related persistent data

rax_skills.json

Skill definitions

rax_routines.json

User routines

RAX_Screenshots/

Captured screenshots

RAX_Code/

Generated code

Some expected runtime files are created only after a feature is used and therefore are not present in the supplied archive.

20. Proposed High-Level Architecture

+------------------------------------------------------+
|                 RAX Desktop GUI                     |
|  HOME | AGENT | VISION | CODE | SKILLS | SYSTEM | PRO |
+-------------------------+----------------------------+
                          |
                          v
+------------------------------------------------------+
|              Interaction Layer                      |
|  Voice Input | Typed Input | TTS | GUI Events      |
+-------------------------+----------------------------+
                          |
                          v
+------------------------------------------------------+
|              Command / Intent Router                |
|  Language Normalizer -> Pro Router -> Legacy Router |
+-------------------------+----------------------------+
                          |
          +---------------+------------------+
          |               |                  |
          v               v                  v
   Local Skills      External Skills     AI Services
   Windows           Web/Search          OpenAI
   Files             Weather             Judge0
   Memory            Maps                Speech API
   Tasks             YouTube
   WhatsApp          Shopping
          |
          v
+------------------------------------------------------+
|                Local Data Layer                     |
| JSON | TXT | Logs | Screenshots | Generated Code    |
+------------------------------------------------------+

21. Main Components

21.1 GUI Layer

Implemented using Tkinter and Pillow.

Responsibilities:

Rendering.

Tabs.

Status indicators.

Chat console.

Input controls.

Visual state animation.

Feature dialogs.

21.2 Voice Layer

Responsibilities:

Microphone capture.

Speech recognition.

Language selection.

Speech output.

21.3 Command Layer

Responsibilities:

Normalize input.

Detect command intent.

Route to skill.

Handle fallback behavior.

Return continue/stop status.

21.4 Skill Layer

Each desktop capability should eventually be isolated into a separate module.

Examples:

Browser skill.

WhatsApp skill.

System skill.

File skill.

Productivity skill.

Code skill.

Vision skill.

21.5 Persistence Layer

Responsible for:

JSON storage.

Text storage.

Activity logging.

Runtime files.

21.6 External Service Layer

Responsible for:

Speech recognition service.

Weather service.

OpenAI API.

Judge0-compatible code execution.

22. Current Project Structure

The important application-level files identified in the supplied archive are approximately:

RAX/
├── main_v4.py
├── test_voice.py
├── rax.jpg
├── rax_memory.json
├── rax_todos.json
├── rax_command_history.txt
├── rax_pro_activity.log
└── RAX_Screenshots/

The archive also contains a large Python virtual environment and a Chromium/WhatsApp profile directory. These are runtime/environment artifacts and should not be treated as core product source code.

Recommended future structure

RAX/
├── app.py
├── requirements.txt
├── .env.example
├── README.md
├── PRD.md
├── config/
│   └── settings.json
├── core/
│   ├── router.py
│   ├── state.py
│   └── events.py
├── ui/
│   ├── main_window.py
│   ├── home.py
│   └── dialogs.py
├── skills/
│   ├── browser.py
│   ├── system.py
│   ├── files.py
│   ├── whatsapp.py
│   ├── productivity.py
│   ├── vision.py
│   └── coding.py
├── services/
│   ├── speech.py
│   ├── tts.py
│   ├── weather.py
│   ├── openai.py
│   └── judge0.py
├── storage/
│   ├── memory.py
│   ├── tasks.py
│   └── history.py
├── data/
├── assets/
└── tests/

23. Dependencies

The supplied code imports or conditionally uses libraries including:

Core/GUI

Python 3.x

Tkinter

Pillow

Voice

SpeechRecognition

NumPy

sounddevice

Networking/API

requests

Optional system automation

psutil

pyautogui

Optional OCR

pytesseract

Tesseract OCR installed separately

Optional voice test

pyttsx3

Windows integration

PowerShell

Windows Task Scheduler

Windows application protocols

Windows APIs through ctypes

A formal requirements.txt should be added to the project because the supplied archive does not contain one.

24. Configuration Requirements

The following configuration should be externalized:

ASSISTANT_NAME
DEFAULT_LANGUAGE
SUPPORTED_LANGUAGES
VOICE_RATE
VOICE_VOLUME
AI_MODEL
OPENAI_API_KEY
JUDGE0_ENDPOINTS
IDLE_TIMEOUT
FEATURE_FLAGS

Secrets must be provided through environment variables or secure OS storage.

A .env.example should document required configuration without containing real credentials.

25. Security Requirements

SEC-01 — Secrets

No passwords, API keys, tokens or authentication secrets may be hard-coded in source code.

SEC-02 — API keys

OpenAI keys must remain in environment variables or secure credential storage.

SEC-03 — Sensitive actions

Messaging, deletion, account actions and external side effects require confirmation.

SEC-04 — Local privacy

RAX should not upload local files, screenshots, clipboard data or memory unless the user explicitly invokes a feature that requires external processing.

SEC-05 — Logging

Logs must not contain:

API keys.

Passwords.

Authentication tokens.

Unnecessary clipboard contents.

Private message contents unless explicitly required.

SEC-06 — External execution

Remote code execution must clearly indicate that source code is leaving the local computer.

SEC-07 — WhatsApp automation

RAX must not send a message without explicit confirmation.

26. Reliability Requirements

RAX should:

Continue running when optional features fail.

Prevent one skill failure from crashing the GUI.

Report errors clearly.

Avoid claiming an action succeeded when the OS/browser/application did not confirm it.

Keep voice processing off the Tkinter UI thread when it may block.

Avoid blocking the GUI during network requests.

Handle unavailable microphones gracefully.

Handle missing external applications gracefully.

27. Performance Requirements

Target behavior:

GUI should remain responsive during voice recognition.

Long-running network operations should run in worker threads.

UI updates should return to the Tkinter event loop.

System dashboard updates should be periodic rather than continuous.

Screenshots should not block the main window.

Code execution should have explicit timeouts.

28. Accessibility Requirements

Future releases should support:

Keyboard-only operation.

Clear focus indicators.

Adjustable text size.

High-contrast mode.

Configurable speech rate.

Configurable microphone.

Visible status messages in addition to voice feedback.

29. Error Handling Requirements

Every external operation should follow a common pattern:

Validate input
      ↓
Execute operation
      ↓
Verify result where possible
      ↓
Update GUI
      ↓
Speak concise result
      ↓
Log safe diagnostic information

Example:

For opening VS Code:

User: "Open VS Code"
        ↓
Router detects application command
        ↓
RAX starts code executable
        ↓
If process launch succeeds:
    "VS Code is open."
Else:
    "I could not open VS Code."

30. Acceptance Criteria

Voice

RAX launches without crashing.

Microphone can be selected/detected.

English commands are recognized.

Supported multilingual commands are recognized where the speech service supports them.

Recognition failures are communicated clearly.

GUI

All seven primary tabs open.

Home chat accepts typed commands.

Listen control works.

Status indicator changes correctly.

RAX image loads when available.

GUI remains responsive while voice/network operations execute.

Desktop automation

Calculator opens.

Notepad opens.

File Explorer opens.

VS Code launch is attempted correctly.

Supported apps can be closed.

PC lock/sleep commands work where Windows permits them.

Browser

Chrome opens.

Chrome profile selection works.

Google search works.

YouTube search works.

New-tab search works.

WhatsApp

WhatsApp opens.

Contact chat can be selected.

Draft message can be typed.

User must confirm before send.

Cancel clears the draft.

Edit/replacement flow works.

Productivity

Notes can be added/read/cleared.

Reminders can be scheduled.

Timers work.

Alarms use Windows scheduling.

Tasks can be added/completed/cleared.

Memory can be added/viewed/cleared.

Pomodoro can start/stop/status-check.

Vision

Screenshot capture works.

Screenshot is saved locally.

Preview opens.

OCR works when Tesseract is installed.

Missing OCR dependency does not crash RAX.

Code Lab

User can choose a language.

User can provide a coding request.

AI code generation works when API configuration is valid.

Online execution works when Judge0 is available.

Generated code can be saved.

Compiler errors are shown clearly.

AI Chat

Missing API key produces a clear configuration message.

Valid API configuration produces an AI response.

API errors do not crash the application.

31. Testing Strategy

Unit tests

Test:

Language normalization.

Command parsing.

Calculator safety.

Reminder parsing.

Alarm parsing.

Timer parsing.

Brightness parsing.

Shopping command parsing.

WhatsApp command parsing.

Task operations.

Memory operations.

Integration tests

Test:

GUI + command dispatcher.

Voice + command dispatcher.

Browser automation.

WhatsApp automation.

Windows scheduler.

OpenAI API.

Judge0 execution.

OCR.

Manual acceptance tests

A Windows test machine should verify:

Start RAX.

Test typed command.

Test microphone.

Test application launch.

Test Chrome.

Test YouTube.

Test WhatsApp confirmation.

Test screenshot.

Test Code Lab.

Test system dashboard.

Test memory/tasks.

Test sleep/wake behavior.

32. Current Limitations Identified From the Supplied Implementation

The application is concentrated in a very large main_v4.py file, making maintenance difficult.

A formal dependency file is missing.

Several runtime files are created dynamically and are not included in the source archive.

Some functionality depends on Windows-specific commands and applications.

Speech recognition depends on an external recognition service.

Weather depends on an external HTTP service.

AI chat and AI code generation depend on OpenAI API configuration.

Code execution depends on an external Judge0-compatible service.

OCR is optional and requires additional software.

WhatsApp automation relies on Windows UI automation and may be sensitive to application UI changes.

Browser automation is strongly tied to Google Chrome.

Some features use hard-coded configuration that should be externalized.

The current command parser is primarily rule-based rather than a generalized intent-classification system.

Agent Mode executes command sequences but does not yet provide robust transaction rollback.

The current memory model is append-oriented rather than a full searchable/editable knowledge store.

Some GUI and voice flows rely on global state.

The archive contains a large virtual environment and browser profile that should not be committed to source control.

33. Recommended Product Roadmap

Phase 1 — Stabilization

Split main_v4.py into modules.

Add requirements.txt.

Add .gitignore.

Add .env.example.

Centralize configuration.

Add structured logging.

Add unit tests for all command parsers.

Remove secrets from source.

Improve error handling.

Phase 2 — Skill Architecture

Create a plugin-like skill interface:

Skill
├── name
├── description
├── commands
├── execute()
└── permissions

Skills should be independently testable.

Phase 3 — Better Agent Mode

Add:

Plan preview.

Permission prompts.

Step status.

Stop button.

Retry.

Confirmation for sensitive steps.

Result verification.

Phase 4 — Improved AI

Add:

Configurable AI providers.

Local-model support.

Conversation context.

Tool calling.

Structured intents.

Better command disambiguation.

Phase 5 — Advanced Vision

Add:

Screen element detection.

OCR + layout understanding.

User-approved UI actions.

Screenshot question answering.

Visual workflow assistance.

Phase 6 — Personalization

Add:

Editable memory.

Custom routines.

User-created skills.

Preference profiles.

Import/export.

34. Future Product Requirements

The following are recommended future features, not claims that they are currently implemented.

FR-FUTURE-01 — Wake Word

Support a configurable wake phrase such as:

Hey RAX
Okay RAX

FR-FUTURE-02 — Local AI

Support a local LLM backend so basic conversational and command interpretation can work without sending prompts to a cloud service.

FR-FUTURE-03 — Skill Marketplace/Registry

Allow optional skill packages to be installed and removed independently.

FR-FUTURE-04 — Routine Builder

Allow users to visually create:

Routine:
"Start my coding workspace"

1. Open VS Code
2. Open Chrome
3. Open project folder
4. Start focus session

FR-FUTURE-05 — Permission Center

Show permissions for:

Microphone.

Screen capture.

Browser control.

Messaging.

External AI.

Remote code execution.

File access.

FR-FUTURE-06 — Activity Center

Provide a searchable history showing:

User command.

Skill invoked.

Action result.

Timestamp.

External service used.

Sensitive information must be redacted.

35. Success Metrics

The product should measure reliability rather than simply the number of features.

Recommended metrics:

Command success rate

Percentage of recognized commands that produce the intended result.

False action rate

Percentage of commands where RAX performs the wrong action.

This should be minimized, especially for messaging and destructive actions.

Voice recognition success

Percentage of clearly spoken supported commands correctly transcribed.

Automation completion rate

Percentage of multi-step workflows completed without interruption.

Crash-free sessions

Percentage of application sessions without an unhandled application crash.

User correction rate

Percentage of actions requiring the user to correct RAX.

External dependency availability

Track failures separately for:

Speech service.

Weather service.

OpenAI.

Judge0.

OCR.

36. Product Definition of Done

A production-ready RAX release should not be considered complete until:

Core commands are modularized.

Sensitive secrets are externalized.

A reproducible installation process exists.

Dependencies are documented.

Automated tests cover command parsing.

GUI responsiveness is verified.

Sensitive actions require confirmation.

External API failures are handled.

Logs are privacy-conscious.

Agent Mode has stop/confirmation controls.

User data can be inspected and deleted.

The README contains setup and troubleshooting instructions.

37. Final Product Summary

RAX is currently an advanced Windows personal desktop assistant implemented primarily in Python.

Its strongest current product areas are:

Desktop GUI command center.

Voice and typed interaction.

Multilingual recognition.

Windows application control.

Chrome/browser control.

WhatsApp desktop automation with confirmation.

Local memory and productivity tools.

System monitoring.

Screen capture/OCR.

Multi-step Agent Mode.

AI Code Lab and online compilation.

Optional cloud AI chat.

The current implementation demonstrates a broad functional prototype. The next major engineering step should be reliability and modularization, followed by a permission-aware agent architecture, stronger testing, better configuration management, and optional local AI capabilities.

RAX should remain a user-controlled assistant: it should make actions easier, while clearly showing what it is about to do and requiring confirmation whenever an action could create a meaningful external consequence.