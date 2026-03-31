# 首发文章草稿：我做了一个让 AI 直接调试板子的工具

我最近在做一个项目，叫 `mcudbg`。

一句话说，它想解决的问题是：

**不是让 AI 只会写嵌入式代码，而是让 AI 也能真正读板子、看日志、连探针、定位故障。**

我一直觉得，AI 在嵌入式开发里最尴尬的一点是：

它可以帮你写驱动、写状态机、写初始化代码，但一旦代码真的烧到板子上，问题就开始变成另外一种东西。

这时候你关心的已经不是“这段 C 代码语法对不对”，而是：

- 板子到底有没有跑起来
- 串口日志停在哪一步
- 探针能不能连上
- 当前 PC 在哪
- 是卡死了、跑飞了，还是进了 HardFault
- 这个 fault 是无效指针、非法执行地址，还是寄存器访问问题

也就是说，真实世界里的嵌入式调试，本质上是一个“板级观测问题”。

而这正是我想做 `mcudbg` 的原因。

## 我想做的不是另一个 probe wrapper

我不想只做一个“让大模型调用 JLink / ST-Link / CMSIS-DAP”的包装层。

我真正想做的是：

**给 AI 一层板级调试与观测能力。**

理想状态下，人只需要接线，AI 就能逐步接管这些事情：

- 看 UART / RTT / log
- 连探针
- 读寄存器、内存、fault 状态
- 查符号
- 判断当前板子到底发生了什么
- 后面再继续扩展到 GPIO、电平、电压、波形、仪器

所以 `mcudbg` 的方向，从一开始就不是一个单点工具，而是：

**AI 的嵌入式现场诊断层**

## 我先把范围压得很窄

这个项目的坑非常大，所以我没有一开始就追求“全能平台”。

我把 `v0.1` 故意压成了一条很窄但很有代表性的路径：

- 板子：`STM32L496VETx`
- 探针：`ST-Link`
- probe runtime：`pyOCD`
- 日志：`UART`
- 符号：`ELF/AXF`
- 场景：启动过程中日志停在 `sensor init...`，随后进入 `HardFault`

我想先证明一件事：

**AI/MCP 工具链能不能在一块真实板子上，把一个真实 startup fault 看懂。**

## 这次不是 mock，不是模拟器，是真板验证

为了让这个场景稳定复现，我改了 STM32L4 的样板工程，让它：

1. 正常打印启动日志
2. 跑到 `sensor init...`
3. 故意跳到非法执行地址
4. 进入 `HardFault`
5. 在 `HardFault_Handler` 里把现场通过 UART 打印出来

最终板子实际打出来的日志是这样的：

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...

[HardFault]
MSP  = 0x20000738
SP[0]= 0xFFFFFFFF
SP[1]= 0x08001975
SP[2]= 0x00010B61
SP[3]= 0x00010B61
SP[4]= 0x00013880
SP[5]= 0x000003E8
SP[6]= 0x00000001
SP[7]= 0x0800273D
CFSR = 0x00000001
HFSR = 0x40000000
MMFAR= 0xE000ED34
BFAR = 0xE000ED38
SHCSR= 0x00000000
```

这一步对我来说很重要。

因为只有当板子侧的 fault 样本是真实的、稳定的、可重复的，后面的 AI 调试才不是空话。

## mcudbg 这次实际跑通了什么

在这块真板上，我已经实际跑通了这条 MCP 调用链：

```text
list_demo_profiles()
load_demo_profile("stm32l4_atk_led_demo")
connect_with_config()
log_tail(30)
diagnose_startup_failure()
diagnose_hardfault()
```

实际结果是：

- `connect_with_config()` 成功连接 probe、UART 和 ELF
- `log_tail(30)` 成功读到真实板子的启动日志和 HardFault 现场
- `diagnose_startup_failure()` 返回 `startup_failure_with_fault`
- `diagnose_hardfault()` 返回 `hardfault_detected`

更关键的是，诊断结果不是泛泛地说“程序出错了”，而是能给出有用的判断：

- 当前 fault class 是 `instruction_access_violation`
- fault 已升级成 `HardFault`
- `PC` 解析到 `HardFault_Handler`
- `LR` 解析到 `_printf_char_file`
- 根因更接近“非法执行目标 / 错误函数入口”

这说明 `mcudbg` 已经能把：

**真实日志 + 真实寄存器 + 真实 fault 状态 + 真实符号上下文**

组合成一个对人有帮助的诊断结果。

## 这件事为什么让我兴奋

因为这意味着一件我一直很想看到的事情，开始变得现实了：

**AI 不再只停留在“帮你写代码”，而是开始进入“帮你调板子”。**

这是两个完全不同的阶段。

前者更多是代码生成问题。
后者才真正进入嵌入式工程的核心现实：

- 硬件在不在
- 外设起没起来
- probe 连没连上
- 日志有没有停
- fault 是怎么来的

如果 AI 不能感知这些真实世界信号，那它在嵌入式里始终只能停留在“写得像工程师”，而不能真正“像工程师一样调试”。

我做 `mcudbg`，想推进的正是这一步。

## 现在的边界也很明确

我不会把这个结果吹成“全自动 AI 调试平台已经完成”。

现在它的边界很清楚：

- 只验证了一块 `STM32L4`
- 主线只验证了一个 startup fault 场景
- probe runtime 目前走的是 `pyOCD`
- 真实验证当前使用的是 `ST-Link`
- 还没有把 build / flash 自动化并进主线
- 还没有接入电压、电平、波形、仪器

但即使边界很窄，我也认为这已经是一个真实的 MVP。

因为它已经证明了一个最核心的产品命题：

**AI 可以在真实板子上，通过 probe + log + ELF 上下文，完成一次有意义的故障诊断。**

## 我接下来会继续做什么

接下来我会继续把这条线往前推，优先级大概是：

1. 把这次真实验证整理进 README 和 demo
2. 继续打磨 `startup failure / HardFault` 这条主路径
3. 让 build / flash 也进入工具链
4. 再往 GPIO、电压、电平、波形这些“更像现场工程师”的能力扩展

如果这个方向你也感兴趣，欢迎来看看 `mcudbg`。

我现在最想打磨清楚的不是“概念有多大”，而是：

**怎么把 AI 调板子这件事，从一句口号，变成一条真正能跑的工程链路。**
