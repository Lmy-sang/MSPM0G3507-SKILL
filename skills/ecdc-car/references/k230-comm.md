# K230 视觉通信: ASCII 文本协议
与轮趣 K210 二进制协议(0xCC/0xDD)完全不同。

## 物理层
UART 115200 8N1, K230 和 MSPM0G 必须共地

## 协议格式
$[长度],[例程ID],[数据1],...,[数据N],#
$: 帧头 #: 帧尾 后附换行符

## 接收解析
void UART_1_INST_IRQHandler(void) {
    if(DL_UART_getPendingInterrupt(UART_1_INST)==DL_UART_IIDX_RX) {
        uint8_t ch=DL_UART_Main_receiveData(UART_1_INST);
        if(ch=='$') k230_idx=0;
        k230_buf[k230_idx++]=ch;
        if(ch=='#') k230_frame_ready=1;
    }
}

## 常用例程 ID
01:颜色(x,y,w,h) 03:二维码(x,y,w,h,msg) 13:OCR(msg) 14:YOLO(x,y,w,h,msg) 15:目标跟踪(x,y,w,h)

## K230 侧开发
固件: CanMV_K230 v1.6+ IDE: CanMV IDE 4.0.7
LAB 校准必须在现场灯光下重新做
陷阱: Timer(-1), PWM(2,50), pin.value(1/0), f-string不支持
