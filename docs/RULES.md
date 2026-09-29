Project: RAX
Document: Engineering, runtime, safety and contribution rules
Version: 1.0
Reviewed: 2026-09-29
Applies to: RAX source code, runtime behavior, skills, automation, AI integrations and future development.

1. Purpose

This document defines the rules that RAX must follow while being developed and while executing user commands.

RAX is a personal Windows desktop assistant. It can interact with the operating system, applications, websites, external services and user data.

Because RAX can perform real actions on a computer, its behavior must prioritize:

User control.

Correctness.

Safety.

Privacy.

Transparency.

Reliability.

Maintainability.

2. Core Product Rules

RULE-001 — User remains in control

RAX must never treat itself as the final authority over the user's computer.

The user controls:

What RAX does.

Which services are enabled.

Which permissions are granted.

Whether sensitive actions are confirmed.

Whether data is stored.

Whether external services are used.

RULE-002 — Do not claim an action succeeded without verification

RAX must distinguish between:

Requested
Started
Completed
Failed
Unknown

Example:

Bad:

"VS Code opened."

when the process could not be started.

Correct:

"I couldn't open VS Code."

If the result cannot be verified:

"I attempted to open VS Code, but I couldn't verify that it started."

RULE-003 — Never silently perform unrelated actions

RAX must execute only the action requested or an obvious required sub-action.

For example:

User:
"Open YouTube."

RAX should not additionally:

Search the user's history.

Open unrelated websites.

Send messages.

Modify files.

Change settings.

RULE-004 — Prefer the smallest action that satisfies the request

If the user asks:

"Open Calculator."

RAX should open Calculator rather than performing additional system operations.

3. Command Processing Rules

RULE-010 — Normalize before execution

Raw voice or text input must pass through normalization before routing.

Raw input
    ↓
Language normalization
    ↓
Command parsing
    ↓
Intent resolution
    ↓
Skill

RULE-011 — Do not execute ambiguous high-impact commands

If a command could have multiple interpretations and one interpretation has a meaningful external consequence, ask for clarification or confirmation.

Example:

"Message Rahul."

RAX should not invent the message.

It should ask:

"What message should I send to Rahul?"

RULE-012 — Never invent missing parameters

Do not invent:

Contact names.

Messages.

File paths.

Passwords.

Locations.

Dates.

Times.

Amounts.

API credentials.

If required information is missing, ask for it.

RULE-013 — Preserve user intent

RAX may normalize language but must not change the meaning.

Example:

"Search YouTube for Python tutorials."

must remain a YouTube search.

It must not become:

Search Google.

unless the user requests Google.

RULE-014 — Supported commands only

RAX must not claim to support a command if the relevant skill is unavailable.

Correct:

"I don't currently have a skill for that."

Incorrect:

"Done."

when no action was performed.

4. Permission Rules

RAX uses action-risk levels.

LEVEL 0 — Read-only
LEVEL 1 — Local reversible
LEVEL 2 — External/reversible
LEVEL 3 — Sensitive
LEVEL 4 — Destructive

RULE-020 — Level 0: Read-only

No confirmation is normally required.

Examples:

CPU usage.

RAM usage.

Battery.

Disk usage.

Weather.

Current time.

Read saved memory.

List tasks.

Network status.

RULE-021 — Level 1: Local reversible actions

Normal command execution is allowed.

Examples:

Open Calculator.

Open Notepad.

Open File Explorer.

Open Chrome.

Open a website.

Start a timer.

Start Pomodoro.

RAX should still report the result.

RULE-022 — Level 2: External actions

External actions should be clearly identified.

Examples:

Search external websites.

Send code to a remote execution service.

Send a screenshot to an external AI service.

Use cloud AI.

Use external weather/speech services.

RAX must not hide the fact that external processing is occurring.

RULE-023 — Level 3: Sensitive actions require confirmation

Examples:

Sending a WhatsApp message.

Making a WhatsApp call.

Scheduling consequential actions.

Remote code execution.

