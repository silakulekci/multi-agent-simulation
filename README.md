# multi-agent-simulation
# Potential Improvements to the AoI-Based Map Sharing Model

> Notes prepared by Sila — 04 March 2025



---

## Overview

The current model uses a fixed Age of Information (AoI) threshold **W = 70 ticks** to govern map exchanges between agents. While this approach is conceptually clean and easy to implement, the literature suggests several directions for improvement. This document outlines three proposals, each grounded in recent work, with a note on what would need to change in the current implementation.

---

## Proposal 1 — Adaptive Threshold W

**Current behaviour:**
W is a fixed constant. Every agent pair uses the same threshold regardless of the environment, the agents' positions, or the current phase of the mission.

**The problem:**
A fixed W creates two failure modes. If W is too small, agents meet too frequently and waste energy on redundant exchanges. If W is too large, information becomes stale before agents can share it. Neither extreme is optimal, and the right value of W is likely to change over the course of a mission.

**What the literature suggests:**
Recent work on adaptive communication in multi-agent systems shows that communication frequency should be adjusted dynamically based on mission urgency and environmental change. In low-activity phases, agents can afford to wait longer before exchanging maps; in high-activity phases, more frequent exchanges improve coordination.

**What would need to change:**
- Each agent maintains a local estimate of how much new information it has accumulated since the last exchange.
- W is updated at each step: if the agent has explored many new cells, W decreases (meet sooner); if the agent has found little new information, W increases (wait longer).
- This can be implemented as a simple linear rule or as a more sophisticated function of exploration rate.

**Source:** *Integrated Adaptive Communication in Multi-Agent Systems: Dynamic Topology, Frequency, and Content Optimization for Efficient Collaboration — ScienceDirect, 2024*

---

## Proposal 2 — Incremental Map Sharing

**Current behaviour:**
When two agents meet and AoI >= W, they exchange their full maps. Each agent sends everything it knows, and the receiving agent merges it with its own knowledge using a boolean OR operation.

**The problem:**
If two agents met 70 ticks ago and have since explored very little new territory, sending the entire map is wasteful. The communication cost is proportional to the total map size rather than the amount of new information, which becomes increasingly inefficient as the map grows.

**What the literature suggests:**
Several studies on cooperative multi-agent pathfinding propose incremental or delta-based map sharing: instead of transmitting the full map, each agent tracks which cells have changed since the last exchange and sends only those.

**What would need to change:**
- Each agent stores, alongside its full map, a delta map: a record of all cells that have changed state since the last exchange with each partner.
- On meeting, only the delta map is transmitted rather than the full map.
- After the exchange, the delta map for that partner is reset to empty.

**Source:** *Cooperative Hybrid Multi-Agent Pathfinding Based on Shared Exploration Maps — arXiv, 2025*

---

## Proposal 3 — Content-Aware AoI

**Current behaviour:**
AoI is computed purely as elapsed time: `AoI = t_now - t_last`. A meeting is triggered when enough time has passed, regardless of whether either agent has actually learned anything new.

**The problem:**
Time elapsed is a weak proxy for information staleness. An agent that has been idle for 70 ticks holds no new information worth sharing. Conversely, an agent that has discovered a large unexplored region after only 30 ticks holds highly valuable information.

**What the literature suggests:**
The concept of Age of Correlated Information (AoCI) extends classical AoI to account for the content of the information being shared, not just the time since the last update.

**What would need to change:**
- AoI is extended with a content term:
```
AoI_content = (t_now - t_last) × new_cells_explored
```
- A meeting is triggered when AoI_content exceeds a threshold, meaning that both sufficient time and sufficient new information are required.
- This naturally prevents redundant exchanges when agents are both idle, while accelerating exchanges when one agent has been highly active.

**Source:** *Age of Correlated Information: Optimal Dynamic Policy Scheduling for Sustainable Green IoT Devices — ScienceDirect, 2024*

---

## Summary

| Proposal | Current model | Proposed change | Source |
|----------|--------------|-----------------|--------|
| **Adaptive W** | Fixed W = 70 ticks | W varies with exploration rate | *IACN — ScienceDirect 2024* |
| **Incremental sharing** | Full map exchanged | Only new cells transmitted | *CHS — arXiv 2025* |
| **Content-aware AoI** | Time only | Time × new cells explored | *AoCI — ScienceDirect 2024* |

---

## Open Questions

- Should all three proposals be implemented together, or tested independently first?
- How should the adaptive W rule be parameterised? What counts as a significant change in exploration rate?
- In the content-aware AoI formula, should `new_cells_explored` be an absolute count or a fraction of total map size?
- How do these changes interact with the existing energy model and return-to-base logic?
