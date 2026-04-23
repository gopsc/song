import numpy as np
import sounddevice as sd
import soundfile as sf
import time
import argparse

class WhiteNoiseBeatGeneratorCLI:
    def __init__(self):
        # 音频参数
        self.sample_rate = 44100
        
        # 音符频率字典 (A4 = 440Hz)
        self.note_frequencies = self.create_note_frequencies()
        
        # 当前默认波形（初始为正弦波）
        self.current_waveform = "sine"
    
    def create_note_frequencies(self):
        """创建完整的音符频率表"""
        base_notes = {
            'C': 261.63, 'C#': 277.18, 'D': 293.66, 'D#': 311.13,
            'E': 329.63, 'F': 349.23, 'F#': 369.99, 'G': 392.00,
            'G#': 415.30, 'A': 440.00, 'A#': 466.16, 'B': 493.88
        }
        
        frequencies = {}
        for octave in range(1, 8):
            for note, freq in base_notes.items():
                note_name = f"{note}{octave}"
                frequencies[note_name] = freq * (2 ** (octave - 4))
        
        # 添加休止符
        frequencies['R'] = 0.0
        return frequencies
    
    def print_note_table(self):
        """输出音符表"""
        print("\n=== 音符频率表 ===")
        print("格式: 音符名称 (频率 Hz)")
        print("-" * 40)
        
        # 按八度分组显示
        for octave in range(1, 8):
            print(f"\n八度 {octave}:")
            for note in ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']:
                note_name = f"{note}{octave}"
                if note_name in self.note_frequencies:
                    freq = self.note_frequencies[note_name]
                    print(f"{note_name:4} : {freq:6.2f} Hz")
        
        print("\n特殊符号:")
        print("R : 休止符 (0 Hz)")
        print("-" * 40)
    
    def generate_sine_wave(self, frequency, duration, volume=0.5):
        """生成正弦波"""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        wave = np.sin(2 * np.pi * frequency * t)
        return wave * volume
    
    def generate_square_wave(self, frequency, duration, volume=0.5):
        """生成方波"""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        wave = np.sign(np.sin(2 * np.pi * frequency * t))
        return wave * volume * 0.7
    
    def generate_sawtooth_wave(self, frequency, duration, volume=0.5):
        """生成锯齿波"""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        wave = 2 * (t * frequency - np.floor(0.5 + t * frequency))
        return wave * volume * 0.5
    
    def generate_triangle_wave(self, frequency, duration, volume=0.5):
        """生成三角波"""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        wave = 2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1
        return wave * volume * 0.8
    
    def generate_note(self, frequency, duration, volume=0.5, waveform="sine"):
        """根据波形类型生成音符"""
        if frequency == 0:  # 休止符
            return np.zeros(int(self.sample_rate * duration))
        
        if waveform == "sine":
            return self.generate_sine_wave(frequency, duration, volume)
        elif waveform == "square":
            return self.generate_square_wave(frequency, duration, volume)
        elif waveform == "sawtooth":
            return self.generate_sawtooth_wave(frequency, duration, volume)
        elif waveform == "triangle":
            return self.generate_triangle_wave(frequency, duration, volume)
        else:
            print(f"警告: 未知波形类型 '{waveform}'，使用正弦波")
            return self.generate_sine_wave(frequency, duration, volume)
    
    def parse_note_sequence(self, sequence_str):
        """解析音符序列（用于命令行参数）"""
        if not sequence_str:
            return []
        
        notes = [note.strip().upper() for note in sequence_str.split(",") if note.strip()]
        
        # 验证音符
        valid_notes = []
        current_waveform = "sine"  # 命令行默认使用正弦波
        valid_waveforms = ["sine", "square", "sawtooth", "triangle"]
        
        for note in notes:
            # 检查是否是波形切换命令
            if note.startswith('@'):
                waveform_cmd = note[1:].lower()
                if waveform_cmd in valid_waveforms:
                    current_waveform = waveform_cmd
                    print(f"切换到波形: {current_waveform}")
                else:
                    print(f"警告: 无效波形类型 '{waveform_cmd}'，忽略切换命令")
                continue
            
            # 解析音符格式：音符-时值-波形 或 音符-时值 或 音符
            if '-' in note:
                parts = note.split('-')
                if len(parts) >= 2:
                    note_name = parts[0]
                    try:
                        duration = int(parts[1])
                        # 如果有第三个部分，使用指定的波形；否则使用当前波形
                        waveform = parts[2].lower() if len(parts) > 2 else current_waveform
                        
                        # 验证波形类型
                        if waveform not in valid_waveforms:
                            print(f"警告: 无效波形类型 '{waveform}'，使用当前波形 '{current_waveform}'")
                            waveform = current_waveform
                        
                        if note_name == 'R' or note_name in self.note_frequencies:
                            valid_notes.append((note_name, duration, waveform))
                            print(f"解析音符: {note_name}, 时值: {duration}, 波形: {waveform}")
                        else:
                            print(f"警告: 忽略无效音符 '{note_name}'")
                    except ValueError:
                        print(f"警告: 忽略无效时值 '{parts[1]}'")
            else:
                # 没有指定时值和波形，默认为四分音符和当前波形
                if note == 'R' or note in self.note_frequencies:
                    valid_notes.append((note, 4, current_waveform))
                    print(f"解析音符: {note}, 时值: 4, 波形: {current_waveform}")
                else:
                    print(f"警告: 忽略无效音符 '{note}'")
        
        return valid_notes
    
    def parse_tone_script(self, script_path):
        """解析音调脚本文件"""
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            note_sequence = []
            current_waveform = "sine"  # 默认波形为正弦波
            valid_waveforms = ["sine", "square", "sawtooth", "triangle"]
            
            for line_num, line in enumerate(lines, 1):
                # 保留原始行用于调试
                original_line = line.strip()
                
                # 忽略空行
                line = original_line
                if not line:
                    continue
                
                # 处理注释（#后的内容为注释）
                if '#' in line:
                    line = line.split('#')[0].strip()
                    if not line:
                        continue
                
                # 检查是否是波形设置命令
                if line.startswith('@WAVEFORM') or line.startswith('@waveform'):
                    parts = line.split()
                    if len(parts) >= 2:
                        waveform_cmd = parts[1].lower()
                        if waveform_cmd in valid_waveforms:
                            current_waveform = waveform_cmd
                            print(f"第{line_num}行: 切换到波形 '{current_waveform}'")
                        else:
                            print(f"警告: 第{line_num}行，无效波形类型 '{waveform_cmd}'，忽略设置")
                    continue
                
                # 检查是否是简写波形切换命令
                if line.startswith('@'):
                    waveform_cmd = line[1:].strip().lower()
                    if waveform_cmd in valid_waveforms:
                        current_waveform = waveform_cmd
                        print(f"第{line_num}行: 切换到波形 '{current_waveform}'")
                    else:
                        print(f"警告: 第{line_num}行，无效波形类型 '{waveform_cmd}'，忽略设置")
                    continue
                
                # 解析每行的音符（支持空格或逗号分隔）
                # 先按逗号分割，如果没有逗号则按空格分割
                if ',' in line:
                    tokens = [token.strip().upper() for token in line.split(',') if token.strip()]
                else:
                    tokens = [token.strip().upper() for token in line.split() if token.strip()]
                
                # 处理每个token（可能是音符或波形切换命令）
                for token in tokens:
                    # 检查是否是行内波形切换命令
                    if token.startswith('@'):
                        waveform_cmd = token[1:].lower()
                        if waveform_cmd in valid_waveforms:
                            current_waveform = waveform_cmd
                            print(f"第{line_num}行: 切换到波形 '{current_waveform}'")
                        else:
                            print(f"警告: 第{line_num}行，无效波形类型 '{waveform_cmd}'，忽略切换命令")
                        continue
                    
                    # 解析音符格式：音符-时值-波形 或 音符-时值 或 音符
                    if '-' in token:
                        parts = token.split('-')
                        if len(parts) >= 2:
                            note_name = parts[0]
                            try:
                                duration = int(parts[1])
                                # 如果有第三个部分，使用指定的波形；否则使用当前波形
                                waveform = parts[2].lower() if len(parts) > 2 else current_waveform
                                
                                # 验证波形类型
                                if waveform not in valid_waveforms:
                                    print(f"警告: 第{line_num}行，无效波形类型 '{waveform}'，使用当前波形 '{current_waveform}'")
                                    waveform = current_waveform
                                
                                if note_name == 'R' or note_name in self.note_frequencies:
                                    note_sequence.append((note_name, duration, waveform))
                                    if len(note_sequence) <= 20:  # 只显示前20个
                                        print(f"解析音符[{len(note_sequence)}]: {note_name}, 时值: {duration}, 波形: {waveform}")
                                else:
                                    print(f"警告: 第{line_num}行，忽略无效音符 '{note_name}'")
                            except ValueError:
                                print(f"警告: 第{line_num}行，忽略无效时值 '{parts[1]}'")
                    else:
                        # 没有指定时值和波形，默认为四分音符和当前波形
                        if token == 'R' or token in self.note_frequencies:
                            note_sequence.append((token, 4, current_waveform))
                            if len(note_sequence) <= 20:  # 只显示前20个
                                print(f"解析音符[{len(note_sequence)}]: {token}, 时值: 4, 波形: {current_waveform}")
                        else:
                            print(f"警告: 第{line_num}行，忽略无效音符 '{token}'")
            
            return note_sequence
        except Exception as e:
            print(f"解析音调脚本时出错: {str(e)}")
            return []
    
    def calculate_beat_info(self, time_signature, bars, bpm, duration_ms, note_sequence):
        """计算节拍相关信息"""
        beats_per_bar = int(time_signature.split('/')[0])
        
        # 计算总拍数
        total_beats = beats_per_bar * bars
        
        # 计算每拍时长（秒）
        beat_duration = 60.0 / bpm
        
        # 计算总时长
        total_duration = total_beats * beat_duration
        
        # 计算节拍持续时间（秒）
        beat_sound_duration = duration_ms / 1000.0
        
        return {
            'beats_per_bar': beats_per_bar,
            'bars': bars,
            'total_beats': total_beats,
            'beat_duration': beat_duration,
            'total_duration': total_duration,
            'beat_sound_duration': beat_sound_duration,
            'note_sequence': note_sequence,
            'sequence_length': len(note_sequence)
        }
    
    def generate_white_noise_beat(self, time_signature, bars, bpm, duration_ms, noise_volume, note_volume, note_sequence):
        """生成带多音符旋律的白噪音节拍音频数据"""
        info = self.calculate_beat_info(time_signature, bars, bpm, duration_ms, note_sequence)
        
        beats_per_bar = info['beats_per_bar']
        total_beats = info['total_beats']
        beat_duration = info['beat_duration']
        total_duration = info['total_duration']
        beat_sound_duration = info['beat_sound_duration']
        note_sequence = info['note_sequence']
        
        if not note_sequence:
            note_sequence = [("C4", 4, "sine")]
        
        # 计算总样本数
        total_samples = int(total_duration * self.sample_rate)
        audio_data = np.zeros(total_samples)
        
        # 计算每个节拍的样本数
        beat_samples = int(beat_duration * self.sample_rate)
        beat_sound_samples = int(beat_sound_duration * self.sample_rate)
        
        # 生成节拍和音符
        current_sample = 0
        note_index = 0
        
        print(f"\n开始生成音频，总节拍数: {total_beats}, 音符序列长度: {len(note_sequence)}")
        print("前10个音符的详细信息:")
        
        while current_sample < total_samples:
            # 生成白噪音（每拍都有）
            end_sample = min(current_sample + beat_sound_samples, total_samples)
            if current_sample < total_samples:
                noise_length = end_sample - current_sample
                if noise_length > 0:
                    noise = np.random.uniform(-noise_volume, noise_volume, noise_length)
                    audio_data[current_sample:end_sample] += noise
            
            # 获取当前音符信息
            current_note_info = note_sequence[note_index % len(note_sequence)]
            
            # 解析音符信息
            if isinstance(current_note_info, tuple):
                if len(current_note_info) == 3:
                    current_note, note_duration, note_waveform = current_note_info
                elif len(current_note_info) == 2:
                    current_note, note_duration = current_note_info
                    note_waveform = "sine"
                else:
                    current_note = current_note_info[0]
                    note_duration = 4
                    note_waveform = "sine"
            else:
                current_note = current_note_info
                note_duration = 4
                note_waveform = "sine"
            
            # 调试输出前10个音符
            if note_index < 10:
                print(f"节拍 {note_index}: 音符={current_note}, 时值=1/{note_duration}, 波形={note_waveform}")
            
            if current_note != 'R':  # 不是休止符
                # 计算音符持续时间（以四分音符为基准）
                note_duration_sec = beat_duration * (4.0 / note_duration)
                frequency = self.note_frequencies.get(current_note, 440.0)
                
                # 使用音符自己的波形类型
                note_wave = self.generate_note(frequency, note_duration_sec, note_volume, note_waveform)
                note_samples = len(note_wave)
                end_note_sample = min(current_sample + note_samples, total_samples)
                if current_sample < total_samples:
                    note_length = end_note_sample - current_sample
                    if note_length > 0:
                        audio_data[current_sample:end_note_sample] += note_wave[:note_length]
            
            # 移动到下一个节拍
            current_sample += beat_samples
            note_index += 1
        
        # 归一化音频数据，避免削波
        max_amplitude = np.max(np.abs(audio_data))
        if max_amplitude > 1.0:
            audio_data = audio_data / max_amplitude * 0.9
        
        return audio_data, info

    def play_audio(self, audio_data, info):
        """播放音频"""
        try:
            total_duration = info['total_duration']
            beats_per_bar = info['beats_per_bar']
            note_sequence = info['note_sequence']
            beat_duration = info['beat_duration']
            
            # 开始播放
            sd.play(audio_data, self.sample_rate)
            
            # 显示进度和状态
            start_time = time.time()
            
            while (time.time() - start_time) < total_duration:
                elapsed = time.time() - start_time
                progress = (elapsed / total_duration) * 100
                
                # 显示当前节拍和音符
                current_beat = int(elapsed / beat_duration)
                bar = current_beat // beats_per_bar + 1
                beat_in_bar = current_beat % beats_per_bar + 1
                
                # 获取当前音符
                if note_sequence and current_beat < len(note_sequence):
                    current_note_info = note_sequence[current_beat]
                    if isinstance(current_note_info, tuple):
                        if len(current_note_info) == 3:
                            current_note, note_duration, note_waveform = current_note_info
                            note_display = f" - 音符: {current_note} (1/{note_duration}) - 波形: {note_waveform}"
                        elif len(current_note_info) == 2:
                            current_note, note_duration = current_note_info
                            note_display = f" - 音符: {current_note} (1/{note_duration})"
                        else:
                            current_note = current_note_info[0]
                            note_display = f" - 音符: {current_note}"
                    else:
                        current_note = current_note_info
                        note_display = f" - 音符: {current_note}"
                else:
                    note_display = ""
                
                print(f"播放中... 第{bar}小节 第{beat_in_bar}拍{note_display} [{progress:.1f}%]", end="\r")
                time.sleep(0.1)
            
            # 等待播放完成
            sd.wait()
            print("\n播放完成!                                                ")
        except Exception as e:
            print(f"播放音频时出错: {str(e)}")
            sd.stop()
    
    def save_audio(self, audio_data, info, output_file, time_signature="4/4", bpm=120):
        """保存音频为文件"""
        try:
            # 保存为音频文件
            sf.write(output_file, audio_data, self.sample_rate)
            
            # 显示保存信息
            sequence_preview_parts = []
            for note_info in info['note_sequence'][:8]:
                if isinstance(note_info, tuple):
                    if len(note_info) == 3:
                        note, duration, waveform_note = note_info
                        sequence_preview_parts.append(f"{note}-{duration}-{waveform_note}")
                    elif len(note_info) == 2:
                        note, duration = note_info
                        sequence_preview_parts.append(f"{note}-{duration}")
                    else:
                        sequence_preview_parts.append(note_info[0])
                else:
                    sequence_preview_parts.append(note_info)
            sequence_preview = " | ".join(sequence_preview_parts)
            if len(info['note_sequence']) > 8:
                sequence_preview += " ..."
            
            print(f"\n音频已保存: {output_file}")
            print(f"节拍: {time_signature}")
            print(f"速度: {bpm} BPM")
            print(f"音符序列: {sequence_preview}")
            print(f"时长: {info['total_duration']:.2f} 秒")
            print(f"总拍数: {info['total_beats']}")
        except Exception as e:
            print(f"保存音频时出错: {str(e)}")
    
    def run(self, args):
        """运行命令行版本"""
        # 输出音符表
        if args.note_table:
            self.print_note_table()
            return
        
        # 处理音符序列
        note_sequence = []
        
        # 优先使用音调脚本文件
        if args.script:
            print(f"正在读取音调脚本文件: {args.script}")
            note_sequence = self.parse_tone_script(args.script)
            if note_sequence:
                print(f"\n从脚本文件中读取到 {len(note_sequence)} 个音符")
        elif args.notes:
            # 使用命令行参数
            note_sequence = self.parse_note_sequence(args.notes)
            if note_sequence:
                print(f"\n从命令行参数读取到 {len(note_sequence)} 个音符")
        
        # 如果没有提供任何音符，使用默认序列
        if not note_sequence:
            default_notes = [
                ("C4", 4, "sine"), ("R", 4, "sine"), 
                ("E4", 4, "square"), ("R", 4, "square"),
                ("G4", 4, "sawtooth"), ("R", 4, "sawtooth"), 
                ("C5", 4, "triangle"), ("R", 4, "triangle")
            ]
            note_sequence = default_notes
            print(f"\n使用默认音符序列（包含不同波形示例）")
        
        # 生成音频
        print("\n正在生成音频...")
        audio_data, info = self.generate_white_noise_beat(
            args.time_signature,
            args.bars,
            args.bpm,
            args.duration,
            args.noise_volume,
            args.note_volume,
            note_sequence
        )
        
        # 显示节拍信息
        print("\n节拍信息:")
        print(f"节拍数: {args.time_signature}")
        print(f"小节数: {args.bars}")
        print(f"速度: {args.bpm} BPM")
        print(f"总拍数: {info['total_beats']}")
        print(f"每拍时长: {info['beat_duration']:.3f}秒")
        print(f"总时长: {info['total_duration']:.2f}秒")
        print(f"白噪音音量: {args.noise_volume:.2f}")
        print(f"音符音量: {args.note_volume:.2f}")
        print(f"音长: {info['beat_sound_duration']:.3f}秒")
        
        # 显示音符序列摘要
        print(f"\n音符序列共 {len(note_sequence)} 个音符")
        
        # 统计使用的波形类型
        waveform_stats = {}
        for note_info in note_sequence:
            if isinstance(note_info, tuple) and len(note_info) == 3:
                waveform = note_info[2]
                waveform_stats[waveform] = waveform_stats.get(waveform, 0) + 1
            elif isinstance(note_info, tuple) and len(note_info) == 2:
                waveform_stats["sine"] = waveform_stats.get("sine", 0) + 1
        
        if waveform_stats:
            print("波形使用统计:")
            for waveform, count in waveform_stats.items():
                print(f"  {waveform}: {count} 个音符")
        
        # 播放或保存
        if args.output:
            self.save_audio(audio_data, info, args.output, args.time_signature, args.bpm)
        else:
            self.play_audio(audio_data, info)

