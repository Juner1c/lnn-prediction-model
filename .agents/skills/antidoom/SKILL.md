---
name: antidoom
description: Detect and break repetition loops (doom loops) in model outputs, reasoning steps, and tool executions. Enforces anti-looping preferences, first-token loop interrupts, and concise forward momentum.
---

# Antidoom (Anti-Repetition & Loop Guard Skill)

Antidoom prevents agentic "doom loops" — runaway repetitive reasoning, circular command execution, redundant text generation, and stalled progress loops.

## Core Rules & Execution

1. **Repetition Detection**: Monitor token output, command executions, and plan steps for self-reinforcing loop patterns (e.g. running the same failing command multiple times, repeating the same diagnostic explanation, or looping on identical code edits).
2. **First-Token Interrupt**: Intercept repetition at the first repeating token or action. Reject the loop-starting token/path and pivot immediately to an alternative strategy or concise summary.
3. **Concise Forward Momentum**: Eliminate filler transitions (`Wait`, `So`, `Alternatively`, `Let me check again`) when they signal stalling. Keep responses code-first and action-oriented.
4. **Regularized Alternatives**: Choose distinct, non-overlapping alternative paths rather than repeating slight variations of a failed attempt.
