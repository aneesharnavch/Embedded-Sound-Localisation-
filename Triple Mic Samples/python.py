import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Define the coordinates for both X and Y axes: [-45, -30, -15, 0, 15, 30, 45]
coords = np.array([-45, -30, -15, 0, 15, 30, 45])

# Generate a grid of these coordinates for both X and Y axes
x_grid, y_grid = np.meshgrid(coords, coords)

# Flatten the grid for easy manipulation
x_flat = x_grid.flatten()
y_flat = y_grid.flatten()

# Generate accuracy values
accuracy = []

for x, y in zip(x_flat, y_flat):
    # Create distance from origin (0,0) for "further" distance check
    distance_from_origin = np.sqrt(x**2 + y**2)
    
    # Fading accuracy: closer to (0, 0), higher accuracy; further, lower accuracy
    fading_factor = np.clip(distance_from_origin / 45.0, 0, 1)  # Scaling the distance factor between 0 and 1
    accuracy_value = np.random.uniform(0.4, 0.76) + (0.25 * fading_factor)  # Fading effect with min 40% accuracy
    
    # Avoid the value 1 (100% accuracy)
    accuracy_value = min(accuracy_value, 0.99)  # Maximum accuracy will be just under 1
    
    accuracy.append(accuracy_value)

# Calculate the current average of the accuracy values
current_avg = np.mean(accuracy)
target_avg = 0.77  # Target average is 77%

# Calculate the scaling factor to adjust the average to 77%
scaling_factor = target_avg / current_avg

# Adjust the accuracy values to achieve the target average
adjusted_accuracy = [min(acc * scaling_factor, 0.99) for acc in accuracy]  # Make sure no value exceeds 0.99

# Create a DataFrame with the adjusted accuracy values
data = pd.DataFrame(np.array(adjusted_accuracy).reshape(len(coords), len(coords)),
                    index=coords, columns=coords)

# Save the data to a CSV file on Desktop
desktop_path = r'C:\Users\anees\Desktop\heatmap_data.csv'
data.to_csv(desktop_path)

# Plot the heatmap live
plt.figure(figsize=(8, 6))
sns.heatmap(data, annot=True, cmap="YlGnBu", cbar_kws={'label': 'Accuracy'})
plt.title("Localization Accuracy Heatmap accross a 10K Sine wave")
plt.xlabel("Y Axis (cm)")
plt.ylabel("X Axis (cm)")
plt.show()

print(f"CSV file saved at: {desktop_path}") 