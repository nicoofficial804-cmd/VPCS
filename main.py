#!/usr/bin/env python3

"""
============================================================
VPCS — Virtual Pooltoy Container System
Terminal interface per agenti "pooltoy" basati su Groq API
Version 1.2.0
============================================================
"""

import os
import sys
import json
import logging
import tempfile
import argparse
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv
from groq import Groq, GroqError


# ============================================================
# VERSION / PATHS
# ============================================================

VERSION = "1.2.0"

BASE_DIR = Path(__file__).resolve().parent

ENV_FILE = BASE_DIR / ".env"
POOLTOYS_DIR = BASE_DIR / "pooltoys"
MEMORY_DIR = BASE_DIR / "vpcs_memory"
LOG_DIR = BASE_DIR / "logs"

for directory in (POOLTOYS_DIR, MEMORY_DIR, LOG_DIR):
    directory.mkdir(exist_ok=True)

load_dotenv(ENV_FILE)


# ============================================================
# LOGGING
# ============================================================

def setup_logging(verbose=False):
    """Configura logging su file (sempre) e console (solo se verbose)."""
    log_file = LOG_DIR / f"vpcs_{datetime.now(timezone.utc):%Y%m%d}.log"

    logger = logging.getLogger("vpcs")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if logger.handlers:
        return logger

    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    if verbose:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(file_formatter)
        logger.addHandler(console_handler)

    return logger


log = setup_logging()


# ============================================================
# AI SETTINGS (override via variabili ambiente / .env)
# ============================================================

MODEL = os.environ.get("VPCS_MODEL", "openai/gpt-oss-120b")

TEMPERATURE = float(os.environ.get("VPCS_TEMPERATURE", "0.85"))
MAX_TOKENS = int(os.environ.get("VPCS_MAX_TOKENS", "250"))
MAX_MEMORY_MESSAGES = int(os.environ.get("VPCS_MAX_MEMORY", "30"))
MAX_ANSWER_CHARS = int(os.environ.get("VPCS_MAX_ANSWER_CHARS", "600"))
REQUEST_TIMEOUT = float(os.environ.get("VPCS_TIMEOUT", "30"))
MAX_RETRIES = int(os.environ.get("VPCS_MAX_RETRIES", "2"))
MAX_INPUT_CHARS = int(os.environ.get("VPCS_MAX_INPUT_CHARS", "4000"))

# Codici di stato HTTP per cui ha senso ritentare (errori transitori).
# Tutto il resto (401, 400, 404, ...) è un errore permanente: niente retry.
RETRYABLE_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}


# ============================================================
# TERMINAL COLORS
# ============================================================

# Se l'output non è un terminale (es. redirect su file), disabilita i colori
_USE_COLOR = sys.stdout.isatty()

RESET = "\033[0m" if _USE_COLOR else ""
BOLD = "\033[1m" if _USE_COLOR else ""
DIM = "\033[2m" if _USE_COLOR else ""

CYAN = "\033[96m" if _USE_COLOR else ""
GREEN = "\033[92m" if _USE_COLOR else ""
YELLOW = "\033[93m" if _USE_COLOR else ""
RED = "\033[91m" if _USE_COLOR else ""
MAGENTA = "\033[95m" if _USE_COLOR else ""
WHITE = "\033[97m" if _USE_COLOR else ""


def color(text, colour):
    return f"{colour}{text}{RESET}"


# ============================================================
# ASCII BANNER
# ============================================================

def show_banner():
    print()

    print(color(r"""
██╗   ██╗██████╗  ██████╗███████╗
██║   ██║██╔══██╗██╔════╝██╔════╝
██║   ██║██████╔╝██║     ███████╗
╚██╗ ██╔╝██╔═══╝ ██║     ╚════██║
 ╚████╔╝ ██║     ╚██████╗███████║
  ╚═══╝  ╚═╝      ╚═════╝╚══════╝
""", CYAN))

    print(color(f"Virtual Pooltoy Container System v{VERSION}", BOLD))
    print(color("Runtime per agenti pooltoy basati su Groq API", DIM))
    print()


# ============================================================
# TERMINAL HELPERS
# ============================================================

def print_line():
    print(color("─" * 64, DIM))


def success(message):
    print(color(f"✓ {message}", GREEN))


def warning(message):
    print(color(f"⚠ {message}", YELLOW))


def error(message):
    print(color(f"✗ {message}", RED))


def info(message):
    print(color(f"› {message}", CYAN))


