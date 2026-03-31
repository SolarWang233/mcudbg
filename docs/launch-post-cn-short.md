# 中文短帖草稿

## 版本一：适合即刻 / 朋友圈 / 微博

我最近做了一个项目，叫 `mcudbg`。

它不是让 AI 只会写嵌入式代码，而是想让 AI 也能真正“调板子”。

我这次先做了一个很窄的 MVP：

- `STM32L4`
- `ST-Link`
- `UART`
- `ELF/AXF`
- 场景是启动跑到 `sensor init...` 后进入 `HardFault`

今天我把这条链路在真板上跑通了，不是 mock，不是模拟器。

`mcudbg` 已经可以：

- 连 probe
- 读串口日志
- 读 fault 寄存器
- 查符号
- 输出诊断结果

实际板子日志是：

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...
[HardFault]
CFSR = 0x00000001
HFSR = 0x40000000
```

工具最后给出的判断是：

- `startup_failure_with_fault`
- `hardfault_detected`
- fault class: `instruction_access_violation`
- `PC` 命中 `HardFault_Handler`

这件事让我很兴奋，因为它说明：

**AI 在嵌入式里，开始从“帮你写代码”走向“帮你看真实板子发生了什么”。**

我觉得这是个很值得继续往下推的方向。

## 版本二：更口语一点

我最近在做一个叫 `mcudbg` 的东西。

目标很直接：

**不是让 AI 只会写单片机代码，而是让 AI 也能直接参与调板子。**

这两天我先打通了第一条真板链路：

- `STM32L4`
- `ST-Link`
- `UART`
- `ELF`
- startup 阶段故意造一个 `HardFault`

然后让 `mcudbg` 去读真实日志、真实寄存器、真实 fault 状态。

结果它已经能在真板上给出正确诊断了。

这次对我来说最关键的不是“功能又多了一个”，而是终于证明了一件事：

**AI 调嵌入式，不一定只能停留在写代码，它是可以开始进入板级调试这一步的。**

后面我会继续把这条线往下做。

## 版本三：适合配图发 GitHub/X 动态

做了一个 `mcudbg`，想让 AI 真正参与嵌入式板级调试。

这次先在真板上打通了一个窄 MVP：

- `STM32L4`
- `ST-Link + pyOCD`
- `UART`
- `ELF`
- `sensor init... -> HardFault`

已经实测跑通：

- `connect_with_config()`
- `log_tail()`
- `diagnose_startup_failure()`
- `diagnose_hardfault()`

真实结果：

- 读到板子启动日志
- 读到 HardFault 现场
- 诊断出 `instruction_access_violation`
- 符号解析到 `HardFault_Handler`

不是 mock，是一块真的板子。

我现在越来越相信一件事：

**AI 在嵌入式里的下一步，不只是写代码，而是开始读板子、控工具、定位故障。**
