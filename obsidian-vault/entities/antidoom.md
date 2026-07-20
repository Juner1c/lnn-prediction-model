---
title: Antidoom (FTPO Preference & Anti-Loop Framework)
category: entity
tags: [antidoom, ftpo, anti-loop, doom-loop, lora, preference-optimization, liquidai]
sources: [https://github.com/Liquid4All/antidoom.git, .agents/AGENTS.md]
created: 2026-07-20T12:23:00Z
updated: 2026-07-20T12:23:00Z
---

# Antidoom (FTPO Preference & Anti-Loop Framework)

**Antidoom** is a preference optimization framework developed by LiquidAI for detecting, preventing, and training models against runaway repetition loops ("doom loops") during complex reasoning and long-sequence generation.

---

## Key Principles & Methodologies

1. **Final Token Preference Optimization (FTPO)**:
   - Identifies the exact token where a repetition loop originates.
   - Treats the loop-starting token as rejected and samples plausible alternative next-tokens as chosen targets.
   - Trains LoRA adapters to regularize overrepresented tokens and eliminate doom loops.

2. **Integration into Workspace Workflow (`.agents/AGENTS.md`)**:
   - **Repetition Detection**: Monitors agent responses, tool execution, and code generation for circular patterns.
   - **First-Token Interrupt**: Immediately interrupts repetition loops at the first repeating token or diagnostic step.
   - **Concise Forward Momentum**: Eliminates filler transition words (`Wait`, `So`, `Alternatively`) when they indicate stalling.

---

## Related
- [[concepts/liquid-neural-networks]]
- [[concepts/system-architecture]]
