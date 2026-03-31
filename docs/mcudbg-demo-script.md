# mcudbg Demo 演示脚本

## Demo 目标

这个 demo 要向观众证明的不是：

- `mcudbg` 能输出一段 JSON
- `mcudbg` 能连接某个调试器

而是下面这件更有冲击力的事：

**AI 可以面对一块真实出故障的板子，读现场、判断问题、定位 bug，并推动修复闭环。**

本次 demo 的主叙事是：

`有 bug 的代码 -> 板子启动异常 -> AI 读取 log 和 fault 现场 -> AI 定位原因 -> 修复后重新验证`

## 推荐 demo 版本

当前最推荐的是 `v1.5` 版本：

- bug 代码真实存在
- 板子是真板
- `mcudbg` 真实读取 probe / log / ELF
- AI 真实输出诊断
- 修复代码可以由 AI 完成
- build / flash 这一步可以先半自动

原因很简单：

你现在已经把“真板诊断”跑通了，但 `build / flash` 自动化还不是主线 MVP。
所以最稳的演示方式是：

- 诊断部分全真
- 修复部分全真
- 编译烧录根据现场情况决定人工或自动

## Demo 场景

硬件和软件环境：

- 板子：`STM32L496VETx`
- probe：`ST-Link`
- probe runtime：`pyOCD`
- log：`UART`
- firmware：`ATK_LED`
- 场景：启动打印到 `sensor init...` 后进入 `HardFault`

bug 设计：

- 在 `sensor init` 后故意跳转到非法执行目标
- 触发 `instruction_access_violation`
- 最终进入 `HardFault`

## 演示结构

整个 demo 建议控制在 `3` 到 `6` 分钟。

分成 6 幕。

### 第一幕：先展示 bug 是真实存在的

画面建议：

- 打开有 bug 的代码文件
- 高亮故障注入位置
- 不要一开始就解释太多，重点让观众看到“这里有一个真实 bug”

建议旁白：

“我先给这块 STM32L4 板子放一个真实 bug。它会在启动阶段打印到 `sensor init...`，然后跳到非法执行地址，最终进入 HardFault。”

如果你想更直接，可以补一句：

“这不是模拟器，也不是 mock，我等会让 AI 直接去读这块真板子的现场。”

### 第二幕：运行板子，让错误真正发生

画面建议：

- 展示串口工具或终端日志窗口
- 复位板子
- 让观众看到日志停在预期位置

推荐展示内容：

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...
[HardFault]
```

建议旁白：

“现在 bug 已经在真板上复现了。日志停在 `sensor init...`，随后进入 HardFault。接下来我不手工查寄存器，而是让 AI 去读这个现场。”

### 第三幕：AI 连接板子并读取现场

这一幕是整个 demo 的核心。

建议在 Codex / MCP 客户端里依次执行：

```text
list_demo_profiles()
load_demo_profile("stm32l4_atk_led_demo")
connect_with_config()
log_tail(30)
```

重点展示：

- `connect_with_config()` 成功连接 probe、UART 和 ELF
- `log_tail(30)` 读到真实板子日志

建议旁白：

“这里不是让 AI 只看代码，而是让它直接接入这块板子的 probe、UART 和 ELF 符号信息。”

### 第四幕：AI 自动诊断

继续执行：

```text
diagnose_startup_failure()
diagnose_hardfault()
```

你要重点展示的不是完整 JSON，而是几条最能让人理解价值的结论：

- `startup_failure_with_fault`
- `hardfault_detected`
- `instruction_access_violation`
- `PC -> HardFault_Handler`
- 根因接近非法执行目标

建议旁白：

“AI 现在已经不是在猜。它拿到了真实日志、真实寄存器、真实 fault 状态和 ELF 符号，所以能把问题定位到 startup 阶段的非法执行路径。”

### 第五幕：AI 修改 bug 代码

这一幕的重点是让观众看到：

**AI 不只是诊断，还开始参与修复。**

建议操作：

- 把有 bug 的代码给 AI
- 让 AI 解释为什么会 fault
- 再让 AI 直接改代码

推荐提示语：

“请根据当前板子日志和 HardFault 诊断结果，修复这段导致非法执行跳转的代码，并说明修改原因。”

如果现场演示要更稳，建议提前准备两个分支：

- `buggy` 分支
- `fixed` 分支

现场可以让 AI 先输出修复 diff，再切到修复后的代码版本，避免录屏时打字过长。

### 第六幕：重新验证，证明 bug 消失

最后一幕一定要有。

因为如果没有“修复后验证成功”，观众对 demo 的感受仍然停留在“看起来会诊断”。

建议操作：

- 重新编译和烧录
- 复位板子
- 再次读取日志

期望结果：

- 不再进入 HardFault
- 日志继续往下执行
- AI 给出“startup flow recovered”或“fault no longer observed”这类判断

建议旁白：

“这一步很重要。我们不是只做了一次诊断展示，而是完成了一次真实的 embedded debug loop。”

## 现场最推荐展示的工具调用顺序

这是录屏时最顺的一套顺序：

```text
list_demo_profiles()
load_demo_profile("stm32l4_atk_led_demo")
connect_with_config()
log_tail(30)
diagnose_startup_failure()
diagnose_hardfault()
```

如果要进入修复后的第二轮验证，再重复：

```text
connect_with_config()
log_tail(30)
diagnose_startup_failure()
diagnose_hardfault()
```

## Demo 里最值得放大的 5 个瞬间

这 5 个瞬间最能打动观众：

1. 真实 bug 代码被展示出来
2. 真板日志停在 `sensor init...`
3. `connect_with_config()` 成功连上 probe + UART + ELF
4. AI 判断出 `instruction_access_violation`
5. 修复后板子不再进 `HardFault`

如果录屏节奏有限，宁可删一些解释，也不要删这 5 个瞬间。

## 最适合放在视频或文章里的关键截图

建议至少准备 4 张截图：

1. 有 bug 的代码截图
2. 串口出现 `sensor init...` 和 `[HardFault]` 的截图
3. `diagnose_hardfault()` 输出核心结论的截图
4. 修复后日志正常继续运行的截图

## 推荐旁白主线

你可以用这条最简主线去串整个 demo：

“我先故意在 STM32 板子里放一个会导致 HardFault 的 bug。然后让 AI 直接连接真板，读取 UART 日志、probe 状态和 ELF 符号。接着它会判断 fault 发生在 startup 的 `sensor init` 附近，并识别出这是一次非法执行目标导致的 HardFault。最后我再让它修复这段代码，并重新验证板子恢复正常。”

## 当前 demo 的最佳定位

这个 demo 最适合对外讲成：

**AI 调试嵌入式真板的第一条可运行闭环**

不要讲成：

- 全自动调试平台已经完成
- 什么板子什么故障都能一键修

最有说服力的表述是：

**我已经把 AI 读真板、查真故障、给真诊断这件事，在一块 STM32 真板上跑通了。**

## 演示前检查清单

录屏前一定确认：

- `ST-Link` 没被别的软件占用
- 串口 `COM` 口正确
- 板子上电正常
- `ATK_LED.axf` 路径正确
- `mcudbg` demo profile 已加载
- 板子当前 firmware 是故障版本
- 修复版本也已经准备好

## 最终目标

这个 demo 最终不是为了展示一个工具命令列表，而是为了让别人看完后产生一个很强的感受：

**AI 开始不只是写嵌入式代码，而是真的开始参与调板子了。**
