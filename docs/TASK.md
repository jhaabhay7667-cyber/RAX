Engineering task list for the RAX Intelligent AI Desktop Assistant.

Based on the supplied project archive reviewed on 2026-09-29.

Status meanings:

[x] implemented/present in the supplied project

[ ] remaining work

[~] partially implemented or needs verification

1. Current Project Snapshot

RAX is currently a Windows desktop AI assistant primarily implemented in Python with Tkinter.

The supplied implementation contains:

Desktop GUI.

Typed commands.

Voice recognition.

Text-to-speech.

Multilingual command/language support.

Windows application control.

Chrome/browser control.

WhatsApp desktop automation.

Screen capture/vision features.

Code Lab and remote code execution.

Weather/search utilities.

Notes, reminders, alarms, tasks and memory.

Pomodoro/focus tools.

System monitoring.

Agent Mode.

Skills and routines.

Optional cloud AI chat.

Command history and activity logging.

The largest engineering concern is that most functionality is concentrated in main_v4.py.

2. Priority Legend

Priority

Meaning

P0

Critical safety/reliability/security

P1

High-priority engineering work

P2

Important product improvement

P3

Future enhancement

3. Phase 0 — Repository Cleanup

P0 — Remove unnecessary runtime artifacts

Remove .venv/ from the source repository/archive.

Remove browser-profile/cache data from the source repository.

Remove generated caches and __pycache__/.

Keep screenshots only when intentionally used as project assets/documentation.

Keep runtime data files separate from source code.

P0 — Secrets and sensitive data

Audit the entire project for hard-coded passwords, API keys, tokens and cookies.

Move all secrets to environment variables or secure OS storage.

Add .env.example.

Add a safe .gitignore.

Ensure secrets are not written to logs.

Ensure secrets are never spoken through TTS.

P1 — Dependency documentation

Add requirements.txt.

Document optional dependencies.

Document Windows-only requirements.

Document optional Tesseract OCR installation.

Document Judge0 requirements.

Document OpenAI configuration.

Document microphone/audio requirements.

4. Phase 1 — Stabilize main_v4.py

P0 — Protect the GUI

Ensure network calls never block the Tkinter event loop.

Ensure voice recognition runs outside the UI thread.

Ensure long-running automation runs outside the UI thread.

Ensure exceptions in one feature do not crash the entire application.

Add safe UI update helpers for worker threads.

P1 — Centralize configuration

Move configuration such as:

Assistant name.

Default language.

Supported languages.

Voice rate.

Voice volume.

AI model.

AI API configuration.

Judge0 endpoints.

Idle timeout.

Feature flags.

into a dedicated configuration module.

P1 — Structured results

Create a common result format:

success
message
data
error_code
external_service
requires_confirmation

Every skill should return structured results rather than relying only on spoken text.

5. Phase 2 — Modular Architecture

Split the large main_v4.py into maintainable modules.

Recommended structure:

RAX/
├── main.py
├── config.py
│
├── core/
│   ├── router.py
│   ├── state.py
│   ├── permissions.py
│   └── events.py
│
├── ui/
│   ├── main_window.py
│   ├── theme.py
│   ├── components.py
│   └── tabs/
│       ├── home.py
│       ├── agent.py
│       ├── vision.py
│       ├── code.py
│       ├── skills.py
│       ├── system.py
│       └── pro.py
│
├── skills/
│   ├── system.py
│   ├── browser.py
│   ├── whatsapp.py
│   ├── vision.py
│   ├── coding.py
│   └── productivity.py
│
├── services/
│   ├── speech.py
│   ├── tts.py
│   ├── ai.py
│   ├── weather.py
│   └── judge0.py
│
├── storage/
│   ├── memory.py
│   ├── tasks.py
│   └── history.py
│
└── tests/

Tasks:

Extract configuration.

Extract GUI.

Extract command router.

Extract permissions.

Extract Windows/system skill.

Extract browser skill.

Extract WhatsApp skill.

Extract vision skill.

Extract Code Lab.

Extract productivity features.

Extract memory/task/history storage.

Extract external service clients.

Keep main.py focused on startup and dependency wiring.

6. Phase 3 — Command Router

Create one consistent execution path:

Input
  ↓
Normalize
  ↓
Intent / command detection
  ↓
Router
  ↓
Permission
  ↓
Skill
  ↓
Execution
  ↓
Verification
  ↓
Result
  ↓
GUI + TTS + safe log

Tasks:

Remove duplicated command-routing logic.

Create a command registry.

Give every command a unique name.

Associate commands with skills.

Associate permissions with commands.

Add command aliases.

Add structured parsing errors.

Add tests for command parsing.

7. Phase 4 — Permission and Safety Layer

P0

Implement a dedicated permission system.

Permission levels:

