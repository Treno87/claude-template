#!/usr/bin/env python3
"""Voice notification script for Windows."""
import sys
import platform


def notify_voice(message):
    """Speak a message using platform-specific TTS.

    Args:
        message: Text to speak
    """
    system = platform.system()

    if system == "Windows":
        # Use Windows SAPI (no dependencies needed)
        import win32com.client
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Rate = 1  # Normal speed
        speaker.Volume = 100  # Maximum volume
        speaker.Speak(message)
    else:
        # For macOS/Linux, try pyttsx3
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.setProperty('volume', 1.0)
            engine.say(message)
            engine.runAndWait()
        except ImportError:
            print(f"[Voice notification not available] {message}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python notify_voice.py <message>")
        sys.exit(1)

    message = " ".join(sys.argv[1:])
    notify_voice(message)
