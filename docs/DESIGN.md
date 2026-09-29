Design specification for the RAX Intelligent AI Desktop Assistant.

Based on the supplied RAX project archive, especially main_v4.py, docs/ARCHITECTURE.md, docs/PRD.md, and docs/RULES.md.

Last reviewed: 2026-09-29

1. Product Identity

Product name: RAX
Product type: Windows desktop AI assistant / command center
Primary implementation: Python
Primary GUI: Tkinter
Primary interaction: Typed commands + voice commands
Design direction: Futuristic, dark, technical, local-first, responsive, safety-aware.

RAX should feel like a personal desktop command center rather than a generic chatbot. The interface combines conversational interaction, system telemetry, automation controls, vision, coding, skills, routines, and productivity tools.

2. Design Goals

Make common computer actions fast to execute.

Make RAX's current state obvious at all times.

Keep the user in control of sensitive actions.

Present technical information without making the UI difficult for a beginner.

Maintain a consistent futuristic visual language.

Keep local functionality visually distinct from optional cloud functionality.

Keep the GUI responsive while voice recognition, networking, automation, or AI work is running.

Make failures visible and understandable instead of pretending an action succeeded.

3. Visual Language

3.1 Overall Style

The visual style is:

Dark cyber/desktop command-center aesthetic.

Near-black application background.

Cyan as the primary interaction accent.

Green for healthy/local/online states.

Purple for AI/coding/pro features.

Pink/magenta for vision-related activity.

Orange for agent activity or attention-required states.

Muted gray text for secondary information.

Thin borders and compact cards.

Minimal gradients; emphasis on glow, contrast, and state changes.

Segoe UI as the primary Windows UI font.

3.2 Core Color Tokens

Token

Value

Purpose

bg-root

#04070a

Main application background

bg-header

#070b0f

Header

bg-nav

#090e12

Navigation

bg-panel

#0b1015

Cards/panels

bg-control

#101a20

Buttons/controls

border

#1d3038

Card boundaries

text-primary

#d7e5ea

Main text

text-secondary

#84939a

Descriptions

text-muted

#68777e

Metadata

cyan

#00eaff

Primary RAX accent

green

#00ff88

Online/success/local

purple

#b66cff

AI/code/Pro

pink

#ff4fd8

Vision

orange

#ffb347

Agent/attention

These values are already reflected in the supplied Tkinter implementation and should remain centralized if the UI is refactored.

4. Application Layout

4.1 Main Window

Default window:

Title: RAX — Intelligent AI Desktop Assistant

Initial size: approximately 1280 × 820

Minimum size: approximately 980 × 680

Root background: #04070a

The layout has four major regions:

┌─────────────────────────────────────────────────────────────┐
│ RAX                         YOUR AI DESKTOP COMMAND CENTER   │
│                                             ● LOCAL CORE    │
├─────────────────────────────────────────────────────────────┤
│ HOME │ AGENT │ VISION │ CODE │ SKILLS │ SYSTEM │ PRO       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                     ACTIVE TAB CONTENT                       │
│                                                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘

4.2 Header

The header should communicate:

RAX identity.

Product purpose.

Local-core status.

Recommended hierarchy:

◉ RAX

YOUR AI DESKTOP COMMAND CENTER

● LOCAL CORE

The header should remain visually quiet compared with the active content.

5. Navigation

Primary tabs currently implemented:

HOME

AGENT

VISION

CODE

SKILLS

SYSTEM

PRO

Active tab

The active tab should use:

Dark selected background.

Cyan text.

Clear contrast from inactive tabs.

Inactive tabs

Use:

Root/nav background.

Muted gray text.

Hover state with subtle cyan emphasis.

Navigation must never trigger a destructive action directly.

6. RAX State System

The UI must visually communicate RAX's current operating state.

States

State

Meaning

Accent

ONLINE

Idle/ready

Green

LISTENING

Voice input active

Cyan

THINKING

Processing command

Purple

SPEAKING

TTS output active

Cyan

AGENT

Agent workflow active

Orange

VISION

Screen/vision operation active

Pink

Current status labels follow the pattern:

● RAX ONLINE
● RAX IS LISTENING...
● RAX IS THINKING...
● RAX IS SPEAKING...
● RAX AGENT ACTIVE...
● RAX VISION ACTIVE...

