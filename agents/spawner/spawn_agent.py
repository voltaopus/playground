#!/usr/bin/env python3
"""
Agent Spawner - Spawns AI agents in parallel tmux sessions.

Supports: Claude Code, Gemini CLI, Codex CLI
Platform: Linux (tmux), macOS (Terminal.app), Windows (cmd)
"""

import subprocess
import sys
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal

REPO_ROOT = Path(__file__).parent.parent.parent
RUNS_DIR = REPO_ROOT / "arena" / "runs"
COOKBOOKS_DIR = Path(__file__).parent.parent / "cookbooks"

AgentType = Literal["claude", "gemini", "codex"]


class AgentSpawner:
    """Spawns and manages AI agent sessions."""

    # Default models for each agent
    MODELS = {
        "claude": {
            "default": "sonnet",
            "fast": "haiku",
            "heavy": "opus"
        },
        "gemini": {
            "default": "gemini-2.5-pro",
            "fast": "gemini-2.5-flash",
            "heavy": "gemini-2.5-pro"
        },
        "codex": {
            "default": "gpt-4.1",
            "fast": "gpt-4.1-mini",
            "heavy": "gpt-4.1"
        }
    }

    # CLI commands for each agent
    COMMANDS = {
        "claude": 'claude --dangerously-skip-permissions "{prompt}"',
        "gemini": 'gemini --model {model} -y "{prompt}"',
        "codex": 'codex -m {model} --dangerously-bypass-approvals-and-sandbox "{prompt}"'
    }

    def __init__(self):
        self.platform = self._detect_platform()

    def _detect_platform(self) -> str:
        """Detect the current platform."""
        if sys.platform == "darwin":
            return "macos"
        elif sys.platform == "win32":
            return "windows"
        else:
            return "linux"

    def spawn(
        self,
        agent_type: AgentType,
        prompt: str,
        session_name: Optional[str] = None,
        model_tier: str = "default",
        working_dir: Optional[str] = None,
        challenge_id: Optional[str] = None,
        output_file: Optional[str] = None
    ) -> dict:
        """
        Spawn an agent in a new session.

        Args:
            agent_type: Type of agent (claude, gemini, codex)
            prompt: The prompt/task for the agent
            session_name: Optional name for the session
            model_tier: Model tier (default, fast, heavy)
            working_dir: Working directory for the agent
            challenge_id: Optional challenge ID for tracking
            output_file: Optional file to capture output

        Returns:
            dict with session info
        """
        # Generate session name if not provided
        if not session_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_name = f"{agent_type}_{timestamp}_{uuid.uuid4().hex[:6]}"

        # Get model for agent
        model = self.MODELS.get(agent_type, {}).get(model_tier, "default")

        # Build the command
        cmd_template = self.COMMANDS.get(agent_type)
        if not cmd_template:
            raise ValueError(f"Unknown agent type: {agent_type}")

        # Escape quotes in prompt
        escaped_prompt = prompt.replace('"', '\\"')
        cmd = cmd_template.format(prompt=escaped_prompt, model=model)

        # Add output capture if specified
        if output_file:
            cmd = f"{cmd} 2>&1 | tee {output_file}"

        # Set working directory
        work_dir = working_dir or str(REPO_ROOT)

        # Spawn based on platform
        if self.platform == "linux":
            result = self._spawn_tmux(session_name, cmd, work_dir)
        elif self.platform == "macos":
            result = self._spawn_macos(session_name, cmd, work_dir)
        elif self.platform == "windows":
            result = self._spawn_windows(session_name, cmd, work_dir)
        else:
            raise RuntimeError(f"Unsupported platform: {self.platform}")

        # Log the spawn
        spawn_info = {
            "session_name": session_name,
            "agent_type": agent_type,
            "model": model,
            "model_tier": model_tier,
            "prompt": prompt,
            "working_dir": work_dir,
            "challenge_id": challenge_id,
            "output_file": output_file,
            "timestamp": datetime.now().isoformat(),
            "platform": self.platform,
            "result": result
        }

        self._log_spawn(spawn_info)
        return spawn_info

    def _spawn_tmux(self, session_name: str, cmd: str, work_dir: str) -> dict:
        """Spawn agent in a new tmux session (Linux)."""
        # Create new tmux session in detached mode
        tmux_cmd = [
            "tmux", "new-session",
            "-d",  # Detached
            "-s", session_name,  # Session name
            "-c", work_dir,  # Working directory
            cmd  # Command to run
        ]

        try:
            subprocess.run(tmux_cmd, check=True, capture_output=True, text=True)
            return {"success": True, "message": f"Spawned tmux session: {session_name}"}
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": e.stderr}

    def _spawn_macos(self, session_name: str, cmd: str, work_dir: str) -> dict:
        """Spawn agent in a new Terminal window (macOS)."""
        # Escape for AppleScript
        escaped_cmd = cmd.replace("\\", "\\\\").replace('"', '\\"')

        applescript = f'''
        tell application "Terminal"
            do script "cd {work_dir} && {escaped_cmd}"
            activate
        end tell
        '''

        try:
            subprocess.run(["osascript", "-e", applescript], check=True, capture_output=True)
            return {"success": True, "message": f"Spawned Terminal window: {session_name}"}
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": str(e)}

    def _spawn_windows(self, session_name: str, cmd: str, work_dir: str) -> dict:
        """Spawn agent in a new cmd window (Windows)."""
        # Use start command to open new window
        full_cmd = f'start cmd /k "cd /d {work_dir} && {cmd}"'

        try:
            subprocess.Popen(full_cmd, shell=True)
            return {"success": True, "message": f"Spawned cmd window: {session_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_sessions(self, agent_type: Optional[AgentType] = None) -> list:
        """List active agent sessions."""
        if self.platform != "linux":
            return []  # Only tmux supported for now

        try:
            result = subprocess.run(
                ["tmux", "list-sessions", "-F", "#{session_name}"],
                capture_output=True, text=True
            )
            sessions = result.stdout.strip().split("\n") if result.stdout else []

            if agent_type:
                sessions = [s for s in sessions if s.startswith(agent_type)]

            return sessions
        except subprocess.CalledProcessError:
            return []

    def attach_session(self, session_name: str) -> None:
        """Attach to an existing tmux session."""
        if self.platform == "linux":
            os.execvp("tmux", ["tmux", "attach-session", "-t", session_name])

    def kill_session(self, session_name: str) -> dict:
        """Kill an agent session."""
        if self.platform == "linux":
            try:
                subprocess.run(
                    ["tmux", "kill-session", "-t", session_name],
                    check=True, capture_output=True
                )
                return {"success": True, "message": f"Killed session: {session_name}"}
            except subprocess.CalledProcessError as e:
                return {"success": False, "error": e.stderr}
        return {"success": False, "error": "Not supported on this platform"}

    def capture_output(self, session_name: str, lines: int = 1000) -> str:
        """Capture output from a tmux session."""
        if self.platform == "linux":
            try:
                result = subprocess.run(
                    ["tmux", "capture-pane", "-t", session_name, "-p", "-S", f"-{lines}"],
                    capture_output=True, text=True
                )
                return result.stdout
            except subprocess.CalledProcessError:
                return ""
        return ""

    def _log_spawn(self, spawn_info: dict) -> None:
        """Log spawn info to runs directory."""
        RUNS_DIR.mkdir(parents=True, exist_ok=True)

        log_file = RUNS_DIR / f"{spawn_info['session_name']}.json"
        with open(log_file, "w") as f:
            json.dump(spawn_info, f, indent=2)


def spawn_multi(
    agents: list[dict],
    challenge_id: Optional[str] = None
) -> list[dict]:
    """
    Spawn multiple agents in parallel.

    Args:
        agents: List of agent configs, each with:
            - type: Agent type (claude, gemini, codex)
            - prompt: The prompt for the agent
            - name: Optional session name
            - model_tier: Optional model tier
        challenge_id: Optional challenge ID for tracking

    Returns:
        List of spawn results
    """
    spawner = AgentSpawner()
    results = []

    for agent in agents:
        result = spawner.spawn(
            agent_type=agent["type"],
            prompt=agent["prompt"],
            session_name=agent.get("name"),
            model_tier=agent.get("model_tier", "default"),
            challenge_id=challenge_id
        )
        results.append(result)

    return results


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Spawn AI agents")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Spawn command
    spawn_parser = subparsers.add_parser("spawn", help="Spawn an agent")
    spawn_parser.add_argument("agent_type", choices=["claude", "gemini", "codex"])
    spawn_parser.add_argument("prompt", help="The prompt for the agent")
    spawn_parser.add_argument("--name", help="Session name")
    spawn_parser.add_argument("--tier", default="default", choices=["default", "fast", "heavy"])
    spawn_parser.add_argument("--dir", help="Working directory")
    spawn_parser.add_argument("--challenge", help="Challenge ID")

    # List command
    list_parser = subparsers.add_parser("list", help="List active sessions")
    list_parser.add_argument("--type", choices=["claude", "gemini", "codex"])

    # Attach command
    attach_parser = subparsers.add_parser("attach", help="Attach to a session")
    attach_parser.add_argument("session_name", help="Session to attach to")

    # Kill command
    kill_parser = subparsers.add_parser("kill", help="Kill a session")
    kill_parser.add_argument("session_name", help="Session to kill")

    # Capture command
    capture_parser = subparsers.add_parser("capture", help="Capture session output")
    capture_parser.add_argument("session_name", help="Session to capture")
    capture_parser.add_argument("--lines", type=int, default=1000)

    args = parser.parse_args()
    spawner = AgentSpawner()

    if args.command == "spawn":
        result = spawner.spawn(
            agent_type=args.agent_type,
            prompt=args.prompt,
            session_name=args.name,
            model_tier=args.tier,
            working_dir=args.dir,
            challenge_id=args.challenge
        )
        print(json.dumps(result, indent=2))

    elif args.command == "list":
        sessions = spawner.list_sessions(args.type)
        for s in sessions:
            print(s)

    elif args.command == "attach":
        spawner.attach_session(args.session_name)

    elif args.command == "kill":
        result = spawner.kill_session(args.session_name)
        print(json.dumps(result, indent=2))

    elif args.command == "capture":
        output = spawner.capture_output(args.session_name, args.lines)
        print(output)

    else:
        parser.print_help()
