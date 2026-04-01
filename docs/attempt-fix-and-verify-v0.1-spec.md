# attempt_fix_and_verify v0.1 规格

这份文档定义 `mcudbg` 里一个更高层的能力：

`attempt_fix_and_verify`

它的目标不是“让 AI 自动修所有嵌入式问题”，而是先把已经验证过的那条闭环，收成一个可以复用的工作流能力：

- 根据当前诊断结果决定是否修复
- 执行代码修改
- 编译
- 烧录
- 复位
- 再验证
- 给出最终结论

这会是 `mcudbg` 从“能诊断”走向“能完成一次调试闭环”的关键一步。

---

## 1. 设计目标

`attempt_fix_and_verify` 在 `v0.1` 只解决一个很明确的问题：

**把“已知、可控、可验证”的修复动作，收成一条标准闭环。**

也就是说，它先不追求智能到能随便改任意 bug，而是先针对这类场景：

- 已经有明确诊断结果
- 修复策略是有限集合
- 修复后是否成功可以通过 build/flash/log/diagnosis 再验证

`v0.1` 的核心价值不是“它会不会写复杂 patch”，而是：

**它能不能把修复和验证变成一个标准化流程。**

---

## 2. v0.1 范围

### v0.1 支持

- 接收当前问题描述和诊断结果
- 选择一个有限的修复策略
- 修改本地代码
- 调用 `build_project`
- 调用 `flash_firmware`
- 调用 `connect_with_config`
- 调用 `probe_reset`
- 调用 `log_tail`
- 调用 `diagnose_startup_failure`
- 返回修复前后对比结果

### v0.1 不支持

- 自由生成任意大规模代码改动
- 一次修多个不相关问题
- 跨多个工程自动找项目入口
- 自动做复杂架构级重构
- 没有诊断依据就盲改代码

---

## 3. 最适合 v0.1 的修复类型

建议 `v0.1` 只支持这种“低风险、高确定性”的修复动作：

### A. 宏开关类修复

例子：

- `MCUDBG_DEMO_BUGGY 1 -> 0`
- 某个 demo 故障开关关闭

这是最适合当前项目的第一类能力，因为：

- 改动小
- 很稳定
- 很容易验证
- 非常适合演示

### B. 配置值修复

例子：

- 错误的初始化参数改回正确值
- 错误的超时值、地址、阈值改回安全值

### C. 有明确模板的故障路径替换

例子：

- 明确的非法跳转路径替换成正常路径
- 明确的错误初始化分支替换成安全分支

---

## 4. 建议输入

`attempt_fix_and_verify` 建议输入如下：

```json
{
  "issue_description": "板子灯不闪",
  "diagnosis_type": "hardfault_detected",
  "suspected_root_causes": [
    "invalid execution target or illegal function entry"
  ],
  "fix_strategy": "disable_demo_fault_injection",
  "auto_build": true,
  "auto_flash": true,
  "auto_verify": true,
  "verification_log_lines": 30,
  "expected_recovery_signal": "startup_completed_normally"
}
```

### 字段说明

- `issue_description`
  - 原始用户描述
- `diagnosis_type`
  - 当前诊断结果类型
- `suspected_root_causes`
  - 诊断阶段得出的根因候选
- `fix_strategy`
  - 本次明确选择哪种修复策略
- `auto_build`
  - 是否自动编译
- `auto_flash`
  - 是否自动烧录
- `auto_verify`
  - 是否自动验证
- `verification_log_lines`
  - 验证时读取多少行日志
- `expected_recovery_signal`
  - 期待最终出现什么结果

---

## 5. 建议输出

输出应该更偏“调试闭环摘要”，而不是只给一堆原始字段。

```json
{
  "status": "ok",
  "summary": "Applied fix strategy disable_demo_fault_injection and verified normal startup on target board.",
  "fix_applied": true,
  "fix_strategy": "disable_demo_fault_injection",
  "code_change": {
    "file": "d:/embed-mcp/实验1 跑马灯(RGB)实验/USER/main.c",
    "change_summary": "Set MCUDBG_DEMO_BUGGY from 1 to 0."
  },
  "build": {
    "status": "ok"
  },
  "flash": {
    "status": "ok"
  },
  "verification": {
    "status": "ok",
    "diagnosis_type": "startup_completed_normally",
    "last_meaningful_log": "app loop running"
  },
  "before_after": {
    "before": "hardfault_detected",
    "after": "startup_completed_normally"
  },
  "evidence": [
    "Faulting firmware previously stopped after sensor init...",
    "Rebuilt and reflashed firmware successfully.",
    "New logs continued through app loop running."
  ],
  "suggested_next_steps": [
    "Repeat once to confirm the recovery is stable.",
    "Capture a demo video of the full repair loop."
  ]
}
```

---

## 6. v0.1 推荐修复策略集合

建议把 `fix_strategy` 做成受控集合，而不是自由文本。

### 第一批建议策略

- `disable_demo_fault_injection`
- `restore_safe_startup_path`
- `replace_invalid_execution_target`
- `restore_expected_init_config`

在 `v0.1`，最值得先落地的是：

- `disable_demo_fault_injection`

因为它已经被真实验证过。

---

## 7. v0.1 内部流程

建议的执行顺序：

1. 校验当前输入
2. 校验当前诊断结果是否支持自动修复
3. 选择并执行修复策略
4. 记录改动摘要
5. 调用 `disconnect_all`
6. 调用 `build_project`
7. 调用 `flash_firmware`
8. 调用 `connect_with_config`
9. 调用 `probe_reset`
10. 调用 `log_tail`
11. 调用 `diagnose_startup_failure`
12. 根据结果判断是否恢复
13. 调用 `disconnect_all`
14. 返回前后对比结果

---

## 8. 失败处理

`attempt_fix_and_verify` 不能把所有失败都压成一句“失败了”。

建议区分这些状态：

- `fix_not_applicable`
  - 当前诊断结果不适合自动修复
- `fix_apply_failed`
  - 代码修改没有成功完成
- `build_failed`
  - 编译失败
- `flash_failed`
  - 烧录失败
- `verification_failed`
  - build/flash 成功，但恢复验证没通过
- `partial_success`
  - 修复动作完成，但验证结果不够确定

---

## 9. v0.1 成功标准

如果下面这些都成立，就说明 `attempt_fix_and_verify v0.1` 是成功的：

1. 能基于受控策略改动代码
2. 能自动串起 build/flash/verify
3. 能输出修复前后对比
4. 能明确说明“修复成功”还是“修复未验证通过”
5. 能在当前 STM32L4 demo 上稳定复现

---

## 10. 为什么这个能力重要

如果没有 `attempt_fix_and_verify`，`mcudbg` 依然更像：

- 很会看现场的工具
- 很会输出诊断的工具

但有了这个能力以后，它开始接近：

**一个能完成最小调试闭环的系统。**

这对产品方向非常重要，因为它把项目从：

- `read board state`

往前推进到：

- `change code`
- `rebuild`
- `reflash`
- `re-verify`

也就是从“看懂问题”走向“推进问题被解决”。

---

## 一句话总结

`attempt_fix_and_verify v0.1` 不追求万能，而是先把一类低风险、可控、可验证的修复动作收成标准闭环，让 `mcudbg` 从诊断工具继续走向调试执行工具。
