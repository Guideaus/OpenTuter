import questionary
import json

apiin = {
    "OpenAI": "https://api.openai.com/v1",
    "Azure OpenAI": "https://{resource}.openai.azure.com/openai/deployments/{deployment}/chat/completions",
    "Anthropic Claude": "https://api.anthropic.com",
    "Google Gemini": "https://generativelanguage.googleapis.com",
    "Alibaba Qwen": "https://dashscope.aliyuncs.com/api/v1",
    "Baidu ERNIE": "https://qianfan.baidubce.com/v2",
    "Zhipu GLM": "https://open.bigmodel.cn/api/paas/v4",
    "ByteDance Doubao": "https://ark.cn-beijing.volces.com/api/v3",
    "Meta Llama (Ollama)": "http://localhost:11434/v1",
    "Local Ollama Model": "http://localhost:11434/v1",
    "Custom API Endpoint": ""
}

options = list(apiin.keys())

def write_cfg(key,val):
    with open("config.json","r",encoding="utf-8") as f:
        d=json.load(f)
    d["llm"][key]=val
    with open("config.json","w",encoding="utf-8") as f:
        json.dump(d,f,indent=4,ensure_ascii=False)

def main():
    input("welcome to opentuter!(Press Enter to continue)")
    input("Now let's finish the basic setup!(Press Enter to continue)")

    selected_vendor=questionary.select("Please choose your API provider",choices=options).ask()
    baserul=apiin[selected_vendor]
    if selected_vendor=="Custom API Endpoint":
        baserul=input("Please input your custom base url:")
    write_cfg("base_url",baserul)

    api = input("Please enter your API key:")
    write_cfg("api_key",api)

    model = input("please enter your AI model:")
    write_cfg("model", model)