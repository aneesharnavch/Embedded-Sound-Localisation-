import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import ifft
from scipy.signal import lfilter

# Generate a random array of amplitude values (input signal)
input_signal = np.random.randn(1000)

# Define the number of filter taps
N = 51  # Number of taps (filter length)

# Define the desired frequency response
# For a simple low-pass filter, define the frequency response as 1 in the passband and 0 in the stopband
freq_response = np.zeros(N, dtype=complex)
passband_end = int(0.2 * (N // 2))  # 0.2 * Nyquist frequency
freq_response[:passband_end] = 1
freq_response[-passband_end:] = 1  # Symmetric for real coefficients

# Compute the FIR filter coefficients using inverse DFT
h = np.real(ifft(freq_response))

# Apply the FIR filter to the input signal using convolution
filtered_signal = lfilter(h, 1.0, input_signal)

# Plot the original signal
plt.figure(figsize=(15, 10))

plt.subplot(3, 1, 1)
plt.plot(input_signal, label='Original Signal', color='blue')
plt.title('Original Signal')
plt.legend()

# Plot the filtered signal
plt.subplot(3, 1, 2)
plt.plot(filtered_signal, label='Filtered Signal', color='red')
plt.title('Filtered Signal (Frequency Sampling Method)')
plt.legend()

# Plot both original and filtered signals overlapping
plt.subplot(3, 1, 3)
plt.plot(input_signal, label='Original Signal', color='blue', alpha=0.5)
plt.plot(filtered_signal, label='Filtered Signal', color='red', alpha=0.5)
plt.title('Original vs. Filtered Signal (Frequency Sampling Method)')
plt.legend()

plt.tight_layout()
plt.show()
