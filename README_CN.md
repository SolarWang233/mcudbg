# mcudbg

**让 AI 直接调试你的嵌入式板子。**

`mcudbg` 是一个 MCP 服务器，让 AI 助手能够直接接入嵌入式硬件——调试探针、串口日志、ELF 符号、外设寄存器——让 AI 具备真正观测、诊断、定位板子问题的能力。

> 人负责接线，AI 负责调试。

---

## 它能做什么

大多数 AI 工具只会帮你写代码。但嵌入式开发真正费时间的是调试：

- 板子上电没有 log 输出
- 启动崩溃或进入 HardFault
- 外设没响应（UART、SPI、I2C、GPIO）
- 程序卡死在某个地方

`mcudbg` 让 AI 能够真正去查这些问题，而不只是对着代码猜。

```
用户："这块 STM32L4 板子上电后没起来，帮我查一下。"

AI：读串口 log → halt CPU → 读 fault 寄存器 →
    加载 ELF 符号 → 读 USART2 寄存器状态 →
    "CR1.UE=0，发送器未使能——UART 根本没初始化"
```

---

## 当前能力

### Phase 1 — 探针 + 串口日志 + Fault 诊断
- 通过 `pyOCD` 支持的探针连接目标（ST-Link、CMSIS-DAP 等）
- Halt、Resume、Reset、单步执行
- 读取 CPU 寄存器和 Cortex-M fault 寄存器（CFSR、HFSR、MMFAR、BFAR）
- 读写目标内存，设置/清除断点
- 加载 ELF/AXF，将 PC 地址解析为函数名
- 实时连接 UART 并读取日志
- `diagnose_hardfault` —— 结构化的 fault 分析，带完整证据链
- `diagnose_startup_failure` —— 启动阶段分析

### Phase 2 — SVD 外设寄存器读取与诊断
- 加载任意 CMSIS-SVD 文件（芯片厂商 SDK 或 Keil MDK pack 中均有）
- `svd_list_peripherals` —— 列出 SVD 中所有外设
- `svd_get_registers` —— 查看寄存器布局，无需读硬件
- `svd_read_peripheral` —— 从硬件读取所有寄存器值，逐字段解析
- 针对 UART、SPI、I2C、GPIO 自动给出诊断建议

---

## 快速示例

```
# AI 排查"UART 没有输出"

svd_load('/path/to/STM32L4x6.svd')
svd_read_peripheral('USART2')

# 返回结果：
# CR1 = 0x0000  [UE=0, TE=0, RE=0]
# BRR = 0x0000
# 诊断："USART 未使能 (CR1.UE=0)，请设置 CR1.UE=1"
#       "发送器未使能 (CR1.TE=0)，无法输出任何数据"
```

---

## 安装

```bash
pip install mcudbg
```

或从源码安装：

```bash
git clone https://github.com/SolarWang233/mcudbg
cd mcudbg
pip install -e .
```

**依赖：**
- Python 3.10+
- `pyOCD` 支持的调试探针（ST-Link、CMSIS-DAP、J-Link CMSIS-DAP 模式）
- 芯片的 CMSIS-SVD 文件（用于外设寄存器解析）

