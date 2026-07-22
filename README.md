# CitizenAgent

一个运行在终端里的 AI 助手。

[![Python](https://img.shields.io/badge/Python-3.8+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue)](LICENSE)

---

## 它能做什么

- 日常对话和问答（DeepSeek）
- 识别图片内容（通义千问 VL）
- 生成图片（通义万相）
- 执行终端命令
- 多个任务同时并行处理
- 跨工作目录切换历史对话

---

## 快速开始

### 安装

```bash
pip install requests
```

可选：`pip install prompt_toolkit`（更好看的输入框）


手机Termux安装指令
```
bash -c "$(curl -fsSL https://raw.githubusercontent.com/ElarineNycanis/Citizen-Agent/main/install.sh)"
```

### 配置

1. 获取 [DeepSeek API Key](https://platform.deepseek.com)（聊天用）
2. 获取 [阿里云百炼 API Key](https://dashscope.aliyun.com)（看图、生图用，可跳过）
3. 复制配置模板并填入 Key：

```bash
copy config.example.json "%USERPROFILE%\CitizenAgentConfig.json"
notepad "%USERPROFILE%\CitizenAgentConfig.json"
```

### 启动

```bash
Python CitizenAgent.py
```

或双击 `CitizenAgent.bat`。

> 详细安装说明见 [安装指导/](安装指导/)

---

## 使用示例

```
> 帮我解释一下什么是机器学习

林清墨: 机器学习是...

> C:\Users\admin\Desktop\照片.jpg 这张照片里有什么？
[视觉模型自动分析...]
林清墨: 照片里有一只猫趴在窗台上...

> 帮我把桌面所有 .txt 文件合并成一个
[*] 已执行

> 同时帮我搜杭州天气、查比特币价格、讲个笑话
[并1] 杭州今天 28°C 晴
[并2] BTC 当前 ¥523,000
[并3] 为什么程序员总是分不清万圣节和圣诞节？
    因为 Oct 31 == Dec 25
```

---

## 命令

| 命令 | 说明 |
|------|------|
| `/help` | 查看帮助 |
| `/history` | 历史对话 |
| `/new` | 新建对话 |
| `/delete` | 删除对话 |
| `/create_picture <描述>` | 生成图片 |
| `/sub <任务>` | 后台子代理 |
| `/quit` | 保存退出 |

---

## 支持的模型

默认使用 DeepSeek（聊天）、通义千问 VL（看图）、通义万相（生图）。

`config.json` 中的模型可替换为任意兼容 OpenAI API 的服务。

---

## 目录

```
├── CitizenAgent.py
├── CitizenAgent.bat
├── config.example.json
├── elc9/
│   ├── main.py
│   ├── config.py
│   ├── tools.py
│   ├── api.py
│   ├── vision.py
│   ├── conversation.py
│   ├── ui.py
│   ├── sub_agent.py
│   └── input_area.py
├── conversations/
└── 安装指导/
```

---

## License

Apache-2.0

---





# English

A terminal-based AI assistant.

[![Python](https://img.shields.io/badge/Python-3.8+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue)](LICENSE)

---

## What it does

- Daily conversation and Q&A (DeepSeek)
- Image content recognition (Qwen-VL)
- Image generation (Wanx)
- Terminal command execution
- Parallel multi-task processing
- Cross-workspace conversation switching

---

## Quick Start

### Install

```bash
pip install requests
```

Optional: `pip install prompt_toolkit`


Termux installation commands for mobile devices
```
bash -c "$(curl -fsSL https://raw.githubusercontent.com/ElarineNycanis/Citizen-Agent/main/install.sh)"
```


### Configure

1. Get a [DeepSeek API Key](https://platform.deepseek.com)
2. Get an [Alibaba Bailian API Key](https://dashscope.aliyun.com) (for vision & image-gen, optional)
3. Copy the config template and fill in your keys:

```bash
copy config.example.json "%USERPROFILE%\CitizenAgentConfig.json"
notepad "%USERPROFILE%\CitizenAgentConfig.json"
```

### Launch

```bash
Python CitizenAgent.py
```

Or double-click `CitizenAgent.bat`.

---

## Commands

| Command | Description |
|------|------|
| `/help` | Show help |
| `/history` | Conversation history |
| `/new` | New conversation |
| `/delete` | Delete conversations |
| `/create_picture <desc>` | Generate image |
| `/sub <task>` | Background sub-agent |
| `/quit` | Save and exit |

---

## Supported Models

Default: DeepSeek (chat), Qwen-VL (vision), Wanx (image-gen). Any OpenAI-compatible API can be swapped in via `config.json`.

---

## License

Apache-2.0

---

# Français

Un assistant IA dans votre terminal.

[![Python](https://img.shields.io/badge/Python-3.8+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue)](LICENSE)

---

## Fonctionnalités

- Conversation et questions-réponses (DeepSeek)
- Reconnaissance d'images (Qwen-VL)
- Génération d'images (Wanx)
- Exécution de commandes terminal
- Traitement parallèle multi-tâches
- Basculement de conversations entre espaces de travail

---





## Démarrage rapide

### Installation

```bash
pip install requests
```

Optionnel : `pip install prompt_toolkit`


### Configuration

1. Obtenez une [clé API DeepSeek](https://platform.deepseek.com)
2. Obtenez une [clé API Alibaba Bailian](https://dashscope.aliyun.com) (optionnel)
3. Copiez le modèle de configuration :

```bash
copy config.example.json "%USERPROFILE%\CitizenAgentConfig.json"
notepad "%USERPROFILE%\CitizenAgentConfig.json"
```

### Lancement

```bash
Python CitizenAgent.py
```

Ou double-cliquez sur `CitizenAgent.bat`.

---

## Commandes

| Commande | Description |
|------|------|
| `/help` | Aide |
| `/history` | Historique |
| `/new` | Nouvelle conversation |
| `/delete` | Supprimer |
| `/create_picture <desc>` | Générer une image |
| `/sub <tâche>` | Sous-agent |
| `/quit` | Sauver et quitter |

---

## Modèles supportés

Par défaut : DeepSeek (chat), Qwen-VL (vision), Wanx (images). Tout API compatible OpenAI peut être utilisée.

---

## Licence

Apache-2.0

---





# Русский

ИИ-ассистент в терминале.

[![Python](https://img.shields.io/badge/Python-3.8+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue)](LICENSE)

---

## Возможности

- Диалоги и ответы на вопросы (DeepSeek)
- Распознавание изображений (Qwen-VL)
- Генерация изображений (Wanx)
- Выполнение команд терминала
- Параллельная обработка задач
- Переключение диалогов между рабочими каталогами

---

## Быстрый старт

### Установка

```bash
pip install requests
```

Опционально: `pip install prompt_toolkit`


Команда для установки Termux на телефоне
```
bash -c "$(curl -fsSL https://raw.githubusercontent.com/ElarineNycanis/Citizen-Agent/main/install.sh)"
```
### Настройка

1. Получите [API-ключ DeepSeek](https://platform.deepseek.com)
2. Получите [API-ключ Alibaba Bailian](https://dashscope.aliyun.com) (опционально)
3. Скопируйте шаблон конфигурации:

```bash
copy config.example.json "%USERPROFILE%\CitizenAgentConfig.json"
notepad "%USERPROFILE%\CitizenAgentConfig.json"
```

### Запуск

```bash
Python CitizenAgent.py
```

Или дважды щёлкните `CitizenAgent.bat`.

---

## Команды

| Команда | Описание |
|------|------|
| `/help` | Помощь |
| `/history` | История |
| `/new` | Новый диалог |
| `/delete` | Удалить |
| `/create_picture <опис>` | Создать изображение |
| `/sub <задача>` | Фоновый под-агент |
| `/quit` | Сохранить и выйти |

---

## Поддерживаемые модели

По умолчанию: DeepSeek (чат), Qwen-VL (зрение), Wanx (изображения). Любой API совместимый с OpenAI можно подключить через `config.json`.

---

## Лицензия

Apache-2.0

---

# Español

Un asistente IA en tu terminal.

[![Python](https://img.shields.io/badge/Python-3.8+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue)](LICENSE)

---

## Qué hace

- Conversación diaria y preguntas (DeepSeek)
- Reconocimiento de imágenes (Qwen-VL)
- Generación de imágenes (Wanx)
- Ejecución de comandos en terminal
- Procesamiento paralelo de múltiples tareas
- Cambio de conversaciones entre espacios de trabajo

---





## Inicio rápido

### Instalación

```bash
pip install requests
```

Opcional: `pip install prompt_toolkit`

### Configuración

1. Obtén una [API Key de DeepSeek](https://platform.deepseek.com)
2. Obtén una [API Key de Alibaba Bailian](https://dashscope.aliyun.com) (opcional)
3. Copia la plantilla de configuración:

```bash
copy config.example.json "%USERPROFILE%\CitizenAgentConfig.json"
notepad "%USERPROFILE%\CitizenAgentConfig.json"
```

### Iniciar

```bash
Python CitizenAgent.py
```

O haz doble clic en `CitizenAgent.bat`.

---

## Comandos

| Comando | Descripción |
|------|------|
| `/help` | Ayuda |
| `/history` | Historial |
| `/new` | Nueva conversación |
| `/delete` | Eliminar |
| `/create_picture <desc>` | Generar imagen |
| `/sub <tarea>` | Sub-agente en segundo plano |
| `/quit` | Guardar y salir |

---

## Modelos compatibles

Por defecto: DeepSeek (chat), Qwen-VL (visión), Wanx (imágenes). Cualquier API compatible con OpenAI puede usarse modificando `config.json`.

---

## Licencia

Apache-2.0
