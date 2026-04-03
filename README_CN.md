# mcudbg

**让 AI 直接调试你的嵌入式板子。**

`mcudbg` 是一个面向嵌入式调试场景的 MCP Server。它把 AI 助手真正需要的硬件观察能力暴露出来，包括调试探针、CPU 寄存器、内存、ELF/DWARF 符号、UART 日志和外设寄存器。

> 人负责接线，AI 负责调试。

## 这个项目解决什么问题

很多 AI 工具只能帮你“写代码”，但真实的嵌入式问题发生在板子上：

- 上电不启动
- 串口没有输出
- 程序掉进 `HardFault`
- 外设配置错误，根本没工作
- 固件卡在启动流程、中断或死循环里

`mcudbg` 的目标不是让 AI 纸上谈兵，而是让它能直接观察板子、读取证据、缩小问题范围，并推动下一步调试动作。

## 当前能力

### Probe 与执行控制

- 连接 `pyOCD` 支持的探针，例如 ST-Link、CMSIS-DAP
- `halt / resume / reset / 单步`
- `step_over / step_out`
- 按符号或地址设置断点
- 设置硬件 watchpoint
- 运行到指定地址或条件命中
- 通过 MCP 直接做 flash 擦除、编程和校验
- 启动、停止并查看 `pyOCD` GDB server 状态

### ELF 与 DWARF

- 加载 ELF / AXF 做符号解析
- 地址解析到函数名和源码行
- 基于 `.debug_line` 的源码级单步
- 直接运行到某个源码行或函数
- 带源码注释的反汇编
- 函数列表与单符号详情查询
- 基于 DWARF 的局部变量读取
- 启发式和 DWARF 两种回溯

### 内存与运行态观察

- 读写目标内存
- 多格式内存 dump
- 内存快照与 diff
- RAM 字节模式搜索
- 比较 ELF section 与 flash 实际内容
- 读取 halted 上下文、FPU 寄存器、MPU 区域
- 直接按符号读写目标变量

### 基于 SVD 的外设寄存器分析

- 加载 CMSIS-SVD 文件
- 枚举外设和寄存器布局
- 从硬件读取并解码寄存器字段
- 写整个寄存器
- 按 field 做 read-modify-write
- 对常见外设问题做自动分析，例如时钟没开、复用配置不对

### 诊断能力

- `diagnose`
- `diagnose_hardfault`
- `diagnose_startup_failure`
- `diagnose_memory_corruption`
- `diagnose_stack_overflow`
- `diagnose_interrupt_issue`
- `diagnose_clock_issue`
- `diagnose_peripheral_stuck`

### RTOS 与 RTT 入口

- FreeRTOS 任务枚举
- 任务上下文读取
- Segger RTT 控制块扫描与日志读取

这些能力已经实现，但要想在真机上完整验证，仍需要对应条件的固件。

### Build / Flash

- Keil UV4 编译集成
- Keil UV4 烧录集成
- `erase_flash / program_flash / verify_flash`
- 可在 MCP 中串起调试闭环

## 真实硬件验证状态

当前不是只靠 mock 或单元测试，已经在真实硬件上做过验证。

已验证环境：

- 目标芯片：`STM32L496VETx`
- 开发板：`ATK_PICTURE`
- 调试探针：`ST-Link`
- ELF：`ATK_PICTURE.axf`

已在真机确认可用：

- ELF 加载与符号解析
- DWARF 源码映射
- `source_step`
- `run_to_function`
- `elf_symbol_info`
- `set_breakpoints_for_function_range`
- `disassemble`
- `read_memory_map`
- `probe_read_mpu_regions`
- `probe_set_watchpoint`
- `probe_remove_watchpoint`
- `probe_clear_all_watchpoints`
- `probe_read_fpu_registers`
- `erase_flash`
- `program_flash`
- `verify_flash`
- `start_gdb_server`
- `get_gdb_server_status`
- `stop_gdb_server`
- `read_rtt_log`
- `list_rtos_tasks`
- `rtos_task_context`
- `diagnose(symptom)`

最近的 flash 真机验证结果：