STM32 的 SVD 文件在 Keil MDK pack 中有（路径：`<pack>/CMSIS/SVD/`），也可以从
[cmsis-svd-data](https://github.com/posborne/cmsis-svd-data) 下载。

---

## MCP 配置

### Claude Desktop（Windows）

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

### Claude Desktop（macOS / Linux）

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

---

## 快速上手

### 1. 加载 Demo profile（可选）

```
list_demo_profiles()
load_demo_profile("stm32l4_atk_led_demo")
```

### 2. 手动配置

```
configure_probe(target="stm32l496vetx")
configure_log(uart_port="COM5", uart_baudrate=115200)
configure_elf(elf_path="/path/to/firmware.axf")
connect_with_config()
```

### 3. 诊断启动失败

```
log_tail(30)
diagnose_startup_failure()
```

### 4. 读取外设寄存器

```
svd_load('/path/to/STM32L4x6.svd')
svd_read_peripheral('USART2')
svd_read_peripheral('GPIOA')
```

### 5. 完整 HardFault 排查

```
connect_with_config()
probe_halt()
diagnose_hardfault()
svd_read_peripheral('USART1')
```

---

## MCP 工具列表

### 配置类
| 工具 | 说明 |
|------|------|
| `configure_probe` | 设置探针目标和 ID |
| `configure_log` | 设置 UART 串口和波特率 |
| `configure_elf` | 设置 ELF/AXF 文件路径 |
| `configure_build` | 设置 Keil UV4 编译参数 |
| `connect_with_config` | 一次性连接所有已配置资源 |
| `get_runtime_config` | 查看当前配置 |

### 探针控制
| 工具 | 说明 |
|------|------|
| `list_connected_probes` | 列出当前连接的所有调试探针 |
| `probe_connect` | 连接目标 |
| `probe_disconnect` | 断开探针 |
| `probe_halt` | Halt 目标 |
| `probe_resume` | Resume 目标 |
| `probe_reset` | Reset 目标 |
| `probe_step` | 单步执行一条指令 |
| `probe_read_registers` | 读取所有 CPU 寄存器 |
| `probe_write_memory` | 向目标内存写入数据 |
| `continue_target` | Resume 并等待 halt（带超时） |
| `read_stopped_context` | 读取 halt 状态下的寄存器和 fault 状态 |
| `set_breakpoint` | 按符号或地址设置断点 |
| `clear_breakpoint` | 清除断点 |
| `clear_all_breakpoints` | 清除所有断点 |

### 日志
| 工具 | 说明 |
|------|------|
| `log_connect` | 连接 UART 日志通道 |
| `log_disconnect` | 断开日志 |
| `log_tail` | 读取最近的日志行 |

### ELF 符号
| 工具 | 说明 |
|------|------|
| `elf_load` | 加载 ELF/AXF 用于符号解析 |

### SVD 外设寄存器
| 工具 | 说明 |
|------|------|
| `svd_load` | 加载 CMSIS-SVD 文件 |
| `svd_list_peripherals` | 列出 SVD 中所有外设 |
| `svd_get_registers` | 获取寄存器布局（不读硬件） |
| `svd_read_peripheral` | 读取寄存器值 + 字段解析 + 自动诊断 |

### 诊断
| 工具 | 说明 |
|------|------|
| `diagnose_hardfault` | Cortex-M HardFault 完整分析 |
| `diagnose_startup_failure` | 启动阶段分析 |
| `run_debug_loop` | AI 驱动的多轮调试循环 |

### 编译与烧录（Keil UV4）
| 工具 | 说明 |
|------|------|
| `build_project` | 通过 Keil UV4 编译固件 |
| `flash_firmware` | 通过 Keil UV4 烧录固件 |

### 生命周期
| 工具 | 说明 |
|------|------|
| `disconnect_all` | 干净地断开所有资源 |

---

## 已验证硬件

| 组件 | 详情 |
|------|------|
| 目标芯片 | STM32L496VETx |
| 调试探针 | ST-Link（通过 pyOCD） |
| 日志通道 | UART 115200 波特率 |
| SVD 文件 | STM32L4x6.svd（Keil STM32L4xx_DFP pack） |

其他 `pyOCD` 支持的目标（STM32F4、RP2040、nRF52 等）理论上可用，但尚未测试。

---

## 已知限制

- **探针后端**：目前只支持 `pyOCD`，JLink 和 OpenOCD 后端计划中
- **编译烧录**：`build_project` / `flash_firmware` 需要 Windows 上的 **Keil UV4**，其他工具链（CMake/GCC/IAR）计划中
- **日志通道**：只支持 UART，RTT 支持计划中
- **SVD 文件**：需要用户自行提供芯片的 SVD 文件，不内置

---

## 路线图

| 阶段 | 状态 | 内容 |
|------|------|------|
| Phase 1 | ✅ 完成 | 探针 + 串口日志 + ELF + HardFault/启动失败诊断 |
| Phase 2 | ✅ 完成 | SVD 外设寄存器读取与自动诊断 |
| Phase 3 | 计划中 | 症状驱动的通用诊断（外设无响应、中断问题、内存越界） |
| Phase 4 | 计划中 | 完整调试闭环——诊断 → 改代码 → 编译 → 烧录 → 验证 |
| Phase 5 | 计划中 | DWARF 深度调试——局部变量、调用栈 |
| Phase 6 | 计划中 | 板级观测——GPIO 电平、电压、波形 |

---

## 参与贡献

欢迎提 Issue 和 PR。

如果你在 STM32L4 以外的目标上测试过，欢迎开 Issue 分享结果——扩大硬件验证覆盖面是优先方向。

---

## 许可证

MIT — 详见 [LICENSE](LICENSE)
