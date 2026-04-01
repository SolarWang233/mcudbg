# mcudbg 断点调试能力 v0.1 规格

这份文档定义 `mcudbg` 下一阶段非常关键的一层能力：

**断点与执行控制**

它的目标不是做一个完整 IDE 调试器，而是给 `mcudbg` 增加一组最小但高价值的能力，让 AI 不只是“读取现场”，而是能主动控制程序停在哪、看哪条路径、验证哪个假设。

如果把前面的能力理解成：

- 看板子当前发生了什么

那么断点能力就是：

- 主动控制板子执行过程，并验证代码路径

这一步会让 `mcudbg` 从“诊断工具”进一步走向“交互式调试工具”。

---

## 1. 设计目标

`v0.1` 的断点能力只做一件事：

**让 AI 能在关键代码路径上停下来，并读取停下时的上下文。**

这意味着它应该能支持这类操作：

- 在某个函数入口打断点
- 继续运行到断点
- 停下后读取寄存器 / PC / LR / SP
- 读取当前日志上下文
- 判断“程序到底有没有走到这里”

`v0.1` 不追求支持所有复杂调试功能，只追求：

**能稳定回答“它有没有执行到这里，以及停下时是什么状态”。**

---

## 2. 为什么这个能力重要

很多嵌入式问题，仅靠最终现场并不能完全解释。

例如：

- 某个初始化函数到底有没有被调用
- 某个分支到底有没有走到
- 是卡在循环里，还是根本没进入某个路径
- fault 发生之前到底执行到了哪一步
- 主循环有没有真正进入

没有断点时，AI 只能：

- 看日志
- 看最后 fault 现场
- 做有限推断

有了断点之后，它就可以更像调试工程师一样工作：

- 在目标位置停住
- 继续运行到该位置
- 读取停下时的上下文
- 验证某个怀疑是否成立

所以这层能力的价值，不是“调试动作变多了”，而是：

**AI 的诊断开始从被动观察走向主动验证。**

---

## 3. v0.1 范围

### v0.1 支持

- 按符号名或地址设置断点
- 清除断点
- 清除全部断点
- 继续运行直到断点或停机
- 单步执行一条最小步长
- 读取停下时的上下文
- 返回断点命中信息

### v0.1 不支持

- 条件断点
- 数据断点 / watchpoint
- 多核复杂调试
- 复杂变量求值
- 完整源码级调用栈浏览
- 完整 IDE 式调试体验

---

## 4. 建议工具集合

建议 `v0.1` 至少新增这几个 MCP tools：

### 1. `set_breakpoint`

用途：

- 在符号或地址处设置断点

建议输入：

```json
{
  "symbol": "sensor_init",
  "address": null
}
```

建议输出：

```json
{
  "status": "ok",
  "summary": "Breakpoint set at sensor_init.",
  "breakpoint": {
    "symbol": "sensor_init",
    "address": "0x08001234"
  }
}
```

### 2. `clear_breakpoint`

用途：

- 清除指定断点

### 3. `clear_all_breakpoints`

用途：

- 清除所有当前断点

### 4. `continue_target`

用途：

- 继续运行目标，直到命中断点、fault、外部 halt 或超时

建议输出：

```json
{
  "status": "ok",
  "summary": "Target stopped after continue.",
  "stop_reason": "breakpoint_hit",
  "pc": "0x08001234",
  "symbol": "sensor_init"
}
```

### 5. `step_instruction`

用途：

- 执行最小步长的单步

`v0.1` 可以先从 instruction 级单步开始，不一定一开始就承诺源码级 step over / step into。

### 6. `read_stopped_context`

用途：

- 在目标已 halt 的情况下，统一读取：
  - `PC/LR/SP/XPSR`
  - fault 寄存器
  - 当前符号上下文
  - 可选最近日志

这是一个很关键的高层 tool，因为它会把原始调试信息组织成更适合 AI 使用的结果。

---

## 5. 建议高层用法

断点能力真正的价值，不在单个 tool，而在高层组合。

例如以后可以支持这种工作流：

### 用法一：验证函数有没有执行到

```text
set_breakpoint(symbol="sensor_init")
probe_reset(halt=false)
continue_target()
read_stopped_context()
```

目标：

- 验证程序是否真的进入 `sensor_init`

### 用法二：验证主循环有没有进

```text
set_breakpoint(symbol="main_loop")
probe_reset(halt=false)
continue_target()
read_stopped_context()
```

目标：

- 验证“灯不闪”是不是因为根本没进主循环

### 用法三：验证 fault 前路径

```text
set_breakpoint(symbol="sensor_init")
probe_reset(halt=false)
continue_target()
step_instruction()
read_stopped_context()
```

目标：

- 看 fault 前控制流到底停在哪

---

## 6. 建议输入输出风格

这一层工具建议遵循一个原则：

**不要只返回“动作成功”，还要返回“停下时最有价值的调试信息”。**

比如 `continue_target` 不应该只说：

- target resumed

而应该尽量告诉上层：

- 为什么停下
- 停在什么地址
- 对应什么符号
- 当前是不是 fault 状态

这样 AI 才能直接把结果纳入推理，而不是下一步还要再问一轮低层工具。

---

## 7. 推荐 stop_reason 枚举

建议统一这些停止原因：

- `breakpoint_hit`
- `fault`
- `manual_halt`
- `reset_halt`
- `step_complete`
- `timeout`
- `unknown_stop`

这样高层 workflow 很容易基于 stop reason 做分支。

---

## 8. 与现有能力的关系

断点能力不是替代已有工具，而是补强它们。

它和现有能力之间的关系大概是：

- `log_tail`
  - 告诉你程序对外打印了什么
- `diagnose_startup_failure`
  - 告诉你大概率卡在哪个阶段
- `diagnose_hardfault`
  - 告诉你最终 fault 现场是什么
- `breakpoint tools`
  - 告诉你程序是否真的走到了某条路径，以及停下时是什么状态

也就是说，这一层能力最适合回答：

**“它到底有没有执行到这里？”**

---

## 9. v0.1 推荐实现顺序

建议不要一口气把所有工具都写完，而是按这个顺序做：

### 第一步

- `set_breakpoint`
- `continue_target`
- `read_stopped_context`

这 3 个先有了，就已经能做第一次强演示。

### 第二步

- `clear_breakpoint`
- `clear_all_breakpoints`

### 第三步

- `step_instruction`

如果第一阶段已经够稳，单步可以放在后面一点。

---

## 10. 成功标准

如果下面这些都成立，就说明断点能力 `v0.1` 是成功的：

1. 能在指定符号处稳定打断点
2. 能继续运行到断点并停下
3. 能返回清楚的 stop reason
4. 能读取停下时的上下文
5. 能在当前 STM32L4 demo 工程上稳定复现
6. 能支持至少一个很有说服力的 demo

---

## 11. 最适合的第一批 demo

最推荐的第一批演示不是复杂 fault，而是这种简单但很有说服力的问题：

- “程序到底有没有进 `sensor_init`？”
- “程序到底有没有进入主循环？”
- “灯不闪是不是因为根本没跑到翻转逻辑？”

这种 demo 的好处是：

- 观众一眼能看懂
- 断点能力的价值很直观
- 很适合和你现有的 `灯不闪` 叙事接起来

---

## 一句话总结

断点调试 `v0.1` 的核心，不是复制 IDE，而是先给 `mcudbg` 增加一层“主动验证代码路径”的能力，让 AI 从被动看现场，走向主动控制执行与验证假设。
