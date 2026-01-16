#!/usr/bin/env python3
"""
Dream Team Arena Orchestrator

The brain that runs challenges:
1. Loads challenge specification
2. Prepares git branches for each agent
3. Spawns agents in parallel
4. Monitors progress
5. Triggers evaluation when complete
"""

import os
import sys
import json
import yaml
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional
import time

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.spawner.spawn_agent import AgentSpawner, spawn_multi

REPO_ROOT = Path(__file__).parent.parent
CHALLENGES_DIR = REPO_ROOT / "arena" / "challenges"
RUNS_DIR = REPO_ROOT / "arena" / "runs"
LIBRARY_DIR = REPO_ROOT / "playground" / "library"


class ChallengeOrchestrator:
    """Orchestrates AI agent challenges."""

    def __init__(self, challenge_path: str):
        self.challenge_path = Path(challenge_path)
        self.challenge = self._load_challenge()
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = RUNS_DIR / f"{self.challenge['id']}_{self.run_id}"
        self.spawner = AgentSpawner()

    def _load_challenge(self) -> dict:
        """Load challenge specification from YAML."""
        with open(self.challenge_path) as f:
            return yaml.safe_load(f)

    def prepare(self) -> None:
        """Prepare the environment for the challenge."""
        print(f"\n{'='*60}")
        print(f"  DREAM TEAM ARENA - Challenge #{self.challenge['id']}")
        print(f"  {self.challenge['name']}")
        print(f"{'='*60}\n")

        # Create run directory
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # Save challenge config to run
        with open(self.run_dir / "challenge.yaml", "w") as f:
            yaml.dump(self.challenge, f)

        # Prepare git branches for each agent
        self._prepare_branches()

        print(f"[+] Run directory: {self.run_dir}")
        print(f"[+] Challenge type: {self.challenge['type']}")
        print(f"[+] Difficulty: {self.challenge['difficulty']}")
        print()

    def _prepare_branches(self) -> None:
        """Create git branches for each agent."""
        agents_config = self.challenge.get("agents", {})
        agent_types = agents_config.get("types", ["claude"])
        branch_prefix = self.challenge.get("git", {}).get("branch_prefix", "challenge/agent")
        base_branch = self.challenge.get("git", {}).get("base_branch", "main")

        print("[*] Preparing git branches...")

        for i, agent_type in enumerate(agent_types):
            branch_name = f"{branch_prefix}_{agent_type}_{i}"

            # Check if branch exists
            result = subprocess.run(
                ["git", "branch", "--list", branch_name],
                capture_output=True, text=True, cwd=REPO_ROOT
            )

            if not result.stdout.strip():
                # Create new branch from base
                try:
                    subprocess.run(
                        ["git", "checkout", "-b", branch_name],
                        check=True, capture_output=True, cwd=REPO_ROOT
                    )
                    subprocess.run(
                        ["git", "checkout", "-"],
                        check=True, capture_output=True, cwd=REPO_ROOT
                    )
                    print(f"    [+] Created branch: {branch_name}")
                except subprocess.CalledProcessError as e:
                    print(f"    [!] Failed to create branch: {branch_name}")
            else:
                print(f"    [=] Branch exists: {branch_name}")

    def spawn_agents(self) -> list:
        """Spawn all agents for the challenge."""
        agents_config = self.challenge.get("agents", {})
        agent_types = agents_config.get("types", ["claude"])
        model_tier = agents_config.get("model_tier", "default")
        prompt = self.challenge.get("prompt", "")

        print(f"[*] Spawning {len(agent_types)} agents...")

        agents = []
        for i, agent_type in enumerate(agent_types):
            session_name = f"dream_{self.challenge['id']}_{agent_type}_{i}"
            output_file = self.run_dir / f"{agent_type}_{i}.log"

            # Build context-enriched prompt
            full_prompt = self._build_prompt(agent_type, i)

            agent_config = {
                "type": agent_type,
                "prompt": full_prompt,
                "name": session_name,
                "model_tier": model_tier
            }
            agents.append(agent_config)

        # Spawn all agents
        results = spawn_multi(agents, challenge_id=self.challenge["id"])

        for result in results:
            status = "SPAWNED" if result.get("result", {}).get("success") else "FAILED"
            print(f"    [{status}] {result['session_name']} ({result['agent_type']})")

        return results

    def _build_prompt(self, agent_type: str, index: int) -> str:
        """Build the full prompt with context for an agent."""
        base_prompt = self.challenge.get("prompt", "")

        # Add arena context
        context = f"""
=== DREAM TEAM ARENA ===
Challenge: #{self.challenge['id']} - {self.challenge['name']}
Agent: {agent_type} (instance {index})
Run ID: {self.run_id}

You are one of multiple AI agents working on this challenge.
Your work will be compared against other agents.
Do your best work. Be creative. Push boundaries.

=== CHALLENGE ===

{base_prompt}

=== INSTRUCTIONS ===
1. Work in this repository: {REPO_ROOT}
2. Commit your changes frequently with clear messages
3. Document your approach and decisions
4. When finished, ensure all changes are committed

Good luck, agent.
"""
        return context

    def monitor(self, interval: int = 30) -> None:
        """Monitor running agent sessions."""
        print("\n[*] Monitoring agent sessions...")
        print("    (Press Ctrl+C to stop monitoring)\n")

        try:
            while True:
                sessions = self.spawner.list_sessions()
                challenge_sessions = [
                    s for s in sessions
                    if f"dream_{self.challenge['id']}" in s
                ]

                if not challenge_sessions:
                    print("[*] No active sessions found. Agents may have completed.")
                    break

                print(f"[{datetime.now().strftime('%H:%M:%S')}] Active sessions: {len(challenge_sessions)}")
                for session in challenge_sessions:
                    print(f"    - {session}")

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n[*] Monitoring stopped.")

    def evaluate(self) -> dict:
        """Evaluate agent outputs."""
        print("\n[*] Running evaluation...")

        # Import evaluator
        from tools.evaluate.evaluator import Evaluator

        evaluator = Evaluator(self.challenge, self.run_dir)
        results = evaluator.evaluate()

        # Save results
        results_file = self.run_dir / "evaluation_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n[+] Evaluation complete. Results saved to: {results_file}")
        return results

    def run(self, skip_spawn: bool = False, auto_evaluate: bool = True) -> None:
        """Run the full challenge workflow."""
        self.prepare()

        if not skip_spawn:
            self.spawn_agents()
            print("\n[*] Agents spawned. They are now working on the challenge.")
            print("[*] Use 'tmux attach -t <session>' to observe an agent.")
            print("[*] Use 'python arena/orchestrator.py monitor' to check status.")

        if auto_evaluate:
            print("\n[*] Waiting for agents to complete...")
            print("    (In production, this would wait for agent completion signals)")


