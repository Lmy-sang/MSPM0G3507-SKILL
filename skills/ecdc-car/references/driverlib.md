# TI DriverLib API 参考
SDK: mspm0_sdk_2_04_00_06, SysConfig 1.23.1, Keil MDK v5.42

## 入口
main() { SYSCFG_DL_init(); ... while(1){} }
SYSCFG_DL_init() 由 SysConfig 根据 .syscfg 生成。

## GPIO
DL_GPIO_setPins(port,pin) / DL_GPIO_clearPins / DL_GPIO_readPins / DL_GPIO_togglePins
DL_GPIO_getEnabledInterruptStatus(port,pin) / DL_GPIO_clearInterruptStatus
引脚宏来自 ti_msp_dl_config.h

## Timer/PWM
DL_Timer_startCounter(PWM_0_INST) / DL_TimerA_startCounter(TIMER_0_INST)
DL_Timer_setCaptureCompareValue(INST, val, CH_IDX)
DL_TimerA_getPendingInterrupt / DL_TIMER_IIDX_ZERO
PWM 频率由 SysConfig 设置, 推荐 10kHz

## UART
DL_UART_Main_transmitData(UART_0_INST, ch) / DL_UART_isBusy
DL_UART_Main_receiveData(UART_1_INST) / DL_UART_getPendingInterrupt
DL_UART_IIDX_RX

## SysTick
DL_SYSTICK_config(CPUCLK_FREQ/1000); CPUCLK_FREQ=80000000
delay_ms(ms) / delay_us(us) 在 board.c 实现

## 中断
NVIC_EnableIRQ / NVIC_ClearPendingIRQ
GROUP1_IRQHandler 处理 GPIO 中断

## printf 重定向
int fputc(int ch, FILE *stream) {
    while(DL_UART_isBusy(UART_0_INST));
    DL_UART_Main_transmitData(UART_0_INST, ch);
    return ch;
}
