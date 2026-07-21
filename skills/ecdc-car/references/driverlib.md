 # TI DriverLib API 鍙傝€?
 
 SDK 鐗堟湰: `mspm0_sdk_2_04_00_06`, SysConfig `1.23.1`
 
 ## 宸ョ▼鍏ュ彛妯″紡
 
 鎵€鏈?MSM0G3507 宸ョ▼閬靛惊鐩稿悓鐨勫垵濮嬪寲娴佺▼:
 
 ```c
 #include "ti_msp_dl_config.h"
 
 int main(void) {
     SYSCFG_DL_init();  // SysConfig 鐢熸垚鐨勫垵濮嬪寲
     // ... 鐢ㄦ埛鍒濆鍖栦唬鐮?...
     while (1) { /* 涓诲惊鐜?*/ }
 }
 ```
 
 **`SYSCFG_DL_init()` 鐢?SysConfig 鏍规嵁 `.syscfg` 閰嶇疆鑷姩鐢熸垚**, 鍖呭惈鏃堕挓銆丟PIO銆佸璁剧殑鍏ㄩ儴鍒濆鍖栥€?
 
 ## GPIO
 
 ```c
 #include "dl_gpio.h"
 
 // 缃珮
 DL_GPIO_setPins(GPIO_PORT, DL_GPIO_PIN_xx);
 // 缃綆
 DL_GPIO_clearPins(GPIO_PORT, DL_GPIO_PIN_xx);
 // 缈昏浆
 DL_GPIO_togglePins(GPIO_PORT, DL_GPIO_PIN_xx);
 // 璇诲彇 (杩斿洖闈為浂琛ㄧず寮曡剼涓洪珮)
 uint32_t val = DL_GPIO_readPins(GPIO_PORT, DL_GPIO_PIN_xx);
 // 鑾峰彇涓柇鐘舵€?
 uint32_t intr = DL_GPIO_getEnabledInterruptStatus(GPIO_PORT, DL_GPIO_PIN_xx);
 // 娓呴櫎涓柇鏍囧織
 DL_GPIO_clearInterruptStatus(GPIO_PORT, DL_GPIO_PIN_xx);
 ```
 
 **寮曡剼瀹忔潵鑷?`ti_msp_dl_config.h`**, 渚嬪 `AIN_PORT`, `AIN_AIN1_PIN`, `LED_PORT`, `LED_UserLED_PIN` 绛夈€?
 
 ## Timer (PWM / 璁℃椂)
 
 ```c
 #include "dl_timer.h"
 
 // 鍚姩 PWM 璁℃暟鍣?(閫氬父鐢?TIMG 瀹炰緥, 濡?PWM_0_INST)
 DL_Timer_startCounter(PWM_0_INST);
 // 鍚姩 TimerA 璁℃暟鍣?
 DL_TimerA_startCounter(TIMER_0_INST);
 // 璁剧疆 PWM 鍗犵┖姣?(value 涓烘瘮杈冨€?
 DL_Timer_setCaptureCompareValue(PWM_0_INST, value, GPIO_PWM_0_C0_IDX);
 // 妫€鏌?TimerA 涓柇鏍囧織
 if (DL_TimerA_getPendingInterrupt(TIMER_0_INST)) { ... }
 // Timer 涓柇绱㈠紩
 if (DL_TIMER_IIDX_ZERO) { ... }
 ```
 
 **PWM 棰戠巼鐢?SysConfig 璁剧疆**, 浠ｇ爜涓彧璋冨崰绌烘瘮銆侾WM 姣旇緝鍊艰寖鍥村彇鍐充簬 SysConfig 涓殑鍛ㄦ湡閰嶇疆銆?
 
 ## UART
 
 ```c
 #include "dl_uart.h"
 #include "dl_uart_main.h"
 
 // 鍙戦€佸崟瀛楄妭
 DL_UART_Main_transmitData(UART_0_INST, ch);
 // 妫€鏌ュ繖鐘舵€?
 while (DL_UART_isBusy(UART_0_INST) == true);
 // 鎺ユ敹鍗曞瓧鑺?(閫氬父鍦?ISR 涓?
 uint8_t data = DL_UART_Main_receiveData(UART_1_INST);
 // 鑾峰彇涓柇鐘舵€?
 switch (DL_UART_getPendingInterrupt(UART_1_INST)) {
     case DL_UART_IIDX_RX: /* 鎺ユ敹涓柇 */ break;
 }
 ```
 
 ## ADC
 
 ```c
 #include "dl_adc12.h"
 
 // ADC 閫氳繃 SysConfig 閰嶇疆閫氶亾鍜岄噰鏍峰弬鏁?
 // 鍏蜂綋 API 瑙?TI SDK 鏂囨。 dl_adc12.h
 ```
 
 ## I2C
 
 ```c
 #include "dl_i2c.h"
 
 // 纭欢 I2C (MPU6050 / OLED 绛?
 // SysConfig 閰嶇疆 SDA/SCL 寮曡剼鍜岄€熺巼 (400kHz)
 // 鍏蜂綋 I2C 璇诲啓闇€鍙傝€冭疆瓒ｄ緥绋嬫垨 TI SDK
 ```
 
 ## SysTick
 
 ```c
 #include "ti_msp_dl_config.h"
 
 // 鍒濆鍖?SysTick (1ms 涓柇)
 DL_SYSTICK_config(CPUCLK_FREQ / 1000);    // CPUCLK_FREQ = 80000000
 NVIC_SetPriority(SysTick_IRQn, 0);         // 鏈€楂樹紭鍏堢骇
 
 // 鑾峰彇褰撳墠璁℃暟鍊?
 uint32_t tick = SysTick->VAL;
 
 // 浼戠湢 ms (闃诲)
 void delay_ms(uint32_t ms);
 void delay_us(uint32_t us);
 ```
 
 `delay_ms`/`delay_us` 鍦?`board.c` 涓熀浜?SysTick 瀹炵幇, 80MHz 鏃堕挓绮惧害銆?
 
 ## 涓柇绠＄悊
 
 ```c
 // 浣胯兘涓柇
 NVIC_EnableIRQ(ENCODERA_INT_IRQN);
 NVIC_EnableIRQ(UART_1_INST_INT_IRQN);
 // 娓呴櫎鎸傝捣
 NVIC_ClearPendingIRQ(TIMER_0_INST_INT_IRQN);
 ```
 
 **GPIO 涓柇鍏辩敤 `GROUP1_IRQHandler`**, 鍐呴儴閫氳繃 `DL_GPIO_getEnabledInterruptStatus` 鍖哄垎寮曡剼銆?
 
 ## printf 閲嶅畾鍚?
 
 ```c
 int fputc(int ch, FILE *stream) {
     while (DL_UART_isBusy(UART_0_INST) == true);
     DL_UART_Main_transmitData(UART_0_INST, ch);
     return ch;
 }
 ```
 
 涓嶄娇鐢ㄥ井搴撴椂, 杩橀渶瀹氫箟 `_sys_exit(int x) { x = x; }`銆?
 
 ## 甯哥敤绫诲瀷瀹氫箟 (board.h)
 
 ```c
 typedef int32_t  s32;
 typedef int16_t  s16;
 typedef int8_t   s8;
 typedef uint32_t u32;
 typedef uint16_t u16;
 typedef uint8_t  u8;
 #define ABS(a) (a > 0 ? a : (-a))
 ```