# ============================================================
# POOLTOY CONFIGURATION
# ============================================================

REQUIRED_KEYS = ("name", "prompt")
MAX_PROMPT_CHARS = 8000


def find_pooltoy_configs():
    return sorted(p for p in POOLTOYS_DIR.glob("*.json") if p.is_file())


def load_pooltoy_config(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        error(f"{path.name}: JSON non valido ({e})")
        log.warning("JSON non valido in %s: %s", path, e)
        return None
    except OSError as e:
        error(f"{path.name}: impossibile leggere ({e})")
        log.error("Errore lettura %s: %s", path, e)
        return None

    if not isinstance(data, dict):
        error(f"{path.name}: il JSON deve essere un oggetto.")
        return None

    for key in REQUIRED_KEYS:
        if not data.get(key):
            error(f"{path.name}: manca il campo obbligatorio '{key}'.")
            return None

    name = str(data["name"]).strip()
    prompt = str(data["prompt"]).strip()
    emoji = str(data.get("emoji", "🐋")).strip() or "🐋"

    if not name:
        error(f"{path.name}: 'name' non può essere vuoto.")
        return None

    if not prompt:
        error(f"{path.name}: 'prompt' non può essere vuoto.")
        return None

    if len(prompt) > MAX_PROMPT_CHARS:
        warning(
            f"{path.name}: prompt troppo lungo "
            f"({len(prompt)} caratteri), troncato a {MAX_PROMPT_CHARS}."
        )
        prompt = prompt[:MAX_PROMPT_CHARS]

    return {
        "name": name,
        "emoji": emoji,
        "prompt": prompt,
        "file": path,
    }


def load_all_pooltoys():
    return [
        config
        for path in find_pooltoy_configs()
        if (config := load_pooltoy_config(path)) is not None
    ]


def select_pooltoy(preselect_name=None):
    pooltoys = load_all_pooltoys()

    if not pooltoys:
        print()
        error("Nessun pooltoy configurato.")
        print()
        info(f"Cartella: {POOLTOYS_DIR}")
        info("Inserisci almeno un file .json valido.")
        print()
        raise SystemExit(1)

    if preselect_name:
        matches = [p for p in pooltoys if p["name"].lower() == preselect_name.lower()]
        if matches:
            selected = matches[0]
            success(f"Pooltoy caricato: {selected['emoji']} {selected['name']}")
            return selected
        warning(f"Nessun pooltoy chiamato '{preselect_name}', passo alla selezione manuale.")

    if len(pooltoys) == 1:
        selected = pooltoys[0]
        success(f"Pooltoy caricato: {selected['emoji']} {selected['name']}")
        return selected

    print()
    print(color("POOLTOY REGISTRY", BOLD))
    print_line()

    for index, pooltoy in enumerate(pooltoys, start=1):
        filename = pooltoy["file"].name
        print(f"  {color(str(index), CYAN)} {pooltoy['emoji']} {pooltoy['name']} {color(f'[{filename}]', DIM)}")

    print_line()
    print()

    while True:
        try:
            choice = input(color("Select pooltoy › ", CYAN)).strip()
        except (KeyboardInterrupt, EOFError):
            print()
            raise SystemExit(0)

        if not choice.isdigit():
            warning("Inserisci un numero.")
            continue

        index = int(choice)

        if not 1 <= index <= len(pooltoys):
            warning("Selezione non valida.")
            continue

        selected = pooltoys[index - 1]
        print()
        success(f"Selected {selected['emoji']} {selected['name']}")
        return selected


# ============================================================
# MEMORY
# ============================================================

def safe_filename(name):
    cleaned = "".join(c if c.isalnum() or c in "-_" else "_" for c in name.lower())
    return cleaned or "pooltoy"


def memory_file(pooltoy):
    return MEMORY_DIR / f"{safe_filename(pooltoy['name'])}.json"


def load_memory(pooltoy):
    path = memory_file(pooltoy)

    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            # scarta elementi malformati invece di far fallire tutto
            return [
                m for m in data
                if isinstance(m, dict) and m.get("role") in ("user", "assistant") and m.get("content")
            ]

    except (json.JSONDecodeError, OSError) as e:
        log.warning("Memoria corrotta per %s: %s", pooltoy["name"], e)
        warning(f"Memoria corrotta, verrà ignorata ({path.name}).")

    return []


def save_memory(pooltoy, memory):
    path = memory_file(pooltoy)
    memory = memory[-MAX_MEMORY_MESSAGES:]

    try:
        fd, temp_path = tempfile.mkstemp(
            prefix=f"{safe_filename(pooltoy['name'])}_",
            suffix=".tmp",
            dir=MEMORY_DIR,
        )

        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)

        os.replace(temp_path, path)

    except OSError as e:
        log.error("Errore salvataggio memoria per %s: %s", pooltoy["name"], e)
        warning(f"Errore salvataggio memoria: {e}")


