# VPCS

### Virtual Pooltoy Container System

VPCS is a terminal-based AI character runtime written in Python.

It allows you to create, configure and interact with your own AI characters using simple JSON configuration files.

Each character can have its own personality, behavior, speaking style and persistent conversation memory.

---

## ⚠️ Platform Support

> **Important:** VPCS has currently been tested only on **Linux**, especially **Arch Linux**.
>
> Windows and macOS are supported as intended platforms, but they have **not been extensively tested** yet. Some commands or dependency behavior may differ depending on the operating system and Python installation.

### Tested

* 🐧 Linux — **tested**
* 🐧 Arch Linux — **primary development/testing environment**

### Not extensively tested

* 🪟 Windows
* 🍎 macOS

If you encounter a platform-specific issue, please open an issue with your operating system, Python version and the error message.

---

# Features

* Multiple custom characters
* JSON-based configuration
* Separate memory for each character
* Groq API support
* `.env` API key configuration
* Interactive terminal interface
* ASCII startup banner
* Character registry
* Runtime status
* Configuration hot reload
* Individual memory management
* Simple and extensible architecture

---

# Requirements

VPCS requires:

* Python **3.10 or newer**
* A Groq API key
* Internet connection
* `pip` or another Python package manager

Python 3.14 is also supported in the current development environment.

---

# Installation

## Linux

### Arch Linux

Arch Linux is the primary development and testing environment for VPCS.

Install Python and Git:

```bash
sudo pacman -S python python-pip git
```

Clone the repository:

```bash
git clone <repository-url>
cd VPCS
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install groq python-dotenv
```

Run VPCS:

```bash
python main.py
```

### Other Linux distributions

The general installation process should be the same.

Install Python and Git using your distribution's package manager, then:

```bash
git clone <repository-url>
cd VPCS
python -m venv .venv
source .venv/bin/activate
pip install groq python-dotenv
python main.py
```

Package names may differ between distributions.

---

# Windows

> ⚠️ Windows support has not been extensively tested.

Install Python from the official Python distribution or your preferred package manager.

Clone the repository:

```powershell
git clone <repository-url>
cd VPCS
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\activate
```

Install dependencies:

```powershell
pip install groq python-dotenv
```

Run:

```powershell
python main.py
```

If your system uses the Python launcher instead:

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install groq python-dotenv
python main.py
```

---

# macOS

> ⚠️ macOS support has not been extensively tested.

Make sure Python 3.10+ is installed.

Clone the repository:

```bash
git clone <repository-url>
cd VPCS
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install groq python-dotenv
```

Run:

```bash
python main.py
```

---

# API Key

VPCS reads the Groq API key from a `.env` file.

Create:

```text
.env
```

in the root directory of the project.

Add:

```env
GROQ_API_KEY=gsk_your_api_key_here
```

Never commit your `.env` file.

Add this to `.gitignore`:

```gitignore
.env
.venv/
vpcs_memory/
__pycache__/
*.pyc
```

---

# Running VPCS

Activate the virtual environment and run:

```bash
python main.py
```

VPCS will initialize its runtime and load the available character configurations.

If multiple characters are available, VPCS will ask which one you want to use.

---

# Creating Characters

Characters are stored inside:

```text
pooltoys/
```

Every `.json` file in this directory represents one character.

Example:

```text
pooltoys/
├── character1.json
├── character2.json
└── character3.json
```

You can create as many characters as you want.

---

# Character Configuration

A basic configuration looks like this:

```json
{
  "name": "Example",
  "emoji": "🤖",
  "prompt": "You are Example, a friendly and helpful AI character. Speak naturally and keep your responses concise."
}
```

There are three main properties.

## `name`

The character's display name.

```json
"name": "Example"
```

## `emoji`

The emoji displayed next to the character.

```json
"emoji": "🤖"
```

You can use any emoji you want.

## `prompt`

The system prompt that defines the character.

```json
"prompt": "You are Example..."
```

This is where you define the character's personality, behavior and communication style.

---

# Designing a Character

A character prompt can define things such as:

* Personality
* Tone
* Speaking style
* Interests
* Humor
* Vocabulary
* Response length
* Behavior
* Preferences
* Background
* Relationship with the user
* Rules the character should follow

For example:

```json
{
  "name": "Nova",
  "emoji": "🌙",
  "prompt": "You are Nova, a calm and friendly AI character. You speak naturally, use occasional humor, and prefer short but meaningful responses. You enjoy discussing technology, games and creative projects."
}
```

The character system is intentionally flexible.

You can create completely different personalities without changing the Python code.

---

# Why Create Custom Characters?

There are many possible uses for custom characters.

## Personal AI companions

Create a character with a personality and communication style that fits you.

## Programming assistants

Create a character focused on programming, debugging and technical explanations.

## Gaming assistants

Create characters designed around games, strategies, builds or game-related conversations.

## Roleplay

Create characters with their own personalities, backgrounds and fictional worlds.

## Creative projects

Characters can be used for stories, prototypes, experiments or interactive projects.

## AI experimentation

Create multiple configurations with different prompts and compare their behavior.

## Learning

Use different characters as tutors for different subjects or learning styles.

---

# Memory

VPCS keeps separate memory for each character.

Example:

```text
vpcs_memory/
├── character1.json
├── character2.json
└── character3.json
```

This prevents conversations between different characters from being mixed together.

Each memory file contains the conversation history for that character.

The number of stored messages is limited by:

```python
MAX_MEMORY_MESSAGES = 30
```

You can change this value in `main.py`.

---

# Commands

VPCS provides several commands.

## `/help`

Display the available commands.

```text
/help
```

## `/status`

Display the current runtime status.

```text
/status
```

Example:

```text
VPCS STATUS
────────────────────────────────────────