def main():
    parser = argparse.ArgumentParser(description="Dream Team Arena Orchestrator")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a challenge")
    run_parser.add_argument("challenge", help="Path to challenge YAML or challenge ID")
    run_parser.add_argument("--skip-spawn", action="store_true", help="Skip spawning agents")
    run_parser.add_argument("--no-eval", action="store_true", help="Skip auto evaluation")

    # List command
    list_parser = subparsers.add_parser("list", help="List available challenges")

    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor running challenge")
    monitor_parser.add_argument("--challenge", help="Challenge ID to monitor")
    monitor_parser.add_argument("--interval", type=int, default=30, help="Check interval in seconds")

    # Evaluate command
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate a completed run")
    eval_parser.add_argument("run_dir", help="Path to run directory")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show arena status")

    args = parser.parse_args()

    if args.command == "run":
        # Find challenge file
        challenge_path = args.challenge
        if not os.path.exists(challenge_path):
            # Try as challenge ID
            challenge_path = CHALLENGES_DIR / f"{args.challenge}.yaml"
            if not challenge_path.exists():
                # Try with prefix
                matches = list(CHALLENGES_DIR.glob(f"*{args.challenge}*.yaml"))
                if matches:
                    challenge_path = matches[0]
                else:
                    print(f"Challenge not found: {args.challenge}")
                    sys.exit(1)

        orchestrator = ChallengeOrchestrator(challenge_path)
        orchestrator.run(
            skip_spawn=args.skip_spawn,
            auto_evaluate=not args.no_eval
        )

    elif args.command == "list":
        print("\nAvailable Challenges:")
        print("-" * 40)
        for challenge_file in sorted(CHALLENGES_DIR.glob("*.yaml")):
            with open(challenge_file) as f:
                challenge = yaml.safe_load(f)
            print(f"  [{challenge.get('id', '?')}] {challenge.get('name', 'Unknown')}")
            print(f"      Type: {challenge.get('type', '?')} | Difficulty: {challenge.get('difficulty', '?')}")
        print()

    elif args.command == "monitor":
        spawner = AgentSpawner()
        print("\nActive Agent Sessions:")
        print("-" * 40)
        sessions = spawner.list_sessions()
        if sessions:
            for session in sessions:
                print(f"  - {session}")
        else:
            print("  No active sessions")
        print()

    elif args.command == "status":
        print("\n=== DREAM TEAM ARENA STATUS ===\n")

        # Count challenges
        challenges = list(CHALLENGES_DIR.glob("*.yaml"))
        print(f"Challenges: {len(challenges)}")

        # Count runs
        runs = list(RUNS_DIR.glob("*/"))
        print(f"Total runs: {len(runs)}")

        # Active sessions
        spawner = AgentSpawner()
        sessions = spawner.list_sessions()
        print(f"Active sessions: {len(sessions)}")

        # Knowledge base
        knowledge_files = list(LIBRARY_DIR.glob("**/*.md")) if LIBRARY_DIR.exists() else []
        print(f"Knowledge entries: {len(knowledge_files)}")

        print()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