- `verify_flash()` 已对当前镜像头部做真机校验，`0x08000000` 处匹配成功
- 在 `0x08010000` scratch sector 上做了可恢复测试：
  `erase_flash()` 成功，读回为 `0xFF`
  `program_flash()` 写入 64 字节测试 pattern 成功
  `verify_flash()` 对 pattern 校验成功
  随后再写回 64 字节 `0x00` 并校验成功
- 这轮 flash 测试后板子仍正常启动，RTT 继续输出：
  `FreeRTOS demo boot`
  `Starting scheduler`
  `RTTTask alive count=...`

最近的 RTT 真机验证结果：

- `read_rtt_log()` 找到 RTT 控制块地址 `0x20012b38`
- `channel 0` 可读，`buffer_size = 1024`
- 实际读到：
  `mcudbg RTT ready`
  `board=ATK_PICTURE target=STM32L496VETx`
  `mcudbg RTT waiting: open 0:/PICTURE`

最近的 FreeRTOS 真机验证结果：

- `list_rtos_tasks()` 已看到：
  `RTTTask`、`ProducerTask`、`ConsumerTask`、`WorkerTask`、`LEDTask`、`IDLE`、`Tmr Svc`
- `rtos_task_context('ConsumerTask')` 成功解析到 `xQueueGenericReceive`
- `rtos_task_context('Tmr Svc')` 成功解析到 `prvProcessTimerOrBlockTask`
- `read_rtt_log()` 能稳定读到：
  `ProducerTask sent value=...`
  `ConsumerTask received value=...`
  `WorkerTask took semaphore`
  `TimerCallback fired count=...`

最近的统一诊断入口真机结果：

- `diagnose("board does not boot", include_logs=False, auto_halt=True)` 成功路由到 `diagnose_startup_failure`
- 返回中包含：
  `pc_symbol = prvCheckTasksWaitingTermination`
  `source = ..\FreeRTOS\tasks.c:3031`

最近的 GDB server 真机结果：

- `start_gdb_server()` 成功拉起 `pyOCD gdbserver`
- `get_gdb_server_status()` 返回：
  `host = 127.0.0.1`
  `port = 3333`
  `state = running`
  `target = stm32l496vetx`
- `stop_gdb_server()` 成功关闭后台进程

## 安装

```bash
pip install mcudbg
```

或者从源码安装：

```bash
git clone https://github.com/SolarWang233/mcudbg
cd mcudbg
pip install -e .
```

依赖条件：

- Python 3.10+
- 一只 `pyOCD` 支持的调试探针
- 带调试信息的 ELF / AXF
- 目标芯片对应的 CMSIS-SVD 文件

## MCP 配置

### Claude Desktop on Windows

```json
{
  "mcpServers": {
    "mcudbg": {
      "command": "python",
      "args": ["-m", "mcudbg"],
      "cwd": "C:/path/to/mcudbg"
    }
  }
}
```

### Claude Desktop on macOS / Linux

```json
{
  "mcpServers": {
    "mcudbg": {
      "command": "python3",
      "args": ["-m", "mcudbg"],
      "cwd": "/path/to/mcudbg"
    }
  }
}
```

## 快速开始

### 1. 枚举并连接探针

```python
list_connected_probes()
probe_connect(target="stm32l496vetx", unique_id="YOUR_PROBE_ID")
```

### 2. 加载 ELF 和可选的 SVD

```python
elf_load("D:/path/to/firmware.axf")
svd_load("D:/path/to/STM32L4x6.svd")
```

### 3. 看 CPU 停在什么位置

```python
probe_halt()
read_stopped_context()
elf_addr_to_source(0x08001234)
```

### 4. 做源码级调试

```python
run_to_function("main")
source_step()
step_over()
step_out()
```

### 5. 看外设和内存

```python
svd_read_peripheral("USART2")
svd_write_field("RCC", "CR", "PLLON", 1)
dump_memory(0x20000000, 64)
read_symbol_value("SystemCoreClock", 4)
```

### 6. 做故障诊断

```python
diagnose("board does not boot")
diagnose_startup_failure()
diagnose_hardfault()
diagnose_peripheral_stuck("USART2", "no output from TX pin")
diagnose_memory_corruption()
```

