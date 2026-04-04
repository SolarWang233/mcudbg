# mcudbg

**面向 AI 的嵌入式板级调试与观测工具。**

> 人类负责接线，AI 负责调板。

`mcudbg` 是一个 [MCP](https://modelcontextprotocol.io/) 服务端，给 AI 助手直接提供调试探针、CPU 寄存器、内存、ELF/DWARF 符号、UART 日志、SVD 外设寄存器和 RTOS 状态的访问能力。

很多 AI 编码工具只停留在“生成固件”。`mcudbg` 解决的是后面的那半段：板子不启动、串口没输出、程序跑进 HardFault、RTOS 任务卡死时，AI 仍然可以继续往下调。

## 快速示例

```text
用户： 这块板子上电后不启动，帮我看一下。

AI：   正在连接探针、暂停目标、读取寄存器……
       PC = 0x08001A3C -> HardFault_Handler (startup.s:42)
       CFSR = 0x00008200 -> 精确数据总线错误
       BFAR = 0x00000000 -> 可能访问了空指针
       固件在 sensor_init() 期间触发了空指针访问。
```

## 功能概览

### Probe backend

| Backend | 状态 |
|---------|------|
| pyOCD（ST-Link、CMSIS-DAP） | 完整支持 |
| J-Link（基于 `pylink-square`） | 完整支持 |

两个 backend 都已支持：

- connect / disconnect
- halt / resume / reset / single-step
- breakpoint / watchpoint
- memory read / write
- flash erase / program / verify
- fault register / FPU register

### ELF 与 DWARF

支持加载 ELF/AXF，用于：

- 符号解析
- 地址到源码行映射
- 源码级单步
- 反汇编附带源码位置
- 函数列表
- 本地变量读取
- backtrace

### SVD 外设检查

支持加载 CMSIS-SVD，用于：

- 解码外设寄存器
- 查看时钟使能
- 诊断外设配置错误
- 对寄存器 field 做读改写

### 按症状诊断

直接告诉 AI “哪里不对”，让 AI 决定先查什么。

| Tool | 用途 |
|------|------|
| `diagnose("board won't boot")` | 自动路由到合适的诊断路径 |
| `diagnose_hardfault` | 解析 fault register 并定位 PC |
| `diagnose_startup_failure` | 启动失败、日志和执行状态联合分析 |
| `diagnose_peripheral_stuck` | 时钟、引脚复用、使能位检查 |
| `diagnose_memory_corruption` | 栈溢出、越界写、内存破坏 |
| `diagnose_interrupt_issue` | NVIC 优先级、使能和 pending 状态 |
| `diagnose_clock_issue` | PLL、HSE、系统时钟树 |
| `diagnose_stack_overflow` | SP、栈边界和 canary 检查 |

### RTOS 与 RTT

支持：

- FreeRTOS 任务列表
- 按任务读取上下文
- 栈使用率扫描
- Segger RTT 日志读取
- J-Link 原生 RTT 读取，以及 RAM 扫描 fallback

在真实硬件上已经验证过的 FreeRTOS 同步场景包括：

- queue send / receive
- binary semaphore handoff
- software timer（`Tmr Svc`）
- event group wait / sync
- task notify
- mutex handoff 与阻塞等待者检查
- ISR-to-task notify（通过定时器中断）

### 构建与烧录

支持 Keil UV4 的 build / flash 集成，也支持独立的 flash：

- `erase_flash`
- `program_flash`
- `verify_flash`

典型闭环是：

`诊断 -> 改代码 -> build -> flash -> verify`

### GDB Server

支持启动、停止和查看以下 GDB server：

- pyOCD GDB server
- J-Link GDB server

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

要求：

- Python 3.10+
- 受支持的调试探针
- 带调试符号的 ELF/AXF

可选：

- CMSIS-SVD 文件
- J-Link backend 需要 `pylink-square`

## 文档

- [AI Playbook](docs/ai-playbook.md)：给 AI 助手的操作手册
- [v0.6 Roadmap](docs/v0.6-roadmap.md)：后续路线图

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

在 macOS / Linux 上请使用 `python3`。

## 快速开始

### 1. 连接探针并加载符号

```python
list_supported_targets("pyocd")  # 可选：先看内建支持矩阵
probe_connect(target="stm32l496vetx", backend="pyocd")
elf_load("firmware.axf")
svd_load("STM32L4x6.svd")  # 可选
```

如果使用 J-Link：

```python
probe_connect(target="STM32F103C8", backend="jlink", unique_id="240710115")
```

### 2. 先看 CPU 停在哪里

```python
probe_halt()
read_stopped_context()
```

### 3. 做源码级调试

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

### 5. 做高层诊断

```python
diagnose("UART2 has no output")
diagnose_hardfault()
```

### 6. 做 flash 操作

```python
erase_flash(start_address=0x08010000, end_address=0x08010800)
program_flash(0x08010000, [0xAA, 0x55, 0x12, 0x34], verify=True)
```

## Tool 分组（70+）

### 配置

`get_runtime_config`、`list_demo_profiles`、`load_demo_profile`、`configure_probe`、`configure_log`、`configure_elf`、`configure_build`、`connect_with_config`

### Probe 控制与单步

`list_connected_probes`、`probe_connect`、`probe_disconnect`、`probe_halt`、`probe_resume`、`probe_reset`、`probe_step`、`continue_target`、`probe_continue_until`、`step_over`、`step_out`、`source_step`、`run_to_source`、`run_to_function`

### 断点与观察点

`set_breakpoint`、`set_breakpoints_for_function_range`、`clear_breakpoint`、`clear_all_breakpoints`、`probe_set_watchpoint`、`probe_remove_watchpoint`、`probe_clear_all_watchpoints`

### 寄存器、内存与状态

`probe_read_registers`、`probe_read_fpu_registers`、`probe_read_mpu_regions`、`probe_read_memory`、`probe_write_memory`、`dump_memory`、`memory_find`、`memory_snapshot`、`memory_diff`、`read_memory_map`、`read_stopped_context`、`erase_flash`、`program_flash`、`verify_flash`

### ELF 与 DWARF

`elf_load`、`elf_addr_to_source`、`elf_list_functions`、`elf_symbol_info`、`read_symbol_value`、`write_symbol_value`、`watch_symbol`、`disassemble`、`backtrace`、`dwarf_backtrace`、`get_locals`、`set_local`、`log_trace`、`reset_and_trace`、`compare_elf_to_flash`

### 日志、RTOS 与 RTT

`log_connect`、`log_disconnect`、`log_tail`、`list_rtos_tasks`、`rtos_task_context`、`read_rtt_log`、`read_stack_usage`

### SVD 与外设诊断

`svd_load`、`svd_list_peripherals`、`svd_get_registers`、`svd_read_peripheral`、`svd_write_register`、`svd_write_field`、`diagnose_peripheral_stuck`

### 高层诊断

`diagnose`、`diagnose_hardfault`、`diagnose_startup_failure`、`diagnose_memory_corruption`、`diagnose_stack_overflow`、`diagnose_interrupt_issue`、`diagnose_clock_issue`、`run_debug_loop`

### Build、flash、GDB 与生命周期

`build_project`、`flash_firmware`、`start_gdb_server`、`stop_gdb_server`、`get_gdb_server_status`、`start_jlink_gdb_server`、`stop_jlink_gdb_server`、`get_jlink_gdb_server_status`、`disconnect_all`

## 真实硬件验证

| 板子 | MCU | Probe | 已验证能力 |
|------|-----|-------|------------|
| ATK_PICTURE | STM32L496VETx | ST-Link（pyOCD） | 完整：ELF、DWARF、SVD、flash、RTT、RTOS、diagnosis、GDB server；已验证 FreeRTOS queue / semaphore / timer / event-group / task-notify / mutex / ISR-notify |
| 自定义板 | STM32F103C8 | J-Link | 完整：connect、registers、memory、watchpoints、flash erase / program / verify、J-Link GDB server、RTT |

近期在 `STM32F103C8` 上的 J-Link RTT 验证结果：

- 自动发现 `JLink_x64.dll`
- 检测到 RTT 控制块地址：`0x20004644`
- 成功通过 J-Link backend 读取 channel 0 的实时文本：
  - `vTaskMsgPro alive`

当前自动化测试：`94 passed`

## 架构

```text
AI assistant / IDE / Agent
        |
        v
     mcudbg MCP server
        |
        +-- core / session / tools / result shaping
        |
        +-- probe backends
        |    +-- pyOCD (ST-Link, CMSIS-DAP)
        |    +-- J-Link (pylink-square)
        |
        +-- UART log / RTT / SVD / ELF-DWARF / RTOS
```

后续可扩展模块：

- `mcudbg-io`（GPIO）
- `mcudbg-bench`（万用表、电源、示波器、逻辑分析仪）

## 当前限制

- 当前 build / flash 集成主要面向 Windows + Keil UV4
- J-Link 的高阶 trace 仍在继续扩展
- SWO 在部分板子上可能受板级引脚复用限制