State changes should also update the RAX image border/glow and listen-button label.

7. RAX Visual Avatar

The RAX image is a primary visual identity element.

When active:

Apply a subtle animated scale/pulse.

Add a soft glow.

Synchronize the visual state with listening/thinking/speaking/agent/vision states.

When idle:

Use a very subtle animation rather than a distracting effect.

The animation must not consume excessive CPU.

8. Waveform

The home/interaction area can use a lightweight animated waveform.

Idle

Low amplitude.

Dim cyan/gray presentation.

Active

Higher amplitude.

More visible cyan waveform.

Animation speed may increase while RAX is listening or speaking.

The waveform is decorative/status feedback. It must never be the only indication of system state; text status should remain available.

9. Card Component

Cards are the primary information container.

Card structure

┌─────────────────────────────────────────┐
│ TITLE                                   │
│ Short explanatory description           │
│                                         │
│ Content / controls                      │
└─────────────────────────────────────────┘

Card characteristics:

Background: #0b1015

Border: #1d3038

Thin border.

Small corner radius if the UI implementation permits it.

Compact spacing.

Accent-colored title.

Muted description text.

Cards should group related actions rather than create one card per tiny button.

10. HOME Tab Design

The HOME tab is the conversational command center.

It should prioritize:

RAX identity/avatar.

Current state.

Conversation history.

Text command input.

Voice listen action.

Quick actions.

System/agent activity when relevant.

Conversation presentation:

YOU
Open calculator

RAX
Calculator is open.

The chat area should:

Scroll automatically to the latest message.

Clearly distinguish user and RAX messages.

Keep timestamps/activity information available.

Avoid storing secrets in visible activity logs.

11. AGENT Tab

Purpose:

Show multi-step workflows.

Show current step.

Provide stop/cancel controls.

Require confirmation for sensitive operations.

Recommended structure:

RAX AGENT

Current workflow
────────────────────────
Step 1/4  Open VS Code       ✓
Step 2/4  Open Chrome        ✓
Step 3/4  Open project       ●
Step 4/4  Start focus        ○

[ STOP AGENT ]

Sensitive steps must visibly pause for confirmation.

The interface must never imply success for a step that failed.

12. VISION Tab

Purpose:

Capture the screen.

Display vision/OCR results.

Show whether external AI processing is being used.

Recommended structure:

RAX VISION

[ CAPTURE SCREEN ]

Preview
┌───────────────────────────────┐
│ Screenshot / analysis result  │
└───────────────────────────────┘

Status: VISION ACTIVE

Privacy requirement:

Screen images may contain passwords, messages, documents, banking data, or private accounts. External transmission must be intentional and clearly indicated.

13. CODE Tab

The CODE tab is the gateway to RAX Code Lab.

Current concept:

RAX CODE LAB

Explanation of generation/save/run capabilities.

OPEN FULL CODE LAB

Voice coding guidance.

Design should separate:

Code generation.

Code display/editing.

Local file saving.

Remote execution.

Execution result.

Remote execution must clearly show that code is being sent to an external service.

14. SKILLS Tab

Purpose:

Show available RAX skills.

Manage repeatable routines.

Current controls:

VIEW SKILLS

CUSTOM ROUTINES

Future skill cards should show:

Skill name
Description
Supported commands
Permission level
Local / External
Enabled / Disabled

Only registered skills should be executable by Agent Mode.

15. SYSTEM Tab

The SYSTEM tab is a local computer dashboard.

Telemetry cards

Current metrics:

CPU

RAM

Battery

Disk

Each metric should use:

Large value.

Short description.

Green accent.

Windows controls

Current quick controls include:

Lock PC

File Explorer

Notepad

Calculator

VS Code

Browser

System controls should visually distinguish reversible actions from sensitive/destructive actions.

16. PRO Tab

The PRO tab groups advanced personal productivity functions.

Current areas:

Memory

Remember

Show memory

Clear memory

Productivity

List tasks

Start Pomodoro

Stop Pomodoro

Tools

System report

Internet test

Pro help

AI Chat

Cloud AI must clearly indicate that it requires external configuration such as OPENAI_API_KEY.

17. Typography

Primary font:

Segoe UI

