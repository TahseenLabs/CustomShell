[![progress-banner](https://backend.codecrafters.io/progress/shell/aca1d7aa-06b2-412d-a933-09d25dd3c4c0)](https://app.codecrafters.io/users/codecrafters-bot?r=2qF)

# Building a Unix Shell from Scratch in Python

A fully functional POSIX-compliant Unix shell built in Python, completing all 9 sections and 50 stages of the [CodeCrafters Shell Challenge](https://app.codecrafters.io/courses/shell/overview). Every stage was test-driven with exact expected output — no hand-waving allowed.

---

## Features

### 1. Core Shell (REPL)
- Read-Eval-Print Loop with prompt display and input parsing
- Error handling for unknown commands
- `exit` builtin

### 2. Navigation
- `pwd` — print working directory
- `cd` with absolute paths, relative paths (`./`, `../`), and `~` (tilde) expansion via `$HOME`

### 3. Quoting
- Single quotes — preserve everything literally
- Double quotes — preserve spaces, escape select characters
- Backslash escaping inside and outside quotes
- Executing programs whose names are quoted (e.g. `'exe with spaces'`)

### 4. Redirection
- `>` and `1>` — redirect stdout
- `>>` and `1>>` — append stdout
- `2>` — redirect stderr
- `2>>` — append stderr
- Auto-creation of output directories if they don't exist

### 5. Command Completion
- `readline`-based tab completion for builtins and PATH executables
- Longest Common Prefix logic for multiple matches
- Bell rings when no match exists
- Prompt re-displays correctly after showing multiple options

### 6. Filename Completion
- Tab completion for filenames and nested directory paths (`path/to/f<TAB>`)
- Trailing `/` for directories (no trailing space)
- Completion works at any argument position in the command

### 7. Pipelines
- `|` operator to chain multiple commands
- Built-ins supported at any position in the pipeline

> **The bug that broke me — and what I learned:**
> `tail -f | head -n 5` was hanging forever. No output. No error. Just silence.
>
> The cause: Python was holding an extra file descriptor reference to the pipe, so `head` never received `SIGPIPE` when it exited, and `tail -f` kept running indefinitely.
>
> The fix: pass stdout directly between processes at the OS level, no Python buffering in between. That's systems programming — you only learn it by breaking things.

### 8. History
- `history` builtin with correct formatting
- `history N` to limit output to last N entries
- Up/down arrow navigation
- `!N` to re-execute a command by number

### 9. History Persistence
- Full `HISTFILE` support
- `history -r` — read from file
- `history -w` — overwrite file
- `history -a` — append only new entries without duplicating
- Auto-loads history on startup, auto-writes on exit

---

## How to Run

### Prerequisites
- Python 3.8+
- Unix-based system (Linux or macOS)
```bash
# Clone the repo
git clone https://github.com/TahseenLabs/CustomShell.git
cd CustomShell

# Option 1 — using the entry point script
./your_program.sh

# Option 2 — directly with Python
python3 app/main.py
```

---

## Project Structure
```
.
├── app/
│   ├── main.py        # Shell implementation
│   └── motd.py        # Message of the day
├── your_program.sh    # Entry point script (run this to start the shell)
├── codecrafters.yml   # CodeCrafters config
├── pyproject.toml     # Python project config
├── uv.lock            # Dependency lock file
└── README.md
```

---

## What I Learned

- How shells parse and tokenize input (quoting, escaping, redirection)
- How pipes work at the OS level using file descriptors
- Why Python's buffering can silently break inter-process communication
- How `readline` powers tab completion in real shells like Bash

---

Built as part of the [CodeCrafters Shell Challenge](https://app.codecrafters.io/courses/shell/overview) — 9 sections, 50 stages, all passed.
