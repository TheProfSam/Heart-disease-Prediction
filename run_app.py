"""Convenience script to launch the CardioSense Streamlit Web Application."""

import subprocess
import sys

if __name__ == "__main__":
    print("Starting CardioSense AI Web Application...")
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port=8501"]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nCardioSense AI stopped.")
