import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

file_path = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\150cm\triangle\triangle_wave_20k.csv'
data = pd.read_csv(file_path)  # Replace with your file path

# Print column names to check the structure of the data
print("Columns in the CSV file:", data.columns)

# Try to access the 'B' column or use the correct column index (assuming it's the second column)
try:
    signal = data['B'][1:].values  # Skip the label in B1
except KeyError:
    # If the 'B' column doesn't exist, access the second column by index (index 1)
    signal = data.iloc[1:, 1].values  # Skips the header (first row)

# Calculate the number of readings (size of the signal)
num_readings = len(signal)

# Time vector (in terms of readings, no arbitrary units)
readings = np.arange(1, num_readings + 1)

# Plot the raw microphone data
plt.figure(figsize=(14, 8))  # Increased figure size for better visibility
plt.plot(readings, signal, label='Recorded Microphone Signal', color='b', alpha=0.7)
plt.title('Raw Microphone Signal (Readings)', fontsize=16)
plt.xlabel('Reading Number', fontsize=12)
plt.ylabel('Signal Amplitude', fontsize=12)
plt.legend(fontsize=12)
plt.tight_layout()
plt.grid(True)  # Add grid for better visibility of data
plt.show()
