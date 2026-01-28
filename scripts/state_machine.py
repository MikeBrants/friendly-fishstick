"""FINAL TRIGGER v4.3 - State Machine Runner"""

from __future__ import annotations

import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple


@dataclass
class TransitionResult:
    next_state: str
    state_updates: Dict[str, Any]
    reason: str


@dataclass
class StateExecutionResult:
    state_name: str
    action_executed: Optional[str]
    transition: TransitionResult
    state_after: Dict[str, Any]


class StateMachine:
    """
    State machine runner for FINAL TRIGGER v4.3 pipeline.

    Supports router.yaml schema:
    ```yaml
    STATE_NAME:
      description: "..."
      action: "handler_name"  # optional
      transitions:
        - if: "condition_expression"  # optional, None = always true
          then: "NEXT_STATE"
          set:
            key: value
          reason: "explanation"
    ```
    """

    def __init__(
        self,
        router_path: str = "configs/router.yaml",
        action_handlers: Optional[Dict[str, Callable]] = None,
    ) -> None:
        self.router = self._load_router(router_path)
        self.action_handlers = action_handlers or {}
        self.execution_history: list[StateExecutionResult] = []

    def _load_router(self, path: str) -> Dict[str, Any]:
        """Load router configuration from YAML."""
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Handle both flat format and nested states format
        if isinstance(config, dict) and "states" in config:
            states_block = config.get("states")
            transitions = config.get("transitions", {})
            if isinstance(states_block, dict):
                return states_block
            if isinstance(transitions, dict) and transitions:
                state_defs: Dict[str, Any] = {}
                for name, definition in transitions.items():
                    if isinstance(definition, list):
                        if len(definition) == 1 and definition[0].get("terminal"):
                            state_defs[name] = {"terminal": True}
                        else:
                            state_defs[name] = {"transitions": definition}
                    elif isinstance(definition, dict):
                        state_defs[name] = definition
                return state_defs
        if isinstance(config, dict):
            return config
        raise ValueError("Invalid router configuration")

    def register_handler(self, action_name: str, handler: Callable) -> None:
        """Register an action handler."""
        self.action_handlers[action_name] = handler

    def register_handlers(self, handlers: Dict[str, Callable]) -> None:
        """Register multiple action handlers."""
        self.action_handlers.update(handlers)

    def _eval_condition(self, condition: Optional[str], state: Dict[str, Any]) -> bool:
        """
        Evaluate a condition string against the current state.

        Supports:
        - "var == 'value'"
        - "var == True/False"
        - "var > number"
        - "var >= number"
        - "var < number"
        - "var <= number"
        - "var and other_var"
        - "var or other_var"
        """
        if condition is None:
            return True

        eval_context = {"True": True, "False": False, "None": None}
        eval_context.update(state)

        try:
            result = eval(condition, {"__builtins__": {}}, eval_context)
            return bool(result)
        except Exception as exc:
            print(f"[StateMachine] Warning: condition eval failed: {condition} -> {exc}")
            return False

    def _apply_state_updates(self, state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Apply state updates from transition."""
        new_state = state.copy()

        for key, value in updates.items():
            if isinstance(value, str) and any(op in value for op in [" - ", " + ", " * ", " / "]):
                try:
                    eval_context = {"__builtins__": {}}
                    eval_context.update(state)
                    new_state[key] = eval(value, eval_context)
                except Exception:
                    new_state[key] = value
            else:
                new_state[key] = value

        return new_state

    def _execute_action(self, action: str, state: Dict[str, Any]) -> Dict[str, Any]:
        if action in self.action_handlers:
            return self.action_handlers[action](state)
        print(f"[StateMachine] Warning: no handler for action '{action}'")
        return state

    def execute_state(
        self,
        state_name: str,
        state: Dict[str, Any],
        execute_actions: bool = True,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Execute a single state and return the next state name and updated state.

        Args:
            state_name: Current state name
            state: Current state dictionary

        Returns:
            Tuple of (next_state_name, updated_state)
        """
        if state_name not in self.router:
            raise ValueError(f"Unknown state: {state_name}")

        state_def = self.router[state_name]

        # Check if terminal state
        if state_def.get("terminal", False):
            return state_name, state

        # Execute state-level action if defined
        action = state_def.get("action")
        if action and execute_actions:
            state = self._execute_action(action, state)

        transitions = state_def.get("transitions", [])

        for transition in transitions:
            condition = transition.get("if")
            if condition is None or condition == "else" or "else" in transition:
                if condition in (None, "else") or "else" in transition or self._eval_condition(condition, state):
                    if execute_actions and transition.get("action"):
                        state = self._execute_action(transition["action"], state)

                    updates = transition.get("set", {})
                    state = self._apply_state_updates(state, updates)

                    next_state = transition.get("then")
                    reason = transition.get("reason", "")

                    self.execution_history.append(
                        StateExecutionResult(
                            state_name=state_name,
                            action_executed=action or transition.get("action"),
                            transition=TransitionResult(next_state, updates, reason),
                            state_after=state.copy(),
                        )
                    )

                    return next_state, state
            else:
                if self._eval_condition(condition, state):
                    if execute_actions and transition.get("action"):
                        state = self._execute_action(transition["action"], state)

                    updates = transition.get("set", {})
                    state = self._apply_state_updates(state, updates)

                    next_state = transition.get("then")
                    reason = transition.get("reason", "")

                    self.execution_history.append(
                        StateExecutionResult(
                            state_name=state_name,
                            action_executed=action or transition.get("action"),
                            transition=TransitionResult(next_state, updates, reason),
                            state_after=state.copy(),
                        )
                    )

                    return next_state, state

        raise ValueError(f"No valid transition from state '{state_name}' with state: {state}")

    def run(
        self,
        initial_state: str = "INIT",
        state: Optional[Dict[str, Any]] = None,
        max_steps: int = 100,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Run the state machine from initial state to terminal state.

        Args:
            initial_state: Starting state name
            state: Initial state dictionary
            max_steps: Maximum steps before forced stop
            dry_run: If True, don't execute actions, just traverse

        Returns:
            Final state dictionary
        """
        current_state = initial_state
        state = state or {}
        steps = 0

        print(f"[StateMachine] Starting from {current_state}")

        while steps < max_steps:
            state_def = self.router.get(current_state, {})

            if state_def.get("terminal", False):
                print(f"[StateMachine] Reached terminal state: {current_state}")
                state["_final_state"] = current_state
                state["_success"] = state_def.get("success", False)
                break

            try:
                next_state, state = self.execute_state(
                    current_state, state, execute_actions=not dry_run
                )
                print(f"[StateMachine] {current_state} -> {next_state}")
                current_state = next_state
            except Exception as exc:
                print(f"[StateMachine] Error in {current_state}: {exc}")
                state["_error"] = str(exc)
                state["_final_state"] = "ERROR"
                break

            steps += 1

        if steps >= max_steps:
            print(f"[StateMachine] Warning: max steps ({max_steps}) reached")
            state["_final_state"] = "MAX_STEPS_REACHED"

        state["_total_steps"] = steps
        return state

    def get_execution_log(self) -> list[dict[str, Any]]:
        """Get the execution history as a list of dicts."""
        return [
            {
                "state": r.state_name,
                "action": r.action_executed,
                "next": r.transition.next_state,
                "updates": r.transition.state_updates,
                "reason": r.transition.reason,
            }
            for r in self.execution_history
        ]

    def print_execution_log(self) -> None:
        """Print a formatted execution log."""
        print("\n" + "=" * 60)
        print("  EXECUTION LOG")
        print("=" * 60)
        for i, entry in enumerate(self.get_execution_log()):
            print(f"\n[{i + 1}] {entry['state']}")
            if entry["action"]:
                print(f"    Action: {entry['action']}")
            print(f"    -> {entry['next']}")
            if entry["updates"]:
                print(f"    Set: {entry['updates']}")
            if entry["reason"]:
                print(f"    Reason: {entry['reason']}")