Actions that expose private information externally.

The user must explicitly confirm.

Accepted confirmation should be clear, such as:

yes
confirm
send
do it

Ambiguous responses should not trigger the action.

RULE-024 — Level 4: Destructive actions require stronger confirmation

Examples:

Deleting files.

Clearing all memory.

Clearing all tasks.

Shutting down the computer.

Actions that may cause irreversible data loss.

The confirmation should identify the action.

Example:

"Delete all saved RAX memory? This cannot be undone. Please confirm."

5. WhatsApp Rules

RULE-030 — Draft before send

WhatsApp messages must follow:

Contact
   ↓
Message
   ↓
Draft
   ↓
Confirmation
   ↓
Send

RULE-031 — Never send without confirmation

RAX must never send a WhatsApp message based only on the initial command.

Example:

User:
"Send Rahul hello."

RAX:
"I drafted: 'hello' to Rahul. Send it?"

Only after confirmation may the message be sent.

RULE-032 — Show the final message before sending

The user must have the opportunity to see the actual text that will be sent.

RULE-033 — Allow message correction

If the user says:

change it
edit
no
wrong message

RAX must not send the message.

It should request the replacement text.

RULE-034 — Cancel means cancel

If the user says:

cancel
stop
don't send
no

the pending WhatsApp action must be discarded.

6. Browser Rules

RULE-040 — Do not assume browser state

RAX should not assume:

A particular tab exists.

A website is logged in.

A particular Chrome profile is open.

A page loaded successfully.

Where possible, verify the result.

RULE-041 — Do not expose credentials

RAX must never read, speak, log or transmit browser passwords unless an explicitly designed secure authentication feature requires it.

RULE-042 — Do not make purchases automatically

Opening a shopping search is allowed.

Autonomous:

Checkout.

Payment.

Order placement.

Subscription purchase.

is not allowed without explicit user interaction and confirmation.

7. File and System Rules

RULE-050 — Protect user files

RAX must not modify or delete files unless the user requested the operation.

RULE-051 — File deletion requires confirmation

Before deleting files, RAX should identify:

File/path.

What will be deleted.

Whether recovery is possible.

RULE-052 — Avoid destructive wildcard operations

Do not execute broad commands such as:

delete everything
remove *
format drive

without a dedicated safety flow and explicit confirmation.

RULE-053 — Avoid system-critical paths

RAX must not modify Windows system files, registry entries or protected directories unless a specific feature explicitly requires it and the user clearly requested it.

RULE-054 — Power actions must be explicit

Commands such as:

sleep
shutdown
restart

should not be triggered by unrelated or ambiguous phrases.

8. Secrets and Credentials

RULE-060 — Never hard-code secrets

Do not put:

API keys.

Passwords.

Tokens.

Session cookies.

Private keys.

inside source code.

RULE-061 — Use environment variables or secure storage

Example:

OPENAI_API_KEY
RAX_AI_MODEL
JUDGE0_ENDPOINT

RULE-062 — Never log secrets

Logs must redact:

API keys
passwords
tokens
cookies
authentication headers

RULE-063 — Do not speak secrets

TTS must never read API keys, passwords or tokens aloud.

RULE-064 — No fake credentials

If credentials are missing, RAX must report the missing configuration rather than pretending that a service is available.

9. Privacy Rules

RULE-070 — Local-first data handling

If an operation can be performed locally, prefer the local implementation.

RULE-071 — External transmission must be intentional

Before sending private data to an external service, the feature should make the destination clear.

Examples:

OpenAI
Judge0
Speech Recognition
Weather Provider

RULE-072 — Screenshots are private

Screenshots may contain:

Personal messages.

Passwords.

Documents.

Banking information.

Personal accounts.

Do not upload screenshots externally unless the user explicitly requests an external analysis feature.

RULE-073 — Clipboard is private

Clipboard contents may contain passwords, tokens or sensitive text.

Do not:

Log clipboard contents.

Send clipboard contents externally without explicit request.

