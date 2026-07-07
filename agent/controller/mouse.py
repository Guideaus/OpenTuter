import json
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
    if text_segments[0] == "press":
        return {"action": "press", "target_key": text_segments[1]}
    if text_segments[0] == "click":
        return {"action": "click", "pos_x": int(text_segments[1]), "pos_y": int(text_segments[2])}
    return {"action": "none"}

def execute_command(parsed_command):
    if parsed_command["action"] == "press":
        pyautogui.press(parsed_command["target_key"])
    elif parsed_command["action"] == "click":
        pyautogui.click(parsed_command["pos_x"], parsed_command["pos_y"])

def agent_task_handler(agent_response):
    mouse_config = load_tool_config("agent/tools.mouse.json")
    keyboard_config = load_tool_config("agent/tools.keyboard.json")
    parsed_cmd = parse_agent_command(agent_response)
    execute_command(parsed_cmd)
    return parsed_cmd