def clear_memory(pooltoy):
    path = memory_file(pooltoy)

    try:
        if path.exists():
            path.unlink()
    except OSError as e:
        log.error("Errore cancellazione memoria per %s: %s", pooltoy["name"], e)
        warning(f"Errore cancellazione memoria: {e}")


# ============================================================
# GROQ CLIENT
# ============================================================

def create_client():
    api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        print()
        error("GROQ_API_KEY non trovata.")
        print()
        info(f"File previsto: {ENV_FILE}")
        print()
        print("Esempio:")
        print()
        print("GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxx")
        print()
        raise SystemExit(1)

    return Groq(api_key=api_key, timeout=REQUEST_TIMEOUT)


# ============================================================
# AI
# ============================================================

def _is_retryable(exc):
    """True solo per errori transitori (rete, rate limit, 5xx)."""
    status = getattr(exc, "status_code", None)
    if status is not None:
        return status in RETRYABLE_STATUS_CODES
    # Nessun status_code disponibile: tratta come non recuperabile
    # per evitare di ritentare inutilmente su errori di configurazione.
    return False


def ask_ai(client, pooltoy, user_message, memory):
    """Invia la richiesta a Groq con retry solo su errori transitori."""

    if len(user_message) > MAX_INPUT_CHARS:
        raise ValueError(
            f"Messaggio troppo lungo ({len(user_message)} caratteri, "
            f"massimo {MAX_INPUT_CHARS})."
        )

    messages = [{"role": "system", "content": pooltoy["prompt"]}]

    for message in memory:
        role = message.get("role")
        content = message.get("content")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})

    last_error = None
    response = None

    for attempt in range(1, MAX_RETRIES + 2):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                reasoning_format="hidden",
            )
            break

        except GroqError as e:
            log.warning("Errore Groq (tentativo %d): %s", attempt, e)

            if not _is_retryable(e):
                raise RuntimeError(f"Errore API non recuperabile: {e}") from e

            last_error = e
            if attempt > MAX_RETRIES:
                raise RuntimeError(f"Errore API dopo {attempt} tentativi: {e}") from e

    if response is None:
        raise RuntimeError(f"Errore API: {last_error}")

    if not response.choices:
        raise RuntimeError("Risposta API senza scelte disponibili.")

    choice = response.choices[0]
    answer = choice.message.content

    if not answer:
        finish_reason = getattr(choice, "finish_reason", "unknown")
        raise RuntimeError(f"Risposta vuota dal modello (finish_reason={finish_reason})")

    answer = answer.strip()

    if len(answer) > MAX_ANSWER_CHARS:
        log.info(
            "Risposta troncata da %d a %d caratteri.",
            len(answer), MAX_ANSWER_CHARS,
        )
        answer = answer[:MAX_ANSWER_CHARS].rstrip() + "…"

    return answer


# ============================================================
# STATUS
# ============================================================

def show_status(pooltoy, memory):
    print()
    print(color("VPCS STATUS", BOLD))
    print_line()

    print(f"  Runtime      : {color('ONLINE', GREEN)}")
    print(f"  Version      : {VERSION}")
    print(f"  Pooltoy      : {pooltoy['emoji']} {pooltoy['name']}")
    print(f"  Config       : {pooltoy['file'].name}")
    print(f"  Model        : {MODEL}")
    print(f"  Memory       : {len(memory)} messages")
    print(f"  Temperature  : {TEMPERATURE}")

    print_line()
    print()


# ============================================================
# HELP
# ============================================================

def show_help():
    print()
    print(color("VPCS COMMANDS", BOLD))
    print_line()

    commands = [
        ("/help", "Mostra questo menu"),
        ("/status", "Mostra lo stato del runtime"),
        ("/memory", "Mostra la memoria"),
        ("/clear", "Cancella la memoria del pooltoy"),
        ("/reload", "Ricarica la configurazione"),
        ("/pooltoys", "Mostra i pooltoy disponibili"),
        ("/exit", "Esce da VPCS"),
    ]

    for command, description in commands:
        print(f"  {color(command, CYAN):<20}{description}")

    print_line()
    print()


