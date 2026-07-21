 # TI DriverLib API 参考
 
 SDK 版本: `mspm0_sdk_2_04_00_06`, SysConfig `1.23.1`
 
 ## 工程入口模式
 
 所有 MSM0G3507 工程遵循相同的初始化流程:
 
 ```c
 #include "ti_msp_dl_config.h"
 
 int main(void) {
     SYSCFG_DL_init();  // SysConfig 生成的初始化
     // ... 用户初始化代码 ...
     while (1) { /* 主循环 */ }
 }
 ```
 
 **`SYSCFG_DL_init()` 由 SysConfig 根据 `.syscfg` 配置自动生成**, 包含时钟、GPIO、外设的全部初始化。
 
 ## GPIO
 
 ```c
 #include "dl_gpio.h"
 
 // 置高
 DL_GPIO_setPins(GPIO_PORT, DL_GPIO_PIN_xx);
 // 置低
 DL_GPIO_clearPins(GPIO_PORT, DL_GPIO_PIN_xx);
 // 翻转
 DL_GPIO_togglePins(GPIO_PORT, DL_GPIO_PIN_xx);
 // 读取 (返回非零表示引脚为高)
 uint32_t val = DL_GPIO_readPins(GPIO_PORT, DL_GPIO_PIN_xx);
 // 获取中断状态
 uint32_t intr = DL_GPIO_getEnabledInterruptStatus(GPIO_PORT, DL_GPIO_PIN_xx);
 // 清除中断标志
 DL_GPIO_clearInterruptStatus(GPIO_PORT, DL_GPIO_PIN_xx);
 ```
 
 **引脚宏来自 `ti_msp_dl_config.h`**, 例如 `AIN_PORT`, `AIN_AIN1_PIN`, `LED_PORT`, `LED_UserLED_PIN` 等。
 
 ## Timer (PWM / 计时)
 
 ```c
 #include "dl_timer.h"
 
 // 启动 PWM 计数器 (通常用 TIMG 实例, 如 PWM_0_INST)
 DL_Timer_startCounter(PWM_0_INST);
 // 启动 TimerA 计数器
 DL_TimerA_startCounter(TIMER_0_INST);
 // 设置 PWM 占空比 (value 为比较值)
 DL_Timer_setCaptureCompareValue(PWM_0_INST, value, GPIO_PWM_0_C0_IDX);
 // 检查 TimerA 中断标志
 if (DL_TimerA_getPendingInterrupt(TIMER_0_INST)) { ... }
 // Timer 中断索引
 if (DL_TIMER_IIDX_ZERO) { ... }
 ```
 
 **PWM 频率由 SysConfig 设置**, 代码中只调占空比。PWM 比较值范围取决于 SysConfig 中的周期配置。
 
 ## UART
 
 ```c
 #include "dl_uart.h"
 #include "dl_uart_main.h"
 
 // 发送单字节
 DL_UART_Main_transmitData(UART_0_INST, ch);
 // 检查忙状态
 while (DL_UART_isBusy(UART_0_INST) == true);
 // 接收单字节 (通常在 ISR 中)
 uint8_t data = DL_UART_Main_receiveData(UART_1_INST);
 // 获取中断状态
 switch (DL_UART_getPendingInterrupt(UART_1_INST)) {
     case DL_UART_IIDX_RX: /* 接收中断 */ break;
 }
 ```
 
 ## ADC
 
 ```c
 #include "dl_adc12.h"
 
 // ADC 通过 SysConfig 配置通道和采样参数
 // 具体 API 见 TI SDK 文档 dl_adc12.h
 ```
 
 ## I2C
 
 ```c
 #include "dl_i2c.h"
 
 // 硬件 I2C (MPU6050 / OLED 等)
 // SysConfig 配置 SDA/SCL 引脚和速率 (400kHz)
 // 具体 I2C 读写需参考轮趣例程或 TI SDK
 ```
 
 ## SysTick
 
 ```c
 #include "ti_msp_dl_config.h"
 
 // 初始化 SysTick (1ms 中断)
 DL_SYSTICK_config(CPUCLK_FREQ / 1000);    // CPUCLK_FREQ = 80000000
 NVIC_SetPriority(SysTick_IRQn, 0);         // 最高优先级
 
 // 获取当前计数值
 uint32_t tick = SysTick->VAL;
 
 // 休眠 ms (阻塞)
 void delay_ms(uint32_t ms);
 void delay_us(uint32_t us);
 ```
 
 `delay_ms`/`delay_us` 在 `board.c` 中基于 SysTick 实现, 80MHz 时钟精度。
 
 ## 中断管理
 
 ```c
 // 使能中断
 NVIC_EnableIRQ(ENCODERA_INT_IRQN);
 NVIC_EnableIRQ(UART_1_INST_INT_IRQN);
 // 清除挂起
 NVIC_ClearPendingIRQ(TIMER_0_INST_INT_IRQN);
 ```
 
 **GPIO 中断共用 `GROUP1_IRQHandler`**, 内部通过 `DL_GPIO_getEnabledInterruptStatus` 区分引脚。
 
 ## printf 重定向
 
 ```c
 int fputc(int ch, FILE *stream) {
     while (DL_UART_isBusy(UART_0_INST) == true);
     DL_UART_Main_transmitData(UART_0_INST, ch);
     return ch;
 }
 ```
 
 不使用微库时, 还需定义 `_sys_exit(int x) { x = x; }`。
 
 ## 常用类型定义 (board.h)
 
 ```c
 typedef int32_t  s32;
 typedef int16_t  s16;
 typedef int8_t   s8;
 typedef uint32_t u32;
 typedef uint16_t u16;
 typedef uint8_t  u8;
 #define ABS(a) (a > 0 ? a : (-a))
 ```
