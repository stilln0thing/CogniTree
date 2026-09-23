# Design Decisions

This document records important architectural and implementation decisions for CogniTree.

## Decision format

Each entry should capture:

- Date
- Status
- Decision
- Context
- Consequences

## 2026-09-23: Keep planning deterministic for now

**Status:** Provisional

**Decision:** Keep the planner as a lightweight, deterministic heuristic instead of making an LLM call for every request.

**Context:** The main agent already performs reasoning and tool selection. An additional planner LLM call would add latency, cost, and another failure point, especially for simple conversations. The current planner identifies likely multi-step requests using message length and action keywords, then initializes a generic execution plan.

**Consequences:**

- Simple requests avoid an unnecessary model call.
- Planning remains predictable and inexpensive.
- The current planner is only a heuristic prototype, not an LLM-backed planner.
- The generated plan must eventually be passed into the agent context if it is expected to influence execution.
- The heuristic and its limitations should be covered by tests.

**Revisit when:** Complex tasks require more reliable decomposition, the heuristic produces poor routing decisions, or evaluation shows that planning improves task success enough to justify its extra latency and cost.
