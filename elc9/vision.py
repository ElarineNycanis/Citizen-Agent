"""多模型协作 - 视觉模型路由"""
import re, os, base64, requests

IMAGE_EXTS = {'.jpg','.jpeg','.png','.gif','.bmp','.webp','.ico','.tiff','.tif'}

def find_image_paths(text):
    """从用户输入中提取存在的图片文件路径"""
    paths = []
    pattern = r'[A-Za-z]:[\\/][^\s"\'<>]*?\.(?:jpg|jpeg|png|gif|bmp|webp|ico|tiff|tif)'
    for m in re.finditer(pattern, text, re.IGNORECASE):
        raw = m.group().strip().rstrip('"\'.,;)')
        if os.path.exists(raw) and os.path.isfile(raw):
            paths.append(raw)
    return paths

def call_vision_model(image_paths, user_text, config):
    """调用视觉模型分析图片，返回文字描述"""
    models_cfg = config.get("models", {})
    vision_cfg = models_cfg.get("vision", {})
    if not vision_cfg:
        return None

    base_url = vision_cfg.get("base_url", "").rstrip("/")
    model = vision_cfg.get("model", "qwen-vl-plus")
    api_key = vision_cfg.get("api_key", "")
    if not api_key or not base_url:
        return None

    # 构建多模态 content 数组
    prompt = f"用户发了一条消息：「{user_text}」。请详细查看图片内容，用中文描述你看到的关键信息（文字、错误提示、界面元素等），以便一个纯文本AI模型能理解图片内容并回答用户。"
    content = [{"type": "text", "text": prompt}]

    for path in image_paths[:5]:  # 最多5张
        try:
            with open(path, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
            ext = os.path.splitext(path)[1].lower().lstrip('.')
            if ext == 'jpg': ext = 'jpeg'
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/{ext};base64,{b64}"}
            })
        except Exception as e:
            content.append({"type": "text", "text": f"(无法读取图片 {path}: {e})"})

    endpoint = f"{base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "user", "content": content}], "max_tokens": 2000}

    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
    except:
        pass
    return None
