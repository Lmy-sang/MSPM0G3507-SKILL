 # 软件架构: BSP / Module / App
 
 ## 三层架构
 
 ```
 ┌─────────────────────────────────┐
 │  App 层: 任务逻辑                │
 │  - 赛题状态机                    │
 │  - 模式切换                      │
 │  - 参数表 / 策略                 │
 │  - 换题主要修改此层               │
 ├─────────────────────────────────┤
 │  Module 层: 功能模块              │
 │  - 电机闭环控制 (PI)             │
 │  - K230 通信协议                  │
 │  - PID / 滤波器 / 控制器          │
 │  - MPU6050 DMP                   │
 │  - 极少改动                       │
 ├─────────────────────────────────┤
 │  BSP 层: 硬件抽象                 │
 │  - GPIO / PWM / ADC / UART / I2C │
 │  - SysConfig 生成配置             │
 │  - 仅更换硬件时修改               │
 └─────────────────────────────────┘
 ```
 
 ## 层间调用规范
 
 - **App 只能调用 Module 接口**, 不直接操作 BSP
 - Module 调用 BSP 的 DriverLib API (`DL_*`)
 - 模块间通过明确命名的函数通信, 不使用全局变量传递状态
 
 ## Keil 工程结构
 
 ```
 Project/
 ├── empty.c                   # main() 入口
 ├── empty.syscfg              # SysConfig 配置
 ├── ti_msp_dl_config.c/h      # SysConfig 生成 (不可手改)
 ├── board.c/h                 # BSP: SysTick, delay, printf
 ├── Hardware/                 # Module: 各模块驱动
 │   ├── motor.c/h             # TB6612 PWM + PI
 │   ├── encoder.c/h           # 编码器中断 + RPM
 │   ├── key.c/h               # BLS 按键
 │   ├── led.c/h               # 用户 LED
 │   ├── K210.c/h              # K230 UART 解析
 │   └── ...
 ├── ti/                       # TI DriverLib (dl_*.c/h)
 ├── source/                   # CMSIS + 第三方
 └── *.uvprojx                 # Keil 工程文件
 ```
 
 ## App 层: main() 模板
 
 ```c
 #include "board.h"
 
 int main(void) {
     SYSCFG_DL_init();                    // BSP 初始化
 
     // Module 初始化
     DL_Timer_startCounter(PWM_0_INST);   // 电机 PWM
     NVIC_EnableIRQ(ENCODERA_INT_IRQN);   // 编码器中断
     NVIC_EnableIRQ(ENCODERB_INT_IRQN);
     NVIC_EnableIRQ(TIMER_0_INST_INT_IRQN); // 10ms 定时中断
     NVIC_EnableIRQ(UART_1_INST_INT_IRQN);  // K230 串口中断
 
     while (1) {
         // App 层: 状态机
         switch (g_mode) {
             case MODE_LINE_FOLLOW:  LineFollowTask();  break;
             case MODE_TRACK:        TargetTrackTask(); break;
             case MODE_STOP:         Set_PWM(0, 0);     break;
         }
     }
 }
 
 // 10ms 定时中断 (Module 层)
 void TIMER_0_INST_IRQHandler(void) {
     if (DL_TimerA_getPendingInterrupt(TIMER_0_INST) && DL_TIMER_IIDX_ZERO) {
         // 读取编码器 -> RPM -> PI -> Set_PWM
         MA_RPM = Calculate_Motor_RPM(Get_Encoder_countA, 10);
         // ... PI 闭环 ...
     }
 }
 ```
 
 ## 编码规范
 
 - 函数命名: 驼峰或下划线 (`Set_PWM`, `ReadEightIR`, `Velocity_A`)
 - 变量命名: 全局首字母大写 (`Flag_Stop`, `MA_RPM`), 局部小写 (`bias`, `i`)
 - 每个 `.c` 配 `.h`, include 防护用 `#ifndef` / `#define` / `#endif`
 - 宏用全大写 (`ABS(a)`, `CPUCLK_FREQ`)
 - 注释用中文简述函数功能
 - 中断 ISR 内不做耗时操作 (只置标志位 + 关键数据读取)
 
 ## 比赛换题策略
 
 1. 确定传感器组合 → 查 [hardware.md](hardware.md) 检查引脚冲突
 2. 添加新 Module → 在 `Hardware/` 下新建 `xxx.c/h`
 3. 修改 App 层 → `main.c` 中新增状态机模式
 4. BSP 层不动 → `ti_msp_dl_config.*` 和 `board.*` 基本不变
