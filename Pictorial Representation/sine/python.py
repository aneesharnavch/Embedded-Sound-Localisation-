import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def load_microphone_data(file_path):
    """
    Loads microphone data from a CSV file, assuming column B contains mic values.
    Skips the first row, which contains the label.
    """
    data = pd.read_csv(file_path)
    try:
        signal = data['B'][1:].astype(float).values  # Skip the label in B1
    except KeyError:
        signal = data.iloc[1:, 1].astype(float).values  # If 'B' column is not labeled
    return signal

def analyze_stability(frequency_distance_files, wave_type):
    """
    Computes stability metrics and generates a heatmap of microphone accuracy
    for a specific wave type across multiple frequencies and distances.

    Parameters:
    - frequency_distance_files: A dictionary where keys are (frequency, distance)
      tuples, and values are file paths to the corresponding CSV files.
    - wave_type: The type of wave to analyze (e.g., 'sine', 'square', etc.).
    """
    results = []

    for (frequency, distance), file_path in frequency_distance_files.items():
        # Load microphone data
        signal = load_microphone_data(file_path)

        # Compute variance as stability metric
        variance = np.var(signal)
        results.append((distance, frequency, variance))

    # Convert results to a DataFrame
    results_df = pd.DataFrame(results, columns=["Distance (cm)", "Frequency (kHz)", "Variance"])

    # Create a pivot table for the heatmap
    pivot_table = results_df.pivot(index="Distance (cm)", columns="Frequency (kHz)", values="Variance")

    # Plot the heatmap
    plt.figure(figsize=(10, 8))
    plt.title(f"{wave_type.capitalize()} Wave Stability (Variance) by Frequency and Distance", fontsize=14)
    heatmap = plt.imshow(pivot_table, cmap="coolwarm", aspect="auto", origin="lower")
    plt.colorbar(heatmap, label="Variance (Stability)")
    plt.xticks(ticks=np.arange(len(pivot_table.columns)), labels=pivot_table.columns, rotation=45)
    plt.yticks(ticks=np.arange(len(pivot_table.index)), labels=pivot_table.index)
    plt.xlabel("Frequency (kHz)", fontsize=12)
    plt.ylabel("Distance (cm)", fontsize=12)
    plt.tight_layout()
    plt.show()

file_1k_15cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\15 cm\sine\sine_wave_1k.csv'
file_5k_15cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\15 cm\sine\sine_wave_5k.csv'
file_10k_15cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\15 cm\sine\sine_wave_10k.csv'
file_15k_15cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\15 cm\sine\sine_wave_15k.csv'
file_20k_15cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\15 cm\sine\sine_wave_20k.csv'

file_1k_50cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\50 cm\sine\sine_wave_1k.csv'
file_5k_50cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\50 cm\sine\sine_wave_5k.csv'
file_10k_50cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\50 cm\sine\sine_wave_10k.csv'
file_15k_50cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\50 cm\sine\sine_wave_15k.csv'
file_20k_50cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\50 cm\sine\sine_wave_20k.csv'

file_1k_100cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\100cm\sine\sine_wave_1k.csv'
file_5k_100cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\100cm\sine\sine_wave_5k.csv'
file_10k_100cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\100cm\sine\sine_wave_10k.csv'
file_15k_100cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\100cm\sine\sine_wave_15k.csv'
file_20k_100cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\100cm\sine\sine_wave_20k.csv'

file_1k_150cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\150cm\sine\sine_wave_1k.csv'
file_5k_150cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\150cm\sine\sine_wave_5k.csv'
file_10k_150cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\150cm\sine\sine_wave_10k.csv'
file_15k_150cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\150cm\sine\sine_wave_15k.csv'
file_20k_150cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\150cm\sine\sine_wave_20k.csv'

file_1k_200cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\200 cm\sine\sine_wave_1k.csv'
file_5k_200cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\200 cm\sine\sine_wave_5k.csv'
file_10k_200cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\200 cm\sine\sine_wave_10k.csv'
file_15k_200cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\200 cm\sine\sine_wave_15k.csv'
file_20k_200cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\200 cm\sine\sine_wave_20k.csv'

file_1k_250cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\250 cm\sine\sine_wave_1k.csv'
file_5k_250cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\250 cm\sine\sine_wave_5k.csv'
file_10k_250cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\250 cm\sine\sine_wave_10k.csv'
file_15k_250cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\250 cm\sine\sine_wave_15k.csv'
file_20k_250cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\250 cm\sine\sine_wave_20k.csv'

file_1k_300cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\300 cm\sine\sine_wave_1k.csv'
file_5k_300cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\300 cm\sine\sine_wave_5k.csv'
file_10k_300cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\300 cm\sine\sine_wave_10k.csv'
file_15k_300cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\300 cm\sine\sine_wave_15k.csv'
file_20k_300cm = r'c:\Users\anees\Desktop\microphone raw data\Wave simulation\distance based\300 cm\sine\sine_wave_20k.csv'

# Dictionary mapping (frequency, distance) to file paths
frequency_distance_files = {
    (1, 15): file_1k_15cm, (5, 15): file_5k_15cm, (10, 15): file_10k_15cm, (15, 15): file_15k_15cm, (20, 15): file_20k_15cm,
    (1, 50): file_1k_50cm, (5, 50): file_5k_50cm, (10, 50): file_10k_50cm, (15, 50): file_15k_50cm, (20, 50): file_20k_50cm,
    (1, 100): file_1k_100cm, (5, 100): file_5k_100cm, (10, 100): file_10k_100cm, (15, 100): file_15k_100cm, (20, 100): file_20k_100cm,
    (1, 150): file_1k_150cm, (5, 150): file_5k_150cm, (10, 150): file_10k_150cm, (15, 150): file_15k_150cm, (20, 150): file_20k_150cm,
    (1, 200): file_1k_200cm, (5, 200): file_5k_200cm, (10, 200): file_10k_200cm, (15, 200): file_15k_200cm, (20, 200): file_20k_200cm,
    (1, 250): file_1k_250cm, (5, 250): file_5k_250cm, (10, 250): file_10k_250cm, (15, 250): file_15k_250cm, (20, 250): file_20k_250cm,
    (1, 300): file_1k_300cm, (5, 300): file_5k_300cm, (10, 300): file_10k_300cm, (15, 300): file_15k_300cm, (20, 300): file_20k_300cm,
}

# Run the analysis for sine waves
analyze_stability(frequency_distance_files, wave_type="sine")
