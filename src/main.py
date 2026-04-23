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
        
        # 默认参数
        self.default_time_signature = "4/4"
        self.default_bars = 8
        self.default_bpm = 120
        self.default_duration = 150
        self.default_noise_volume = 0.3
        self.default_note_volume = 0.5
        self.default_waveform = "sine"
    
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
        
        frequencies['R'] = 0.0
        return frequencies
    
    def print_note_table(self):
        """输出音符表"""
        print("\n=== 音符频率表 ===")
        print("格式: 音符名称 (频率 Hz)")
        print("-" * 40)
        
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
        if frequency == 0:
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
    
    def parse_tone_script(self, script_path):
        """解析音调脚本文件，支持动态参数设置"""
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            events = []
            
            # 当前参数状态
            current_params = {
                'bpm': self.default_bpm,
                'duration': self.default_duration,
                'noise_volume': self.default_noise_volume,
                'note_volume': self.default_note_volume,
                'waveform': self.default_waveform
            }
            
            # 全局参数（不适合动态变化）
            global_params = {
                'time_signature': self.default_time_signature,
                'bars': self.default_bars
            }
            
            valid_waveforms = ["sine", "square", "sawtooth", "triangle"]
            beat_position = 0
            
            print("\n=== 开始解析乐谱脚本 ===")
            
            for line_num, line in enumerate(lines, 1):
                original_line = line.strip()
                
                if not original_line:
                    continue
                
                if '#' in original_line:
                    line_content = original_line.split('#')[0].strip()
                    if not line_content:
                        continue
                else:
                    line_content = original_line
                
                # 检查是否是参数设置命令
                if line_content.startswith('@'):
                    parts = line_content[1:].split()
                    if len(parts) >= 2:
                        param_name = parts[0].lower()
                        param_value = parts[1]
                        
                        if param_name == 'time_signature' or param_name == 'time-signature' or param_name == 'ts':
                            global_params['time_signature'] = param_value
                            print(f"第{line_num}行: 设置节拍为 {param_value} (全局)")
                        elif param_name == 'bars' or param_name == 'b':
                            try:
                                global_params['bars'] = int(param_value)
                                print(f"第{line_num}行: 设置小节数为 {param_value} (全局)")
                            except ValueError:
                                print(f"警告: 第{line_num}行，无效的小节数值 '{param_value}'")
                        elif param_name == 'bpm':
                            try:
                                bpm_val = int(param_value)
                                current_params['bpm'] = bpm_val
                                events.append(('param_change', beat_position, 'bpm', bpm_val))
                                print(f"第{line_num}行: 设置速度为 {param_value} BPM (从位置 {beat_position} 开始)")
                            except ValueError:
                                print(f"警告: 第{line_num}行，无效的速度值 '{param_value}'")
                        elif param_name == 'duration' or param_name == 'd':
                            try:
                                dur_val = int(param_value)
                                current_params['duration'] = dur_val
                                events.append(('param_change', beat_position, 'duration', dur_val))
                                print(f"第{line_num}行: 设置节拍持续时间为 {param_value} ms (从位置 {beat_position} 开始)")
                            except ValueError:
                                print(f"警告: 第{line_num}行，无效的持续时间值 '{param_value}'")
                        elif param_name == 'noise_volume' or param_name == 'nv':
                            try:
                                vol = float(param_value)
                                current_params['noise_volume'] = vol
                                events.append(('param_change', beat_position, 'noise_volume', vol))
                                print(f"第{line_num}行: 设置白噪音音量为 {param_value} (从位置 {beat_position} 开始)")
                            except ValueError:
                                print(f"警告: 第{line_num}行，无效的白噪音音量值 '{param_value}'")
                        elif param_name == 'note_volume' or param_name == 'vol':
                            try:
                                vol = float(param_value)
                                current_params['note_volume'] = vol
                                events.append(('param_change', beat_position, 'note_volume', vol))
                                print(f"第{line_num}行: 设置音符音量为 {param_value} (从位置 {beat_position} 开始)")
                            except ValueError:
                                print(f"警告: 第{line_num}行，无效的音符音量值 '{param_value}'")
                        elif param_name == 'waveform' or param_name == 'w':
                            waveform_cmd = param_value.lower()
                            if waveform_cmd in valid_waveforms:
                                current_params['waveform'] = waveform_cmd
                                events.append(('param_change', beat_position, 'waveform', waveform_cmd))
                                print(f"第{line_num}行: 设置默认波形为 '{waveform_cmd}' (从位置 {beat_position} 开始)")
                            else:
                                print(f"警告: 第{line_num}行，无效波形类型 '{waveform_cmd}'")
                        else:
                            if param_name in valid_waveforms:
                                current_params['waveform'] = param_name
                                events.append(('param_change', beat_position, 'waveform', param_name))
                                print(f"第{line_num}行: 切换到波形 '{param_name}' (从位置 {beat_position} 开始)")
                            else:
                                print(f"警告: 第{line_num}行，未知参数 '{param_name}'")
                    elif len(parts) == 1:
                        waveform_cmd = parts[0].lower()
                        if waveform_cmd in valid_waveforms:
                            current_params['waveform'] = waveform_cmd
                            events.append(('param_change', beat_position, 'waveform', waveform_cmd))
                            print(f"第{line_num}行: 切换到波形 '{waveform_cmd}' (从位置 {beat_position} 开始)")
                        else:
                            print(f"警告: 第{line_num}行，无效波形类型 '{waveform_cmd}'")
                    continue
                
                # 解析音符
                if ',' in line_content:
                    tokens = [token.strip().upper() for token in line_content.split(',') if token.strip()]
                else:
                    tokens = [token.strip().upper() for token in line_content.split() if token.strip()]
                
                for token in tokens:
                    if token.startswith('@'):
                        waveform_cmd = token[1:].lower()
                        if waveform_cmd in valid_waveforms:
                            current_params['waveform'] = waveform_cmd
                            events.append(('param_change', beat_position, 'waveform', waveform_cmd))
                            print(f"第{line_num}行: 切换到波形 '{waveform_cmd}' (从位置 {beat_position} 开始)")
                        continue
                    
                    if '-' in token:
                        parts = token.split('-')
                        if len(parts) >= 2:
                            note_name = parts[0]
                            try:
                                duration = int(parts[1])
                                waveform = parts[2].lower() if len(parts) > 2 else current_params['waveform']
                                
                                if waveform not in valid_waveforms:
                                    waveform = current_params['waveform']
                                
                                if note_name == 'R' or note_name in self.note_frequencies:
                                    note_params = {
                                        'note_volume': current_params['note_volume'],
                                        'waveform': waveform,
                                        'bpm': current_params['bpm'],
                                        'duration': current_params['duration'],
                                        'noise_volume': current_params['noise_volume']
                                    }
                                    events.append(('note', beat_position, note_name, duration, note_params))
                                    
                                    if len([e for e in events if e[0] == 'note']) <= 20:
                                        print(f"解析音符[位置{beat_position}]: {note_name}, 时值: 1/{duration}, "
                                              f"BPM: {note_params['bpm']}, 音量: {note_params['note_volume']}")
                                    
                                    beat_position += 1
                                else:
                                    print(f"警告: 第{line_num}行，忽略无效音符 '{note_name}'")
                            except ValueError:
                                print(f"警告: 第{line_num}行，忽略无效时值 '{parts[1]}'")
                    else:
                        if token == 'R' or token in self.note_frequencies:
                            note_params = {
                                'note_volume': current_params['note_volume'],
                                'waveform': current_params['waveform'],
                                'bpm': current_params['bpm'],
                                'duration': current_params['duration'],
                                'noise_volume': current_params['noise_volume']
                            }
                            events.append(('note', beat_position, token, 4, note_params))
                            
                            if len([e for e in events if e[0] == 'note']) <= 20:
                                print(f"解析音符[位置{beat_position}]: {token}, 时值: 1/4, "
                                      f"BPM: {note_params['bpm']}, 音量: {note_params['note_volume']}")
                            
                            beat_position += 1
                        else:
                            print(f"警告: 第{line_num}行，忽略无效音符 '{token}'")
            
            final_params = {**global_params, **current_params}
            note_count = len([e for e in events if e[0] == 'note'])
            print(f"=== 乐谱解析完成，共 {note_count} 个音符 ===\n")
            
            return events, final_params
        except Exception as e:
            print(f"解析音调脚本时出错: {str(e)}")
            return [], {}
    
    def generate_audio_with_dynamic_params(self, events, final_params):
        """根据事件序列生成音频，支持所有动态参数变化"""
        
        base_time_signature = final_params['time_signature']
        base_bars = final_params['bars']
        
        # 分离音符
        note_events = [e for e in events if e[0] == 'note']
        
        if not note_events:
            print("错误: 没有找到任何音符")
            return None, None
        
        # 计算总节拍数
        beats_per_bar = int(base_time_signature.split('/')[0])
        total_beats = beats_per_bar * base_bars
        
        # 因为 BPM 可能动态变化，我们需要逐个节拍计算
        # 先计算每个节拍的时间位置
        
        beat_times = [0.0]  # 每个节拍的开始时间
        current_time = 0.0
        
        print("\n计算节拍时间线...")
        
        for beat_index in range(total_beats):
            # 获取这个节拍对应的参数（使用音符事件的参数）
            note_event = note_events[beat_index % len(note_events)]
            bpm = note_event[4].get('bpm', self.default_bpm)
            
            beat_duration = 60.0 / bpm
            current_time += beat_duration
            beat_times.append(current_time)
            
            if beat_index < 5:
                print(f"节拍 {beat_index}: BPM={bpm}, 节拍时长={beat_duration:.3f}秒, 累计时间={current_time:.3f}秒")
        
        total_duration = current_time
        total_samples = int(total_duration * self.sample_rate)
        audio_data = np.zeros(total_samples)
        
        print(f"\n总时长: {total_duration:.2f}秒, 总样本数: {total_samples}")
        print("开始生成音频...\n")
        
        # 为每个节拍生成音频
        for beat_index in range(total_beats):
            note_event = note_events[beat_index % len(note_events)]
            _, _, note_name, note_duration, note_params = note_event
            
            # 获取这个节拍的参数
            bpm = note_params.get('bpm', self.default_bpm)
            duration_ms = note_params.get('duration', self.default_duration)
            noise_volume = note_params.get('noise_volume', self.default_noise_volume)
            note_volume = note_params.get('note_volume', self.default_note_volume)
            note_waveform = note_params.get('waveform', self.default_waveform)
            
            # 计算这个节拍的时间信息
            beat_start_time = beat_times[beat_index]
            beat_duration = 60.0 / bpm
            beat_sound_duration = duration_ms / 1000.0
            
            # 计算样本位置
            start_sample = int(beat_start_time * self.sample_rate)
            beat_samples = int(beat_duration * self.sample_rate)
            sound_samples = int(beat_sound_duration * self.sample_rate)
            
            if beat_index < 10:
                print(f"生成节拍 {beat_index}: BPM={bpm}, 噪音音量={noise_volume}, "
                      f"音符音量={note_volume}, 波形={note_waveform}")
            
            # 生成白噪音
            end_sample = min(start_sample + sound_samples, total_samples)
            if start_sample < total_samples:
                noise_length = end_sample - start_sample
                if noise_length > 0:
                    noise = np.random.uniform(-noise_volume, noise_volume, noise_length)
                    audio_data[start_sample:end_sample] += noise
            
            # 生成音符
            if note_name != 'R':
                note_duration_sec = beat_duration * (4.0 / note_duration)
                frequency = self.note_frequencies.get(note_name, 440.0)
                
                note_wave = self.generate_note(frequency, note_duration_sec, note_volume, note_waveform)
                note_samples = len(note_wave)
                end_note_sample = min(start_sample + note_samples, total_samples)
                
                if start_sample < total_samples:
                    note_length = end_note_sample - start_sample
                    if note_length > 0:
                        audio_data[start_sample:end_note_sample] += note_wave[:note_length]
        
        # 归一化
        max_amplitude = np.max(np.abs(audio_data))
        if max_amplitude > 1.0:
            audio_data = audio_data / max_amplitude * 0.9
        
        info = {
            'beats_per_bar': beats_per_bar,
            'bars': base_bars,
            'total_beats': total_beats,
            'total_duration': total_duration,
            'note_count': len(note_events)
        }
        
        return audio_data, info

    def play_audio(self, audio_data, info):
        """播放音频"""
        try:
            total_duration = info['total_duration']
            
            sd.play(audio_data, self.sample_rate)
            
            start_time = time.time()
            
            while (time.time() - start_time) < total_duration:
                elapsed = time.time() - start_time
                progress = (elapsed / total_duration) * 100
                
                print(f"播放中... [{progress:.1f}%]", end="\r")
                time.sleep(0.1)
            
            sd.wait()
            print("\n播放完成!                                                ")
        except Exception as e:
            print(f"播放音频时出错: {str(e)}")
            sd.stop()
    
    def save_audio(self, audio_data, info, output_file, time_signature="4/4", bpm=120):
        """保存音频为文件"""
        try:
            sf.write(output_file, audio_data, self.sample_rate)
            
            print(f"\n音频已保存: {output_file}")
            print(f"节拍: {time_signature}")
            print(f"参考速度: {bpm} BPM")
            print(f"时长: {info['total_duration']:.2f} 秒")
            print(f"总拍数: {info['total_beats']}")
            print(f"音符数: {info['note_count']}")
        except Exception as e:
            print(f"保存音频时出错: {str(e)}")
    
    def run(self, args):
        """运行命令行版本"""
        if args.note_table:
            self.print_note_table()
            return
        
        if not args.script:
            print("错误: 必须提供乐谱脚本文件！")
            print("使用方法: python script.py -s <脚本文件> [-o <输出文件>]")
            return
        
        print(f"正在读取乐谱脚本文件: {args.script}")
        events, final_params = self.parse_tone_script(args.script)
        
        if not events:
            print("错误: 脚本中没有找到有效的音符序列")
            return
        
        print(f"\n=== 最终参数 ===")
        for key, value in final_params.items():
            print(f"{key}: {value}")
        print("===============\n")
        
        print("正在生成音频...")
        audio_data, info = self.generate_audio_with_dynamic_params(events, final_params)
        
        if audio_data is None:
            print("错误: 音频生成失败")
            return
        
        if args.output:
            self.save_audio(audio_data, info, args.output, 
                          final_params['time_signature'], final_params['bpm'])
        else:
            self.play_audio(audio_data, info)

if __name__ == "__main__":
    try:
        import numpy as np
        import sounddevice as sd
        import soundfile as sf
    except ImportError as e:
        print(f"缺少必要的依赖库: {e}")
        print("请使用以下命令安装:")
        print("pip install numpy sounddevice soundfile")
        exit(1)
    
    parser = argparse.ArgumentParser(description="白噪音节拍生成器 - 所有参数由乐谱脚本动态控制")
    parser.add_argument("--script", "-s", required=True, help="乐谱脚本文件路径（必需）")
    parser.add_argument("--output", "-o", help="输出音频文件路径（可选）")
    parser.add_argument("--note-table", action="store_true", help="输出音符频率表")
    
    args = parser.parse_args()
    
    generator = WhiteNoiseBeatGeneratorCLI()
    generator.run(args)