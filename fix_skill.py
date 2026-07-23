import os
# 1. sensors.md: 替换灰度模块章节
p = r'D:\Downloads\diansai\代码\电赛skill\skills\m0-skills\references\sensors.md'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()
idx = c.find('## HJ-DXJ8')
end = c.find('## ', idx+1) if idx>=0 else len(c)
new = '## HJ-DXJ8 八路灰度循线 (8 路独立输出)\n\n- 模块: 8 路数字灰度传感器, 每路独立 OUT 线 (OUT1~OUT8)\n- 接口: VCC / GND / OUT1 / OUT2 / ... / OUT8 (共 10 根线)\n- 每路输出: 数字量 0/1\n- 感应距离: 最佳 15-30mm\n- 灵敏度: 每个通道有独立电位器调节\n\n### 引脚配置\n\n此模块需要 8 个独立 GPIO, 用户根据底板空闲引脚自行分配。\n\n### 巡线算法\n\n`c\nint weights[8] = {-35, -25, -15, -5, 5, 15, 25, 35};\nint err = 0, active = 0;\nfor (int i = 0; i < 8; i++) {\n    if (results[i] == ACTIVE_VALUE) { err += weights[i]; active++; }\n}\nif (active > 0) err /= active;\nSet_PWM(base + err*KP, base - err*KP);\n`\n\n**ACTIVE_VALUE**: 现场测试确定。\n'
c = c[:idx] + new + c[end:]
with open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(c)
print('1/4 sensors.md')

# 2. hardware.md: 改硬件引用
p2 = r'D:\Downloads\diansai\代码\电赛skill\skills\m0-skills\references\hardware.md'
with open(p2, 'r', encoding='utf-8') as f:
    c2 = f.read()
c2 = c2.replace('| 八路灰度 | HJ-DXJ8 | PA12,AD0 PA27,AD1 PB16,AD2 PB17,OUT | GPIO->CD4051 |', '| 八路灰度(8路独立) | HJ-DXJ8 | 8 x GPIO 自定义 | 独立数字输出 |')
with open(p2, 'w', encoding='utf-8', newline='\n') as f:
    f.write(c2)
print('2/4 hardware.md')

# 3. SKILL.md: C07A V1.1
p3 = r'D:\Downloads\diansai\代码\电赛skill\skills\m0-skills\SKILL.md'
with open(p3, 'r', encoding='utf-8') as f:
    c3 = f.read()
c3 = c3.replace('WHEELTEC C07A V1.0/V1.1', 'WHEELTEC C07A V1.1')
c3 = c3.replace('C07A 核心板', 'C07A V1.1 核心板')
with open(p3, 'w', encoding='utf-8', newline='\n') as f:
    f.write(c3)
print('3/4 SKILL.md')

# 4. openai.yaml: C07A V1.1
p4 = r'D:\Downloads\diansai\代码\电赛skill\skills\m0-skills\agents\openai.yaml'
with open(p4, 'r', encoding='utf-8') as f:
    c4 = f.read()
c4 = c4.replace('C07A', 'C07A V1.1')
with open(p4, 'w', encoding='utf-8', newline='\n') as f:
    f.write(c4)
print('4/4 openai.yaml')

print('ALL DONE')
