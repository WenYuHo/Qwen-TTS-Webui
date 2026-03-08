# EXECUTION PROTOCOL

## 1. HIERARCHY
- **STRATEGY:** [/conductor/](/conductor/)
- **STATE:** [/agent/](/agent/) (Current tasks in `TASK_QUEUE.md`)

## 2. COMMAND
Run `/ralph:start` to initialize the environment and begin the next task.

## 3. AUTOMATION
The system will automatically:
1. Bootstrap missing folders.
2. Install dependencies.
3. Activate the `autonomous-dev` skill.
4. Launch the persistent iteration loop.
