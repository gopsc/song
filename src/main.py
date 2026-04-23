import numpy as np
import sounddevice as sd
import soundfile as sf
import time
import argparse
import re

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
        
        # 时值映射表（支持各种音符时值）
        self.duration_map = {
            '1': 1.0,      # 全音符
            '2': 0.5,      # 二分音符
            '4': 0.25,     # 四分音符
            '8': 0.125,    # 八分音符
            '16': 0.0625,  # 十六分音符
            '32': 0.03125, # 三十二分音符
            '64': 0.015625,# 六十四分音符
        }
    
    def normalize_note_name(self, note_name):
        """规范化音符名称，处理等音转换（如 E# -> F）"""
        # 等音映射表
        enharmonic_map = {
            'E#': 'F',    # E# 等于 F
            'B#': 'C',    # B# 等于 C
            'Fb': 'E',    # Fb 等于 E
            'Cb': 'B',    # Cb 等于 B
            'E##': 'F#',  # E## 等于 F#
            'B##': 'C#',  # B## 等于 C#
            'F##': 'G',   # F## 等于 G
            'C##': 'D',   # C## 等于 D
        }
        
        # 分离音符名和八度
        match = re.match(r'([A-G][#b]*)(\d+)', note_name)
        if match:
            note_root = match.group(1)
            octave = match.group(2)
            
            # 检查是否需要等音转换
            if note_root in enharmonic_map:
                normalized_root = enharmonic_map[note_root]
                normalized_name = f"{normalized_root}{octave}"
                print(f"提示: 将 {note_name} 转换为 {normalized_name} (等音)")
                return normalized_name
        
        return note_name
    
    def parse_note_duration(self, duration_str):
        """解析音符时值，支持分数形式（如 4, 8, 16, 4.5, 8.3等）"""
        try:
            # 支持浮点数时值
            if '.' in duration_str:
                duration_value = float(duration_str)
                # 时值基准：4 = 四分音符
                # 所以 8 = 八分音符，16 = 十六分音符，等等
                duration_ratio = 4.0 / duration_value
                return duration_ratio
            else:
                duration_int = int(duration_str)
                if duration_int in self.duration_map:
                    return self.duration_map[duration_int]
                else:
                    # 对于其他整数，计算相对时值
                    return 4.0 / duration_int
        except ValueError:
            print(f"警告: 无效的时值 '{duration_str}'，使用默认四分音符")
            return 0.25
    
    def create_note_frequencies(self):
        """创建完整的音符频率表（包含等音支持）"""
        base_notes = {
            'C': 261.63, 'C#': 277.18, 'Db': 277.18,  # Db 是 C# 的等音
            'D': 293.66, 'D#': 311.13, 'Eb': 311.13,  # Eb 是 D# 的等音
            'E': 329.63, 'F': 349.23, 'E#': 349.23,   # E# 是 F 的等音
            'F#': 369.99, 'Gb': 369.99,                # Gb 是 F# 的等音
            'G': 392.00, 'G#': 415.30, 'Ab': 415.30,  # Ab 是 G# 的等音
            'A': 440.00, 'A#': 466.16, 'Bb': 466.16,  # Bb 是 A# 的等音
            'B': 493.88, 'Cb': 493.88,                # Cb 是 B 的等音
            'B#': 523.25,                             # B# 是 C 的等音（下一八度）
        }
        
        frequencies = {}
        for octave in range(1, 8):
            for note, freq in base_notes.items():
                note_name = f"{note}{octave}"
                # 计算正确的八度频率
                if note in ['C', 'C#', 'Db', 'D', 'D#', 'Eb', 'E', 'F', 'E#', 
                           'F#', 'Gb', 'G', 'G#', 'Ab', 'A', 'A#', 'Bb', 'B', 'Cb']:
                    # A4 = 440Hz 基准
                    if note in ['A'] and octave == 4:
                        multiplier = 1.0
                    else:
                        # 计算相对于 A4 的半音数
                        note_refs = {
                            'C': -9, 'C#': -8, 'Db': -8,
                            'D': -7, 'D#': -6, 'Eb': -6,
                            'E': -5, 'F': -4, 'E#': -4,
                            'F#': -3, 'Gb': -3,
                            'G': -2, 'G#': -1, 'Ab': -1,
                            'A': 0, 'A#': 1, 'Bb': 1,
                            'B': 2, 'Cb': 2, 'B#': 3,
                        }
                        semitones = note_refs.get(note, 0) + (octave - 4) * 12
                        multiplier = 2 ** (semitones / 12)
                    frequencies[note_name] = 440.0 * multiplier
        
        # 手动确保 E# 在正确八度的频率
        for octave in range(1, 8):
            f_note = f"F{octave}"
            e_sharp_note = f"E#{octave}"
            if f_note in frequencies:
                frequencies[e_sharp_note] = frequencies[f_note]
            
            b_sharp_note = f"B#{octave}"
            c_next_octave = f"C{octave + 1}"
            if c_next_octave in frequencies:
                frequencies[b_sharp_note] = frequencies[c_next_octave]
        
        frequencies['R'] = 0.0
        return frequencies
    
    def print_note_table(self):
        """输出音符表（包含等音）"""
        print("\n=== 音符频率表 ===")
        print("格式: 音符名称 (频率 Hz)")
        print("注: 显示等音关系 (如 E# = F)")
        print("-" * 50)
        
        for octave in range(1, 8):
            print(f"\n八度 {octave}:")
            # 显示主要音符和等音
            display_notes = [
                'C', 'C#/Db', 'D', 'D#/Eb', 'E', 'F', 'F#/Gb', 
                'G', 'G#/Ab', 'A', 'A#/Bb', 'B'
            ]
            
            for display_note in display_notes:
                if '/' in display_note:
                    note1, note2 = display_note.split('/')
                    note_name1 = f"{note1}{octave}"
                    note_name2 = f"{note2}{octave}"
                    freq1 = self.note_frequencies.get(note_name1)
                    freq2 = self.note_frequencies.get(note_name2)
                    if freq1 and freq2:
                        print(f"{display_note:8} : {freq1:6.2f} Hz (等音: {note_name2} {freq2:.2f}Hz)")
                else:
                    # 显示 E# 和 B# 等特殊音符
                    note_name = f"{display_note}{octave}"
                    if note_name in self.note_frequencies:
                        freq = self.note_frequencies[note_name]
                        if display_note == 'E':
                            e_sharp = f"E#{octave}"
                            if e_sharp in self.note_frequencies:
                                e_sharp_freq = self.note_frequencies[e_sharp]
                                print(f"{display_note:8} : {freq:6.2f} Hz (E# = {e_sharp_freq:.2f}Hz)")
                            else:
                                print(f"{display_note:8} : {freq:6.2f} Hz")
                        elif display_note == 'B':
                            b_sharp = f"B#{octave}"
                            if b_sharp in self.note_frequencies:
                                b_sharp_freq = self.note_frequencies[b_sharp]
                                print(f"{display_note:8} : {freq:6.2f} Hz (B# = {b_sharp_freq:.2f}Hz)")
                            else:
                                print(f"{display_note:8} : {freq:6.2f} Hz")
                        else:
                            print(f"{display_note:8} : {freq:6.2f} Hz")
        
        print("\n特殊符号:")
        print("R : 休止符 (0 Hz)")
        print("\n等音说明:")
        print("E# = F,  B# = C,  Cb = B,  Fb = E")
        print("E## = F#, B## = C#, F## = G, C## = D")
        
        print("\n=== 音符时值表 ===")
        print("支持的时值:")
        print("1  : 全音符")
        print("2  : 二分音符")
        print("4  : 四分音符")
        print("8  : 八分音符")
        print("16 : 十六分音符")
        print("32 : 三十二分音符")
        print("64 : 六十四分音符")
        print("也支持数字时值（如 4, 8, 16, 4.5, 3.2等）")
        print("-" * 50)
    
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
        """解析音调脚本文件，支持动态参数设置和16分音符"""
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
            print("支持时值: 1(全),2(二分),4(四分),8(八分),16(十六分),32(三十二分),64(六十四分)")
            print("-" * 50)
            
            for line_num, line in enumerate(lines, 1):
                original_line = line.strip()
                
                if not original_line:
                    continue
                
                # 核心修复：注释处理逻辑
                # 仅匹配「行首/空白字符后的#」为注释，保留音符里的升号#（如C#4、D#4）
                line_content = re.sub(r'(?<!\S)#.*', '', original_line).strip()
                if not line_content:
                    continue
                
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
                            # 规范化音符名称（处理 E# 等）
                            normalized_note_name = self.normalize_note_name(note_name)
                            
                            # 解析时值（支持分数和整数）
                            duration_str = parts[1]
                            duration_ratio = self.parse_note_duration(duration_str)
                            
                            # 可选波形参数
                            waveform = current_params['waveform']
                            if len(parts) > 2:
                                waveform_candidate = parts[2].lower()
                                if waveform_candidate in valid_waveforms:
                                    waveform = waveform_candidate
                            
                            if normalized_note_name == 'R' or normalized_note_name in self.note_frequencies:
                                note_params = {
                                    'note_volume': current_params['note_volume'],
                                    'waveform': waveform,
                                    'bpm': current_params['bpm'],
                                    'duration': current_params['duration'],
                                    'noise_volume': current_params['noise_volume']
                                }
                                # 存储时值比率而不是分数分母
                                events.append(('note', beat_position, normalized_note_name, duration_ratio, note_params))
                                
                                if len([e for e in events if e[0] == 'note']) <= 20:
                                    # 显示时值信息
                                    if duration_str in self.duration_map:
                                        duration_name = {1:'全',2:'二分',4:'四分',8:'八分',16:'十六分',32:'三十二分',64:'六十四分'}.get(int(duration_str), f'{duration_str}分')
                                        print(f"解析音符[位置{beat_position}]: {normalized_note_name} (原始: {note_name}), 时值: {duration_name}音符, "
                                              f"BPM: {note_params['bpm']}, 音量: {note_params['note_volume']}")
                                    else:
                                        print(f"解析音符[位置{beat_position}]: {normalized_note_name} (原始: {note_name}), 时值: {duration_ratio:.4f}倍四分音符, "
                                              f"BPM: {note_params['bpm']}, 音量: {note_params['note_volume']}")
                                
                                beat_position += 1
                            else:
                                print(f"警告: 第{line_num}行，忽略无效音符 '{note_name}'")
                    else:
                        # 规范化音符名称（处理 E# 等）
                        normalized_token = self.normalize_note_name(token)
                        
                        if normalized_token == 'R' or normalized_token in self.note_frequencies:
                            note_params = {
                                'note_volume': current_params['note_volume'],
                                'waveform': current_params['waveform'],
                                'bpm': current_params['bpm'],
                                'duration': current_params['duration'],
                                'noise_volume': current_params['noise_volume']
                            }
                            # 默认四分音符（时值比率 0.25）
                            events.append(('note', beat_position, normalized_token, 0.25, note_params))
                            
                            if len([e for e in events if e[0] == 'note']) <= 20:
                                print(f"解析音符[位置{beat_position}]: {normalized_token} (原始: {token}), 时值: 四分音符, "
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
        """根据事件序列生成音频，支持所有动态参数变化和精细时值"""
        
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
            _, _, note_name, duration_ratio, note_params = note_event
            
            # 获取这个节拍的参数
            bpm = note_params.get('bpm', self.default_bpm)
            duration_ms = note_params.get('duration', self.default_duration)
            noise_volume = note_params.get('noise_volume', self.default_noise_volume)
            note_volume = note_params.get('note_volume', self.default_note_volume)
            note_waveform = note_params.get('waveform', self.default_waveform)
            
            # 计算这个节拍的时间信息
            beat_start_time = beat_times[beat_index]
            beat_duration = 60.0 / bpm
            
            # 使用 duration_ratio 计算音符持续时间
            # duration_ratio 是相对于四分音符的比率（四分音符=0.25）
            # 例如：十六分音符 duration_ratio = 0.0625
            note_duration_sec = beat_duration * (duration_ratio / 0.25)
            
            # 白噪音持续时间
            beat_sound_duration = duration_ms / 1000.0
            
            # 计算样本位置
            start_sample = int(beat_start_time * self.sample_rate)
            sound_samples = int(beat_sound_duration * self.sample_rate)
            
            if beat_index < 10:
                print(f"生成节拍 {beat_index}: BPM={bpm}, 噪音音量={noise_volume}, "
                      f"音符音量={note_volume}, 波形={note_waveform}, 音符时长={note_duration_sec:.3f}秒")
            
            # 生成白噪音
            end_sample = min(start_sample + sound_samples, total_samples)
            if start_sample < total_samples:
                noise_length = end_sample - start_sample
                if noise_length > 0:
                    noise = np.random.uniform(-noise_volume, noise_volume, noise_length)
                    audio_data[start_sample:end_sample] += noise
            
            # 生成音符
            if note_name != 'R':
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
            print(f"采样率: {self.sample_rate} Hz")
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
    
    parser = argparse.ArgumentParser(description="白噪音节拍生成器 - 支持E#等音和16分音符等精细时值")
    parser.add_argument("--script", "-s", required=True, help="乐谱脚本文件路径（必需）")
    parser.add_argument("--output", "-o", help="输出音频文件路径（可选）")
    parser.add_argument("--note-table", action="store_true", help="输出音符频率表和时值表")
    
    args = parser.parse_args()
    
    generator = WhiteNoiseBeatGeneratorCLI()
    generator.run(args)
