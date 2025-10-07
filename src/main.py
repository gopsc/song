import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import sounddevice as sd
import soundfile as sf
import threading
import time
import math

class WhiteNoiseBeatGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("白噪音节拍生成器 - 带音符功能")
        self.root.geometry("600x700")
        self.root.resizable(False, False)
        
        # 音频参数
        self.sample_rate = 44100
        self.is_playing = False
        self.play_thread = None
        
        # 音符频率字典 (A4 = 440Hz)
        self.note_frequencies = {
            'C': 261.63, 'C#': 277.18, 'D': 293.66, 'D#': 311.13,
            'E': 329.63, 'F': 349.23, 'F#': 369.99, 'G': 392.00,
            'G#': 415.30, 'A': 440.00, 'A#': 466.16, 'B': 493.88
        }
        
        # 创建GUI
        self.create_widgets()
        
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="白噪音节拍生成器 - 带音符功能", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 15))
        
        # 节拍设置框架
        beat_frame = ttk.LabelFrame(main_frame, text="节拍设置", padding="10")
        beat_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 常见节拍数选择
        ttk.Label(beat_frame, text="节拍数:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.time_signature_var = tk.StringVar(value="4/4")
        time_signatures = ["4/4", "3/4", "2/4", "6/8", "5/4", "7/8"]
        time_signature_combo = ttk.Combobox(beat_frame, textvariable=self.time_signature_var, 
                                           values=time_signatures, state="readonly", width=10)
        time_signature_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # 小节数
        ttk.Label(beat_frame, text="小节数:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        self.bars_var = tk.IntVar(value=8)
        bars_spinbox = ttk.Spinbox(beat_frame, from_=1, to=64, textvariable=self.bars_var, width=8)
        bars_spinbox.grid(row=0, column=3, sticky=tk.W, pady=5, padx=(10, 0))
        
        # 速度(BPM)
        ttk.Label(beat_frame, text="速度 (BPM):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.bpm_var = tk.IntVar(value=120)
        bpm_scale = ttk.Scale(beat_frame, from_=40, to=240, variable=self.bpm_var, 
                             orient=tk.HORIZONTAL, length=200)
        bpm_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        self.bpm_entry = ttk.Entry(beat_frame, textvariable=self.bpm_var, width=10)
        self.bpm_entry.grid(row=1, column=2, padx=(10, 0), pady=5)
        
        # 音量和持续时间框架
        sound_frame = ttk.LabelFrame(main_frame, text="声音设置", padding="10")
        sound_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 10))
        
        # 白噪音音量
        ttk.Label(sound_frame, text="白噪音音量 (0-1):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.noise_volume_var = tk.DoubleVar(value=0.5)
        noise_volume_scale = ttk.Scale(sound_frame, from_=0.0, to=1.0, variable=self.noise_volume_var, 
                                      orient=tk.HORIZONTAL, length=200)
        noise_volume_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        self.noise_volume_entry = ttk.Entry(sound_frame, textvariable=self.noise_volume_var, width=10)
        self.noise_volume_entry.grid(row=0, column=2, padx=(10, 0), pady=5)
        
        # 音符音量
        ttk.Label(sound_frame, text="音符音量 (0-1):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.note_volume_var = tk.DoubleVar(value=0.3)
        note_volume_scale = ttk.Scale(sound_frame, from_=0.0, to=1.0, variable=self.note_volume_var, 
                                     orient=tk.HORIZONTAL, length=200)
        note_volume_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        self.note_volume_entry = ttk.Entry(sound_frame, textvariable=self.note_volume_var, width=10)
        self.note_volume_entry.grid(row=1, column=2, padx=(10, 0), pady=5)
        
        # 持续时间
        ttk.Label(sound_frame, text="节拍持续时间 (ms):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.duration_ms_var = tk.IntVar(value=100)
        duration_scale = ttk.Scale(sound_frame, from_=10, to=500, variable=self.duration_ms_var, 
                                  orient=tk.HORIZONTAL, length=200)
        duration_scale.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        self.duration_entry = ttk.Entry(sound_frame, textvariable=self.duration_ms_var, width=10)
        self.duration_entry.grid(row=2, column=2, padx=(10, 0), pady=5)
        
        # 音符设置框架
        note_frame = ttk.LabelFrame(main_frame, text="音符设置", padding="10")
        note_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 10))
        
        # 音符选择
        ttk.Label(note_frame, text="音符:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.note_var = tk.StringVar(value="C")
        note_combo = ttk.Combobox(note_frame, textvariable=self.note_var, 
                                 values=list(self.note_frequencies.keys()), state="readonly", width=10)
        note_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # 八度选择
        ttk.Label(note_frame, text="八度:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        self.octave_var = tk.IntVar(value=4)
        octave_spinbox = ttk.Spinbox(note_frame, from_=1, to=7, textvariable=self.octave_var, width=8)
        octave_spinbox.grid(row=0, column=3, sticky=tk.W, pady=5, padx=(10, 0))
        
        # 音符波形选择
        ttk.Label(note_frame, text="波形:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.waveform_var = tk.StringVar(value="sine")
        waveform_combo = ttk.Combobox(note_frame, textvariable=self.waveform_var, 
                                     values=["sine", "square", "sawtooth", "triangle"], state="readonly", width=10)
        waveform_combo.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # 音符应用模式
        ttk.Label(note_frame, text="应用模式:").grid(row=1, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        self.note_mode_var = tk.StringVar(value="first_beat")
        note_mode_combo = ttk.Combobox(note_frame, textvariable=self.note_mode_var, 
                                      values=["first_beat", "all_beats", "alternate", "custom"], state="readonly", width=10)
        note_mode_combo.grid(row=1, column=3, sticky=tk.W, pady=5, padx=(10, 0))
        
        # 信息显示框架
        info_frame = ttk.LabelFrame(main_frame, text="节拍信息", padding="10")
        info_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 计算并显示节拍信息
        self.info_text = tk.Text(info_frame, height=4, width=60, font=("Courier", 9))
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        scrollbar = ttk.Scrollbar(info_frame, orient="vertical", command=self.info_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.info_text.configure(yscrollcommand=scrollbar.set)
        
        # 控制按钮框架
        controls_frame = ttk.Frame(main_frame)
        controls_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        # 播放/停止按钮
        self.play_button = ttk.Button(controls_frame, text="播放节拍", command=self.toggle_playback)
        self.play_button.grid(row=0, column=0, padx=5)
        
        # 保存按钮
        self.save_button = ttk.Button(controls_frame, text="保存为音频文件", command=self.save_audio)
        self.save_button.grid(row=0, column=1, padx=5)
        
        # 更新信息按钮
        self.update_button = ttk.Button(controls_frame, text="更新节拍信息", command=self.update_beat_info)
        self.update_button.grid(row=0, column=2, padx=5)
        
        # 测试音符按钮
        self.test_note_button = ttk.Button(controls_frame, text="测试当前音符", command=self.test_note)
        self.test_note_button.grid(row=0, column=3, padx=5)
        
        # 状态标签
        self.status_var = tk.StringVar(value="准备就绪 - 设置参数后点击'更新节拍信息'")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="blue")
        status_label.grid(row=6, column=0, columnspan=2, pady=10)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 配置列权重
        main_frame.columnconfigure(1, weight=1)
        beat_frame.columnconfigure(1, weight=1)
        sound_frame.columnconfigure(1, weight=1)
        note_frame.columnconfigure(1, weight=1)
        info_frame.columnconfigure(0, weight=1)
        
        # 初始更新节拍信息
        self.update_beat_info()
        
        # 绑定事件
        time_signature_combo.bind('<<ComboboxSelected>>', lambda e: self.update_beat_info())
        note_combo.bind('<<ComboboxSelected>>', lambda e: self.update_beat_info())
        waveform_combo.bind('<<ComboboxSelected>>', lambda e: self.update_beat_info())
        note_mode_combo.bind('<<ComboboxSelected>>', lambda e: self.update_beat_info())
        
        for widget in [bars_spinbox, self.bpm_entry, self.noise_volume_entry, self.note_volume_entry, 
                      self.duration_entry, octave_spinbox]:
            widget.bind('<KeyRelease>', lambda e: self.update_beat_info())
        
    def generate_sine_wave(self, frequency, duration, volume=0.5):
        """生成正弦波"""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        wave = np.sin(2 * np.pi * frequency * t)
        return wave * volume
    
    def generate_square_wave(self, frequency, duration, volume=0.5):
        """生成方波"""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        wave = np.sign(np.sin(2 * np.pi * frequency * t))
        return wave * volume * 0.7  # 降低音量避免削波
    
    def generate_sawtooth_wave(self, frequency, duration, volume=0.5):
        """生成锯齿波"""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        wave = 2 * (t * frequency - np.floor(0.5 + t * frequency))
        return wave * volume * 0.5  # 降低音量避免削波
    
    def generate_triangle_wave(self, frequency, duration, volume=0.5):
        """生成三角波"""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        wave = 2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1
        return wave * volume * 0.8  # 降低音量避免削波
    
    def generate_note(self, frequency, duration, volume=0.5, waveform="sine"):
        """根据波形类型生成音符"""
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
        
        # 计算音符频率
        base_frequency = self.note_frequencies[self.note_var.get()]
        octave = self.octave_var.get()
        note_frequency = base_frequency * (2 ** (octave - 4))
        
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
            'note_frequency': note_frequency
        }
    
    def update_beat_info(self):
        """更新节拍信息显示"""
        try:
            info = self.calculate_beat_info()
            
            note_name = self.note_var.get()
            octave = self.octave_var.get()
            waveform = self.waveform_var.get()
            note_mode = self.note_mode_var.get()
            
            info_text = f"""
节拍数: {self.time_signature_var.get():<5} 小节数: {info['bars']:<3} 速度: {self.bpm_var.get()} BPM
总拍数: {info['total_beats']:<3} 每拍时长: {info['beat_duration']:.3f}秒 总时长: {info['total_duration']:.2f}秒
音符: {note_name}{octave} ({info['note_frequency']:.2f}Hz) 波形: {waveform:<10} 模式: {note_mode}
白噪音音量: {self.noise_volume_var.get():.2f} 音符音量: {self.note_volume_var.get():.2f} 音长: {info['beat_sound_duration']:.3f}秒
            """.strip()
            
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, info_text)
            self.status_var.set("节拍信息已更新")
            
        except Exception as e:
            self.status_var.set(f"错误: {str(e)}")
    
    def should_play_note(self, beat, total_beats, beats_per_bar, mode):
        """根据模式判断是否在当前拍播放音符"""
        if mode == "first_beat":
            return beat % beats_per_bar == 0  # 每小节第一拍
        elif mode == "all_beats":
            return True  # 所有拍
        elif mode == "alternate":
            return beat % 2 == 0  # 每隔一拍
        elif mode == "custom":
            return beat % 4 == 0  # 自定义模式，这里设为每4拍
        else:
            return beat % beats_per_bar == 0
    
    def generate_white_noise_beat(self):
        """生成带音符的白噪音节拍音频数据"""
        info = self.calculate_beat_info()
        
        beats_per_bar = info['beats_per_bar']
        total_beats = info['total_beats']
        beat_duration = info['beat_duration']
        total_duration = info['total_duration']
        beat_sound_duration = info['beat_sound_duration']
        note_frequency = info['note_frequency']
        
        noise_volume = self.noise_volume_var.get()
        note_volume = self.note_volume_var.get()
        waveform = self.waveform_var.get()
        note_mode = self.note_mode_var.get()
        
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
            
            # 生成白噪音
            end_sample = min(start_sample + beat_sound_samples, total_samples)
            if start_sample < total_samples:
                noise_length = end_sample - start_sample
                if noise_length > 0:
                    noise = np.random.uniform(-noise_volume, noise_volume, noise_length)
                    audio_data[start_sample:end_sample] += noise
            
            # 生成音符（根据模式判断是否播放）
            if self.should_play_note(beat, total_beats, beats_per_bar, note_mode):
                note_wave = self.generate_note(note_frequency, beat_sound_duration, note_volume, waveform)
                note_samples = len(note_wave)
                end_note_sample = min(start_sample + note_samples, total_samples)
                if start_sample < total_samples:
                    note_length = end_note_sample - start_sample
                    if note_length > 0:
                        audio_data[start_sample:end_note_sample] += note_wave[:note_length]
        
        # 归一化音频数据，避免削波
        max_amplitude = np.max(np.abs(audio_data))
        if max_amplitude > 1.0:
            audio_data = audio_data / max_amplitude * 0.9  # 保留一些余量
        
        return audio_data
    
    def test_note(self):
        """测试当前音符设置"""
        try:
            info = self.calculate_beat_info()
            note_frequency = info['note_frequency']
            note_volume = self.note_volume_var.get()
            waveform = self.waveform_var.get()
            
            # 生成0.5秒的音符
            test_duration = 0.5
            note_wave = self.generate_note(note_frequency, test_duration, note_volume, waveform)
            
            # 播放测试音符
            sd.play(note_wave, self.sample_rate)
            self.status_var.set(f"正在测试音符: {self.note_var.get()}{self.octave_var.get()} ({note_frequency:.1f}Hz)")
            
            # 在0.5秒后更新状态
            self.root.after(500, lambda: self.status_var.set("测试完成"))
            
        except Exception as e:
            messagebox.showerror("错误", f"测试音符时出错: {str(e)}")
    
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
            current_beat = 0
            
            while self.is_playing and (time.time() - start_time) < total_duration:
                elapsed = time.time() - start_time
                progress = (elapsed / total_duration) * 100
                self.progress_var.set(progress)
                
                # 显示当前节拍
                current_beat = int(elapsed / info['beat_duration'])
                bar = current_beat // beats_per_bar + 1
                beat_in_bar = current_beat % beats_per_bar + 1
                
                # 检查是否播放音符
                play_note = self.should_play_note(current_beat, info['total_beats'], beats_per_bar, self.note_mode_var.get())
                note_indicator = " ♪" if play_note else ""
                
                self.status_var.set(f"播放中... 第{bar}小节 第{beat_in_bar}拍{note_indicator}")
                
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
                self.status_var.set(f"音频已保存: {file_path}")
                messagebox.showinfo("成功", 
                    f"音频文件已保存!\n"
                    f"文件: {file_path}\n"
                    f"节拍: {self.time_signature_var.get()}\n"
                    f"速度: {self.bpm_var.get()} BPM\n"
                    f"音符: {self.note_var.get()}{self.octave_var.get()}\n"
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