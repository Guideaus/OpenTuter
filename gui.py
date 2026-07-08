import json
import sys
import time
from openai import OpenAI
import ugui.oobe as oobe
import core as engine

def setup():
    with open("config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)
    llm = cfg["llm"]
    if any(not llm.get(field, "").strip() for field in ["api_key", "base_url", "model"]):
        oobe.main()
        with open("config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
        llm = cfg["llm"]
    if not llm.get("api_key", "").strip():
        base = llm.get("base_url", "")
        is_local = any(h in base for h in ("localhost", "127.0.0.1"))
        if is_local:
            llm["api_key"] = "not-needed"
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=4, ensure_ascii=False)
        else:
            print("API key is required for remote providers. Run OOBE setup again.")
            sys.exit(1)
    return cfg

def call_llm(messages, client, llm_cfg):
    return client.chat.completions.create(
        model=llm_cfg["model"],
        messages=messages,
        temperature=llm_cfg.get("temperature", 0.2),
    ).choices[0].message.content

def main():
    cfg = setup()
    llm_cfg = cfg["llm"]
    tools_cfg = cfg["tools"]

    abort = engine.AbortController()
    abort.start()

    client = OpenAI(api_key=llm_cfg["api_key"], base_url=llm_cfg["base_url"])

    with open(tools_cfg["mouse_path"], "r", encoding="utf-8") as f:
        mouse_tools = json.load(f)["tools"]
    mouse_names = {t["name"] for t in mouse_tools}

    with open(tools_cfg["keyboard_path"], "r", encoding="utf-8") as f:
        keyboard_tools = json.load(f)["tools"]
    keyboard_names = {t["name"] for t in keyboard_tools}

    mouse_commands = engine.load_mouse_commands()

    system_prompt = f"""You are a desktop automation assistant that controls mouse and keyboard.

## Available Commands
- **Tool commands** — one per line with space-separated arguments
- **screenshot** — request a screenshot of the current screen (you will receive the image automatically)
- **FINISHED** — signal that the task is complete

## Mouse Tools
{engine.build_tool_descriptions(mouse_tools)}

## Keyboard Tools
{engine.build_tool_descriptions(keyboard_tools)}

## Flow
1. You receive a text task from the user.
2. If you need to see the screen, output: screenshot
3. After receiving the screenshot, output tool commands to perform actions.
4. After commands execute, you will see the updated screen automatically.
5. Repeat until the task is done, then output: FINISHED

## Example
screenshot
mouse_goto 500 400
mouse_left_click
key_type Hello World
key_enter
screenshot
FINISHED"""

    messages = [{"role": "system", "content": system_prompt}]
    print("OpenTuter ready. Type your task (or 'exit' to quit).")
    print("Press DEL 3 times quickly to abort any operation.\n")

    while True:
        try:
            user_input = input("> ")
        except (EOFError, KeyboardInterrupt):
            break
        if user_input.lower() in ("exit", "quit", "q"):
            break

        abort.aborted = False
        messages.append({"role": "user", "content": user_input})

        max_rounds = 20
        for _ in range(max_rounds):
            if abort.aborted:
                break

            try:
                content = call_llm(messages, client, llm_cfg)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                break
            print(f"\n{content}\n")
            messages.append({"role": "assistant", "content": content})

            if "FINISHED" in content:
                break

            lines = [l.strip() for l in content.split("\n") if l.strip()]

            if any(l.lower() == "screenshot" for l in lines):
                b64 = engine.capture_screen_base64(scale=1.0, fmt="PNG")
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Here is the current screen."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                    ]
                })
                continue

            for line in lines:
                if abort.aborted:
                    break
                if line.lower() != "screenshot":
                    engine.execute_command(line, mouse_names, keyboard_names, mouse_commands, tools_cfg)

            if abort.aborted:
                break

            time.sleep(0.3)
            b64 = engine.capture_screen_base64(scale=1.0, fmt="PNG")
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": "Commands executed. Updated screen below. Continue or output FINISHED if done."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                ]
            })

        if abort.aborted:
            print("[Operation aborted by user - triple DEL detected]")
            abort.aborted = False

if __name__ == "__main__":
    main()
