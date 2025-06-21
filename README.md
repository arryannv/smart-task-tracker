# 📋 Smart Task Tracker

Smart Task Tracker is a full-stack Flask web application designed to help users manage their tasks efficiently. It includes features like task creation, completion tracking, due date filtering, category labeling, email reminders, and an integrated AI assistant powered by a local LLM using Ollama.

## 🚀 Features

- ✅ Add, edit, complete, and delete tasks
- 🗂️ Categorize tasks by Work, Personal, Study, etc.
- 🏷️ Use tags, priorities, and due dates for better task sorting
- 🔔 Email reminders for tasks due today
- 🧠 AI Assistant (via Ollama with LLaMA3) for natural language support
- 🎤 Voice-to-text input for adding tasks
- 🌙 Theme toggle (dark/light mode)
- 📊 Dashboard with task statistics

## 📦 Tech Stack

- **Backend**: Python, Flask, SQLite
- **Frontend**: HTML, CSS (Poppins font), JavaScript
- **AI**: Local LLaMA3 model via Ollama + OpenAI-compatible API
- **Scheduler**: APScheduler (for periodic email reminders)
- **Email**: SMTP (Gmail)
