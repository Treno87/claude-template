#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#   "openai>=1.0.0",
#   "sounddevice>=0.4.6",
#   "soundfile>=0.12.1",
#   "numpy>=1.24.0",
# ]
# ///
"""
Claude Code Voice Handler - Refactored Main Entry Point

A voice notification system for Claude Code hooks that provides natural text-to-speech
notifications using OpenAI's TTS API with automatic fallback to system TTS.
"""

import argparse
import sys
import json
import os
import time
from pathlib import Path
from datetime import datetime

# Import our modular components
from logger import logger
from state_manager import StateManager
from tts_provider import TTSProvider
from message_generator import MessageGenerator
from deduplication import MessageDeduplicator
from transcript_reader import TranscriptReader
from speech_lock import SpeechLock


class VoiceNotificationHandler:
    """
    Main handler class for voice notifications.
    Orchestrates all modules for processing Claude Code hook events.
    """

    def __init__(self):
        """Initialize the handler with all necessary components."""
        logger.log_info("Initializing VoiceNotificationHandler")

        # Load configurations
        self.script_dir = Path(__file__).parent
        self.config = self.load_config()
        self.sound_mapping = self.load_sound_mapping()

        # Initialize components
        self.state_manager = StateManager()
        self.tts_provider = TTSProvider(config=self.config, logger=logger)
        self.message_generator = MessageGenerator(
            config=self.config,
            sound_mapping=self.sound_mapping,
            state_manager=self.state_manager
        )
        self.deduplicator = MessageDeduplicator()
        self.speech_lock = SpeechLock()  # Add speech lock for inter-process coordination

        # Speech timing control
        self.min_speech_delay = 1.0

        # List of tools that should not trigger voice announcements
        self.silent_tools = []

        # Active voice hooks - Modified for summary-only mode
        self.active_voice_hooks = {
            # "UserPromptSubmit",  # Disabled - no greeting
            # "PreToolUse",  # Disabled - no real-time announcements
            # "PostToolUse",  # Disabled - no real-time announcements
            "Stop",  # Enabled - summary at end of task
            "Notification"  # Enabled - approval request announcements
        }
        
        # Track last PreToolUse announcement time per tool
        self.last_tool_announcement = {}
        self.min_tool_announcement_interval = 3.0  # Minimum seconds between same tool announcements

    def load_config(self):
        """Load voice configuration from config.json."""
        config_file = self.script_dir / "config.json"
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        return {}

    def load_sound_mapping(self):
        """Load sound mapping configuration from sound_mapping.json."""
        mapping_file = self.script_dir / "sound_mapping.json"
        if mapping_file.exists():
            with open(mapping_file, 'r') as f:
                return json.load(f)
        return {}

    def check_speech_delay(self):
        """Check if enough time has passed since last speech."""
        current_time = time.time()
        time_since_last = current_time - self.state_manager.last_speech_time

        if time_since_last < self.min_speech_delay:
            wait_time = self.min_speech_delay - time_since_last
            logger.log_info(f"Delaying speech by {wait_time:.2f}s to prevent overlap")
            time.sleep(wait_time)

        return True

    def speak(self, message, voice=None):
        """
        Main speech output method with inter-process locking.

        Args:
            message (str or dict): Message to speak
            voice (str, optional): Override voice selection
        """
        # Convert message to string if needed
        if isinstance(message, dict):
            message = message.get('message') or message.get('content') or message.get('text') or str(message)

        message = str(message)

        # Check for duplicate announcements
        if self.deduplicator.is_duplicate(message):
            logger.log_debug(f"Skipping duplicate announcement: {message[:50]}...")
            return

        # Acquire speech lock to prevent overlapping announcements
        try:
            with self.speech_lock.acquire(min_spacing=self.min_speech_delay):
                # Speak the message
                self.tts_provider.speak(message, voice)
                
                # Update last speech time in state manager too (for backward compatibility)
                self.state_manager.last_speech_time = time.time()
                self.state_manager.save_state()
        except TimeoutError as e:
            logger.log_warning(f"Could not acquire speech lock: {e}")
            # Skip announcement if we can't get the lock in time

    def should_announce(self, hook_type, tool_name=None):
        """
        Determine if this hook should trigger voice announcements.

        Args:
            hook_type (str): Hook type
            tool_name (str, optional): Tool name for PreToolUse

        Returns:
            bool: True if should announce
        """
        if hook_type not in self.active_voice_hooks:
            return False

        # For PreToolUse, check rate limiting
        if hook_type == "PreToolUse" and tool_name:
            # Check if enough time has passed since last announcement for this tool
            current_time = time.time()
            last_time = self.last_tool_announcement.get(tool_name, 0)
            if current_time - last_time < self.min_tool_announcement_interval:
                return False
            # TodoWrite always announces for completions
            if tool_name == "TodoWrite":
                return True
            # Other tools announce with rate limiting
            return tool_name in self.message_generator.tool_action_phrases

        return True

    def process_user_prompt_submit(self, stdin_data):
        """Process UserPromptSubmit hook."""
        if stdin_data and isinstance(stdin_data, dict):
            session_id = stdin_data.get('session_id')
            transcript_path = stdin_data.get('transcript_path')
            
            if transcript_path:
                logger.log_debug(f"UserPromptSubmit: Found transcript path: {transcript_path}")
                logger.log_debug(f"UserPromptSubmit: Session ID: {session_id}")
                
                # Store current session ID to track if we're in a new conversation
                self.state_manager.current_session_id = session_id
                
                # Reset everything for new conversation to avoid announcing previous session's work
                self.state_manager.reset_task_context()
                # Mark that we want to announce the initial summary
                self.state_manager.initial_summary_announced = False
                self.state_manager.save_state()
                # Return personalized acknowledgment
                return self.message_generator.get_personalized_acknowledgment()
        return None

    def process_pre_tool_use(self, stdin_data, tool_name):
        """Process PreToolUse hook."""
        # Handle TodoWrite completions
        if tool_name == "TodoWrite":
            if stdin_data and isinstance(stdin_data, dict):
                tool_input = stdin_data.get('tool_input', {})
                if tool_input and 'todos' in tool_input:
                    new_todos = tool_input['todos']
                    completed_todos = self.state_manager.detect_completed_todos(new_todos)

                    if completed_todos:
                        # Announce the most recent completion
                        task = completed_todos[-1]
                        return self.message_generator.format_todo_completion(task)
            return None
        
        # Special handling for Read tool to announce filename
        if tool_name == "Read" and stdin_data and isinstance(stdin_data, dict):
            tool_input = stdin_data.get('tool_input', {})
            file_path = tool_input.get('file_path')
            if file_path:
                return self.message_generator.format_read_announcement(file_path)
        
        # Special handling for Edit/Write/MultiEdit tools to announce file type and name
        if tool_name in ["Edit", "Write", "MultiEdit"] and stdin_data and isinstance(stdin_data, dict):
            tool_input = stdin_data.get('tool_input', {})
            file_path = tool_input.get('file_path')
            if file_path:
                return self.message_generator.format_edit_announcement(file_path)
        
        # For other tools, get contextual message from sound mapping
        if tool_name in self.message_generator.tool_action_phrases:
            # Update last announcement time for this tool
            self.last_tool_announcement[tool_name] = time.time()
            
            # Get the action phrase or mapped message
            action_phrase = self.message_generator.tool_action_phrases.get(tool_name)
            if action_phrase:
                return action_phrase
            else:
                return self.message_generator.get_mapped_message("PreToolUse", tool_name)
        
        return None

    def process_post_tool_use(self, stdin_data):
        """Process PostToolUse hook."""
        if not stdin_data or not isinstance(stdin_data, dict):
            return None

        tool_name = stdin_data.get('tool_name')
        session_id = stdin_data.get('session_id')

        # Special handling for TodoWrite completions
        if tool_name == "TodoWrite":
            tool_output = stdin_data.get('tool_output', {})
            if "completed" in str(tool_output).lower():
                return "Task completed"

        # Process transcript messages
        transcript_path = stdin_data.get('transcript_path')
        if not transcript_path:
            return None

        try:
            # Pass session ID to transcript reader for session awareness
            reader = TranscriptReader(transcript_path, session_id=session_id)
            new_messages = reader.get_messages_since_last_check()
            
            # Always try to announce new messages if we have them
            if new_messages:
                # Join all new messages
                combined_message = " ".join(new_messages)
                
                # Check if this is the first response (longer initial summary)
                if not self.state_manager.initial_summary_announced:
                    # First response - allow longer summary
                    if len(combined_message) > 400:
                        combined_message = reader.extract_meaningful_summary(combined_message, 400, 100)
                    self.state_manager.initial_summary_announced = True
                    self.state_manager.save_state()
                    return combined_message
                else:
                    # Subsequent responses - keep them shorter
                    # Check for too recent speech
                    current_time = time.time()
                    if current_time - self.state_manager.last_speech_time < 1.0:
                        return None

                    # CRITICAL: Check for approval requests first
                    for msg in new_messages:
                        if reader.detect_approval_request(msg):
                            # Immediately announce approval needed with user's name
                            return self.message_generator.get_approval_request_message()

                    # Check for todo completion patterns
                    for msg in new_messages:
                        if any(phrase in msg.lower() for phrase in ["completed:", "finished:", "✓", "☑", "done:"]):
                            # Extract task name if possible
                            if "completed:" in msg.lower():
                                task_part = msg.split("completed:", 1)[1].strip()
                                return f"Completed {task_part[:50]}"
                            elif "finished:" in msg.lower():
                                task_part = msg.split("finished:", 1)[1].strip()
                                return f"Finished {task_part[:50]}"
                            elif "☑" in msg or "✓" in msg:
                                import re
                                match = re.search(r'[☑✓]\s*(.+?)(?:\n|$)', msg)
                                if match:
                                    return f"Completed {match.group(1)[:50]}"

                    # Regular intermediate message handling
                    meaningful_messages = [msg for msg in new_messages if len(msg) > 20]
                    if meaningful_messages:
                        claude_message = meaningful_messages[-1]
                        if len(claude_message) > 200:
                            claude_message = reader.extract_meaningful_summary(claude_message, 200, 50)
                        return claude_message

        except Exception as e:
            logger.log_error("Error processing transcript", exception=e)

        return None

    def process_stop(self, stdin_data):
        """Process Stop hook - Generate summary based on git diff analysis."""
        if stdin_data and isinstance(stdin_data, dict):
            cwd = stdin_data.get('cwd')

            # Try git diff analysis first
            git_summary = self._get_git_diff_summary(cwd)
            if git_summary:
                return git_summary

            # Fall back to transcript analysis if no git changes
            transcript_path = stdin_data.get('transcript_path')
            if transcript_path:
                try:
                    reader = TranscriptReader(transcript_path)
                    messages = reader.extract_recent_messages(since_position=0)

                    if messages:
                        bullet_points = self._extract_bullet_points(messages, count=3)
                        summary = self._format_bullet_summary(bullet_points)
                        return summary

                except Exception as e:
                    logger.log_error("Error reading transcript", exception=e)

        # Fall back to personalized task summary
        return self.message_generator.get_personalized_completion()

    def _extract_bullet_points(self, messages, count=3):
        """
        Extract key bullet points from conversation messages.

        Args:
            messages (list): List of message dictionaries with 'text' field
            count (int): Number of bullet points to extract

        Returns:
            list: List of concise bullet point strings
        """
        if not messages:
            return []

        # Collect all message texts
        all_text = []
        for msg in messages[-10:]:  # Look at last 10 messages only
            text = msg.get('text', '')
            if text:
                all_text.append(text)

        if not all_text:
            return []

        combined_text = ' '.join(all_text)

        # Look for existing numbered lists or bullet points in the messages
        import re
        list_pattern = r'(?:^|\n)\s*(?:\d+[\.)]\s+|\*\s+|\-\s+)(.+?)(?=\n|$)'
        list_items = re.findall(list_pattern, combined_text, re.MULTILINE)

        if list_items and len(list_items) >= 2:
            # Clean up and return the found list items
            cleaned_items = []
            for item in list_items[:count]:
                cleaned = item.strip().rstrip('.')
                if len(cleaned) > 10 and len(cleaned) < 100:  # Skip too short or too long items
                    cleaned_items.append(cleaned)

            if len(cleaned_items) >= 2:
                return cleaned_items[:count]

        # If no clear list items found, extract key sentences
        # Split by sentences
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
        sentences = re.split(sentence_pattern, combined_text)

        # Filter for meaningful sentences (action verbs, completions)
        key_phrases = [
            r'\b(created|added|implemented|fixed|updated|modified|refactored|improved)\b',
            r'\b(completed|finished|done with)\b',
            r'\b(analyzed|reviewed|checked|examined|identified)\b',
            r'\b(found|discovered|detected)\b',
            r'\b(configured|set up|enabled|disabled)\b'
        ]

        meaningful_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20 or len(sentence) > 120:
                continue

            # Check if sentence contains key action phrases
            if any(re.search(pattern, sentence, re.IGNORECASE) for pattern in key_phrases):
                # Clean up the sentence
                sentence = re.sub(r'\*\*(.*?)\*\*', r'\1', sentence)  # Remove bold
                sentence = re.sub(r'\*(.*?)\*', r'\1', sentence)      # Remove italic
                sentence = re.sub(r'`(.*?)`', r'\1', sentence)        # Remove code marks
                meaningful_sentences.append(sentence.rstrip('.'))

        # Return top N sentences
        return meaningful_sentences[:count]

    def _format_bullet_summary(self, bullet_points):
        """
        Format bullet points into natural speech.

        Args:
            bullet_points (list): List of bullet point strings

        Returns:
            str: Formatted summary for speech
        """
        if not bullet_points:
            # Use personalized completion instead of plain "Task complete"
            return self.message_generator.get_personalized_completion()

        # Get user nickname and personality
        user_nickname = self.config.get("voice_settings", {}).get("user_nickname")
        personality = self.config.get("voice_settings", {}).get("personality", "butler")

        # Format based on number of points
        if len(bullet_points) == 1:
            summary = f"Task complete. {bullet_points[0]}"
        elif len(bullet_points) == 2:
            summary = f"Task complete. First, {bullet_points[0]}. Second, {bullet_points[1]}"
        else:
            # 3 or more points
            summary = f"Task complete. First, {bullet_points[0]}. Second, {bullet_points[1]}. Third, {bullet_points[2]}"

        # Add personalized ending based on personality
        if personality == "butler" and user_nickname:
            summary += f". Is there anything else I can assist you with, {user_nickname}?"
        elif personality == "butler":
            summary += ". Is there anything else I can assist you with?"

        return summary

    def _get_git_diff_summary(self, cwd):
        """
        Analyze git diff to extract what files were changed and what was done.

        Args:
            cwd (str): Current working directory

        Returns:
            str: Natural language summary of changes, or None if no git repo or no changes
        """
        if not cwd:
            return None

        try:
            import subprocess

            # Check if we're in a git repo
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode != 0:
                logger.log_debug("Not a git repository")
                return None

            # Get list of changed files (staged and unstaged)
            result = subprocess.run(
                ['git', 'diff', 'HEAD', '--name-status'],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0 or not result.stdout.strip():
                logger.log_debug("No git changes detected")
                return None

            # Parse git diff output
            changes = []
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue

                parts = line.split('\t', 1)
                if len(parts) != 2:
                    continue

                status = parts[0].strip()
                filepath = parts[1].strip()

                # Extract filename from path
                filename = os.path.basename(filepath)

                # Determine action
                if status == 'A':
                    action = "Created"
                elif status == 'M':
                    action = "Modified"
                elif status == 'D':
                    action = "Deleted"
                elif status.startswith('R'):
                    action = "Renamed"
                else:
                    action = "Updated"

                changes.append((action, filename, filepath))

            if not changes:
                return None

            # Format summary
            return self._format_git_summary(changes)

        except subprocess.TimeoutExpired:
            logger.log_warning("Git command timed out")
            return None
        except Exception as e:
            logger.log_error("Error analyzing git diff", exception=e)
            return None

    def _format_git_summary(self, changes):
        """
        Format git changes into natural speech summary.

        Args:
            changes (list): List of (action, filename, filepath) tuples

        Returns:
            str: Formatted summary for speech
        """
        if not changes:
            return None

        # Group by action
        created = [f for a, f, _ in changes if a == "Created"]
        modified = [f for a, f, _ in changes if a == "Modified"]
        deleted = [f for a, f, _ in changes if a == "Deleted"]
        renamed = [f for a, f, _ in changes if a == "Renamed"]

        summary_parts = []

        # Limit to 3 items per category for speech clarity
        if created:
            files_list = ", ".join(created[:3])
            if len(created) > 3:
                files_list += f" and {len(created) - 3} more"
            summary_parts.append(f"Created {files_list}")

        if modified:
            files_list = ", ".join(modified[:3])
            if len(modified) > 3:
                files_list += f" and {len(modified) - 3} more"
            summary_parts.append(f"Modified {files_list}")

        if deleted:
            files_list = ", ".join(deleted[:3])
            if len(deleted) > 3:
                files_list += f" and {len(deleted) - 3} more"
            summary_parts.append(f"Deleted {files_list}")

        if renamed:
            files_list = ", ".join(renamed[:3])
            if len(renamed) > 3:
                files_list += f" and {len(renamed) - 3} more"
            summary_parts.append(f"Renamed {files_list}")

        # Combine parts (max 3 for clarity)
        if len(summary_parts) == 0:
            return None
        elif len(summary_parts) == 1:
            summary = f"Task complete. {summary_parts[0]}"
        elif len(summary_parts) == 2:
            summary = f"Task complete. {summary_parts[0]}. {summary_parts[1]}"
        else:
            summary = f"Task complete. {summary_parts[0]}. {summary_parts[1]}. {summary_parts[2]}"

        # Add personalized ending
        user_nickname = self.config.get("voice_settings", {}).get("user_nickname")
        personality = self.config.get("voice_settings", {}).get("personality", "butler")

        if personality == "butler" and user_nickname:
            summary += f". Is there anything else I can assist you with, {user_nickname}?"
        elif personality == "butler":
            summary += ". Is there anything else I can assist you with?"

        return summary

    def process_notification(self, stdin_data):
        """Process Notification hook for permission requests and waiting for input."""
        logger.log_info("Processing Notification hook", stdin_data=stdin_data)
        
        # The Notification hook fires when:
        # 1. "Claude needs your permission to use a tool" (file edit permissions)
        # 2. "Claude is waiting for your input"
        
        # Extract the message to determine what needs approval
        message = ""
        if stdin_data and isinstance(stdin_data, dict):
            message = stdin_data.get('message', '')
        
        # Parse the permission request message
        if "permission to use" in message:
            # Extract the tool name from "Claude needs your permission to use [ToolName]"
            parts = message.split("permission to use")
            if len(parts) > 1:
                tool_name = parts[1].strip()
                return self.message_generator.get_approval_request_message(tool_name=tool_name)
        
        # Default to generic approval message
        return self.message_generator.get_approval_request_message()


def read_stdin_data():
    """Read and parse stdin data from Claude Code."""
    stdin_data = None
    stdin_text = None

    if not sys.stdin.isatty():
        try:
            stdin_input = sys.stdin.read()
            if stdin_input:
                logger.log_debug(f"Raw stdin received",
                               length=len(stdin_input),
                               first_chars=stdin_input[:200])
                try:
                    stdin_data = json.loads(stdin_input)
                    logger.log_stdin_data(stdin_data)
                except json.JSONDecodeError:
                    # If it's not JSON, treat it as plain text
                    stdin_text = stdin_input.strip()
                    logger.log_stdin_data(stdin_text)
        except Exception as e:
            logger.log_error("Error reading stdin", exception=e)
    else:
        logger.log_debug("No stdin data (terminal mode)")

    return stdin_data, stdin_text


def main():
    """Main entry point for voice handler."""
    parser = argparse.ArgumentParser(description="Claude Code Voice Handler - Natural TTS for hook events")
    parser.add_argument("--voice", help="Voice to use (overrides config)")
    parser.add_argument("--message", help="Message to speak (overrides automatic)")
    parser.add_argument("--hook", help="Hook type")
    parser.add_argument("--tool", help="Tool name")
    parser.add_argument("--file", help="File path")
    parser.add_argument("--command", help="Command being run")
    parser.add_argument("--query", help="Search query")

    args = parser.parse_args()

    # Log invocation
    logger.log_info("Voice handler invoked",
                   hook=args.hook,
                   tool=args.tool,
                   file=args.file,
                   command=args.command,
                   query=args.query,
                   has_message=bool(args.message))

    # Initialize handler
    handler = VoiceNotificationHandler()

    # Read stdin data
    stdin_data, stdin_text = read_stdin_data()

    # Log the hook event
    logger.log_hook_event(
        args.hook,
        tool=args.tool,
        stdin_data=stdin_data or stdin_text,
        file=args.file,
        command=args.command,
        query=args.query
    )

    # Determine tool name
    tool_name = args.tool
    if stdin_data and isinstance(stdin_data, dict):
        tool_name = stdin_data.get('tool_name') or tool_name

    # Check if this hook should trigger voice announcements
    if not handler.should_announce(args.hook, tool_name):
        logger.log_info(f"Hook {args.hook} logged only (no voice announcement)")
        sys.exit(0)

    # Update context for voice-enabled hooks
    if args.hook:
        handler.state_manager.update_context(
            args.hook,
            tool_name=tool_name,
            file_path=args.file,
            command=args.command,
            query=args.query
        )

    # Process hook-specific logic
    message = None

    if args.hook == "UserPromptSubmit":
        message = handler.process_user_prompt_submit(stdin_data)

    elif args.hook == "PreToolUse":
        message = handler.process_pre_tool_use(stdin_data, tool_name)
        if not message:
            sys.exit(0)  # Exit if no todo completions

    elif args.hook == "PostToolUse":
        message = handler.process_post_tool_use(stdin_data)
        if not message:
            sys.exit(0)  # Exit if no message to speak

    elif args.hook == "Stop":
        message = handler.process_stop(stdin_data)
    
    elif args.hook == "Notification":
        message = handler.process_notification(stdin_data)

    # Fall back to command line argument
    if not message and args.message:
        message = args.message

    # Generate contextual message for other hooks
    if not message and args.hook and args.hook not in ["Stop", "PostToolUse"]:
        message = handler.message_generator.get_contextual_message(
            args.hook,
            tool_name=tool_name,
            file_path=args.file,
            command=args.command,
            query=args.query
        )

    # Default messages for specific hooks
    if not message:
        if args.hook == "Stop":
            message = "Done"
        elif args.hook in ["PostToolUse", "PreToolUse"]:
            sys.exit(0)  # Exit silently for these hooks without messages

    # Check if tool should be silent
    if tool_name and tool_name in handler.silent_tools:
        sys.exit(0)

    # Speak the message if we have one
    if message:
        logger.log_message_flow("Speaking", message)
        handler.speak(message, voice=args.voice)


if __name__ == "__main__":
    main()
# Test change
