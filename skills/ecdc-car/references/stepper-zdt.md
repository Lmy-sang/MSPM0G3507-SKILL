# ZDT 张大头步进: Modbus RTU 闭环
Emm_V5.0 总线型智能闭环步进, 内置 FOC+PID

## 接线
UART TTL 直连 MCU, 115200 8N1, 独立 12-24V 供电
S28A 底板舵机口 PA8 是 TIMG0 PWM, 步进走 UART 需另选引脚

## Modbus RTU 帧
[Addr(01H)] [Func] [Data] [CRC16_Lo] [CRC16_Hi]

## 关键指令
Enable:   01 10 00 F3 00 02 04 AB 01 00 00 CRC16
速度模式: 01 10 00 F6 00 03 06 [dir] [acc] [rpm] [sync] 00 CRC16
位置(相对): 01 10 00 FD 00 05 0A [dir] [acc] [rpm] [pulse] 00 [sync] CRC16
停止:     01 10 00 FE 00 01 02 [sync] CRC16
读转速:   01 04 00 35 00 02 CRC16
读位置:   01 04 00 36 00 03 CRC16
清零:     01 06 00 0A 00 01 CRC16
校准:     01 06 00 06 00 01 CRC16

## 字段
dir:0=CW 1=CCW acc:0-255 rpm:0-3000 pulse:16细分3200=1圈
角度=位置*360/65536

## CRC16
uint16_t crc=0xFFFF;
for(i=0;i<len;i++){crc^=data[i]; for(j=0;j<8;j++) crc=(crc&1)?(crc>>1)^0xA001:(crc>>1);}
先发低字节后高字节

## 流程
上电等2s->使能->确认->速度/位置指令->循环读状态
