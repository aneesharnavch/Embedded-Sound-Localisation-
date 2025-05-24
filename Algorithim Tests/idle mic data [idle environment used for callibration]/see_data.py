import pandas as pd
import matplotlib.pyplot as plt

# Step 1: Load the Excel file
file_path = r'C:\Users\anees\Desktop\idle mic data\filtered_data.xlsx'
data = pd.read_excel(file_path)

# Step 2: Extract data from Column A
column_a = data.iloc[:, 0]  # Assuming column A is the first column

# Step 3: Plot the data
plt.figure(figsize=(10, 6))
plt.plot(column_a, marker='o')
plt.title('Plot of Data from Column A')
plt.xlabel('Index')
plt.ylabel('Value')
plt.grid(True)
plt.show()