Suggested hierarchy:

Element

Size

Weight

Main page title

24px

Bold

Section title

11–14px

Bold

Header logo

22px

Bold

Telemetry number

22px

Bold

Body

9–11px

Regular

Metadata

8–9px

Regular

Avoid excessive font-size variation.

18. Buttons

Buttons should be compact and action-oriented.

Primary action:

Cyan or feature accent.

Strong text contrast.

Secondary action:

Dark background.

Light text.

Thin/no border.

Dangerous action:

Must be clearly identified.

Should not use the same visual treatment as harmless actions.

Must require the appropriate confirmation flow.

Button text should describe the action:

Good:

LOCK PC
OPEN CODE LAB
VIEW SKILLS
STOP AGENT

Avoid vague labels such as:

OK
GO
DO IT

for consequential actions.

19. Interaction Design

RAX supports:

Typed commands.

Voice commands.

Buttons/quick actions.

Agent workflows.

All interaction paths should eventually converge on the same command/permission/skill execution architecture.

Conceptual flow:

User
 ↓
Input
 ↓
Command / Intent
 ↓
Router
 ↓
Permission Check
 ↓
Registered Skill
 ↓
Action
 ↓
Verification
 ↓
GUI Result + Voice Result + Safe Log

The AI layer must not bypass the router or permission layer.

20. Confirmation UX

Sensitive actions require an explicit confirmation experience.

Example:

RAX wants to send this WhatsApp message:

Contact: Rahul
Message: Hello, I will reach at 6 PM.

[ SEND ]    [ EDIT ]    [ CANCEL ]

Voice confirmation examples:

yes

confirm

send

do it

Ambiguous responses must not trigger the action.

21. Error UX

Errors should be short, truthful, and actionable.

Good:

I could not open VS Code.
Please check that VS Code is installed.

For external service failures:

OpenAI is unavailable.
The local RAX features are still available.

Do not display raw stack traces to ordinary users. Keep detailed diagnostics in developer logs.

22. Responsive Behavior

Although Tkinter is desktop-oriented, the UI should remain usable when:

Window is resized.

Text becomes longer.

Chat history grows.

A skill fails.

A network operation is slow.

A microphone is unavailable.

Long-running work should run away from the Tkinter event loop.

23. Accessibility

Future design requirements:

Keyboard-only operation.

Visible focus states.

Adjustable text size.

High-contrast mode.

Configurable speech rate.

Configurable microphone.

Text equivalents for voice-only feedback.

Do not communicate critical information through color alone.

24. Privacy UX

RAX should visibly distinguish:

LOCAL

Examples:

CPU/RAM/Battery.

Local notes.

Local memory.

Local Windows controls.

EXTERNAL

Examples:

Cloud AI.

Speech recognition where applicable.

Weather provider.

Judge0.

External search.

When external processing occurs, the UI should make the destination/function clear.

25. Motion Guidelines

Motion should communicate state, not decorate every element.

Use animation for:

RAX active state.

Waveform.

Agent progress.

Loading/network state.

Avoid:

Constant large-scale movement.

Excessive flashing.

Long blocking animations.

Motion that interferes with reading.

26. Design Architecture

The visual layer should eventually be separated from business logic.

Recommended direction:

RAX
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
└── storage/
    ├── memory.py
    ├── tasks.py
    └── history.py

The supplied implementation currently concentrates most behavior in main_v4.py; this structure is the target for maintainability.

27. Design Rules

User control comes first.

Sensitive actions must be obvious.

Never claim an action succeeded unless it actually succeeded.

Never expose secrets in the UI or logs.

Keep local and external processing distinguishable.

Never allow Agent Mode to bypass normal permissions.

Keep the GUI responsive.

Use consistent status colors.

Prefer clear labels over decorative labels.

Preserve the RAX cyber/desktop-command-center identity while improving accessibility.

28. Definition of Done — Design

The design is considered complete when:

All seven main tabs have a consistent visual system.

Active states are visible.

Sensitive actions have confirmation UX.

Errors have a consistent presentation.

Local vs external processing is understandable.

The UI remains usable at the minimum supported window size.

Keyboard and text alternatives exist for important voice interactions.

Theme tokens are centralized.

UI code is separated from command/skill logic.