LEVEL 0 — Read-only
LEVEL 1 — Local reversible
LEVEL 2 — External/reversible
LEVEL 3 — Sensitive
LEVEL 4 — Destructive

Tasks:

Create permission definitions.

Require confirmation for Level 3 actions.

Require stronger confirmation for Level 4 actions.

Ensure Agent Mode uses the same permission system.

Ensure routines use the same permission system.

Add a visible confirmation dialog.

Add voice confirmation.

Add cancel handling.

Add global emergency stop.

8. Phase 5 — WhatsApp Safety

Required flow:

Contact
   ↓
Message
   ↓
Draft
   ↓
Confirmation
   ↓
Send

Tasks:

Confirm the selected contact.

Display the final message before sending.

Allow edit/replacement.

Cancel must discard the pending message.

Never send from the initial command alone.

Verify that the message was actually submitted where possible.

Report failure instead of claiming success.

Handle WhatsApp UI changes gracefully.

9. Phase 6 — Agent Mode

Current direction:

Agent
 ↓
Registered Skill
 ↓
Router
 ↓
Permission
 ↓
Execution

Tasks:

Add plan preview.

Show every planned step.

Show permission requirements.

Pause before sensitive steps.

Add STOP button.

Support voice stop, cancel, and abort.

Show Step X/Y.

Verify each step.

Stop safely after a failed step.

Do not report the whole workflow as successful when one step failed.

Add retry for safe steps.

Add failure recovery where practical.

Avoid pretending rollback exists unless rollback was actually implemented.

10. Phase 7 — Voice and Multilingual Support

Current supported language configuration includes:

English

Hindi

Bengali

Maithili

Bhojpuri

Marathi

French

Tasks:

Verify each configured language.

Add graceful microphone failure handling.

Add microphone selection.

Add configurable speech rate.

Add configurable TTS volume.

Improve recognition confidence/error reporting.

Separate language detection from command execution.

Add multilingual command aliases.

Document external speech-processing behavior.

Add optional wake-word support later.

11. Phase 8 — GUI

Main shell

RAX header.

Local Core status.

Seven primary tabs.

Dark command-center theme.

Animated RAX visual.

State indicator.

Animated waveform.

HOME

[~] Verify typed command flow.

[~] Verify voice-listen flow.

Improve conversation history rendering.

Add clear confirmation cards.

Add visible external-processing indicators.

AGENT

[~] Verify agent window.

Add step progress.

Add stop button.

Add confirmation UI.

Add failure state.

VISION

[~] Verify screen capture.

Add clear privacy warning.

Add screenshot preview.

Clearly identify external vision processing.

CODE

[~] Verify Code Lab.

Separate generation from execution.

Add remote execution warning.

Add timeout/result limits.

Improve code/result presentation.

SKILLS

[~] Skills window exists.

[~] Routines window exists.

Add permission information per skill.

Add enabled/disabled state.

SYSTEM

CPU card.

RAM card.

Battery card.

Disk card.

Windows quick controls.

Add clearer error state for unavailable metrics.

PRO

Memory controls.

Task controls.

Pomodoro controls.

Diagnostics.

Optional AI Chat.

Add privacy-aware activity history.

12. Phase 9 — Memory

Current files include local memory-related storage.

Tasks:

Create dedicated memory module.

View memory.

Search memory.

Edit individual memory.

Delete individual memory.

Clear all memory with strong confirmation.

Minimize stored data.

Prevent secrets from being saved accidentally.

Add import/export only after privacy rules are defined.

13. Phase 10 — Productivity

Tasks:

Notes.

Reminders.

Alarms.

Tasks/todos.

Pomodoro.

Command history.

Add structured task storage.

Add task priorities.

Add task due dates.

Add searchable command history.

Redact sensitive values from history.

14. Phase 11 — Browser and Windows Automation

Tasks:

Open Chrome.

Chrome profile selection.

Google search.

YouTube search.

New-tab search.

Open Calculator.

Open Notepad.

Open File Explorer.

Open VS Code.

Lock PC.

Sleep PC.

Add verification after application launch.

Avoid assuming a browser tab/profile exists.

Improve failure messages.

Keep credentials inaccessible to RAX.

Require explicit confirmation for consequential browser actions.

15. Phase 12 — Vision and Screenshots

Tasks:

Screen capture path.

[~] Vision analysis.

Add OCR dependency documentation.

Add explicit external-processing indicator.

Avoid automatic upload of screenshots.

Redact sensitive information where feasible.

Add screenshot retention policy.

Add user-controlled screenshot cleanup.

16. Phase 13 — AI and Code Lab

Tasks:

Optional OpenAI configuration.

AI chat path.

AI code generation path.

Judge0-compatible execution path.

Move AI integration into services/ai.py.

Move Judge0 integration into services/judge0.py.

Add configurable providers.

Add explicit external-processing notices.

Add code timeout.

Add output limit.

