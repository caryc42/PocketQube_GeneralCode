import numpy as np
from scipy.signal import butter, sosfiltfilt
from scipy.io import wavfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from load_iq import load_rf64_iq

# ============================================================
# 1. Load raw I/Q recording
# ============================================================
iq, fs = load_rf64_iq(r"C:\Users\Oscar\Downloads\1_12-38-05_434400000Hz.wav")
print(f"Loaded {len(iq)} samples @ {fs} Hz ({len(iq)/fs:.2f} s)")

# ============================================================
# 2. Shift signal of interest down to baseband (0 Hz)
#    (signal was found at -256014 Hz offset from tuned center freq)
# ============================================================
f_offset = -256_014
t = np.arange(len(iq)) / fs
iq_baseband = iq * np.exp(-1j * 2 * np.pi * f_offset * t)

# ============================================================
# 3. Channel filter - isolate just the signal bandwidth,
#    reject the rest of the noisy capture
# ============================================================
channel_bw = 20_000  # Hz
sos_channel = butter(4, channel_bw / (fs / 2), btype='low', output='sos')
iq_filtered = sosfiltfilt(sos_channel, iq_baseband)

# ============================================================
# 4. Envelope detection = AM demodulation
# ============================================================
demodulated = np.abs(iq_filtered)

# Smooth slightly to remove residual high-frequency noise
smooth_cutoff = 12_000  # Hz, generous headroom above the ~2kHz tone
sos_smooth = butter(4, smooth_cutoff / (fs / 2), btype='low', output='sos')
demodulated_smooth = sosfiltfilt(sos_smooth, demodulated)

# ============================================================
# 5. Save as a playable, listenable .wav (downsampled to a normal audio rate)
# ============================================================
audio_fs = 48_000
decim_factor = int(fs / audio_fs)  # 2,400,000 / 48,000 = 50
audio = demodulated_smooth[::decim_factor]

# normalize to int16 audio range
audio_norm = audio - audio.mean()
audio_norm = audio_norm / np.max(np.abs(audio_norm))
audio_int16 = (audio_norm * 32767 * 0.9).astype(np.int16)

wavfile.write('/mnt/user-data/outputs/demodulated_audio.wav', audio_fs, audio_int16)
print(f"Saved demodulated_audio.wav at {audio_fs} Hz, {len(audio_int16)/audio_fs:.2f} s")

# ============================================================
# 6. Quick plot for visual confirmation
# ============================================================
plt.figure(figsize=(14, 4))
t_plot = np.arange(len(demodulated_smooth)) / fs
decim_plot = 500
plt.plot(t_plot[::decim_plot], demodulated_smooth[::decim_plot])
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')
plt.title('Demodulated signal (full recording)')
plt.tight_layout()
plt.savefig('/mnt/user-data/outputs/demodulated_signal.png', dpi=110)
plt.close()
print("Saved demodulated_signal.png")