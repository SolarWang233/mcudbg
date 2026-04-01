# mcudbg 3 分钟录屏脚本

## 目标

这版脚本只服务一件事：

**在 3 分钟内，让观众看懂 AI 已经能在一块真实 STM32 板子上完成一次从故障到恢复的调试闭环。**

不要讲太多背景，不要展开太多架构。

只打最有冲击力的主线：

`有 bug 的代码 -> 真板 HardFault -> AI 诊断 -> AI 修复 -> 再编译下载 -> 板子恢复`

## 总时长建议

- 第 1 幕：20 秒
- 第 2 幕：25 秒
- 第 3 幕：35 秒
- 第 4 幕：35 秒
- 第 5 幕：25 秒
- 第 6 幕：40 秒

总计约 `3` 分钟。

## 第 1 幕：开场钩子

画面：

- VS Code 打开 [main.c](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/main.c)
- 高亮：

```c
#define MCUDBG_DEMO_BUGGY 1
```

和：

```c
void (*invalid_entry)(void) = (void (*)(void))0xFFFFFFFF;
invalid_entry();
```

台词：

“我先故意在 STM32L4 的启动路径里放一个 bug。它会让板子在 `sensor init...` 之后直接进入 HardFault。接下来我不手工查寄存器，而是让 AI 自己编译、下载、连板、诊断，再修复它。”

## 第 2 幕：AI 编译和下载故障固件

画面：

- Codex / MCP 面板
- 调用：

```text
disconnect_all()
load_demo_profile("stm32l4_atk_led_demo")
build_project()
flash_firmware()
```

台词：

“现在不是我手工点 Keil。AI 直接通过 `mcudbg` 调用了编译和下载链路，把这个故障固件烧进真板。”

重点停留：

- `build_project()` 成功
- `flash_firmware()` 成功

## 第 3 幕：AI 读取真板日志

画面：

- 调用：

```text
connect_with_config()
probe_reset()
log_tail(30)
```

展示日志：

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...
[HardFault]
```

台词：

“这里最关键。AI 现在看到的不是代码推测，而是这块真板子的 UART 日志和 probe 现场。”

## 第 4 幕：AI 诊断 HardFault

画面：

- 调用：

```text
diagnose_startup_failure()
diagnose_hardfault()
```

重点只展示这些结果：

- `startup_failure_with_fault`
- `hardfault_detected`
- `instruction_access_violation`
- `PC -> HardFault_Handler`

台词：

“AI 现在已经知道问题不是普通卡死，而是 startup 阶段发生了一次非法执行目标导致的 HardFault。”

## 第 5 幕：AI 修复代码

画面：

- 回到 [main.c](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/main.c)
- 把：

```c
#define MCUDBG_DEMO_BUGGY 1
```

改成：

```c
#define MCUDBG_DEMO_BUGGY 0
```

如果你想现场让 AI 说一句，可用这句：

“根据当前 HardFault 诊断结果，修复 startup 路径中的非法执行跳转问题。”

台词：

“修复并不复杂，关键是 AI 已经知道该改哪条路径。这里把故障开关切回正常初始化逻辑。”

## 第 6 幕：重新编译下载并验证恢复

画面：

- 调用：

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

重点展示修复后日志：

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...
sensor init ok
app loop running
```

重点展示修复后诊断：

- `startup_completed_normally`

台词：

“重新编译、重新下载之后，板子不再进入 HardFault，日志继续往下执行，`mcudbg` 也把结果判断成 `startup_completed_normally`。这就不是只会看问题，而是完成了一次真实的 embedded debug loop。”

## 结尾一句话

录屏最后建议用这句收尾：

“AI 在嵌入式里的下一步，不只是写代码，而是开始真正连接板子、读取现场、定位故障，并参与修复闭环。”

## 录屏时最重要的 5 个镜头

如果时间不够，至少保留这 5 个画面：

1. `MCUDBG_DEMO_BUGGY 1`
2. `flash_firmware()` 成功
3. `[HardFault]` 日志
4. `instruction_access_violation`
5. `startup_completed_normally`

## 录屏注意事项

- 开始前先 `disconnect_all()`
- 演示时避免打开 `Keil` debug session 抢 probe
- 串口窗口不要太花，尽量只保留核心日志
- JSON 不要整屏读，挑结论给观众看
- 你的重点不是“工具很多”，而是“闭环跑通了”
