#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""音频录音线程（带实时音量）"""

import os
import time
import tempfile

import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal


class AudioRecorderThread(QThread):
    recording_finished = pyqtSignal(bytes)
    recording_progress = pyqtSignal(str)
    amplitude_update = pyqtSignal(float)

    CHUNK = 1024
    CHANNELS = 1
    RATE = 16000

    def __init__(self):
        super().__init__()
        self.is_recording = False

    def run(self):
        try:
            import pyaudio
            import wave

            audio = pyaudio.PyAudio()
            fmt = pyaudio.paInt16
            frames = []

            stream = audio.open(
                format=fmt, channels=self.CHANNELS,
                rate=self.RATE, input=True,
                frames_per_buffer=self.CHUNK,
            )
            self.recording_progress.emit("🔴 正在录音...")

            while self.is_recording:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                frames.append(data)
                samples = np.frombuffer(data, dtype=np.int16)
                amp = float(np.abs(samples).mean() / 32768.0)
                self.amplitude_update.emit(amp)

            stream.stop_stream()
            stream.close()

            tmp = os.path.join(tempfile.gettempdir(), f"rec_{int(time.time())}.wav")
            wf = wave.open(tmp, "wb")
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(audio.get_sample_size(fmt))
            wf.setframerate(self.RATE)
            wf.writeframes(b"".join(frames))
            wf.close()

            with open(tmp, "rb") as f:
                audio_bytes = f.read()
            try:
                os.unlink(tmp)
            except OSError:
                pass

            audio.terminate()
            self.recording_finished.emit(audio_bytes)

        except ImportError:
            self.recording_progress.emit("❌ 缺少 pyaudio: pip install pyaudio")
        except Exception as e:
            self.recording_progress.emit(f"❌ 录音失败: {e}")

    def start_recording(self):
        self.is_recording = True
        self.start()

    def stop_recording(self):
        self.is_recording = False
