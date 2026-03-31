# mcudbg Demo Buggy / Fixed 版本方案

## 目标

为了让 demo 更顺，最好的方式不是临场手改一大段代码，而是提前准备好：

- 一个 `buggy` 版本
- 一个 `fixed` 版本

这样你演示时可以稳定完成这条叙事：

`有 bug 的代码 -> 真板出错 -> AI 诊断 -> AI 修复 -> 真板恢复`

## 当前实现方式

在 [main.c](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/main.c) 里，现在已经加入了一个演示开关：

```c
#define MCUDBG_DEMO_BUGGY 1
```

含义如下：

- `1`：buggy 版本
- `0`：fixed 版本

## Buggy 版本行为

当：

```c
#define MCUDBG_DEMO_BUGGY 1
```

时，`sensor_init()` 里会走这条路径：

```c
trigger_demo_hardfault();
```

而 `trigger_demo_hardfault()` 会执行：

```c
void (*invalid_entry)(void) = (void (*)(void))0xFFFFFFFF;
invalid_entry();
```

这会导致：

- 启动日志打印到 `sensor init...`
- 随后进入 `HardFault`
- UART 打印出 fault 现场

这是你当前 demo 的“故障版本”。

## Fixed 版本行为

当：

```c
#define MCUDBG_DEMO_BUGGY 0
```

时，`sensor_init()` 里会走正常路径：

```c
sensor_init_success_path();
```

它会打印：

```text
sensor init ok
app loop running
```

这意味着：

- 板子不再进入 `HardFault`
- 日志会继续往下
- 你可以用它作为“修复后验证成功”的结束画面

## 最推荐的演示方式

### 方案一：单文件开关切换

这是当前最简单、最稳的方案。

步骤如下：

1. 先把 `MCUDBG_DEMO_BUGGY` 设为 `1`
2. 编译并烧录，作为故障版本
3. 让 AI 诊断
4. 再把 `MCUDBG_DEMO_BUGGY` 改成 `0`
5. 重新编译并烧录，作为修复版本
6. 再次验证日志恢复正常

### 方案二：准备两个分支或两份截图

如果你担心录屏时改宏定义不够顺，可以提前准备：

- `buggy` 代码截图
- `fixed` 代码截图

现场让 AI 给出修复建议后，你再切到修复后的版本去编译运行。

这样演示会更流畅。

## 录屏时最值得展示的代码差异

你真正要让观众看到的，不是很多行代码，而是这一点：

### Buggy 版本

```c
#define MCUDBG_DEMO_BUGGY 1
```

### Fixed 版本

```c
#define MCUDBG_DEMO_BUGGY 0
```

你可以把这个差异讲成：

“这里我先故意让固件跳到非法执行地址，制造一个真实 startup HardFault。等 AI 诊断完以后，我再把它切回正常初始化路径，重新编译烧录，验证板子恢复正常。”

## 预期日志差异

### Buggy 版本

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

### Fixed 版本

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

这组差异非常适合录屏最后做 before / after 对比。

## 最适合 AI 修复时说的话

你可以在 demo 里让 AI 接这样的提示：

“根据当前板子的 HardFault 诊断结果，修复 `sensor_init()` 路径中的非法执行跳转问题，让系统继续正常启动。”

因为当前代码结构已经是可切换的，所以这个提示会更容易导向你想要的演示结果。

## 推荐最终讲法

你可以把整个修复过程讲成：

“我先故意放了一个会导致 startup HardFault 的 bug。AI 通过 probe、UART 和 ELF 诊断出问题后，我再让它把这段故障路径改回正常初始化逻辑。重新烧录之后，板子不再进 HardFault，日志继续往下运行。”

这会比单纯展示“AI 输出了一个 diagnosis JSON”更有说服力。
