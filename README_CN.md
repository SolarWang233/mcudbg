# mcudbg

**让 AI 直接调试你的嵌入式板子。**

> 人负责接线，AI 负责调试。

`mcudbg` 是一个 [MCP](https://modelcontextprotocol.io/) Server，让 AI 助手能直接访问调试探针、CPU 寄存器、内存、ELF/DWARF 符号、UART 日志、SVD 外设寄存器和 RTOS 状态。

大多数 AI 工具只能帮你写固件。`mcudbg` 解决的是写完之后的事——板子不启动、串口没输出、程序掉进 HardFault。

<!-- TODO: 替换为实际 demo GIF -->
<!-- ![demo](docs/demo.gif) -->

## 快速演示

```text
用户：这块板子上电后没起来，帮我看看。

AI：  连接探针… 暂停目标… 读取寄存器…
      PC = 0x08001A3C → HardFault_Handler (startup.s:42)
      CFSR = 0x00008200 — 精确数据总线错误
      BFAR = 0x00000000 — 空指针解引用
      固件在 sensor_init() 阶段访问了空指针。
      建议检查传给 HAL_I2C_Init() 的 I2C 句柄。
```

## 核心能力

### 调试探针

| 后端 | 状态 |
|------|------|
| pyOCD（ST-Link、CMSIS-DAP） | 完整支持 |
| J-Link（通过 pylink-square） | 完整支持 |

两种后端均支持：连接、halt、resume、reset、单步、断点、watchpoint、内存读写、flash 擦除/编程/校验、FPU 和 fault 寄存器。

### ELF 与 DWARF

加载 ELF/AXF 做符号解析、源码级单步、带源码注释的反汇编、函数列表、局部变量读取、调用栈回溯。

### SVD 外设寄存器

加载 CMSIS-SVD 文件，解码外设寄存器，检查时钟门控，按字段做 read-modify-write 诊断外设配置问题。

### 症状驱动的诊断

告诉 AI 哪里不对，它自己决定查什么。

| 工具 | 场景 |
|------|------|
| `diagnose("板子不启动")` | 自动路由到合适的诊断路径 |
| `diagnose_hardfault` | fault 寄存器解码 + PC 定位 |
| `diagnose_startup_failure` | 日志 + 执行状态分析 |
| `diagnose_peripheral_stuck` | 时钟门控、引脚复用、使能位 |
| `diagnose_memory_corruption` | 栈溢出、缓冲区越界 |
| `diagnose_interrupt_issue` | NVIC 优先级、使能、挂起 |
| `diagnose_clock_issue` | PLL、HSE、系统时钟树 |
| `diagnose_stack_overflow` | SP 与栈边界、canary 检查 |

### RTOS 与 RTT

FreeRTOS 任务枚举和逐任务上下文读取。Segger RTT 控制块扫描和日志读取。

### 编译与烧录

Keil UV4 编译和烧录集成。完整调试闭环：诊断 → 改代码 → 编译 → 烧录 → 验证。

### GDB Server

从 MCP 启动、停止和查询 pyOCD GDB server。

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

**依赖：** Python 3.10+，一只支持的调试探针，带调试信息的 ELF/AXF。

**可选：** CMSIS-SVD 文件用于外设寄存器解码。J-Link 后端需要 `pylink-square`。

## MCP 配置

### Claude Desktop / Claude Code

```json
{
  "mcpServers": {
    "mcudbg": {
      "command": "python",
      "args": ["-m", "mcudbg"]
    }
  }
}
```

macOS/Linux 上用 `python3`。

## 快速开始

### 1. 连接探针，加载符号

```python
probe_connect(target="stm32l496vetx", backend="pyocd")
elf_load("firmware.axf")
svd_load("STM32L4x6.svd")  # 可选
```

J-Link：

```python
probe_connect(target="STM32F103C8", backend="jlink", unique_id="240710115")
```

### 2. 看 CPU 停在哪

```python
probe_halt()
read_stopped_context()
```

### 3. 源码级调试

```python
run_to_function("main")
source_step()
step_over()
step_out()
```

### 4. 看外设和内存

```python
svd_read_peripheral("USART2")
dump_memory(0x20000000, 64)
read_symbol_value("SystemCoreClock", 4)
```

### 5. 故障诊断

```python
diagnose("UART2 没有输出")
diagnose_hardfault()
```

### 6. Flash 操作

```python
erase_flash(start_address=0x08010000, end_address=0x08010800)
program_flash(0x08010000, [0xAA, 0x55, 0x12, 0x34], verify=True)
```

## 全部工具（70+）

<details>
<summary>配置</summary>

`get_runtime_config` · `list_demo_profiles` · `load_demo_profile` · `configure_probe` · `configure_log` · `configure_elf` · `configure_build` · `connect_with_config`
</details>

<details>
<summary>Probe 控制与步进</summary>

`list_connected_probes` · `probe_connect` · `probe_disconnect` · `probe_halt` · `probe_resume` · `probe_reset` · `probe_step` · `continue_target` · `probe_continue_until` · `step_over` · `step_out` · `source_step` · `run_to_source` · `run_to_function`
</details>

<details>
<summary>断点与观察点</summary>

`set_breakpoint` · `set_breakpoints_for_function_range` · `clear_breakpoint` · `clear_all_breakpoints` · `probe_set_watchpoint` · `probe_remove_watchpoint` · `probe_clear_all_watchpoints`
</details>

<details>
<summary>寄存器、内存与上下文</summary>

`probe_read_registers` · `probe_read_fpu_registers` · `probe_read_mpu_regions` · `probe_read_memory` · `probe_write_memory` · `dump_memory` · `memory_find` · `memory_snapshot` · `memory_diff` · `read_memory_map` · `read_stopped_context` · `erase_flash` · `program_flash` · `verify_flash`
</details>

<details>
<summary>ELF 与 DWARF</summary>

`elf_load` · `elf_addr_to_source` · `elf_list_functions` · `elf_symbol_info` · `read_symbol_value` · `write_symbol_value` · `watch_symbol` · `disassemble` · `backtrace` · `dwarf_backtrace` · `get_locals` · `set_local` · `log_trace` · `reset_and_trace` · `compare_elf_to_flash`
</details>

<details>
<summary>日志、RTOS 与 RTT</summary>

`log_connect` · `log_disconnect` · `log_tail` · `list_rtos_tasks` · `rtos_task_context` · `read_rtt_log` · `read_stack_usage`
</details>

<details>
<summary>SVD 与外设诊断</summary>

`svd_load` · `svd_list_peripherals` · `svd_get_registers` · `svd_read_peripheral` · `svd_write_register` · `svd_write_field` · `diagnose_peripheral_stuck`
</details>

<details>
<summary>高层诊断</summary>

`diagnose` · `diagnose_hardfault` · `diagnose_startup_failure` · `diagnose_memory_corruption` · `diagnose_stack_overflow` · `diagnose_interrupt_issue` · `diagnose_clock_issue` · `run_debug_loop`
</details>

<details>
<summary>编译、烧录、GDB、生命周期</summary>

`build_project` · `flash_firmware` · `start_gdb_server` · `stop_gdb_server` · `get_gdb_server_status` · `disconnect_all`
</details>

## 真实硬件验证

| 开发板 | 芯片 | 探针 | 已验证能力 |
|--------|------|------|-----------|
| ATK_PICTURE | STM32L496VETx | ST-Link (pyOCD) | 全量：ELF、DWARF、SVD、flash、RTT、RTOS、诊断、GDB server |
| 自制板 | STM32F103C8 | J-Link | 全量：连接、寄存器、内存、watchpoint、flash 擦除/编程/校验 |

89 个自动化测试通过。

## 架构

```
AI 助手 / IDE / Agent
        │
        ▼
   ┌─────────┐
   │ mcudbg  │  MCP server
   │  core   │  会话、工具、结果格式化
   └────┬────┘
        │
   ┌────┴─────────────────────────┐
   │         probe backends       │
   ├──────────┬───────────────────┤
   │  pyOCD   │    J-Link         │
   │ (ST-Link,│  (pylink-square)  │
   │ CMSIS-DAP│                   │
   └──────────┴───────────────────┘
        │
   ┌────┴────┐  ┌────────┐  ┌──────┐
   │  UART   │  │  RTT   │  │ SVD  │
   │   log   │  │  log   │  │解析  │
   └─────────┘  └────────┘  └──────┘
```

未来模块：`mcudbg-io`（GPIO）、`mcudbg-bench`（万用表、电源、示波器、逻辑分析仪）。

## 已知限制

- 编译/烧录集成当前仅支持 Windows 上的 Keil UV4
- RTOS 检查需要 FreeRTOS 并匹配配置
- 高级 DWARF 功能受编译器调试信息质量影响
- SVD 文件不内置——需要用户提供目标芯片对应的文件

## 参与贡献

欢迎提 Issue 和 PR。如果你在 STM32 之外的芯片上验证过 mcudbg，特别欢迎反馈。

## 许可证

MIT，见 [LICENSE](LICENSE)。
