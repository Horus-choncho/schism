#!/usr/bin/env python3
import sys
import re
import tokenize

# Blocklist of highly dangerous keywords, system hooks, and obfuscation patterns
BANNED_PATTERNS = [
    r"sudo\b",                  # Privilege escalation
    r"os\.system\b",            # Arbitrary shell execution
    r"subprocess\.Popen\b",     # Raw process spawning
    r"subprocess\.run\b",       # Raw process spawning
    r"__import__\(['\"]os['\"]\)", # Obfuscated imports
    r"eval\(",                  # Dynamic code execution
    r"(?<!\.)\bexec\(",         # Precise built-in exec function detection (ignores .exec())
    r"base64\.b64decode",       # Payload obfuscation prevention
    r"requests\.(get|post)",    # Prevent unauthorized exfiltration of your data
    r"urllib\.request",         # Alternative network exfiltration vectors
    r"socket\.",                # Raw TCP/UDP socket hooks
    r"chmod\b",                 # Unauthorized file permission adjustments
]

def scan_file(filepath):
    print(f"🔍 [Security Guard] Auditing file: {filepath}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Regex check for hard blocklists
    for pattern in BANNED_PATTERNS:
        match = re.search(pattern, content)
        if match:
            print(f"❌ [CRITICAL SECURITY ALERT] Banned execution sequence detected: '{match.group()}'")
            return False

    # 2. Tokenizer check to look for obfuscated unicode injection attacks
    try:
        with open(filepath, "rb") as f:
            tokens = list(tokenize.tokenize(f.readline))
            for token in tokens:
                # Check for bidirectional unicode characters (used to trick human eyes in code)
                if token.type == tokenize.COMMENT or token.type == tokenize.STRING:
                    if any(c in token.string for c in ["\u202a", "\u202b", "\u202c", "\u202d", "\u202e"]):
                        print("❌ [CRITICAL SECURITY ALERT] Hidden bidirectional unicode injection detected in string/comment!")
                        return False
    except Exception as e:
        print(f"⚠️ [Warning] Parsing token safety failed: {e}")
        return False

    print("✅ [Security Guard] File cleared. No structural anomalies or backdoor triggers found.")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python secure_guard.py <path_to_source_file>")
        sys.exit(1)
        
    success = scan_file(sys.argv[1])
    sys.exit(0 if success else 1)