Speak sensitive clipboard contents unnecessarily.

RULE-074 — Memory belongs to the user

RAX memory must be user-controlled.

The user must eventually be able to:

View memory.

Search memory.

Edit memory.

Delete individual memory.

Clear all memory.

RULE-075 — Minimize stored data

Only store data required for the requested feature.

10. AI Rules

RULE-080 — AI is an assistant, not an authority

AI-generated responses must not be treated as automatically correct.

RULE-081 — Do not fabricate tool results

If an API, browser, compiler or OS action was not actually executed, RAX must not claim that it was.

RULE-082 — Separate AI generation from action execution

The AI layer should suggest or structure an action.

The command/skill layer should decide whether the action is supported and permitted.

Architecture:

AI
 ↓
Intent / Plan
 ↓
Router
 ↓
Permission
 ↓
Skill
 ↓
Action

AI should not directly execute arbitrary operating-system commands.

RULE-083 — Do not blindly execute generated commands

Generated shell commands or code must be treated as untrusted.

Before execution:

Generated command
      ↓
Validation
      ↓
Risk assessment
      ↓
Permission
      ↓
Execution

11. Code Lab Rules

RULE-090 — Generated code is untrusted

Code generated by an AI model must be treated as potentially unsafe.

RULE-091 — Remote execution must be explicit

When code is sent to Judge0 or another external compiler, the user should know that the code is being processed externally.

RULE-092 — Never send secrets with code

Do not include:

API keys.

Passwords.

Environment secrets.

Private files.

in remote code execution requests.

RULE-093 — Apply execution limits

Remote code execution should use:

Timeouts.

Resource limits where available.

Output limits.

Sandboxing provided by the execution service.

12. Agent Mode Rules

RULE-100 — Agent Mode may only use registered skills

Agent Mode must not invent arbitrary capabilities.

RULE-101 — Every agent step goes through the normal router

Agent commands must use the same execution path as normal commands.

Agent Step
   ↓
Router
   ↓
Permission
   ↓
Skill

RULE-102 — Sensitive agent steps require confirmation

An agent plan containing:

send message
delete file
remote execution
power action

must stop for appropriate confirmation.

RULE-103 — Agent must report each step

Example:

Step 1/3 — Open VS Code — Success
Step 2/3 — Open Chrome — Success
Step 3/3 — Start focus timer — Success

RULE-104 — Agent must stop safely

The user should be able to stop an agent workflow.

Commands such as:

stop
cancel
abort

should stop future steps.

RULE-105 — Failure must not be hidden

If Step 2 fails, RAX must not report the entire workflow as successful.

13. Voice Rules

RULE-110 — Voice recognition failure is not command success

If speech recognition returns no reliable command:

"I didn't catch that."

must be preferred over guessing.

RULE-111 — Do not infer sensitive commands from unclear speech

For high-impact actions, uncertainty should result in clarification.

RULE-112 — Voice commands must follow the same permissions as typed commands

Voice must not bypass security.

14. Multilingual Rules

RULE-120 — Preserve intent across languages

Translation/normalization should preserve:

Target.

Action.

Message.

Time.

Quantity.

Location.

RULE-121 — Do not silently change language settings

If the user changes RAX's language, the active setting should be visible or reported.

RULE-122 — Unsupported language must fail gracefully

RAX should say that the requested language is unavailable rather than pretending to understand it.

15. GUI Rules

RULE-130 — GUI must remain responsive

Never perform long blocking operations directly on the Tkinter event loop.

RULE-131 — UI state must match actual state

If RAX is not listening, the GUI must not show:

LISTENING

If an agent stopped, the UI must stop showing it as active.

RULE-132 — Errors must be visible

Important failures should be visible in the GUI even if TTS also reports them.

RULE-133 — Do not rely on color alone

Status should also use:

Text.

Icons.

Labels.

for accessibility.

16. Threading Rules

RULE-140 — Tkinter widgets belong to the main thread

Worker threads must not directly modify Tkinter widgets.

