# 白噪音节拍生成器

一个功能强大的数字乐器，用于生成带有多音符旋律的白噪音节拍。

## 功能特点

- **多种波形选择**：支持正弦波、方波、锯齿波、三角波
- **自定义音符序列**：可以自由定义音符序列，支持休止符
- **音调脚本支持**：通过脚本文件创作音乐，支持注释和多行格式
- **不同时值音符**：支持全音符、二分音符、四分音符、八分音符等
- **灵活的参数调整**：可调整节拍、速度、音量等参数
- **音频输出**：支持直接播放或保存为WAV文件
- **命令行版本**：提供命令行接口，方便脚本调用
- **音符表**：可查看完整的音符频率表

## 安装

1. 克隆或下载本项目
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

### 命令行版本

#### 基本用法

```bash
python src/main.py
```

#### 常用参数

- `--time-signature, -t`：节拍数，默认 4/4
- `--bars, -b`：小节数，默认 8
- `--bpm`：速度，默认 120 BPM
- `--duration`：节拍持续时间(ms)，默认 150
- `--noise-volume`：白噪音音量(0-1)，默认 0.3
- `--note-volume`：音符音量(0-1)，默认 0.5
- `--waveform, -w`：波形类型，默认 sine
- `--notes, -n`：音符序列，用逗号分隔，R表示休止符
- `--script, -s`：音调脚本文件路径
- `--output, -o`：输出音频文件路径
- `--note-table`：输出音符频率表

#### 使用示例

1. **播放默认节拍**：
   ```bash
   python src/main.py
   ```

2. **自定义音符序列**：
   ```bash
   python src/main.py --notes "C4,R,E4,R,G4,R,C5,R"
   ```

3. **保存为音频文件**：
   ```bash
   python src/main.py --output output.wav --notes "C4,D4,E4,F4,G4,A4,B4,C5"
   ```

4. **调整参数**：
   ```bash
   python src/main.py --bpm 140 --waveform square --noise-volume 0.4 --note-volume 0.6
   ```

5. **查看音符表**：
   ```bash
   python src/main.py --note-table
   ```

6. **使用音调脚本**：
   ```bash
   python src/main.py --script test_script.txt
   ```

7. **使用带有时值的音调脚本**：
   ```bash
   python src/main.py --script test_duration_script.txt
   ```

## 音调脚本

### 基本格式

音调脚本是一个文本文件，每行代表一个小节，音符之间用空格分隔。

```txt
# 这是一个注释
C4 E4 G4 C5
R E4 G4 E4
C4 R G4 R
R E4 C4 R
```

### 支持不同时值

可以在音符后面添加时值标记，格式为 `音符-时值`：

- `1`：全音符（4拍）
- `2`：二分音符（2拍）
- `4`：四分音符（1拍）
- `8`：八分音符（1/2拍）
- `16`：十六分音符（1/4拍）

```txt
# 第一小节：四分音符
C4-4 E4-4 G4-4 C5-4

# 第二小节：八分音符
C5-8 B4-8 A4-8 G4-8

# 第三小节：二分音符和四分音符
F4-2 E4-4

# 第四小节：全音符
C4-1
```

### 脚本规则

- 以 `#` 开头的行是注释
- 空行会被忽略
- 音符格式为 `音符名+八度`，例如 `C4`、`E4`、`G4` 等
- `R` 表示休止符
- 如果不指定时值，默认为四分音符（4）

## 音符表示

- 使用标准音乐符号，如 C4、D4 等
- R 表示休止符
- 音符频率基于十二平均律，A4 = 440Hz

## 依赖库

- numpy：用于生成波形
- sounddevice：用于播放音频
- soundfile：用于保存音频文件

## 项目结构

```
song/
├── src/
│   └── main.py        # 主程序（包含命令行版本）
├── out/               # 输出目录
├── requirements.txt   # 依赖文件
├── README.md          # 本说明文件
├── LICENSE            # 许可证文件
├── test_script.txt    # 测试音调脚本
└── test_duration_script.txt  # 测试不同时值的音调脚本
```

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

