# mcudbg Auto-Fix Demo 方案

## Demo 目标

这次 demo 要展示的不是：

- `mcudbg` 可以连板
- `mcudbg` 可以输出一段诊断 JSON

而是更强的一件事：

**AI 面对一块真实有 bug 的板子，完成一次“发现问题 -> 定位问题 -> 修改代码 -> 重新编译烧录 -> 验证恢复”的闭环。**

核心叙事是：

`buggy firmware -> board HardFault -> AI diagnosis -> AI code fix -> build_project -> flash_firmware -> reset -> logs recovered`

## 当前最适合的 demo 边界

基于你现在已经跑通的能力，最稳的闭环 demo 范围是：

- 板子：`STM32L496VETx`
- probe：`ST-Link`
- runtime：`pyOCD`
- 日志：`UART`
- 编译：`Keil UV4`
- 下载：`Keil UV4`
- 诊断：`diagnose_startup_failure` + `diagnose_hardfault`
- bug 类型：非法执行目标，触发 `instruction_access_violation`

这条链已经是现实可跑的，不需要再靠讲故事补空白。

## 适合 demo 的代码设计

当前 [main.c](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/main.c) 已经有开关：

```c
#define MCUDBG_DEMO_BUGGY 1
```

你可以把它当成 demo 里的“故障开关”。

### Buggy 版本

```c
#define MCUDBG_DEMO_BUGGY 1
```

表现：

- 打印到 `sensor init...`
- 进入 `HardFault`
- `mcudbg` 诊断为 `instruction_access_violation`

### Fixed 版本

```c
#define MCUDBG_DEMO_BUGGY 0
```

表现：

- 打印到 `sensor init...`
- 继续打印 `sensor init ok`
- 继续打印 `app loop running`
- 不再进入 `HardFault`

## Demo 结构

推荐控制在 `4` 到 `7` 分钟。

分成 7 幕。

### 第一幕：先展示 bug 代码

展示 [main.c](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/main.c) 中这几行：

```c
#define MCUDBG_DEMO_BUGGY 1
...
trigger_demo_hardfault();
...
void (*invalid_entry)(void) = (void (*)(void))0xFFFFFFFF;
invalid_entry();
```

旁白建议：

“这里我先故意在 STM32L4 固件里放一个会导致 startup HardFault 的 bug。等会我不手工排查，而是让 AI 直接去处理这块真板。”

### 第二幕：AI 编译并下载 buggy 固件

直接展示 MCP 调用：

```text
build_project()
flash_firmware()
```

展示重点：

- `build_project()` 返回成功
- `flash_firmware()` 返回成功

旁白建议：

“现在不是我手工点 Keil，而是让 AI 直接通过 `mcudbg` 调起编译和下载链路。”

### 第三幕：AI 读取板子现场

调用：

```text
connect_with_config()
probe_reset()
log_tail(30)
```

期望看到：

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...
[HardFault]
```

这一幕一定要让观众看到：

- 这是一块真板
- 这是实时日志
- 不是 mock

### 第四幕：AI 自动诊断

调用：

```text
diagnose_startup_failure()
diagnose_hardfault()
```

你要重点放大的不是完整 JSON，而是这些结论：

- `startup_failure_with_fault`
- `hardfault_detected`
- `instruction_access_violation`
- `PC -> HardFault_Handler`
- 根因方向：非法执行目标 / 错误函数入口

旁白建议：

“AI 现在已经拿到了真实日志、真实 fault 寄存器和真实符号信息，所以它判断这不是普通卡死，而是 startup 阶段的一次非法执行路径导致的 HardFault。”

### 第五幕：AI 修改代码

这一步建议你在 Codex 里直接下这种指令：

```text
根据当前板子的 HardFault 诊断结果，修复 sensor_init() 路径里的非法执行跳转问题，让系统继续正常启动。
```

最理想的演示结果是 AI 把：

```c
#define MCUDBG_DEMO_BUGGY 1
```

改成：

```c
#define MCUDBG_DEMO_BUGGY 0
```

如果你想让演示更“像真实修 bug”，也可以让 AI 解释：

- 为什么当前代码会 fault
- 为什么改成正常初始化路径后能恢复

### 第六幕：AI 重新编译和下载 fixed 固件

再次调用：

```text
build_project()
flash_firmware()
```

这一幕非常重要，因为它把“修复建议”变成了“修复闭环”。

### 第七幕：AI 再次验证，证明 bug 消失

调用：

```text
connect_with_config()
probe_reset()
log_tail(30)
diagnose_startup_failure()
```

修复后期望日志：

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...
sensor init ok
app loop running
```

修复后你要强调的点：

- 不再进入 `HardFault`
- startup 继续往下
- 板子恢复正常

这是整个 demo 最有说服力的一幕。

## 最推荐的演示词

你可以用这条一句话来串整个 demo：

“我先故意在 STM32 板子里放一个 bug。然后让 AI 自己编译、下载、连板、读日志、查 fault、改代码，再重新编译烧录，最后验证板子恢复正常。”

## 最短演示命令链

### 故障版本

```text
build_project()
flash_firmware()
connect_with_config()
probe_reset()
log_tail(30)
diagnose_startup_failure()
diagnose_hardfault()
```

### 修复版本

```text
build_project()
flash_firmware()
connect_with_config()
probe_reset()
log_tail(30)
diagnose_startup_failure()
```

## 需要提前准备的东西

为了让 demo 稳，建议提前准备：

1. 保证 [main.c](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/main.c) 当前是 `buggy` 版本
2. 确保 `ST-Link`、`COM3`、板子供电都稳定
3. 录屏前先手动跑一次 `build_project()` 和 `flash_firmware()`
4. 提前准备好修复后版本的预期日志

## 最值得放大的瞬间

这个 demo 最值得放大的不是工具列表，而是这 4 个瞬间：

1. AI 自己调用 `build_project()` 和 `flash_firmware()`
2. AI 读到真板 `[HardFault]`
3. AI 判断出 `instruction_access_violation`
4. AI 修复后，日志从 `sensor init...` 继续往下跑

如果这 4 个点都被观众看到，这个 demo 就成立了。

## 当前最准确的对外表述

这个 demo 最适合对外讲成：

**AI 驱动嵌入式调试闭环的第一版可运行验证**

或者：

**我让 AI 在一块真实 STM32 板子上，完成了一次从故障到修复的调试闭环**

不要急着讲成“AI 已经能自动修所有嵌入式 bug”。

你现在最强的地方在于：

**这条闭环已经真的在真板上跑起来了。**
