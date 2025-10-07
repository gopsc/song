import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import sounddevice as sd
import soundfile as sf
import threading
import time
import math
import json
import platform

class WhiteNoiseBeatGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("白噪音节拍生成器 - 多音符旋律")
        
        # 检测操作系统并设置窗口最大化
        self.setup_window()
        
        # 音频参数
        self.sample_rate = 44100
        self.is_playing = False
        self.play_thread = None
        
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
            "自定义": []
        }
        
        # 当前音符序列
        self.note_sequence = ["C4", "R", "E4", "R", "G4", "R", "C5", "R"]
        
        # 创建GUI
        self.create_widgets()
        
    def setup_window(self):
        """设置窗口大小和位置"""
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 设置窗口大小为屏幕的90%
        window_width = int(screen_width * 0.9)
        window_height = int(screen_height * 0.9)
        
        # 计算居中位置
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # 设置窗口大小和位置
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 尝试设置最大化（根据不同操作系统）
        system = platform.system()
        if system == "Windows":
            try:
                self.root.state('zoomed')
            except:
                pass
        elif system == "Linux":
            try:
                self.root.attributes('-zoomed', True)
            except:
                pass
        elif system == "Darwin":  # macOS
            try:
                self.root.attributes('-fullscreen', False)
                # macOS 没有直接的zoomed，我们使用geometry来模拟
            except:
                pass
        
        # 设置最小窗口大小
        self.root.minsize(1000, 700)
        
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
    
    def create_widgets(self):
        # 主框架 - 使用更大的padding适应大屏幕
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置根窗口的网格权重，使其可以扩展
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(7, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # 标题 - 使用更大的字体
        title_label = ttk.Label(main_frame, text="白噪音节拍生成器 - 多音符旋律", 
                               font=("Arial", 20, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 25))
        
        # 节拍设置框架 - 增加内边距
        beat_frame = ttk.LabelFrame(main_frame, text="节拍设置", padding="15")
        beat_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        beat_frame.grid_columnconfigure(1, weight=1)
        beat_frame.grid_columnconfigure(3, weight=1)
        
        # 常见节拍数选择 - 调整布局适应大窗口
        ttk.Label(beat_frame, text="节拍数:", font=("Arial", 11)).grid(row=0, column=0, sticky=tk.W, pady=8)
        self.time_signature_var = tk.StringVar(value="4/4")
        time_signatures = ["4/4", "3/4", "2/4", "6/8", "5/4", "7/8"]
        time_signature_combo = ttk.Combobox(beat_frame, textvariable=self.time_signature_var, 
                                           values=time_signatures, state="readonly", width=12, font=("Arial", 10))
        time_signature_combo.grid(row=0, column=1, sticky=tk.W, pady=8, padx=(15, 0))
        
        # 小节数
        ttk.Label(beat_frame, text="小节数:", font=("Arial", 11)).grid(row=0, column=2, sticky=tk.W, pady=8, padx=(30, 0))
        self.bars_var = tk.IntVar(value=8)
        bars_spinbox = ttk.Spinbox(beat_frame, from_=1, to=64, textvariable=self.bars_var, 
                                  width=10, font=("Arial", 10))
        bars_spinbox.grid(row=0, column=3, sticky=tk.W, pady=8, padx=(15, 0))
        
        # 速度(BPM) - 使用更长的滑块
        ttk.Label(beat_frame, text="速度 (BPM):", font=("Arial", 11)).grid(row=1, column=0, sticky=tk.W, pady=12)
        self.bpm_var = tk.IntVar(value=120)
        bpm_scale = ttk.Scale(beat_frame, from_=40, to=240, variable=self.bpm_var, 
                             orient=tk.HORIZONTAL, length=300)
        bpm_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=12, padx=(15, 0))
        self.bpm_entry = ttk.Entry(beat_frame, textvariable=self.bpm_var, width=12, font=("Arial", 10))
        self.bpm_entry.grid(row=1, column=2, padx=(20, 0), pady=12)
        
        # 显示BPM范围
        ttk.Label(beat_frame, text="(40-240)", font=("Arial", 9), foreground="gray").grid(row=1, column=3, sticky=tk.W, pady=12, padx=(10, 0))
        
        # 音量和持续时间框架
        sound_frame = ttk.LabelFrame(main_frame, text="声音设置", padding="15")
        sound_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        sound_frame.grid_columnconfigure(1, weight=1)
        sound_frame.grid_columnconfigure(3, weight=1)
        
        # 白噪音音量 - 使用更长的滑块
        ttk.Label(sound_frame, text="白噪音音量 (0-1):", font=("Arial", 11)).grid(row=0, column=0, sticky=tk.W, pady=10)
        self.noise_volume_var = tk.DoubleVar(value=0.3)
        noise_volume_scale = ttk.Scale(sound_frame, from_=0.0, to=1.0, variable=self.noise_volume_var, 
                                      orient=tk.HORIZONTAL, length=300)
        noise_volume_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=10, padx=(15, 0))
        self.noise_volume_entry = ttk.Entry(sound_frame, textvariable=self.noise_volume_var, width=12, font=("Arial", 10))
        self.noise_volume_entry.grid(row=0, column=2, padx=(20, 0), pady=10)
        
        # 音符音量
        ttk.Label(sound_frame, text="音符音量 (0-1):", font=("Arial", 11)).grid(row=1, column=0, sticky=tk.W, pady=10)
        self.note_volume_var = tk.DoubleVar(value=0.5)
        note_volume_scale = ttk.Scale(sound_frame, from_=0.0, to=1.0, variable=self.note_volume_var, 
                                     orient=tk.HORIZONTAL, length=300)
        note_volume_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=10, padx=(15, 0))
        self.note_volume_entry = ttk.Entry(sound_frame, textvariable=self.note_volume_var, width=12, font=("Arial", 10))
        self.note_volume_entry.grid(row=1, column=2, padx=(20, 0), pady=10)
        
        # 持续时间
        ttk.Label(sound_frame, text="节拍持续时间 (ms):", font=("Arial", 11)).grid(row=2, column=0, sticky=tk.W, pady=10)
        self.duration_ms_var = tk.IntVar(value=150)
        duration_scale = ttk.Scale(sound_frame, from_=10, to=500, variable=self.duration_ms_var, 
                                  orient=tk.HORIZONTAL, length=300)
        duration_scale.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=10, padx=(15, 0))
        self.duration_entry = ttk.Entry(sound_frame, textvariable=self.duration_ms_var, width=12, font=("Arial", 10))
        self.duration_entry.grid(row=2, column=2, padx=(20, 0), pady=10)
        
        # 显示持续时间范围
        ttk.Label(sound_frame, text="(10-500ms)", font=("Arial", 9), foreground="gray").grid(row=2, column=3, sticky=tk.W, pady=10, padx=(10, 0))
        
        # 音符设置框架
        note_frame = ttk.LabelFrame(main_frame, text="音符和旋律设置", padding="15")
        note_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        note_frame.grid_columnconfigure(1, weight=1)
        note_frame.grid_columnconfigure(3, weight=1)
        
        # 波形选择
        ttk.Label(note_frame, text="波形类型:", font=("Arial", 11)).grid(row=0, column=0, sticky=tk.W, pady=8)
        self.waveform_var = tk.StringVar(value="sine")
        waveform_combo = ttk.Combobox(note_frame, textvariable=self.waveform_var, 
                                     values=["sine", "square", "sawtooth", "triangle"], 
                                     state="readonly", width=12, font=("Arial", 10))
        waveform_combo.grid(row=0, column=1, sticky=tk.W, pady=8, padx=(15, 0))
        
        # 预设旋律选择
        ttk.Label(note_frame, text="预设旋律:", font=("Arial", 11)).grid(row=0, column=2, sticky=tk.W, pady=8, padx=(30, 0))
        self.preset_var = tk.StringVar(value="节奏模式1")
        preset_combo = ttk.Combobox(note_frame, textvariable=self.preset_var, 
                                   values=list(self.melody_presets.keys()), 
                                   state="readonly", width=15, font=("Arial", 10))
        preset_combo.grid(row=0, column=3, sticky=tk.W, pady=8, padx=(15, 0))
        
        # 音符序列编辑框架
        ttk.Label(note_frame, text="音符序列编辑 (用逗号分隔, R表示休止符):", 
                 font=("Arial", 11)).grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(15, 8))
        
        self.note_sequence_var = tk.StringVar(value=", ".join(self.note_sequence))
        self.note_sequence_entry = ttk.Entry(note_frame, textvariable=self.note_sequence_var, 
                                           width=80, font=("Arial", 10))
        self.note_sequence_entry.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=8)
        
        # 应用预设按钮
        apply_preset_btn = ttk.Button(note_frame, text="应用预设", command=self.apply_preset)
        apply_preset_btn.grid(row=2, column=3, sticky=tk.W, padx=(15, 0), pady=8)
        
        # 音符序列显示
        ttk.Label(note_frame, text="当前序列预览:", font=("Arial", 11)).grid(row=3, column=0, sticky=tk.W, pady=10)
        self.sequence_display_var = tk.StringVar(value=" | ".join(self.note_sequence))
        sequence_display = ttk.Label(note_frame, textvariable=self.sequence_display_var, 
                                   font=("Courier", 12, "bold"), foreground="blue")
        sequence_display.grid(row=3, column=1, columnspan=3, sticky=tk.W, pady=10, padx=(15, 0))
        
        # 信息显示框架 - 增加高度
        info_frame = ttk.LabelFrame(main_frame, text="节拍信息", padding="15")
        info_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        info_frame.grid_columnconfigure(0, weight=1)
        
        # 计算并显示节拍信息 - 使用更大的文本框
        self.info_text = tk.Text(info_frame, height=6, width=90, font=("Courier", 11))
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        scrollbar = ttk.Scrollbar(info_frame, orient="vertical", command=self.info_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.info_text.configure(yscrollcommand=scrollbar.set)
        
        # 控制按钮框架 - 使用更大的按钮
        controls_frame = ttk.Frame(main_frame)
        controls_frame.grid(row=5, column=0, columnspan=2, pady=25)
        
        # 播放/停止按钮 - 更大的按钮
        self.play_button = ttk.Button(controls_frame, text="播放节拍", 
                                     command=self.toggle_playback, width=15)
        self.play_button.grid(row=0, column=0, padx=12)
        
        # 保存按钮
        self.save_button = ttk.Button(controls_frame, text="保存为音频文件", 
                                     command=self.save_audio, width=15)
        self.save_button.grid(row=0, column=1, padx=12)
        
        # 更新信息按钮
        self.update_button = ttk.Button(controls_frame, text="更新节拍信息", 
                                       command=self.update_beat_info, width=15)
        self.update_button.grid(row=0, column=2, padx=12)
        
        # 测试音符按钮
        self.test_note_button = ttk.Button(controls_frame, text="测试当前序列", 
                                          command=self.test_sequence, width=15)
        self.test_note_button.grid(row=0, column=3, padx=12)
        
        # 状态标签 - 更大的字体
        self.status_var = tk.StringVar(value="准备就绪 - 设置参数后点击'更新节拍信息'")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                                foreground="blue", font=("Arial", 11))
        status_label.grid(row=6, column=0, columnspan=2, pady=15)
        
        # 进度条 - 更长的进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                           maximum=100, length=600)
        self.progress_bar.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # 初始更新节拍信息
        self.update_beat_info()
        
        # 绑定事件
        time_signature_combo.bind('<<ComboboxSelected>>', lambda e: self.update_beat_info())
        waveform_combo.bind('<<ComboboxSelected>>', lambda e: self.update_beat_info())
        preset_combo.bind('<<ComboboxSelected>>', lambda e: self.apply_preset())
        
        for widget in [bars_spinbox, self.bpm_entry, self.noise_volume_entry, self.note_volume_entry, 
                      self.duration_entry, self.note_sequence_entry]:
            widget.bind('<KeyRelease>', lambda e: self.update_beat_info())
    
    def apply_preset(self):
        """应用预设旋律"""
        preset_name = self.preset_var.get()
        if preset_name in self.melody_presets:
            self.note_sequence = self.melody_presets[preset_name].copy()
            self.note_sequence_var.set(", ".join(self.note_sequence))
            self.sequence_display_var.set(" | ".join(self.note_sequence))
            self.update_beat_info()
            self.status_var.set(f"已应用预设: {preset_name}")
    
    def parse_note_sequence(self):
        """解析音符序列"""
        sequence_text = self.note_sequence_var.get()
        notes = [note.strip().upper() for note in sequence_text.split(",") if note.strip()]
        
        # 验证音符
        valid_notes = []
        for note in notes:
            if note == 'R' or note in self.note_frequencies:
                valid_notes.append(note)
            else:
                self.status_var.set(f"警告: 忽略无效音符 '{note}'")
        
        if valid_notes:
            self.note_sequence = valid_notes
            self.sequence_display_var.set(" | ".join(self.note_sequence))
        else:
            self.status_var.set("错误: 没有有效的音符")
        
        return valid_notes
    
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
    
    def calculate_beat_info(self):
        """计算节拍相关信息"""
        time_signature = self.time_signature_var.get()
        beats_per_bar = int(time_signature.split('/')[0])
        bars = self.bars_var.get()
        bpm = self.bpm_var.get()
        duration_ms = self.duration_ms_var.get()
        
        # 解析音符序列
        note_sequence = self.parse_note_sequence()
        
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
    
    def update_beat_info(self):
        """更新节拍信息显示"""
        try:
            info = self.calculate_beat_info()
            
            note_sequence = info['note_sequence']
            sequence_display = " | ".join(note_sequence[:12])  # 显示更多音符
            if len(note_sequence) > 12:
                sequence_display += " ..."
            
            info_text = f"""
节拍数: {self.time_signature_var.get():<6} 小节数: {info['bars']:<4} 速度: {self.bpm_var.get():<4} BPM
总拍数: {info['total_beats']:<4} 每拍时长: {info['beat_duration']:.3f}秒 总时长: {info['total_duration']:.2f}秒
波形: {self.waveform_var.get():<12} 音符序列长度: {info['sequence_length']:>2} 个音符
白噪音音量: {self.noise_volume_var.get():.2f} 音符音量: {self.note_volume_var.get():.2f} 音长: {info['beat_sound_duration']:.3f}秒
预设: {self.preset_var.get():<12} 当前序列: {sequence_display}
            """.strip()
            
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, info_text)
            self.status_var.set("节拍信息已更新")
            
        except Exception as e:
            self.status_var.set(f"错误: {str(e)}")
    
    def generate_white_noise_beat(self):
        """生成带多音符旋律的白噪音节拍音频数据"""
        info = self.calculate_beat_info()
        
        beats_per_bar = info['beats_per_bar']
        total_beats = info['total_beats']
        beat_duration = info['beat_duration']
        total_duration = info['total_duration']
        beat_sound_duration = info['beat_sound_duration']
        note_sequence = info['note_sequence']
        
        if not note_sequence:
            note_sequence = ["C4"]  # 默认音符
        
        noise_volume = self.noise_volume_var.get()
        note_volume = self.note_volume_var.get()
        waveform = self.waveform_var.get()
        
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
        
        return audio_data
    
    def test_sequence(self):
        """测试当前音符序列"""
        try:
            note_sequence = self.parse_note_sequence()
            if not note_sequence:
                messagebox.showwarning("警告", "没有有效的音符序列")
                return
            
            # 播放序列中的前4个音符
            test_notes = note_sequence[:4]
            test_duration = 0.3  # 每个音符0.3秒
            
            def play_test():
                for i, note in enumerate(test_notes):
                    if note != 'R':
                        frequency = self.note_frequencies.get(note, 440.0)
                        note_wave = self.generate_note(frequency, test_duration, self.note_volume_var.get(), self.waveform_var.get())
                        sd.play(note_wave, self.sample_rate)
                        sd.wait()
                    else:
                        time.sleep(test_duration)
                    self.status_var.set(f"测试中: {i+1}/{len(test_notes)} - {note}")
                
                self.status_var.set("测试完成")
            
            # 在新线程中播放测试
            test_thread = threading.Thread(target=play_test)
            test_thread.daemon = True
            test_thread.start()
            
        except Exception as e:
            messagebox.showerror("错误", f"测试序列时出错: {str(e)}")
    
    def play_audio(self):
        """播放音频"""
        try:
            audio_data = self.generate_white_noise_beat()
            info = self.calculate_beat_info()
            total_duration = info['total_duration']
            
            # 开始播放
            sd.play(audio_data, self.sample_rate)
            
            # 更新进度条和状态
            start_time = time.time()
            beats_per_bar = info['beats_per_bar']
            note_sequence = info['note_sequence']
            
            while self.is_playing and (time.time() - start_time) < total_duration:
                elapsed = time.time() - start_time
                progress = (elapsed / total_duration) * 100
                self.progress_var.set(progress)
                
                # 显示当前节拍和音符
                current_beat = int(elapsed / info['beat_duration'])
                bar = current_beat // beats_per_bar + 1
                beat_in_bar = current_beat % beats_per_bar + 1
                
                # 获取当前音符
                if note_sequence:
                    current_note_index = current_beat % len(note_sequence)
                    current_note = note_sequence[current_note_index]
                    note_display = f" - 音符: {current_note}"
                else:
                    note_display = ""
                
                self.status_var.set(f"播放中... 第{bar}小节 第{beat_in_bar}拍{note_display}")
                
                self.root.update_idletasks()
                time.sleep(0.05)
            
            # 播放完成或停止
            if self.is_playing:
                sd.wait()  # 等待播放完成
                self.is_playing = False
                self.play_button.config(text="播放节拍")
                self.status_var.set("播放完成")
                self.progress_var.set(0)
        except Exception as e:
            messagebox.showerror("错误", f"播放音频时出错: {str(e)}")
            self.is_playing = False
            self.play_button.config(text="播放节拍")
            self.status_var.set("播放出错")
    
    def toggle_playback(self):
        """切换播放/停止状态"""
        if not self.is_playing:
            self.is_playing = True
            self.play_button.config(text="停止节拍")
            self.status_var.set("开始播放...")
            self.play_thread = threading.Thread(target=self.play_audio)
            self.play_thread.daemon = True
            self.play_thread.start()
        else:
            self.is_playing = False
            self.play_button.config(text="播放节拍")
            self.status_var.set("已停止")
            sd.stop()
    
    def save_audio(self):
        """保存音频为文件"""
        try:
            # 生成音频数据
            self.status_var.set("正在生成音频...")
            self.root.update_idletasks()
            
            audio_data = self.generate_white_noise_beat()
            info = self.calculate_beat_info()
            
            # 选择保存位置
            file_path = filedialog.asksaveasfilename(
                defaultextension=".wav",
                filetypes=[("WAV 文件", "*.wav"), ("所有文件", "*.*")],
                title="保存音频文件"
            )
            
            if file_path:
                # 保存为音频文件
                sf.write(file_path, audio_data, self.sample_rate)
                
                # 显示保存信息
                sequence_preview = " | ".join(info['note_sequence'][:8])
                if len(info['note_sequence']) > 8:
                    sequence_preview += " ..."
                
                self.status_var.set(f"音频已保存: {file_path}")
                messagebox.showinfo("成功", 
                    f"音频文件已保存!\n"
                    f"文件: {file_path}\n"
                    f"节拍: {self.time_signature_var.get()}\n"
                    f"速度: {self.bpm_var.get()} BPM\n"
                    f"波形: {self.waveform_var.get()}\n"
                    f"音符序列: {sequence_preview}\n"
                    f"时长: {info['total_duration']:.2f} 秒\n"
                    f"总拍数: {info['total_beats']}")
            else:
                self.status_var.set("保存取消")
        except Exception as e:
            messagebox.showerror("错误", f"保存音频时出错: {str(e)}")
            self.status_var.set("保存出错")

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
    
    # 创建GUI
    root = tk.Tk()
    app = WhiteNoiseBeatGenerator(root)
    root.mainloop()