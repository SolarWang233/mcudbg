# mcudbg Final Demo Runbook

## Demo 目标

这份 runbook 用于执行 `mcudbg` 当前最强的一条真实闭环 demo：

`AI 编译 -> AI 下载 -> AI 连板 -> AI 读取日志 -> AI 诊断 HardFault -> AI 修复代码 -> AI 再编译下载 -> AI 验证恢复`

这不是 mock，不是模拟器，也不是离线分析。

这是基于以下真实链路：

- 板子：`STM32L496VETx`
- probe：`ST-Link`
- runtime：`pyOCD`
- log：`UART`
- 编译：`Keil UV4`
- 下载：`Keil UV4`
- 诊断：`mcudbg`

## Demo 要证明什么

演示要让观众明确看到两件事：

1. AI 已经可以读取一块真实嵌入式板子的故障现场
2. AI 已经可以参与一次真实的嵌入式调试闭环，而不只是“输出建议”

## 当前演示版本

当前建议使用两版固件来演示：

### Buggy 版本

[main.c](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/main.c) 中：

```c
#define MCUDBG_DEMO_BUGGY 1
```

效果：

- 板子启动到 `sensor init...`
- 随后进入 `HardFault`
- `mcudbg` 诊断为：
  - `startup_failure_with_fault`
  - `hardfault_detected`
  - `instruction_access_violation`

### Fixed 版本

[main.c](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/main.c) 中：

```c
#define MCUDBG_DEMO_BUGGY 0
```

效果：

- 板子继续打印：
  - `sensor init ok`
  - `app loop running`
- `mcudbg` 诊断为：
  - `startup_completed_normally`

## 演示前准备

演示前确认：

1. 板子已上电
2. `ST-Link` 已连接
3. 串口为 `COM3`
4. `mcudbg` MCP server 已正常加载
5. 演示开始前先执行一次：

```text
disconnect_all()
```

这一步很重要，可以尽量避免探针或串口残留占用。

## 演示主线

推荐按下面 8 幕来录。

### 第一幕：展示 bug 代码

打开 [main.c](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/main.c)，展示：

```c
#define MCUDBG_DEMO_BUGGY 1
```

以及：

```c
void (*invalid_entry)(void) = (void (*)(void))0xFFFFFFFF;
invalid_entry();
```

旁白建议：

“这里我先故意放一个会导致 startup HardFault 的 bug。接下来我不手工调板子，而是让 AI 直接去处理这块真板。”

### 第二幕：AI 清场

调用：

```text
disconnect_all()
```

目的：

- 释放 probe
- 释放串口
- 让后续 build/flash/diagnose 更稳

### 第三幕：AI 编译并下载 buggy 固件

调用：

```text
load_demo_profile("stm32l4_atk_led_demo")
build_project()
flash_firmware()
```

你要重点展示：

- `build_project()` 成功
- `flash_firmware()` 成功

这一步意味着 AI 已经不只是“看代码”，而是在真正驱动嵌入式工具链。

### 第四幕：AI 连接板子并读取现场

调用：

```text
connect_with_config()
probe_reset()
log_tail(30)
```

预期日志：

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...
[HardFault]
...
```

这一幕一定要给观众看，因为它能最直接证明：

**AI 看到的不是代码推测，而是板子真实现场。**

### 第五幕：AI 诊断故障

调用：

```text
diagnose_startup_failure()
diagnose_hardfault()
```

预期重点结果：

- `startup_failure_with_fault`
- `hardfault_detected`
- `instruction_access_violation`
- `PC -> HardFault_Handler`

你要讲的不是“JSON 很长”，而是：

“AI 知道 fault 发生在 startup 的 `sensor init` 附近，并且能判断这是一次非法执行目标导致的 HardFault。”

### 第六幕：AI 修复代码

把 [main.c](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/main.c) 里的：

```c
#define MCUDBG_DEMO_BUGGY 1
```

改成：

```c
#define MCUDBG_DEMO_BUGGY 0
```

如果你现场让 AI 来改，可以给它这个提示：

```text
根据当前板子的 HardFault 诊断结果，修复 sensor_init() 路径中的非法执行跳转问题，让系统继续正常启动。
```

### 第七幕：AI 重新编译和下载 fixed 固件

再次调用：

```text
disconnect_all()
build_project()
flash_firmware()
```

建议保留 `disconnect_all()`，这样第二轮更稳。

### 第八幕：AI 再次验证恢复结果

调用：

```text
connect_with_config()
probe_reset()
log_tail(30)
diagnose_startup_failure()
disconnect_all()
```

预期日志：

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...
sensor init ok
app loop running
```

预期诊断：

- `startup_completed_normally`

这是整个 demo 最关键的结束画面。

## 最短可执行命令序列

### 故障版本

```text
disconnect_all()
load_demo_profile("stm32l4_atk_led_demo")
build_project()
flash_firmware()
connect_with_config()
probe_reset()
log_tail(30)
diagnose_startup_failure()
diagnose_hardfault()
disconnect_all()
```

### 修复版本

```text
disconnect_all()
build_project()
flash_firmware()
connect_with_config()
probe_reset()
log_tail(30)
diagnose_startup_failure()
disconnect_all()
```

## 最值得截图的 6 个画面

1. `MCUDBG_DEMO_BUGGY 1` 的 buggy 代码
2. `build_project()` 成功输出
3. `flash_firmware()` 成功输出
4. `[HardFault]` 串口日志
5. `diagnose_hardfault()` 里 `instruction_access_violation`
6. 修复后 `sensor init ok` / `app loop running`

## 最适合的旁白主线

你可以全程围绕这一句来讲：

“我先故意在 STM32L4 的启动路径里放一个 bug。然后让 AI 自己编译、下载、连接真板、读取 UART 日志和 fault 现场，定位出这是一次 startup 阶段的非法执行跳转。接着我再让它修复代码，重新编译烧录，并验证板子恢复正常。”

## 演示时最重要的原则

不要试图在一次 demo 里展示太多能力。

你现在最能打动人的，不是：

- 工具列表很多
- 文档很多
- 架构很宏大

而是：

**你真的让 AI 在一块真实 STM32 板子上，完成了一次从故障到恢复的调试闭环。**

## 当前最准确的对外表述

这套 demo 最适合对外说成：

**AI 驱动嵌入式真板调试闭环的第一版可运行验证**

或者：

**我让 AI 在一块真实 STM32 板子上，从 HardFault 诊断走到了修复后验证**
