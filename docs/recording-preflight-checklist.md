# mcudbg 录屏前检查清单

## 目标

这份清单只服务一件事：

**让你在正式录 `mcudbg` demo 之前，把最容易翻车的地方先排干净。**

建议录屏前 `5` 到 `10` 分钟按顺序过一遍。

## 一、硬件状态

确认以下项目：

- `STM32L496VETx` 板子已上电
- `ST-Link` 已连接稳定
- `UART` 已连接稳定
- USB 线没有松动
- 板子当前能正常复位

最简单的判断：

- `ST-Link` 在系统里可见
- `COM3` 还在

## 二、避免资源占用

录屏前先关闭这些容易抢资源的程序：

- `Keil` 的 Debug Session
- 串口调试助手
- 任何可能占用 `ST-Link` 的调试工具

然后先执行一次：

```text
disconnect_all()
```

这一步很重要，能减少“第一次能跑、第二次找不到 ST-Link”的问题。

## 三、代码版本确认

录屏前要明确你现在要录的是哪一段：

### 故障段

[main.c](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/main.c) 中应为：

```c
#define MCUDBG_DEMO_BUGGY 1
```

### 修复段

[main.c](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/main.c) 中应为：

```c
#define MCUDBG_DEMO_BUGGY 0
```

如果你先录故障段，建议先确认当前确实是 `1`。

## 四、MCP 工具状态

在录屏开始前，建议先手工验证这几个工具还能正常调用：

```text
load_demo_profile("stm32l4_atk_led_demo")
build_project()
flash_firmware()
connect_with_config()
```

如果这四步都通，基本就说明当前 demo 状态是健康的。

## 五、日志预期确认

### 故障版本预期日志

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...
[HardFault]
```

### 修复版本预期日志

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...
sensor init ok
app loop running
```

录屏前你要先知道：

- 你现在这一轮该看到哪一种
- 如果看到不对，应该立刻停下来重试，而不是硬录

## 六、最重要的诊断结果

### 故障版本

你录屏时最关键的结论是：

- `startup_failure_with_fault`
- `hardfault_detected`
- `instruction_access_violation`

### 修复版本

你录屏时最关键的结论是：

- `startup_completed_normally`

如果这些结论没有出现，说明这一轮不适合正式录。

## 七、录屏窗口准备

建议只保留这些窗口：

1. `VS Code` 代码窗口
2. `Codex / MCP` 聊天面板
3. 必要时的串口日志窗口

尽量不要在屏幕上保留：

- 太多标签页
- 无关终端
- 无关聊天窗口
- 会打断注意力的通知

## 八、最容易翻车的 5 个点

录屏前重点检查：

1. `ST-Link` 是否还在线
2. 串口是否还在 `COM3`
3. 当前是不是正确的 `buggy` / `fixed` 宏值
4. `disconnect_all()` 是否先跑过
5. `build_project()` 和 `flash_firmware()` 是否能先试通一次

## 九、正式录屏前最后一次试跑

建议正式录屏前，先完整试跑一次：

### 故障段试跑

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

### 修复段试跑

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

只有试跑成功后，再正式点录制。

## 十、录屏时最稳的原则

如果现场有任何一步异常，不要硬撑着继续讲。

最稳的做法是：

- 停下来
- `disconnect_all()`
- 重新加载 profile
- 重新跑当前阶段

你的 demo 最重要的不是“一次性演完”，而是：

**每一步都像真的工程链路，而不是硬撑过去。**