Runtime      : ONLINE
Version      : 1.0
Character    : Example
Config       : example.json
Model        : openai/gpt-oss-120b
Memory       : 12 messages
Temperature  : 0.85

────────────────────────────────────────
```

## `/memory`

Display the current character's conversation memory.

```text
/memory
```

## `/clear`

Delete the current character's memory.

```text
/clear
```

This only affects the currently selected character.

## `/pooltoys`

Display all available character configurations.

```text
/pooltoys
```

## `/reload`

Reload the currently selected character's JSON configuration.

```text
/reload
```

This allows you to modify a character's configuration without restarting VPCS.

## `/exit`

Exit VPCS.

```text
/exit
```

---

# Project Structure

A typical VPCS installation looks like this:

```text
VPCS/
│
├── main.py
├── README.md
├── .env
├── .gitignore
│
├── pooltoys/
│   ├── character1.json
│   ├── character2.json
│   └── character3.json
│
├── vpcs_memory/
│   ├── character1.json
│   └── character2.json
│
└── .venv/
```

---

# AI Model

VPCS currently uses:

```text
openai/gpt-oss-120b
```

through the Groq API.

The model is configured in `main.py`:

```python
MODEL = "openai/gpt-oss-120b"
```

You can change the model if the selected Groq model is supported by the API.

---

# Configuration

Several runtime settings can be changed in `main.py`.

```python
MODEL = "openai/gpt-oss-120b"

TEMPERATURE = 0.85

MAX_TOKENS = 250

MAX_MEMORY_MESSAGES = 30
```

### Temperature

Controls how varied the model's responses can be.

```python
TEMPERATURE = 0.85
```

### Max Tokens

Controls the maximum response length.

```python
MAX_TOKENS = 250
```

### Memory Limit

Controls how many messages are retained.

```python
MAX_MEMORY_MESSAGES = 30
```

---

# Creating Your Own Character

A simple workflow is:

### 1. Create a JSON file

```text
pooltoys/my_character.json
```

### 2. Define the character

```json
{
  "name": "My Character",
  "emoji": "✨",
  "prompt": "You are My Character. You are friendly, curious and energetic. Speak naturally and keep responses concise."
}
```

### 3. Start VPCS

```bash
python main.py
```

### 4. Select the character

If multiple configurations exist, VPCS will display them and ask you to choose one.

No Python code needs to be changed.

---

# Security

Never expose your Groq API key.

Do not commit:

```text
.env
```

to a public repository.

It is also recommended to keep:

```text
vpcs_memory/
```

out of Git repositories because conversation history may contain private information.

Recommended `.gitignore`:

```gitignore
.env
.venv/
vpcs_memory/
__pycache__/
*.pyc
```

---

# Philosophy

VPCS is designed around a simple idea:

> **The runtime provides the infrastructure.
> The user defines the character.**

Characters are configuration rather than hard-coded Python classes.

This makes it possible to create, modify and experiment with characters without changing the core application.

---

# Troubleshooting

## `ModuleNotFoundError`

If you see:

```text
ModuleNotFoundError: No module named 'dotenv'
```

make sure the virtual environment is activated and install the dependencies again:

```bash
pip install groq python-dotenv
```

Check that the correct Python is being used:

```bash
which python
```

On Windows:

```powershell
where python
```

The path should point to the VPCS `.venv` directory.

---

## `GROQ_API_KEY non trovata`

Make sure `.env` exists in the VPCS root directory:

```text
VPCS/
├── main.py
└── .env
```

and contains:

```env
GROQ_API_KEY=gsk_your_api_key_here
```

---

## Character not appearing

Make sure the configuration is inside:

```text
pooltoys/
```

and has the `.json` extension.

Also verify that the JSON is valid.
