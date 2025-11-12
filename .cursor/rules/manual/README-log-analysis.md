# Log Analysis Framework - Complete Documentation

This directory contains comprehensive guidelines for analyzing backend logs and system diagnostics.

## Documents Overview

### 📋 **log-analysis-agent-instructions.mdc** (START HERE FOR AGENTS)
**Best for**: AI coding agents assigned to analyze logs

The complete step-by-step process an agent should follow:
- 7-step systematic analysis process
- Required output format
- Critical rules and heuristics
- Common patterns and anti-patterns
- Checklist for completion
- Contains the exact process I used to analyze your session logs

**Use when**: An agent needs to analyze logs from scratch
**Time**: 15 minutes per set of logs

---

### ⚡ **log-analysis-quick-start.mdc** (TL;DR VERSION)
**Best for**: Quick analysis, refresher, or time-constrained scenarios

5-minute quick reference version:
- Single-page process
- Template to copy/paste
- Common issues cheat sheet
- Decision tree
- Red flags reference
- Decision tree for categorizing problems

**Use when**: You need results fast or just need a refresh
**Time**: 5-10 minutes

---

### 📚 **log-analysis-guidelines.mdc** (COMPREHENSIVE REFERENCE)
**Best for**: Deep understanding, reference material, edge cases

Complete detailed framework with theory and examples:
- 8 analysis phases with deep explanations
- Analysis heuristics and patterns
- WebSocket-specific guidance
- Async/database/API-specific analysis
- Common mistakes to avoid
- Tools and libraries
- Detailed examples

**Use when**: You need comprehensive understanding or handling complex cases
**Time**: Reference material, not meant to be read start-to-finish

---

## Quick Start for New Users

1. **First time analyzing logs?**
   → Read: `log-analysis-agent-instructions.mdc`
   → Follow the 7-step process
   → Use the required output format

2. **Just need quick analysis?**
   → Read: `log-analysis-quick-start.mdc`
   → Use the template
   → Fill in your specific details

3. **Need to understand a specific aspect?**
   → Search: `log-analysis-guidelines.mdc`
   → Look for relevant section
   → Review examples

4. **Teaching someone else?**
   → Share: `log-analysis-agent-instructions.mdc`
   → Have them work through the 7 steps
   → Review using the checklist

---

## Real-World Example

These guidelines were used to analyze the Nov 12, 2025 VSM backend session:

- **Input**: 547 lines of raw backend logs
- **Output**: Complete analysis identifying:
  - 5 critical cascading issues
  - Root cause (file watcher triggering shutdown during in-flight request)
  - Expected vs actual behavior
  - Impact assessment
  - 5 prioritized recommendations

**Results**: See companion documents:
- `docs/BACKEND_LOG_ANALYSIS.md` (full analysis)
- `docs/LOG_ANALYSIS_QUICK_REFERENCE.md` (summary)

---

## The Process at a Glance

```
STEP 1: Structure & Scope
└─ Understand what data you have

STEP 2: Operation Tracing
└─ Follow user actions through system

STEP 3: Error Identification
└─ Find all problems

STEP 4: Failure Point
└─ Identify WHEN it went wrong

STEP 5: Root Cause
└─ Understand WHY it went wrong

STEP 6: Impact Assessment
└─ Determine severity and scope

STEP 7: Expected vs Actual
└─ Document deviation from normal

STEP 8: Output Report
└─ Create structured findings
```

**Time**: 15 minutes per session

---

## Key Principles

### ✅ Always
- ✅ Ground conclusions in log evidence
- ✅ Distinguish symptoms from root causes
- ✅ Question "Why?" at least 3 times
- ✅ Create expected vs actual comparison
- ✅ Propose testable verification

### ❌ Never
- ❌ Speculate without evidence
- ❌ Stop at symptoms
- ❌ Skip the "why wasn't this prevented" question
- ❌ Mix multiple root causes into one
- ❌ Propose fixes before understanding cause

---

## Common Scenarios

### Scenario 1: Server Crash
**Process**: 
1. Find first ERROR/CRITICAL
2. Trace backwards to normal operation
3. Identify what changed between normal and error
4. → That's your root cause

**Example**: See Session Analysis - Issue #1 (file watcher)

---

### Scenario 2: Slow Performance
**Process**:
1. Extract timing data for each operation
2. Identify which step is slowest
3. Check if that's expected (e.g., LLM should be slow)
4. If unexpected, investigate that component

**Example**: If LLM call took 28s instead of 30s, that's normal. If it took 5 minutes, investigate.

---

### Scenario 3: Data Never Reached User
**Process**:
1. Verify data was retrieved (check query results)
2. Verify data was processed (check LLM response)
3. Find where delivery failed (check connection logs)
4. Fix delivery issue

**Example**: See Session Analysis - Issue #5 (response delivery failed)

---

### Scenario 4: Cascading Errors
**Process**:
1. Find the FIRST error (earliest timestamp)
2. That's likely the root cause
3. Others are consequences
4. Fix the first error, others disappear

**Example**: See Session Analysis - Issues #2-4 (cascading WebSocket errors)

---

## Tools Mentioned

- **grep/rg**: Extract relevant lines
- **jq**: Parse JSON logs
- **awk**: Extract timing data
- **sort/uniq**: Find patterns
- **Mermaid**: Visualize cause chains

---

## When Analysis is Complete

You should be able to answer these 8 questions:

1. ✅ What specifically failed?
2. ✅ Why did it fail (root cause)?
3. ✅ When did it start (timestamp)?
4. ✅ What component was involved?
5. ✅ What did the user experience?
6. ✅ What was the missing safeguard?
7. ✅ What are the 3 top fixes?
8. ✅ How do you verify the fix?

If you can't answer all 8, keep analyzing.

---

## Related Resources

- **Debugging Fundamentals**: See Wikipedia articles referenced in guidelines
- **Async Patterns**: MDN's async documentation
- **Root Cause Analysis**: The 5 Whys technique
- **WebSocket Protocol**: RFC 6455

---

## For Specific Domains

### WebSocket Debugging
See: `log-analysis-guidelines.mdc` → "Special Cases" → "WebSocket Analysis"

### Async/Promise Debugging
See: `log-analysis-guidelines.mdc` → "Special Cases" → "Async Task Analysis"

### Database Query Issues
See: `log-analysis-guidelines.mdc` → "Special Cases" → "Database Query Analysis"

### External API Integration
See: `log-analysis-guidelines.mdc` → "Special Cases" → "API Integration Analysis"

---

## Contribution Guidelines

To improve these guidelines:
1. Document patterns you discover
2. Add them to the appropriate section
3. Include real-world examples
4. Update the framework if you find gaps
5. Create tests/scenarios for new patterns

---

## Questions?

If something is unclear:
1. Check all three documents (Agent → Quick Start → Guidelines)
2. Look for similar examples
3. Review the "When Stuck" section in Agent Instructions
4. Apply the "Question Everything" principle

---

## Version & Updates

- **Created**: November 12, 2025
- **Last Updated**: November 12, 2025
- **Used Successfully**: VSM Backend Log Analysis (Nov 12, 2025 session)

**Status**: Production-ready for general use

