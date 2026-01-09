#!/usr/bin/env python3
"""Test script for voice handler"""

import json
import sys
from voice_handler import VoiceNotificationHandler

# Create handler
handler = VoiceNotificationHandler()

# Simulate stdin data
stdin_data = {
    'cwd': r'c:\Users\Ken\.claude\hooks\voice_notifications',
    'session_id': 'test-123',
    'transcript_path': ''
}

# Process stop
print("Testing Stop hook with git diff analysis...")
result = handler.process_stop(stdin_data)
print('Summary:', result)
