# mcudbg `diagnose_startup_failure` MCP Tool 规格

> 版本：v0.1-draft
> 日期：2026-03-31

## 目标

`diagnose_startup_failure` 用来回答一个更宽的问题：

**板子为什么没正常启动。**

它不要求一定已经进入 HardFault，也可以用于：

1. 启动日志中断
2. 程序卡在初始化阶段
3. 目标停在非预期位置
4. 疑似 fault，但还不能完全确认

## 推荐输入

```json
{
  "auto_halt": true,
  "include_logs": true,
  "log_tail_lines": 50,
  "resolve_symbols": true,
  "suspected_stage": "sensor init"
}
```

## 推荐输出重点

输出应包含：

1. `summary`
2. `diagnosis_type`
3. `startup_context`
4. `fault`
5. `symbol_context`
6. `log_context`
7. `evidence`
8. `suspected_root_causes`
9. `suggested_next_steps`

## `diagnosis_type` 建议值

1. `startup_failure_with_fault`
2. `startup_failure_no_fault_confirmed`
3. `startup_failure_inconclusive`

## 设计原则

1. 优先帮助 AI 判断“停在哪一阶段”
2. 如果检测到 fault，要把它作为证据链的一部分，而不是唯一结论
3. 建议下一步动作必须围绕当前最后一个成功阶段展开
