import json
import time
import pyautogui

def load_tool_config(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def write_config(config_key, config_value):
    with open("config.json", "r", encoding="utf-8") as file:
        config_data = json.load(file)
    config_data["llm"][config_key] = config_value
    with open("config.json", "w", encoding="utf-8") as file:
        json.dump(config_data, file, indent=4, ensure_ascii=False)

def parse_agent_command(command_text):
    text_segments = command_text.strip().split()
    if not text_segments:
        return {"action": "none"}
    action = text_segments[0]

    if action == "key_type":
        text = command_text[len("key_type"):].strip()
        return {"action": "key_type", "text": text}
    if action in ("key_press", "key_release", "key_tap"):
        return {"action": action, "key": text_segments[1]} if len(text_segments) > 1 else {"action": "none"}
    if action == "key_hotkey":
        return {"action": "key_hotkey", "keys": text_segments[1].split(",")} if len(text_segments) > 1 else {"action": "none"}
    if action == "key_backspace":
        return {"action": "key_backspace"}
    if action == "key_delete":
        return {"action": "key_delete"}
    if action == "key_enter":
        return {"action": "key_enter"}
    if action == "key_tab":
        return {"action": "key_tab"}
    if action == "key_space":
        return {"action": "key_space"}
    if action == "key_escape":
        return {"action": "key_escape"}
    if action == "key_arrow_up":
        return {"action": "key_arrow_up"}
    if action == "key_arrow_down":
        return {"action": "key_arrow_down"}
    if action == "key_arrow_left":
        return {"action": "key_arrow_left"}
    if action == "key_arrow_right":
        return {"action": "key_arrow_right"}
    if action == "key_page_up":
        return {"action": "key_page_up"}
    if action == "key_page_down":
        return {"action": "key_page_down"}
    if action == "key_home":
        return {"action": "key_home"}
    if action == "key_end":
        return {"action": "key_end"}
    if action == "key_wait_input":
        return {"action": "key_wait_input", "delay_ms": int(text_segments[1])} if len(text_segments) > 1 else {"action": "none"}
    return {"action": "none"}

def execute_command(parsed_command):
    action = parsed_command["action"]
    if action == "key_type":
        pyautogui.typewrite(parsed_command["text"])
    elif action == "key_press":
        pyautogui.keyDown(parsed_command["key"])
    elif action == "key_release":
        pyautogui.keyUp(parsed_command["key"])
    elif action == "key_tap":
        pyautogui.press(parsed_command["key"])
    elif action == "key_hotkey":
        pyautogui.hotkey(*parsed_command["keys"])
    elif action == "key_backspace":
        pyautogui.press("backspace")
    elif action == "key_delete":
        pyautogui.press("delete")
    elif action == "key_enter":
        pyautogui.press("enter")
    elif action == "key_tab":
        pyautogui.press("tab")
    elif action == "key_space":
        pyautogui.press("space")
    elif action == "key_escape":
        pyautogui.press("esc")
    elif action == "key_arrow_up":
        pyautogui.press("up")
    elif action == "key_arrow_down":
        pyautogui.press("down")
    elif action == "key_arrow_left":
        pyautogui.press("left")
    elif action == "key_arrow_right":
        pyautogui.press("right")
    elif action == "key_page_up":
        pyautogui.press("pageup")
    elif action == "key_page_down":
        pyautogui.press("pagedown")
    elif action == "key_home":
        pyautogui.press("home")
    elif action == "key_end":
        pyautogui.press("end")
    elif action == "key_wait_input":
        time.sleep(parsed_command["delay_ms"] / 1000.0)

def agent_task_handler(agent_response):
    keyboard_config = load_tool_config("agent/tools.keyboard.json")
    parsed_cmd = parse_agent_command(agent_response)
    execute_command(parsed_cmd)
    return parsed_cmd
