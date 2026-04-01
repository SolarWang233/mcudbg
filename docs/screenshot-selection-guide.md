# mcudbg 截图选择指南

## 目标

这份指南只做一件事：

**告诉你在 README、公众号、GitHub 动态、短帖里，最值得截哪几张图。**

原则不是“截得多”，而是：

**每一张图都在强化同一个事实：AI 已经在真板上跑通了从故障到恢复的调试闭环。**

## 最推荐的 6 张截图

如果你只准备一套最小素材，我建议就准备这 6 张。

### 1. Buggy 代码截图

截图位置：

- [main.c](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/main.c)

建议截到的内容：

```c
#define MCUDBG_DEMO_BUGGY 1
...
void (*invalid_entry)(void) = (void (*)(void))0xFFFFFFFF;
invalid_entry();
```

这张图的作用：

- 证明 bug 是真实代码，不是口头设定
- 给后面的 HardFault 一个明确起点

建议图注：

`故意在 startup 路径里放一个非法执行跳转 bug`

### 2. build_project() 成功截图

建议截图重点：

- `Keil batch build completed successfully`
- `0 Error(s), 0 Warning(s)`

这张图的作用：

- 证明 AI 已经开始驱动编译链
- 不是手工点 Keil

建议图注：

`AI 直接调用 Keil 批量编译工程`

### 3. flash_firmware() 成功截图

建议截图重点：

- `Keil batch flash download completed successfully`
- `Erase Done`
- `Programming Done`
- `Verify OK`
- `Application running`

这张图很重要。

因为它把你的故事从“AI 会分析”推进到了：

**AI 会把固件真的烧进板子。**

建议图注：

`AI 直接完成固件下载和校验`

### 4. 故障日志截图

建议截图重点：

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...
[HardFault]
```

如果空间够，再带上：

```text
CFSR = 0x00000001
HFSR = 0x40000000
```

这张图的作用：

- 证明 fault 发生在真板
- 让观众直观看到“启动到了哪一步、在哪一步挂掉”

建议图注：

`真板启动到 sensor init 后进入 HardFault`

### 5. diagnose_hardfault() 结果截图

建议截图重点只保留这几行，不要整屏大 JSON：

- `hardfault_detected`
- `instruction_access_violation`
- `PC -> HardFault_Handler`
- `invalid execution target or illegal function entry`

这张图的作用：

- 证明 AI 不是只会“看见异常”
- 而是能把 fault 类型和根因方向说清楚

建议图注：

`AI 结合 probe、log 和 ELF 符号给出故障诊断`

### 6. 修复后恢复截图

建议截图重点：

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...
sensor init ok
app loop running
```

再加上：

- `startup_completed_normally`

这是整套素材里最值钱的一张。

因为它证明的不是“看懂了 bug”，而是：

**完成了从故障到恢复的闭环。**

建议图注：

`修复后重新编译下载，板子恢复正常启动`

## 如果只能发 3 张图

如果你的平台空间有限，只发这 3 张最够用：

1. 故障日志图
2. `diagnose_hardfault()` 结果图
3. 修复后恢复图

这 3 张已经足够讲清楚：

`有问题 -> AI 看懂 -> 修好后恢复`

## README 最适合的截图组合

README 最推荐放 4 张：

1. `build_project()` 成功图
2. `flash_firmware()` 成功图
3. `HardFault` 日志图
4. `startup_completed_normally` 恢复图

README 的重点不是情绪，而是：

- 真链路
- 真工具
- 真结果

## 公众号最适合的截图组合

公众号最推荐放 5 张：

1. Buggy 代码图
2. `HardFault` 日志图
3. `diagnose_hardfault()` 图
4. 修复代码图
5. 恢复后日志图

公众号比 README 更适合讲叙事，所以代码图和 before/after 对比图会更有用。

## 社媒短帖最适合的截图组合

如果你发即刻、微博、X、朋友圈，最推荐只放 2 到 3 张：

1. `HardFault` 日志图
2. `diagnose_hardfault()` 图
3. `startup_completed_normally` 图

短平台不要塞太多。

最关键的是让人一眼看到：

- 真板挂了
- AI 看懂了
- AI 修完后恢复了

## 截图时的注意事项

### 1. 不要整屏都是 JSON

如果输出太长，优先截核心字段：

- `diagnosis_type`
- `summary`
- `fault_class`
- `pc_symbol`
- `suspected_root_causes`

### 2. 画面里尽量保留真板痕迹

哪怕只有一点点，也尽量让人感知到：

- 这是实际串口输出
- 这是真实 probe 调试
- 这不是离线 mock

### 3. before / after 要成对

最强的传播素材通常不是单图，而是对比：

- 故障前
- 修复后

### 4. 一张图只讲一件事

不要试图一张图里既讲 build、又讲 flash、又讲 diagnose。

一张图只强化一个信息点，传播效果反而更强。

## 最终建议

如果你现在就要开始准备发文，我建议你优先截这 4 张：

1. `flash_firmware()` 成功
2. `[HardFault]` 日志
3. `diagnose_hardfault()` 的核心结论
4. `startup_completed_normally`

这 4 张足够支撑：

- README
- 公众号
- GitHub 动态
- 社媒短帖

而且它们共同讲的是同一件事：

**AI 不只是会写嵌入式代码，而是已经开始在真板上参与调试闭环。**
