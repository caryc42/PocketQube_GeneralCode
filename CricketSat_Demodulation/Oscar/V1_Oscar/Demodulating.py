import numpy as np
import matplotlib.pyplot as plt
import scipy

# fs - sampling frequency/ sample rate
fs, signal = scipy.io.wavfile.read(r"C:\Users\Oscar\Downloads\1_12-38-05_434400000Hz.wav")
fc = 433.92e6
bit_rate = 8e3
bit_dur = 1/bit_rate # 1/(8kb/s)
samples_per_bit = int(fs / bit_rate)
print("Samples per bit:", samples_per_bit)
total_samples = signal.shape[0]
total_bits = int(total_samples / samples_per_bit)
print("Total amount of bits:", total_bits)
Ts = total_samples / fs
print("duration:", Ts)
t = np.arange(total_samples) / fs

# demodulation attempt
# envelope detector method
# envelope is the trail of the varying heights between each peak. Envelope is tracing the outer boundary of the signal. This trail tells the actual data transmitted
# 1. rectification
rectified_signal = np.abs(signal) # all positive signals
# 2. smooth out
# determine cut off frequency
# rule of thumb is: Ideal cutoff frequency is 2-3 times the bit rate
# scrapes away the quick carrier wave and leave the envelope behind
f_cutoff = 5000
# 2 * bit_rate
# nyquist frequency - nyquist frequency is half the sampling frequency\
# tellse the *absolute* maximum frequency the system can create
f_nyquist = fs/2
# normalized cutoff frequency
f_norm = f_cutoff / f_nyquist

# Butterworth Filter - A type of low pass filter. Doesn't produce as much ripples on high and low ends. Steady
# butter function parameters
# 1 - (N): filter order or how sharp the filter will reduce the gain of high frequencies
#   Most tasks are fine with a filter order between 4 and 6. 
#   If the signal is a bit fuzzy or jagged, increase the order. If the signal is completely distorted and has massive spikes, decrease the order.
# 2 - (Wn): For digital filters, if fs is not specified, Wn units are normalized from 0 to 1, 
#   where 1 is the Nyquist frequency (Wn is thus in half cycles / sample and defined as 2*critical frequencies / fs). 
#   If fs is specified, Wn is in the same units as fs.
#   we will use f_norm for this parameter
# 3 - (btype): type of filter. {‘lowpass’, ‘highpass’, ‘bandpass’, ‘bandstop’} default is lowpass
# 4 - (analog): True will return an analog filter. False returns a digital filter
# 5 - (output): determines if the output comes out in pole zero ("ba") or second order sections ("sos"). pole zero is by default.
#   What is pole zero? values used to decribe
# 6 - (fs): digital system's sampling frequency
sos = scipy.signal.butter(4, f_cutoff, btype = "lowpass", analog = False, output = "sos", fs = fs)
# sosfiltfilt function
# 1 - (sos): array of second order filter coefficients
# 3 - (x): the array of data to be filter
envelope = scipy.signal.sosfiltfilt(sos, rectified_signal, axis = 0)

# Comparator Section
channel_0_raw = signal[:, 0]
channel_0_envelope = envelope[:, 0]
threshold = (np.max(channel_0_envelope) + np.min(channel_0_envelope)) / 2
demodulated_signal = (channel_0_envelope > threshold).astype(int)
demodulated_bits = np.zeros(total_bits, dtype = int)

for i in range(total_bits):
    center_sample = i * samples_per_bit + (samples_per_bit // 2)
    demodulated_bits[i] = 1 if channel_0_envelope[center_sample] > threshold else 0
print(demodulated_bits)


bit_string_spaces = " ".join(map(str, demodulated_bits))
with open("demodulated_bits.txt", "w") as f:
    f.write(bit_string_spaces)

# pulling spectrogram of demodulated signal
# Try 1


# print("Sampling Rate:", fs)
# fft_size = 1024
# num_rows = demodulated_signal.size // fft_size # // is an integer division which rounds down
# spectrogram = np.zeros((num_rows, fft_size))

# for i in range(num_rows):
#     spectrogram[i,:] = 10*np.log10(np.abs(np.fft.fftshift(np.fft.fft(demodulated_signal[i*fft_size:(i+1)*fft_size])))**2)

# # Time starts at the top and goes down, eg sample x[0] will be part of the top row displayed
# plt.imshow(spectrogram, aspect='auto', extent = (fs/-2/1e6, fs/2/1e6, len(demodulated_signal)/fs, 0))
# plt.xlabel("Frequency [MHz]")
# plt.ylabel("Time [s]")
# plt.show()

# Try 2


plt.specgram(demodulated_signal, Fs=fs, cmap="plasma")
plt.show

# plt.figure(1)
# plt.subplot(2, 1, 1)
# plt.plot(t, channel_0_envelope)
# plt.subplot(2, 1, 2)
# plt.plot(t, demodulated_signal)
# plt.show()

# spectrogram
# plt.figure(2)
# plt.subplot(2, 1, 1)
# plt.plot(t, fft_spectrum)
# plt.show()