### 7. 擦除、编程并校验 flash

```python
erase_flash(start_address=0x08010000, end_address=0x08010800)
program_flash(0x08010000, [0xAA, 0x55, 0x12, 0x34], verify=True)
verify_flash(0x08010000, [0xAA, 0x55, 0x12, 0x34])
```

### 8. 启动 GDB server

```python
start_gdb_server()
get_gdb_server_status()
stop_gdb_server()
```

## 工具分组

### 配置

- `get_runtime_config`
- `list_demo_profiles`
- `load_demo_profile`
- `configure_probe`
- `configure_log`
- `configure_elf`
- `configure_build`
- `connect_with_config`

### GDB server

- `start_gdb_server`
- `stop_gdb_server`
- `get_gdb_server_status`

### Probe 控制与步进

- `list_connected_probes`
- `probe_connect`
- `probe_disconnect`
- `probe_halt`
- `probe_resume`
- `probe_reset`
- `probe_step`
- `continue_target`
- `probe_continue_until`
- `step_over`
- `step_out`
- `source_step`
- `run_to_source`
- `run_to_function`

### 断点与观察点

- `set_breakpoint`
- `set_breakpoints_for_function_range`
- `clear_breakpoint`
- `clear_all_breakpoints`
- `probe_set_watchpoint`
- `probe_remove_watchpoint`
- `probe_clear_all_watchpoints`

### 寄存器、内存与上下文

- `probe_read_registers`
- `probe_read_fpu_registers`
- `probe_read_mpu_regions`
- `probe_read_memory`
- `probe_write_memory`
- `dump_memory`
- `memory_find`
- `memory_snapshot`
- `memory_diff`
- `read_memory_map`
- `read_stopped_context`
- `erase_flash`
- `program_flash`
- `verify_flash`

### ELF 与 DWARF

- `elf_load`
- `elf_addr_to_source`
- `elf_list_functions`
- `elf_symbol_info`
- `read_symbol_value`
- `write_symbol_value`
- `watch_symbol`
- `disassemble`
- `backtrace`
- `dwarf_backtrace`
- `get_locals`
- `set_local`
- `log_trace`
- `reset_and_trace`
- `compare_elf_to_flash`

### 日志、RTOS 与 RTT

- `log_connect`
- `log_disconnect`
- `log_tail`
- `list_rtos_tasks`
- `rtos_task_context`
- `read_rtt_log`
- `read_stack_usage`

### SVD 与外设分析

- `svd_load`
- `svd_list_peripherals`
- `svd_get_registers`
- `svd_read_peripheral`
- `svd_write_register`
- `svd_write_field`
- `diagnose_peripheral_stuck`

### 更高层的诊断

- `diagnose`
- `diagnose_hardfault`
- `diagnose_startup_failure`
- `diagnose_memory_corruption`
- `diagnose_stack_overflow`
- `diagnose_interrupt_issue`
- `diagnose_clock_issue`
- `run_debug_loop`

### 编译、烧录与收尾

- `build_project`
- `flash_firmware`
- `disconnect_all`

## 已知限制

- 当前 probe backend 只有 `pyOCD`
- 编译与烧录集成当前只面向 Windows 上的 Keil UV4
- RTT 和 RTOS 相关能力要依赖匹配的固件条件
- 一些高级 DWARF 能力会受编译器和调试信息质量影响
- 项目不内置 SVD 文件，需要用户自行提供目标芯片对应版本

## 当前开发状态

- 本地自动化测试快照：`73 passed`
- 当前实现已经明显超出最早的 Phase 2 范围，进入 Phase 3 调试能力补全
- 最近新增了 `diagnose(symptom)` 统一入口、已在真机验证过的 flash `erase / program / verify`，以及 `GDB server` 生命周期入口
- 下一步高价值工作是补第二套 probe backend，例如 J-Link

## 参与贡献

欢迎提 Issue 和 PR。如果你在 STM32L4 之外的芯片上验证过 `mcudbg`，也很欢迎反馈结果。

## 许可证

MIT，见 [LICENSE](LICENSE)。
