# 如何获取 API Key

CitizenAgent 需要 API Key 才能调用 AI 模型。别怕，5 分钟搞定，**花 10 块钱能用好几个月**。

---

## 推荐方案（总花费 ≈ ¥10，够用很久）

| 用途 |    平台    |       模型        |        价格        |
|------|------------|-------------------|--------------------|
| 聊天 |  DeepSeek  |   deepseek-chat   | ¥1 / 100万 token    |
| 看图 | 阿里云百炼 |   qwen-vl-plus    | ¥1.5 / 100万 token  |
| 生图 | 阿里云百炼 | wanx2.1-t2i-turbo | ¥0.12 / 张          |

---


## 第一步：获取 DeepSeek API Key（聊天）
1. 打开 https://platform.deepseek.com
2. 点右上角「登录/注册」（支持微信扫码）
3. 登录后点左侧菜单「API Keys」
4. 点「创建 API Key」→ 起个名字（比如 `CitizenAgent`）→ 点创建
5. 复制那一串 `sk-` 开头的 Key（**只显示一次，赶紧保存！**）

> 💰 充值建议：先充 10 块钱，够你用几个月。点左侧「充值」→ 支付宝/微信扫码。

---

## 第二步：获取阿里云百炼 API Key（看图 + 生图）
1. 打开 https://dashscope.aliyun.com
2. 点右上角登录（支付宝/淘宝扫码）
3. 登录后点右上角头像 → 「API-KEY 管理」
4. 点「创建 API-KEY」→ 复制保存

> 💰 百炼默认有免费额度（新用户 100 万 token），短期内不充钱也能用。

---

## 第三步：填入配置
打开 `C:\Users\你的用户名\CitizenAgentConfig.json`，找到对应的位置：

```json
"models": {
    "main": {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "api_key": "把这里的文字替换成你的 DeepSeek Key"
    },
    "vision": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-vl-plus",
        "api_key": "把这里的文字替换成你的百炼 Key"
    },
    "image_gen": {
        "base_url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis",
        "model": "wanx2.1-t2i-turbo",
        "api_key": "把这里的文字替换成你的百炼 Key（和上面同一个）"
    }
}
```

> ⚠️ 只需要填三个 `api_key` 的值，其他的不用动。

---

## 省钱方案（只要聊天，不要看图/生图）
如果你只想聊天，只配 DeepSeek 的 Key 就行：

```json
"models": {
    "main": {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "api_key": "你的 DeepSeek Key"
    }
}
```

把 `vision` 和 `image_gen` 整段删掉。启动时看图/生图功能自动禁用。

---

## 常见问题

**Q: API Key 安全吗？会扣很多钱吗？**
A: Key 只存在你自己电脑上。DeepSeek 和阿里云都支持**设置消费限额**（后台 → 预算管理），建议设个 50 块上限，防止意外。

**Q: DeepSeek 提示模型不可用？**
A: 去 platform.deepseek.com → 充值（最少 1 元）。DeepSeek 余额为 0 时 API 不可用。

**Q: 能不能用其他模型？**
A: 能。任何兼容 OpenAI API 格式的模型都支持。把 `base_url`、`model`、`api_key` 换成对应厂商的就行。
