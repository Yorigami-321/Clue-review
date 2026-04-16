from PyQt5.QtCore import QObject, pyqtSignal
from threads.file_load_thread import FileLoadThread
from threads.batch_screen_thread import BatchScreenThread
from threads.whisper_thread import WhisperLoadThread
from threads.recorder_thread import AudioRecorderThread
from threads.transcribe_thread import AudioTranscribeThread


class ClueService(QObject):
    """线索业务服务 - 封装所有业务相关逻辑"""
    
    # 信号定义
    file_loaded = pyqtSignal(object)  # DataFrame
    file_load_error = pyqtSignal(str)
    screen_progress = pyqtSignal(int, int, str)  # current, total, message
    screen_finished = pyqtSignal(list)  # 新记录列表
    whisper_loaded = pyqtSignal(object)  # 模型对象
    whisper_error = pyqtSignal(str)
    recording_started = pyqtSignal()
    recording_progress = pyqtSignal(str)
    recording_finished = pyqtSignal(bytes)  # 音频数据
    transcribe_finished = pyqtSignal(str, str, bool)  # raw, masked, ok
    progress_updated = pyqtSignal(str)  # 通用进度消息
    
    def __init__(self, db, analyzer, parent=None):
        super().__init__(parent)
        self.db = db
        self.analyzer = analyzer
        self._pending_df = None
        self.whisper_model = None
        self.recorder_thread = None
    
    def load_file(self, file_path: str):
        """加载线索文件"""
        self._thread = FileLoadThread(file_path)
        self._thread.progress.connect(self.progress_updated.emit)
        self._thread.finished.connect(self._on_file_loaded)
        self._thread.error.connect(self._on_file_error)
        self._thread.start()
    
    def _on_file_loaded(self, df):
        """文件加载完成"""
        self._pending_df = df
        self.file_loaded.emit(df)
    
    def _on_file_error(self, err):
        """文件加载错误"""
        self.file_load_error.emit(err)
    
    def start_screen(self, use_llm: bool, api_key: str, api_url: str, model: str):
        """开始批量筛查"""
        if self._pending_df is None:
            return
        
        existing = self.db.get_all_clues()
        existing_hashes = set(existing["text_hash"].dropna().tolist()) if not existing.empty else set()
        
        self._thread = BatchScreenThread(
            self._pending_df, self.analyzer,
            use_llm=use_llm,
            api_key=api_key,
            api_url=api_url,
            model=model,
            existing_hashes=existing_hashes
        )
        self._thread.progress.connect(self.screen_progress.emit)
        self._thread.finished.connect(self._on_screen_finished)
        self._thread.start()
    
    def _on_screen_finished(self, records):
        """筛查完成"""
        self.screen_finished.emit(records)
        self._pending_df = None
    
    def load_whisper(self, model_size: str):
        """加载Whisper模型"""
        self._thread = WhisperLoadThread(model_size)
        self._thread.progress.connect(self.progress_updated.emit)
        self._thread.finished.connect(self._on_whisper_loaded)
        self._thread.error.connect(self._on_whisper_error)
        self._thread.start()
    
    def _on_whisper_loaded(self, model):
        """Whisper模型加载完成"""
        self.whisper_model = model
        self.whisper_loaded.emit(model)
    
    def _on_whisper_error(self, err):
        """Whisper模型加载错误"""
        self.whisper_error.emit(err)
    
    def start_recording(self):
        """开始录音"""
        try:
            import pyaudio  # noqa
        except ImportError:
            self.recording_progress.emit("缺少依赖: pyaudio")
            return
        
        self.recorder_thread = AudioRecorderThread()
        self.recorder_thread.recording_progress.connect(self.recording_progress.emit)
        self.recorder_thread.amplitude_update.connect(self._on_amplitude_update)
        self.recorder_thread.recording_finished.connect(self._on_recording_finished)
        self.recorder_thread.start_recording()
        self.recording_started.emit()
    
    def stop_recording(self):
        """停止录音"""
        if self.recorder_thread:
            self.recorder_thread.stop_recording()
    
    def _on_amplitude_update(self, amplitude: float):
        """音频振幅更新"""
        # 这里可以通过信号传递振幅值，让UI更新音量条
        pass
    
    def _on_recording_finished(self, data: bytes):
        """录音完成"""
        self.recording_finished.emit(data)
    
    def transcribe(self, audio_data: bytes):
        """转写音频"""
        if not self.whisper_model:
            self.transcribe_finished.emit("", "请先加载语音模型", False)
            return
        
        self._thread = AudioTranscribeThread(audio_data, self.whisper_model)
        self._thread.progress.connect(self.progress_updated.emit)
        self._thread.finished.connect(self._on_transcribe_finished)
        self._thread.start()
    
    def _on_transcribe_finished(self, result):
        """转写完成"""
        raw, masked, ok = result
        self.transcribe_finished.emit(raw, masked, ok)
    
    def get_pending_df(self):
        """获取待处理的DataFrame"""
        return self._pending_df
    
    def get_whisper_model(self):
        """获取Whisper模型"""
        return self.whisper_model
