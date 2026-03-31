# mcudbg Docs

This directory collects the working documentation for `mcudbg`.

The project is still early, so the docs are optimized for one thing:

**getting the first `pyOCD probe + UART + STM32L4` diagnosis loop working and explainable.**

If you are new to the repository, use the reading order below.

---

## Start Here

If you only want the fastest path into the project, read these first:

1. [quickstart.md](/d:/embed-mcp/mcudbg/docs/quickstart.md)
2. [stm32l4-hardware-checklist.md](/d:/embed-mcp/mcudbg/docs/stm32l4-hardware-checklist.md)
3. [mcp-usage-example.md](/d:/embed-mcp/mcudbg/docs/mcp-usage-example.md)

That is the shortest path to the first real-board session.

---

## Product And Scope

These documents explain what `mcudbg` is trying to become, and why the first version is intentionally narrow:

1. [embedded-mcp-product-plan.md](/d:/embed-mcp/embedded-mcp-product-plan.md)
2. [mcudbg-v0.1-mvp-spec.md](/d:/embed-mcp/mcudbg-v0.1-mvp-spec.md)
3. [mcudbg-v0.1-demo-and-launch.md](/d:/embed-mcp/mcudbg-v0.1-demo-and-launch.md)

Read these when you want to understand:

1. the product direction
2. the MVP boundary
3. the first demo story

---

## Diagnosis Tool Specs

These define the high-level AI-facing diagnosis interfaces:

1. [mcudbg-diagnose-hardfault-spec.md](/d:/embed-mcp/mcudbg-diagnose-hardfault-spec.md)
2. [mcudbg-diagnose-startup-failure-spec.md](/d:/embed-mcp/mcudbg/mcudbg-diagnose-startup-failure-spec.md)

Read these when you want to work on:

1. tool inputs
2. output JSON shape
3. evidence and next-step design

---

## Hardware Bring-Up

These documents are for the first real `STM32L4` validation:

1. [stm32l4-hardware-checklist.md](/d:/embed-mcp/mcudbg/docs/stm32l4-hardware-checklist.md)
2. [first-hardware-debug-checklist.md](/d:/embed-mcp/mcudbg/docs/first-hardware-debug-checklist.md)

Read these when you want to:

1. wire the board correctly
2. verify UART and probe behavior
3. troubleshoot first-run issues

---

## MCP Usage And Output

These documents show how the current tool flow is expected to look:

1. [mcp-usage-example.md](/d:/embed-mcp/mcudbg/docs/mcp-usage-example.md)
2. [demo-output.md](/d:/embed-mcp/mcudbg/docs/demo-output.md)

Read these when you want to:

1. run the first MCP workflow
2. compare your output with the expected diagnosis shape
3. prepare README screenshots or launch material

---

## Launch And Repository Positioning

These documents are for public-facing communication:

1. [github-launch-kit.md](/d:/embed-mcp/mcudbg/docs/github-launch-kit.md)

Read this when you want to:

1. set the GitHub description
2. prepare release notes
3. write launch posts

---

## Suggested Reading Orders

### If you want to run the first board demo

1. [stm32l4-hardware-checklist.md](/d:/embed-mcp/mcudbg/docs/stm32l4-hardware-checklist.md)
2. [first-hardware-debug-checklist.md](/d:/embed-mcp/mcudbg/docs/first-hardware-debug-checklist.md)
3. [mcp-usage-example.md](/d:/embed-mcp/mcudbg/docs/mcp-usage-example.md)

### If you want to improve the diagnosis tools

1. [mcudbg-diagnose-hardfault-spec.md](/d:/embed-mcp/mcudbg-diagnose-hardfault-spec.md)
2. [mcudbg-diagnose-startup-failure-spec.md](/d:/embed-mcp/mcudbg/mcudbg-diagnose-startup-failure-spec.md)
3. [demo-output.md](/d:/embed-mcp/mcudbg/docs/demo-output.md)

### If you want to publish the repository

1. [README.md](/d:/embed-mcp/mcudbg/README.md)
2. [github-launch-kit.md](/d:/embed-mcp/mcudbg/docs/github-launch-kit.md)
3. [mcudbg-v0.1-demo-and-launch.md](/d:/embed-mcp/mcudbg-v0.1-demo-and-launch.md)

---

## Current Center Of Gravity

Right now, the center of gravity of the project is still:

**STM32L4 + pyOCD-supported probe + UART + startup failure / HardFault diagnosis**

That narrow focus is deliberate.
