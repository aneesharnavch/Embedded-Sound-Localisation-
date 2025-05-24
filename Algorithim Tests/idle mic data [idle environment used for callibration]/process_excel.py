import pandas as pd

def process_excel(file_path, output_file_path):
    # Load the Excel file
    df = pd.read_excel(file_path, usecols=[0], header=None, names=['Data'])

    # Drop empty cells
    df = df.dropna()

    # Convert the 'Data' column to numeric, coercing errors into NaN
    df['Data'] = pd.to_numeric(df['Data'], errors='coerce')

    # Drop rows with non-numeric data (NaN values after conversion)
    df = df.dropna()

    # Filter out numbers under 10 or over 5000
    df = df[(df['Data'] >= 1100) & (df['Data'] <= 1500)]

    # Reset index to maintain chronology in the new file
    df = df.reset_index(drop=True)

    # Save the processed data to a new Excel file
    df.to_excel(output_file_path, index=False, header=False)

if __name__ == "__main__":
    # Define the input file path and output file path
    file_path = r"C:\Users\anees\Desktop\idle mic data\data.xlsx"
    output_file_path = r"C:\Users\anees\Desktop\idle mic data\filtered data.xlsx"

    # Process the Excel file
    process_excel(file_path, output_file_path)
