#!/usr/bin/env python3
import subprocess
import sys
import os

def install_requirements():
    """Install required packages."""
    print("📦 Installing requirements...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"])

def check_ollama():
    """Check if Ollama is running."""
    import requests
    try:
        requests.get("http://localhost:11434/api/tags", timeout=5)
        print("✅ Ollama is running")
        return True
    except:
        print("❌ Ollama is not running. Please start Ollama first:")
        print("   ollama serve")
        print("\nAlso pull required models:")
        print("   ollama pull all-minilm")
        print("   ollama pull deepseek-r1:1.5b")
        return False

def main():
    print("="*60)
    print(" AI Assistant")
    print("="*60)
    
    # Check Ollama
    if not check_ollama():
        sys.exit(1)
    
    # Create necessary directories
    os.makedirs("data/videos", exist_ok=True)
    os.makedirs("data/audios", exist_ok=True)
    os.makedirs("data/jsons", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    
    # Start Flask server
    print("\n🚀 Starting web server...")
    print("📍 Access the website at: http://localhost:5000")
    print("Press Ctrl+C to stop the server\n")
    
    os.chdir("backend")
    subprocess.run([sys.executable, "app.py"])

if __name__ == "__main__":
    main()