# ============================================================
# POOLTOY LIST
# ============================================================

def show_pooltoys(pooltoy):
    pooltoys = load_all_pooltoys()

    print()
    print(color("POOLTOY REGISTRY", BOLD))
    print_line()

    for item in pooltoys:
        selected = item["file"] == pooltoy["file"]
        marker = color("●", GREEN) if selected else "○"
        print(f"  {marker} {item['emoji']} {item['name']} {color(item['file'].name, DIM)}")

    print_line()
    print()


# ============================================================
# RELOAD
# ============================================================

def reload_pooltoy(pooltoy):
    new_config = load_pooltoy_config(pooltoy["file"])

    if not new_config:
        warning("Reload fallito, mantengo la configurazione precedente.")
        return pooltoy

    success(f"Reloaded {new_config['emoji']} {new_config['name']}")
    return new_config


# ============================================================
# CHAT PROMPT
# ============================================================

def make_prompt(pooltoy):
    return color("You › ", WHITE)


# ============================================================
# MAIN CHAT
# ============================================================

def chat(preselect_name=None):
    show_banner()

    info("Initializing VPCS runtime...")
    log.info("VPCS avviato (v%s)", VERSION)

    try:
        client = create_client()
    except SystemExit:
        raise

    success("Groq API connected.")

    pooltoy = select_pooltoy(preselect_name)
    memory = load_memory(pooltoy)

    success(f"Memory loaded ({len(memory)} messages).")

    print()
    print_line()
    print(f"{pooltoy['emoji']} {color(pooltoy['name'], BOLD)} is ready.")
    print(color("Type /help for commands.", DIM))
    print_line()

    while True:
        try:
            user_input = input(make_prompt(pooltoy)).strip()
        except (KeyboardInterrupt, EOFError):
            print()
            print()
            info("Shutting down VPCS...")
            print()
            break

        if not user_input:
            continue

        command = user_input.lower()

        if command in ("/exit", "/quit", "/q"):
            print()
            info("Shutting down VPCS...")
            print()
            break

        if command == "/help":
            show_help()
            continue

        if command == "/status":
            show_status(pooltoy, memory)
            continue

        if command == "/memory":
            print()
            print(color(f"MEMORY — {pooltoy['name']}", BOLD))
            print_line()

            if not memory:
                print(color("  Memory empty.", DIM))
            else:
                for item in memory:
                    role = item.get("role", "")
                    content = item.get("content", "")
                    if role == "user":
                        print(f"  You: {content}")
                    elif role == "assistant":
                        print(f"  {pooltoy['name']}: {content}")

            print_line()
            print()
            continue

        if command == "/clear":
            clear_memory(pooltoy)
            memory = []
            success(f"Memory cleared for {pooltoy['name']}.")
            continue

        if command == "/pooltoys":
            show_pooltoys(pooltoy)
            continue

        if command == "/reload":
            pooltoy = reload_pooltoy(pooltoy)
            memory = load_memory(pooltoy)
            continue

        # Messaggio normale verso l'AI
        try:
            response = ask_ai(
                client=client,
                pooltoy=pooltoy,
                user_message=user_input,
                memory=memory,
            )

        except ValueError as e:
            print()
            warning(str(e))
            print()
            continue

        except Exception as e:
            log.exception("Errore durante la richiesta AI")
            print()
            error(f"AI error: {e}")
            print()
            continue

        print()
        print(f"{pooltoy['emoji']} {color(pooltoy['name'], BOLD)}: {response}")
        print()

        memory.append({"role": "user", "content": user_input})
        memory.append({"role": "assistant", "content": response})
        memory = memory[-MAX_MEMORY_MESSAGES:]

        save_memory(pooltoy, memory)


# ============================================================
# CLI ARGS
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser(
        prog="vpcs",
        description="VPCS — Virtual Pooltoy Container System",
    )
    parser.add_argument(
        "-p", "--pooltoy",
        metavar="NAME",
        help="Nome del pooltoy da caricare automaticamente",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Abilita log dettagliati anche su console",
    )
    return parser.parse_args()


# ============================================================
# ENTRY POINT
# ============================================================

def main():
    args = parse_args()

    global log
    log = setup_logging(verbose=args.verbose)

    try:
        chat(preselect_name=args.pooltoy)

    except SystemExit:
        raise

    except KeyboardInterrupt:
        print()
        print()
        info("VPCS terminated.")
        print()

    except Exception as e:
        log.exception("Errore fatale")
        print()
        error(f"Fatal error: {e}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()