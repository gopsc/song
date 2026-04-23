import numpy as np
import sounddevice as sd
import soundfile as sf
import time
import argparse
import json

class WhiteNoiseBeatGeneratorCLI:
    def __init__(self):
        # 音频参数
        self.sample_rate = 44100
        
        # 音符频率字典 (A4 = 440Hz)
        self.note_frequencies = self.create_note_frequencies()
        
        # 预设旋律模式
        self.melody_presets = {
            "简单上行": ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"],
            "简单下行": ["C5", "B4", "A4", "G4", "F4", "E4", "D4", "C4"],
            "C大调音阶": ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"],
            "和弦进行": ["C4", "E4", "G4", "C4", "F4", "A4", "C5", "G4"],
            "琶音模式": ["C4", "E4", "G4", "C5", "G4", "E4", "C4", "R"],
            "节奏模式1": ["C4", "R", "E4", "R", "G4", "R", "C5", "R"],
            "节奏模式2": ["C4", "C4", "E4", "E4", "G4", "G4", "C5", "C5"],
        }
    
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
            return self.generate_sine_wave(frequency, duration, volume)
    
    def parse_note_sequence(self, sequence_str):
        """解析音符序列"""
        if not sequence_str:
            return []
        
        notes = [note.strip().upper() for note in sequence_str.split(",") if note.strip()]
        
        # 验证音符
        valid_notes = []
        for note in notes:
            if note == 'R' or note in self.note_frequencies:
                valid_notes.append(note)
            else:
                print(f"警告: 忽略无效音符 '{note}'")
        
        return valid_notes
    
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
    
    def generate_white_noise_beat(self, time_signature, bars, bpm, duration_ms, noise_volume, note_volume, waveform, note_sequence):
        """生成带多音符旋律的白噪音节拍音频数据"""
        info = self.calculate_beat_info(time_signature, bars, bpm, duration_ms, note_sequence)
        
        beats_per_bar = info['beats_per_bar']
        total_beats = info['total_beats']
        beat_duration = info['beat_duration']
        total_duration = info['total_duration']
        beat_sound_duration = info['beat_sound_duration']
        note_sequence = info['note_sequence']
        
        if not note_sequence:
            note_sequence = ["C4"]  # 默认音符
        
        # 计算总样本数
        total_samples = int(total_duration * self.sample_rate)
        audio_data = np.zeros(total_samples)
        
        # 计算每个节拍的样本数
        beat_samples = int(beat_duration * self.sample_rate)
        beat_sound_samples = int(beat_sound_duration * self.sample_rate)
        
        # 生成节拍
        for beat in range(total_beats):
            # 计算节拍开始位置
            start_sample = beat * beat_samples
            
            # 生成白噪音（每拍都有）
            end_sample = min(start_sample + beat_sound_samples, total_samples)
            if start_sample < total_samples:
                noise_length = end_sample - start_sample
                if noise_length > 0:
                    noise = np.random.uniform(-noise_volume, noise_volume, noise_length)
                    audio_data[start_sample:end_sample] += noise
            
            # 生成音符（根据序列循环）
            note_index = beat % len(note_sequence)
            current_note = note_sequence[note_index]
            
            if current_note != 'R':  # 不是休止符
                frequency = self.note_frequencies.get(current_note, 440.0)
                note_wave = self.generate_note(frequency, beat_sound_duration, note_volume, waveform)
                note_samples = len(note_wave)
                end_note_sample = min(start_sample + note_samples, total_samples)
                if start_sample < total_samples:
                    note_length = end_note_sample - start_sample
                    if note_length > 0:
                        audio_data[start_sample:end_note_sample] += note_wave[:note_length]
        
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
                if note_sequence:
                    current_note_index = current_beat % len(note_sequence)
                    current_note = note_sequence[current_note_index]
                    note_display = f" - 音符: {current_note}"
                else:
                    note_display = ""
                
                print(f"播放中... 第{bar}小节 第{beat_in_bar}拍{note_display} [{progress:.1f}%]", end="\r")
                time.sleep(0.1)
            
            # 等待播放完成
            sd.wait()
            print("播放完成!                                                ")
        except Exception as e:
            print(f"播放音频时出错: {str(e)}")
            sd.stop()
    
    def save_audio(self, audio_data, info, output_file):
        """保存音频为文件"""
        try:
            # 保存为音频文件
            sf.write(output_file, audio_data, self.sample_rate)
            
            # 显示保存信息
            sequence_preview = " | ".join(info['note_sequence'][:8])
            if len(info['note_sequence']) > 8:
                sequence_preview += " ..."
            
            print(f"音频已保存: {output_file}")
            print(f"节拍: {args.time_signature}")
            print(f"速度: {args.bpm} BPM")
            print(f"波形: {args.waveform}")
            print(f"音符序列: {sequence_preview}")
            print(f"时长: {info['total_duration']:.2f} 秒")
            print(f"总拍数: {info['total_beats']}")
        except Exception as e:
            print(f"保存音频时出错: {str(e)}")
    
    def run(self, args):
        """运行命令行版本"""
        # 处理音符序列
        if args.preset:
            if args.preset in self.melody_presets:
                note_sequence = self.melody_presets[args.preset]
                print(f"使用预设旋律: {args.preset}")
            else:
                print(f"警告: 预设 '{args.preset}' 不存在，使用默认序列")
                note_sequence = ["C4", "R", "E4", "R", "G4", "R", "C5", "R"]
        else:
            note_sequence = self.parse_note_sequence(args.notes)
            if not note_sequence:
                note_sequence = ["C4", "R", "E4", "R", "G4", "R", "C5", "R"]
                print("使用默认音符序列")
        
        # 生成音频
        print("正在生成音频...")
        audio_data, info = self.generate_white_noise_beat(
            args.time_signature,
            args.bars,
            args.bpm,
            args.duration,
            args.noise_volume,
            args.note_volume,
            args.waveform,
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
        print(f"波形: {args.waveform}")
        print(f"白噪音音量: {args.noise_volume:.2f}")
        print(f"音符音量: {args.note_volume:.2f}")
        print(f"音长: {info['beat_sound_duration']:.3f}秒")
        print(f"音符序列: {' | '.join(note_sequence[:12])}{' ...' if len(note_sequence) > 12 else ''}")
        
        # 播放或保存
        if args.output:
            self.save_audio(audio_data, info, args.output)
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
    parser.add_argument("--waveform", "-w", default="sine", choices=["sine", "square", "sawtooth", "triangle"], help="波形类型，默认: sine")
    
    # 音符序列
    parser.add_argument("--notes", "-n", default="", help="音符序列，用逗号分隔，R表示休止符，例如: C4,R,E4,R,G4,R,C5,R")
    parser.add_argument("--preset", "-p", help="预设旋律模式，例如: 节奏模式1")
    
    # 输出选项
    parser.add_argument("--output", "-o", help="输出音频文件路径，例如: output.wav")
    
    args = parser.parse_args()
    
    # 运行
    generator = WhiteNoiseBeatGeneratorCLI()
    generator.run(args)
