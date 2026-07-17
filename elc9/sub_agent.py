"""子代理系统 — 从原始 Elc9_Code.py 拆分。"""
import json, threading, requests
from .config import load_config

class SubAgentManager:
    def __init__(self):
        self.result = None; self.status = "idle"; self.status_text = ""
    def start(self, sub_task, history_messages):
        if self.status == "running": return False, "子代理正在运行"
        self.result = None; self.status = "running"
        self.status_text = "子代理处理中: " + sub_task[:40] + "..."
        threading.Thread(target=self._worker, args=(sub_task, history_messages), daemon=True).start()
        return True, "子代理已启动"
    def _worker(self, sub_task, history_messages):
        try:
            config = load_config()
            main_cfg = config.get("models",{}).get("main",{})
            api_key = main_cfg.get("api_key","") or config.get("api_key","")
            base_url = main_cfg.get("base_url","") or config.get("base_url","https://api.deepseek.com")
            model = main_cfg.get("model","") or config.get("model","deepseek-chat")
            tools = config.get("tools",None)
            if not api_key: self.result = "[-] 子代理错误: 未配置 API Key"; self.status = "error"; return
            sub_messages = []
            sub_messages.append({"role":"system","content":"你是一个子代理（Sub-Agent），正在协助主代理处理一个子任务。请专注于完成分配给你的子任务。"})
            if history_messages:
                history_text = json.dumps(history_messages, ensure_ascii=False)
                sub_messages.append({"role":"user","content":"【主对话历史背景】\n" + history_text})
            sub_messages.append({"role":"user","content":sub_task})
            payload = {"model":model,"messages":sub_messages,"stream":False}
            if tools: payload["tools"] = tools
            headers = {"Authorization":f"Bearer {api_key}","Content-Type":"application/json"}
            self.status_text = "子代理请求 API..."
            response = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=300)
            if response.status_code != 200: self.result = f"[-] 子代理请求失败: {response.status_code}"; self.status = "error"; return
            resp = response.json()
            msg = resp["choices"][0]["message"]
            content = msg.get("content","")
            tool_calls = msg.get("tool_calls",None)
            if tool_calls:
                sub_messages.append(msg); limit = 10; count = 0
                while tool_calls and count < limit:
                    count += 1
                    for tc in tool_calls:
                        func_name = tc["function"]["name"]
                        if func_name in ("run_command","play_music","open_image"):
                            from .tools import execute_tool_call
                            res = execute_tool_call(tc, config)
                        else: res = json.dumps({"status":"failed","error_code":"unknown_tool","error_reason":"未知工具: "+func_name,"output":""},ensure_ascii=False)
                        sub_messages.append({"role":"tool","tool_call_id":tc["id"],"content":res})
                    payload["messages"] = sub_messages
                    r2 = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=300)
                    if r2.status_code != 200: break
                    r2d = r2.json(); msg = r2d["choices"][0]["message"]
                    content = msg.get("content",""); tool_calls = msg.get("tool_calls",None)
            self.result = content or "(子代理未返回结果)"; self.status = "done"
        except Exception as e: self.result = "[-] 子代理异常: " + str(e); self.status = "error"
    def get_result_and_reset(self):
        res = self.result; self.result = None; self.status = "idle"; return res