RULE-141 — Use queues/events for worker results

Recommended:

Worker
  ↓
Result Queue
  ↓
Tkinter main loop
  ↓
UI update

RULE-142 — Threads must terminate cleanly

RAX must avoid leaving background workers running after application shutdown.

17. External API Rules

RULE-150 — Use timeouts

Every HTTP/API request must have a timeout.

RULE-151 — Handle service unavailability

External failures must produce a clear result:

Service unavailable
Timeout
Authentication failure
Invalid response
Rate limited

RULE-152 — Do not retry endlessly

Retries must have a finite limit.

RULE-153 — Do not expose raw API errors to users unnecessarily

Technical details can go into safe logs.

The user should receive a concise explanation.

18. Storage Rules

RULE-160 — Validate stored data

RAX must tolerate:

Missing files.

Empty files.

Invalid JSON.

Partial records.

Older data formats.

RULE-161 — Avoid corrupting persistent data

Write operations should preferably use safe replacement techniques.

Example:

Write temporary file
       ↓
Validate
       ↓
Replace original

RULE-162 — Do not store arbitrary command input indefinitely

Command history should be limited and privacy-conscious.

19. Logging Rules

RULE-170 — Logs are for diagnostics

Logs should help developers determine:

What happened.

Which skill ran.

Whether it succeeded.

Why it failed.

RULE-171 — Logs must be privacy-aware

Do not log sensitive content unnecessarily.

RULE-172 — Use consistent log levels

DEBUG
INFO
WARNING
ERROR
CRITICAL

20. Error Handling Rules

RULE-180 — Catch expected errors at the appropriate layer

A skill should handle errors caused by its own dependencies.

RULE-181 — Do not swallow errors silently

Bad:

try:
    ...
except:
    pass

Preferred:

try:
    ...
except SpecificError as exc:
    logger.error(...)
    return SkillResult(success=False, ...)

RULE-182 — Never expose stack traces to normal users

Developer diagnostics may be logged separately.

RULE-183 — Preserve application stability

A failed feature must not unnecessarily terminate RAX.

21. Coding Rules

RULE-190 — Use clear names

Prefer:

send_whatsapp_message()

over:

swm()

RULE-191 — Keep functions focused

A function should have one clear responsibility.

Avoid functions that:

Parse input.

Modify UI.

Call APIs.

Write files.

Speak text.

all at the same time.

RULE-192 — Avoid unnecessary global state

Prefer:

class RAXApp:
    ...

and injected dependencies over uncontrolled global variables.

RULE-193 — Keep UI and business logic separate

Do not put command logic directly inside button callbacks.

RULE-194 — Use type hints where practical

Example:

def open_application(name: str) -> SkillResult:
    ...

RULE-195 — Use docstrings for public components

Document:

Purpose.

Parameters.

Return value.

Important side effects.

22. Dependency Rules

RULE-200 — Every dependency must have a reason

Do not add a package for a feature that can be implemented reliably with the standard library.

RULE-201 — Optional dependencies must remain optional where possible

Example:

Tesseract
OpenAI
Judge0

should not prevent basic RAX functionality from launching.

RULE-202 — Pin or constrain production dependencies

The project should eventually maintain a reproducible dependency file.

23. Configuration Rules

RULE-210 — Configuration must be externalized

Do not hard-code user-specific settings into source code.

RULE-211 — Provide safe defaults

RAX should launch with reasonable defaults when optional configuration is missing.

RULE-212 — Never commit .env

.env belongs in .gitignore.

Provide:

.env.example

instead.

24. Git Rules

RULE-220 — Do not commit runtime environments

Do not commit:

.venv/
venv/
__pycache__/
*.pyc

RULE-221 — Do not commit private runtime profiles

Do not commit:

Chrome profile data
WhatsApp profile data
private screenshots
private logs
personal memory files

RULE-222 — Use meaningful commit messages

Examples:

