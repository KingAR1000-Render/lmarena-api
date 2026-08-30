import os
import sys
import subprocess
import gradio as gr

# Fetch Camoufox browser binaries if not present
try:
    subprocess.run([sys.executable, "-m", "camoufox", "fetch"], check=False)
except Exception:
    pass

from src.main import app as fastapi_app

# Gradio Info UI
with gr.Blocks(title="LMArenaBridge API Server", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🌉 LMArenaBridge API Server")
    gr.Markdown(
        """
        * **API Base URL:** `http://localhost:8000/api/v1` (or your cloud URL)
        * **API Key:** Configured in `config.json` (e.g. `sk-lmab-...`)
        * **Endpoint:** `POST /api/v1/chat/completions`
        * **Model Listesi:** `GET /api/v1/models`
        * **Dashboard:** [Yönetim Paneli](/dashboard)
        """
    )

# Mount Gradio app into FastAPI
app = gr.mount_gradio_app(fastapi_app, demo, path="/ui")

# For local testing or direct execution
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
