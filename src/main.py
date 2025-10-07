import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import sounddevice as sd
import soundfile as sf
import threading
import time

class WhiteNoiseBeatGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("白噪音节拍生成器")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # 音频参数
        self.sample_rate = 44100
        self.is_playing = False
        self.play_thread = None
        
        # 创建GUI
        self.create_widgets()
        
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="白噪音节拍生成器", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 参数设置框架
        params_frame = ttk.LabelFrame(main_frame, text="节拍参数", padding="10")
        params_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 间隔参数
        ttk.Label(params_frame, text="间隔 (秒):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.interval_var = tk.DoubleVar(value=1.0)
        interval_scale = ttk.Scale(params_frame, from_=0.1, to=5.0, variable=self.interval_var, 
                                  orient=tk.HORIZONTAL, length=200)
        interval_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        self.interval_entry = ttk.Entry(params_frame, textvariable=self.interval_var, width=10)
        self.interval_entry.grid(row=0, column=2, padx=(10, 0), pady=5)
        
        # 强度参数
        ttk.Label(params_frame, text="强度 (0-1):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.intensity_var = tk.DoubleVar(value=0.5)
        intensity_scale = ttk.Scale(params_frame, from_=0.0, to=1.0, variable=self.intensity_var, 
                                   orient=tk.HORIZONTAL, length=200)
        intensity_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        self.intensity_entry = ttk.Entry(params_frame, textvariable=self.intensity_var, width=10)
        self.intensity_entry.grid(row=1, column=2, padx=(10, 0), pady=5)
        
        # 持续时间参数
        ttk.Label(params_frame, text="持续时间 (秒):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.duration_var = tk.DoubleVar(value=0.1)
        duration_scale = ttk.Scale(params_frame, from_=0.01, to=1.0, variable=self.duration_var, 
                                  orient=tk.HORIZONTAL, length=200)
        duration_scale.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        self.duration_entry = ttk.Entry(params_frame, textvariable=self.duration_var, width=10)
        self.duration_entry.grid(row=2, column=2, padx=(10, 0), pady=5)
        
        # 偏移量参数
        ttk.Label(params_frame, text="偏移量 (秒):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.offset_var = tk.DoubleVar(value=0.0)
        offset_scale = ttk.Scale(params_frame, from_=0.0, to=2.0, variable=self.offset_var, 
                                orient=tk.HORIZONTAL, length=200)
        offset_scale.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        self.offset_entry = ttk.Entry(params_frame, textvariable=self.offset_var, width=10)
        self.offset_entry.grid(row=3, column=2, padx=(10, 0), pady=5)
        
        # 总时长参数
        ttk.Label(params_frame, text="总时长 (秒):").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.total_duration_var = tk.DoubleVar(value=10.0)
        total_duration_scale = ttk.Scale(params_frame, from_=1.0, to=60.0, variable=self.total_duration_var, 
                                        orient=tk.HORIZONTAL, length=200)
        total_duration_scale.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        self.total_duration_entry = ttk.Entry(params_frame, textvariable=self.total_duration_var, width=10)
        self.total_duration_entry.grid(row=4, column=2, padx=(10, 0), pady=5)
        
        # 控制按钮框架
        controls_frame = ttk.Frame(main_frame)
        controls_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        # 播放/停止按钮
        self.play_button = ttk.Button(controls_frame, text="播放", command=self.toggle_playback)
        self.play_button.grid(row=0, column=0, padx=5)
        
        # 保存按钮
        self.save_button = ttk.Button(controls_frame, text="保存为音频文件", command=self.save_audio)
        self.save_button.grid(row=0, column=1, padx=5)
        
        # 状态标签
        self.status_var = tk.StringVar(value="准备就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="blue")
        status_label.grid(row=3, column=0, columnspan=2, pady=10)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 配置列权重
        main_frame.columnconfigure(1, weight=1)
        params_frame.columnconfigure(1, weight=1)
        
    def generate_white_noise_beat(self):
        """生成白噪音节拍音频数据"""
        interval = self.interval_var.get()
        intensity = self.intensity_var.get()
        duration = self.duration_var.get()
        offset = self.offset_var.get()
        total_duration = self.total_duration_var.get()
        
        # 计算总样本数
        total_samples = int(total_duration * self.sample_rate)
        audio_data = np.zeros(total_samples)
        
        # 计算节拍位置
        beat_start = int(offset * self.sample_rate)
        beat_samples = int(duration * self.sample_rate)
        interval_samples = int(interval * self.sample_rate)
        
        # 生成节拍
        current_pos = beat_start
        while current_pos < total_samples:
            end_pos = min(current_pos + beat_samples, total_samples)
            # 生成白噪音
            noise = np.random.uniform(-intensity, intensity, end_pos - current_pos)
            audio_data[current_pos:end_pos] = noise
            current_pos += interval_samples
        
        return audio_data
    
    def play_audio(self):
        """播放音频"""
        try:
            audio_data = self.generate_white_noise_beat()
            total_duration = self.total_duration_var.get()
            
            # 开始播放
            sd.play(audio_data, self.sample_rate)
            
            # 更新进度条
            start_time = time.time()
            while self.is_playing and (time.time() - start_time) < total_duration:
                elapsed = time.time() - start_time
                progress = (elapsed / total_duration) * 100
                self.progress_var.set(progress)
                self.root.update_idletasks()
                time.sleep(0.1)
            
            # 播放完成或停止
            if self.is_playing:
                sd.wait()  # 等待播放完成
                self.is_playing = False
                self.play_button.config(text="播放")
                self.status_var.set("播放完成")
                self.progress_var.set(0)
        except Exception as e:
            messagebox.showerror("错误", f"播放音频时出错: {str(e)}")
            self.is_playing = False
            self.play_button.config(text="播放")
            self.status_var.set("播放出错")
    
    def toggle_playback(self):
        """切换播放/停止状态"""
        if not self.is_playing:
            self.is_playing = True
            self.play_button.config(text="停止")
            self.status_var.set("正在播放...")
            self.play_thread = threading.Thread(target=self.play_audio)
            self.play_thread.daemon = True
            self.play_thread.start()
        else:
            self.is_playing = False
            self.play_button.config(text="播放")
            self.status_var.set("已停止")
            sd.stop()
    
    def save_audio(self):
        """保存音频为文件"""
        try:
            # 生成音频数据
            self.status_var.set("正在生成音频...")
            self.root.update_idletasks()
            
            audio_data = self.generate_white_noise_beat()
            
            # 选择保存位置
            file_path = filedialog.asksaveasfilename(
                defaultextension=".wav",
                filetypes=[("WAV 文件", "*.wav"), ("所有文件", "*.*")],
                title="保存音频文件"
            )
            
            if file_path:
                # 保存为WAV文件
                sf.write(file_path, audio_data, self.sample_rate)
                self.status_var.set(f"音频已保存: {file_path}")
                messagebox.showinfo("成功", f"音频文件已保存到:\n{file_path}")
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