feat: add WhatsApp confirmation flow
fix: prevent GUI freeze during voice recognition
refactor: extract system skill
docs: add architecture documentation
test: add router unit tests

25. Documentation Rules

The project should maintain:

README.md
PRD.md
ARCHITECTURE.md
RULES.md

Documentation should describe the actual implementation.

Do not document features as implemented if they are only planned.

Use wording such as:

Implemented
Experimental
Optional
Planned
Future

26. Testing Rules

RULE-230 — New features need tests

At minimum, test:

Normal input.

Invalid input.

Missing dependency.

External failure.

Permission denial.

RULE-231 — Test destructive paths carefully

Destructive operations should use mocked/test environments.

Do not run destructive integration tests against the developer's real files.

RULE-232 — Test both voice and text routing

Where possible, the same command intent should be testable without requiring a microphone.

27. Feature Development Rules

Every new feature should follow:

Requirement
    ↓
Design
    ↓
Skill
    ↓
Permission
    ↓
Implementation
    ↓
Error Handling
    ↓
Tests
    ↓
Documentation

28. New Skill Checklist

Before adding a skill, answer:

[ ] What problem does the skill solve?
[ ] What commands does it support?
[ ] What permissions does it require?
[ ] What data does it read?
[ ] What data does it write?
[ ] Does it use an external service?
[ ] Can it fail?
[ ] How is failure reported?
[ ] Does it need confirmation?
[ ] How is it tested?

29. New External Service Checklist

Before adding an external service:

[ ] What data is sent?
[ ] Why must it be sent?
[ ] Is the service optional?
[ ] Is there a timeout?
[ ] Is there a retry limit?
[ ] How are credentials stored?
[ ] What happens when the service is unavailable?
[ ] Is the user informed?
[ ] Are private data and secrets protected?

30. New Automation Checklist

Before adding desktop automation:

[ ] Is the target application installed?
[ ] What happens if it is not installed?
[ ] Is the automation reversible?
[ ] Can the UI change?
[ ] Can the result be verified?
[ ] Does the action require confirmation?
[ ] Can it accidentally affect another application?
[ ] Is there a safe stop mechanism?

31. AI Agent Rules

When AI is used for planning:

AI proposes
     ↓
RAX validates
     ↓
RAX checks permissions
     ↓
RAX executes

Never:

AI proposes
     ↓
AI directly executes arbitrary OS command

32. Prompt Rules

AI system prompts should:

Define RAX's role.

Encourage concise answers.

Avoid claiming tool execution without tool evidence.

Respect user intent.

Avoid requesting unnecessary sensitive information.

Clearly distinguish generated suggestions from completed actions.

33. Memory Rules

RULE-300 — Do not remember everything automatically

Only information explicitly intended for memory should be stored.

RULE-301 — Memory must be user-accessible

Users should be able to inspect stored memory.

RULE-302 — Memory deletion must be respected

If a user asks RAX to delete a memory, the corresponding persistent record should be removed.

34. Routine Rules

User routines may contain multiple actions.

A routine should be represented as:

Routine
├── Name
├── Description
├── Steps
├── Permissions
└── Enabled

Each step must still pass through normal safety rules.

A routine must not become a mechanism for bypassing confirmation.

35. Shutdown and Emergency Stop Rules

RULE-310 — User must be able to stop active automation

RAX should provide a clear stop mechanism for:

Agent Mode.

Long-running automation.

Voice capture.

Future autonomous workflows.

RULE-311 — Stop must prevent future steps

For an agent:

Step 1 → completed
Step 2 → running
User presses STOP
Step 3 → must not execute

36. Compatibility Rules

When refactoring RAX:

RULE-320 — Do not remove working features without a replacement

Existing functionality should be preserved during migration.

RULE-321 — Prefer incremental refactoring

Move one subsystem at a time.

RULE-322 — Preserve command compatibility

Existing commands should continue to work unless intentionally deprecated and documented.

37. Performance Rules

RULE-330 — Avoid unnecessary polling

System information should refresh at a reasonable interval.

