# 🌿 Willow

Willow is an offline-first modular AI assistant designed for automation, intelligent prompt chaining, and integration with OpenAI, Gemini, and future LLM agents.

---

## ✨ Features

- 🧠 LLM fallback with Gemini & OpenAI
- 🪢 Prompt chaining via function maps
- 🖥️ Simple GUI interface (Tkinter)
- 🧩 Modular architecture (`core/`, `config/`, `prompts/`)
- 📡 Local + online modes (WIP)
- 🔐 Secrets handled locally (`config/keys.py` excluded from Git)

---

## 🧰 Setup

```bash
git clone https://github.com/Luka-ws-bored/Willow.git
cd Willow
pip install -r requirements.txt
```

Place your API keys in `config/keys.py`:

```python
openai_key = "sk-..."
gemini_key = "AIza..."
```

Then run:

```bash
python main.py
```

---

## 🧱 Project Structure

```
Willow/
├── main.py
├── core/
│   ├── agent.py
│   ├── tasks.py
│   └── speech.py
├── config/
│   ├── keys.py  # (excluded)
│   └── settings.json
├── prompts/
│   └── default.md
├── docs/
│   └── Willow_Upgrade_Plan.md
├── README.md
├── CHANGELOG.md
├── requirements.txt
└── .gitignore
```

---

## 👤 Author

**BoredPerson**
With guidance from Meliodas

---

> "Let the trees speak. Let the agents rise." 🌲