Never send secrets with code.

Validate generated commands before execution.

Treat generated code as untrusted.

17. Phase 14 — Testing

Create automated tests for:

Unit tests

Language normalization.

Command aliases.

Timer parsing.

Reminder parsing.

Alarm parsing.

Brightness parsing.

WhatsApp command parsing.

Shopping command parsing.

Chrome command parsing.

Programming command parsing.

Permission evaluation.

Agent stop/cancel behavior.

Integration tests

GUI startup.

Voice-to-command flow.

Command-to-skill flow.

External service failure.

WhatsApp draft flow.

Agent workflow.

Code execution timeout.

Memory persistence.

Task persistence.

Safety tests

Sensitive action without confirmation is blocked.

Cancel prevents action.

Ambiguous confirmation prevents action.

Destructive action requires stronger confirmation.

Secrets are absent from logs.

Agent cannot bypass permissions.

Failed actions are not reported as successful.

18. Phase 15 — Logging and Observability

Tasks:

Replace ad-hoc prints with structured logging where practical.

Add log levels.

Add safe error IDs.

Redact API keys.

Redact passwords.

Redact authentication tokens.

Avoid unnecessary clipboard logging.

Avoid unnecessary private-message logging.

Record external-service failures separately.

Make user-visible activity history privacy-conscious.

19. Phase 16 — Performance

Tasks:

Audit every network request.

Move blocking requests to workers.

Add request timeouts.

Add code-execution timeouts.

Prevent animation loops from consuming excessive CPU.

Limit chat/activity history in memory.

Limit screenshot retention.

Profile startup time.

Profile voice-processing latency.

20. Phase 17 — Accessibility

Tasks:

Keyboard-only navigation.

Visible focus indicators.

Adjustable UI text size.

High-contrast mode.

Configurable microphone.

Configurable speech rate.

Text equivalents for important voice-only information.

Do not rely on color alone for status.

21. Phase 18 — Documentation

Required documentation:

docs/ARCHITECTURE.md

docs/PRD.md

docs/RULES.md

docs/DESIGN.md

README.md

TASK.md

requirements.txt

.env.example

Installation guide.

Troubleshooting guide.

Voice setup guide.

Optional AI setup guide.

Judge0 setup guide.

Security/privacy guide.

22. Phase 19 — Future Features

These are not required for the current prototype.

P2/P3

Wake word: Hey RAX.

Local LLM support.

Configurable AI providers.

Visual routine builder.

Skill registry.

Permission Center.

Activity Center.

User-created skills.

Preference profiles.

Import/export.

Better screen-element understanding.

Advanced OCR/layout understanding.

23. Release Checklist

Before calling a release stable:

Security

No secrets in source.

No secrets in logs.

Sensitive actions require confirmation.

Destructive actions have stronger confirmation.

Agent Mode cannot bypass permissions.

External data transmission is intentional.

Reliability

GUI remains responsive.

Network failures are handled.

Microphone failures are handled.

Missing applications are handled.

Failed actions are not reported as successful.

Agent failures are visible.

Packaging

.venv/ excluded.

Browser profile excluded.

Cache files excluded.

requirements.txt present.

.env.example present.

README setup instructions present.

Testing

Command parser tests pass.

Permission tests pass.

WhatsApp safety tests pass.

Agent stop tests pass.

External-service failure tests pass.

GUI startup test passes.

24. Recommended Implementation Order

If development is done step-by-step, use this order:

P0 — Security audit

P0 — Repository cleanup

P0 — Permission layer

P0 — GUI/thread reliability

P1 — requirements.txt + .env.example

P1 — Command router

P1 — Modularize main_v4.py

P1 — WhatsApp confirmation flow

P1 — Agent Mode safety

P1 — Automated tests

P1 — Structured logging

P2 — Memory improvements

P2 — Accessibility

P2 — Better AI/tool calling

P3 — Local AI

P3 — Wake word

P3 — Skill registry/routine builder

25. Definition of Done

RAX can be considered a production-ready desktop assistant when:

Core commands are modular.

Dependencies are reproducible.

Configuration is centralized.

Secrets are externalized.

Sensitive actions require confirmation.

Agent Mode follows the same permission system.

GUI stays responsive.

External failures are handled.

Logs are privacy-conscious.

User memory can be viewed and deleted.

Automated command-parser tests exist.

Installation and troubleshooting are documented.

The project can be built/run without the archived virtual environment.

The application never claims an action succeeded without verification.

26. Golden Engineering Rules

Never pretend.

Never guess sensitive information.

Never perform sensitive external actions without confirmation.

Never expose secrets.

Never allow AI to bypass the safety layer.

Never let one failed feature crash the entire assistant.

Never block the GUI unnecessarily.

Never store unnecessary private information.

Never let Agent Mode or routines bypass permissions.

Always preserve user control.