RULE-331 — Do not block on network calls

Use worker execution for slow services.

RULE-332 — Avoid repeated initialization

Services should be initialized once where appropriate.

38. Resource Rules

RAX should release:

Microphone streams.

Camera/screen resources.

File handles.

HTTP sessions where appropriate.

Worker threads.

Temporary files.

39. Windows-Specific Rules

Because RAX is Windows-first:

Use Windows-specific APIs only inside platform adapters where possible.

Detect unsupported platforms clearly.

Do not assume every Windows installation has the same applications.

Do not assume Chrome is installed.

Do not assume WhatsApp Desktop is installed.

Do not assume Tesseract is installed.

Do not assume VS Code is installed.

Do not assume PowerShell paths are identical on every system.

40. Fallback Rules

If a preferred implementation fails, RAX may use a safe fallback.

Example:

Screenshot
   ↓
pyautogui
   ↓
fails
   ↓
ImageGrab fallback

Fallbacks must not silently change the requested action into something unrelated.

41. User Feedback Rules

Responses should be:

Concise.

Clear.

Action-oriented.

Honest about uncertainty.

Examples:

Success

"Calculator opened."

Failure

"I couldn't open Calculator."

Missing configuration

"Cloud AI isn't configured. Add OPENAI_API_KEY to enable it."

Confirmation

"I drafted the WhatsApp message. Send it?"

42. TTS Rules

TTS should not read extremely long technical output by default.

For code execution:

GUI:
full compiler output

TTS:
"Execution finished. Check the Code Lab for the output."

43. Command History Rules

History may store:

Timestamp.

Command category.

Success/failure.

Safe summary.

Avoid storing sensitive full content unnecessarily.

44. Screenshot Rules

Screenshot filenames should use timestamps or unique IDs.

Example:

rax_screen_20260929_191500.png

Do not overwrite existing screenshots accidentally.

45. Code Generation Rules

Generated files should:

Use the requested language.

Have appropriate file extensions.

Be saved in a predictable location.

Not overwrite unrelated user files.

Not include fake execution results.

46. API Failure Rules

If an API returns an error:

API failure
   ↓
Catch
   ↓
Log safe diagnostic
   ↓
Return SkillResult failure
   ↓
Inform user

Do not crash RAX.

47. Development Priority Rules

When choosing between:

New Feature
vs
Reliability Fix

the development process should prioritize:

Security.

Data integrity.

Crash prevention.

Existing feature reliability.

Testing.

Maintainability.

New features.

48. Definition of a Safe RAX Action

An action is considered safe to execute automatically when:

- The intent is clear.
- Required parameters are known.
- The action is supported.
- Required permissions are satisfied.
- The action is not unnecessarily destructive.
- External side effects are understood.
- The result can be reported honestly.

49. Definition of a Safe RAX Agent

An agent workflow is safe when:

Goal
 ↓
Plan
 ↓
Supported steps
 ↓
Risk check
 ↓
Permission check
 ↓
Execution
 ↓
Verification
 ↓
Report

50. Golden Rules

The following rules summarize the entire document.

1. Never pretend

If RAX did not perform an action, it must not say it did.

2. Never guess sensitive information

Ask the user when an important parameter is missing.

3. Never send sensitive external actions without confirmation

Especially messages and other consequential actions.

4. Never expose secrets

API keys, passwords and tokens must remain protected.

5. Never let AI bypass the safety layer

AI generates plans or content; RAX validates and executes.

6. Never allow one failed feature to crash the whole assistant

Isolate errors.

7. Never block the GUI unnecessarily

Use asynchronous/worker execution for long operations.

8. Never store unnecessary private information

Use local-first and data minimization.

9. Never bypass permissions through Agent Mode or routines

All actions use the same permission system.

10. Always preserve user control

The user can stop, cancel or decline sensitive operations.

51. Final Rule

RAX exists to make the user's computer easier to control, not to take control away from the user. Every action must be understandable, appropriately authorized, safely executed, and honestly reported.