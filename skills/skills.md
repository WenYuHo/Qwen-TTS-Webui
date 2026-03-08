# Specialized Agent Skills

This directory contains modular, on-demand instructions for specific agent roles. 
Instead of loading all instructions at once, the agent should only read the relevant skill file based on the task.

## 📋 Available Skills

### 🧬 [DNA Evolution](dna-evolution/SKILL.md)
**Use when:** Refining instructions, memory, or DNA files.
- Prunes `MEMORY.md` to under 50 lines.
- Updates historical milestones and architectural logs.

### 🧪 [Tester](tester/SKILL.md)
**Use when:** Writing tests, fixing bugs, or verifying features.
- Enforces strict TDD.
- Standardizes browser automation and audio quality audits.

### 🏗️ [Architect](architect/SKILL.md)
**Use when:** Making system-level changes or refactors.
- Manages cross-cutting concerns and core engine integrity.
- Updates codebase maps and decision logs.

---
*To use a skill: Read the linked SKILL.md file at the start of the relevant task phase.*