if __name__ == "__main__":
    # 检查依赖库
    try:
        import numpy as np
        import sounddevice as sd
        import soundfile as sf
    except ImportError as e:
        print(f"缺少必要的依赖库: {e}")
        print("请使用以下命令安装:")
        print("pip install numpy sounddevice soundfile")
        exit(1)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="白噪音节拍生成器 - 命令行版本")
    
    # 基本参数
    parser.add_argument("--time-signature", "-t", default="4/4", help="节拍数，默认: 4/4")
    parser.add_argument("--bars", "-b", type=int, default=8, help="小节数，默认: 8")
    parser.add_argument("--bpm", type=int, default=120, help="速度，默认: 120 BPM")
    parser.add_argument("--duration", type=int, default=150, help="节拍持续时间(ms)，默认: 150")
    
    # 声音参数
    parser.add_argument("--noise-volume", type=float, default=0.3, help="白噪音音量(0-1)，默认: 0.3")
    parser.add_argument("--note-volume", type=float, default=0.5, help="音符音量(0-1)，默认: 0.5")
    
    # 音符序列（二选一）
    parser.add_argument("--notes", "-n", default="", help="音符序列，用逗号分隔，R表示休止符，支持@波形切换和音符-时值-波形格式")
    parser.add_argument("--script", "-s", help="音调脚本文件路径，例如: script.txt")
    
    # 输出选项
    parser.add_argument("--output", "-o", help="输出音频文件路径，例如: output.wav")
    parser.add_argument("--note-table", action="store_true", help="输出音符频率表")
    
    args = parser.parse_args()
    
    # 运行
    generator = WhiteNoiseBeatGeneratorCLI()
    generator.run(args)