 # K230 视觉通信: ASCII 文本协议
 
 K230 (亚博智能) 与 MSPM0G3507 通过 UART 通信。**注意: 协议与轮趣 K210 的二进制协议 (0xCC/0xDD) 完全不同。**
 
 ## 物理层
 
 - 接口: UART
 - 波特率: 115200 (可配置)
 - 数据位: 8N1
 - 电平: TTL 3.3V, K230 和 MSPM0G 必须共地
 
 ## 协议格式
 
 K230 发送格式 (ASCII 文本串):
 
 ```
 $[长度],[例程ID],[数据1],[数据2],...,[数据N],#
 ```
 
 - `$`: 帧头
 - `长度`: 本帧所有字符数 (不含换行)
 - `例程ID`: 两位数字, 对应视觉任务类型
 - `数据`: 逗号分隔的多个字段
 - `#`: 帧尾
 - 帧尾后附换行符 (不计数)
 
 **MSPM0G 接收后需要逐字节解析, 找到 `$` 开始, `#` 结束, 验证长度和字段数量。**
 
 ## 接收端解析框架
 
 ```c
 #define K230_BUF_SIZE 128
 static uint8_t k230_buf[K230_BUF_SIZE];
 static uint8_t k230_idx = 0;
 static uint8_t k230_frame_ready = 0;
 
 void UART_1_INST_IRQHandler(void) {
     if (DL_UART_getPendingInterrupt(UART_1_INST) == DL_UART_IIDX_RX) {
         uint8_t ch = DL_UART_Main_receiveData(UART_1_INST);
         if (ch == '$') { k230_idx = 0; }
         k230_buf[k230_idx++] = ch;
         if (ch == '#' && k230_idx < K230_BUF_SIZE) {
             k230_frame_ready = 1;
         }
     }
 }
 
 // 主循环中处理
 void K230_ProcessFrame(void) {
     if (!k230_frame_ready) return;
     k230_frame_ready = 0;
     // 解析 k230_buf[1] 和 k230_buf[2] 获取例程 ID
     // 根据 ID 解析后续字段
 }
 ```
 
 ## 常用例程 ID 速查
 
 | ID | 功能 | 数据字段 |
 |----|------|---------|
 | `01` | 颜色识别 | `x`, `y`, `w`, `h` (识别框坐标和尺寸) |
 | `02` | 条形码 | `x`, `y`, `w`, `h`, `msg` |
 | `03` | 二维码 | `x`, `y`, `w`, `h`, `msg` |
 | `04` | AprilTag 识别 | `x`, `y`, `w`, `h`, `id`, `degrees` |
 | `05` | DM码识别 | `x`, `y`, `w`, `h`, `msg`, `degrees` |
 | `06` | 人脸检测 | `x`, `y`, `w`, `h` |
 | `07` | 注视方向 | `start_x`, `start_y`, `end_x`, `end_y` |
 | `08` | 人脸识别 | `x`, `y`, `w`, `h`, `name`, `score` |
 | `09` | 人体检测 | `x`, `y`, `w`, `h` |
 | `10` | 跌倒检测 | `x`, `y`, `w`, `h`, `msg`, `score` |
 | `11` | 手掌检测 | `x`, `y`, `w`, `h` |
 | `12` | 手势识别 | `msg` (UP/DOWN/LEFT/RIGHT/MIDDLE) |
 | `13` | OCR 字符识别 | `msg` |
 | `14` | YOLO 物体检测 | `x`, `y`, `w`, `h`, `msg` (物体名称) |
 | `15` | 目标跟踪 | `x`, `y`, `w`, `h` |
 | `16` | 自学习物体识别 | `category`, `score` |
 | `17` | 车牌识别 | `msg` |
 
 ## 比赛常用场景
 
 ### 色块跟踪 (ID=01)
 
 ```
 $18,01,120,85,45,38,#
 → x=120, y=85, w=45, h=38
 → 中心点: (120+45/2, 85+38/2) = (142, 104)
 → 画面中心: 320/2 = 160
 → 偏差: 142 - 160 = -18 (目标偏左)
 ```
 
 ### 二维码/数字识别 (ID=03/13)
 
 ```
 $15,03,80,60,120,90,HELLO,#
 → msg = "HELLO" (二维码内容)
 ```
 
 ## K230 侧开发要点 (MicroPython/CanMV)
 
 - 固件: CanMV_K230_YAHBOOM_micropython_v1.6+
 - IDE: CanMV IDE v4.0.7
 - UART 输出: `uart.write(f"${len},{id},{data},#\n".encode())`
 - 颜色识别: 必须在现场灯光下重新 LAB 校准, 否则阈值不准
 - 帧率优化: 使用 ROI + stride 缩帧, 不跑全分辨率
 - 已知陷阱: `Timer` 必须用 `Timer(-1)`, `PWM` 用位置参数非关键字, `Pin.value(1/0)` 不用 `high()/low()`
