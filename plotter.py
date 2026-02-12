import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import yaml
matplotlib.use("Agg") # Use Agg since we only want to save the final file

def load_date_test_dir(filename='test.yaml'):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, filename)

    try:
        with open(filename, 'r') as f:
            config = yaml.safe_load(f)
        return config['save_fp']
    except FileNotFoundError:
        print(f"Error: config gile not found at {config_path}")
        sys.exit(1)

BASE_DIR = '/home/pi/TESTING_DATA'
date_test_dir = str(load_date_test_dir())

if date_test_dir.startswith(os.path.sep):
    date_test_dir = date_test_dir.lstrip(os.path.sep)

plot_save_path_dir = os.path.join(BASE_DIR, date_test_dir)

CONTROL_FILE = os.path.join(BASE_DIR, 'latest_csv_path.txt')



def get_latest_csv_path():
    """Reads the path of the most recently created CSV from the control file."""
    try:
        with open(CONTROL_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: Control file not found at {CONTROL_FILE}. Cannot proceed with plotting.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading control file: {e}")
        sys.exit(1)


def save_final_plots(csv_path):
    """Generates and saves final shock and brake plots from the specified CSV."""

    print(f"Processing CSV: {csv_path}")

    # Read the completed CSV
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: CSV data file not found at {csv_path}")
        return

    # Derive the base filename for the output plots
    # This removes the '.csv' and '_MAPPPED' from the full path/filename
    base_path = os.path.splitext(csv_path)[0].replace('_MAPPPED', '')

    # Define channels
    shock_channels = [5, 6, 13, 14]
    brake_channels = [4, 12]
    all_channels = [5,6,13,14,4,12]

    channel_names = {
            5: 'FR Shockpot',
            13: 'RR Shockpot',
            6: 'RL Shockpot',
            14: 'FL Shockpot',
            12: 'Rear Brake',
            4: 'Front Brake'

            }
    channel_name_units = {
            5: 'Front Right Shock Pot (Inches)',
            13: 'Rear Right Shock Pot (Inches)',
            6: 'Rear Left Shock Pot (Inches)',
            14: 'Front Left Shock Pot (Inches)',
            12: 'Rear Brake Pressure Sensor (PSI)',
            4: 'Front Brake Pressure Sensor (PSI)'

            }
    # SHOCKS PLOT
    plt.figure()
    for ch in shock_channels:
        if str(ch) in df.columns:
            plt.plot(df['Time'], df[str(ch)], label=f'{channel_names[ch]}')
    plt.xlabel('Time (s)')
    plt.ylabel('Shock Pot Length (inches)')
    plt.title('Final Shock Pot Data')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'{base_path}_SHOCKS_FINAL.png')
    plt.close()

    # BRAKES PLOT
    plt.figure()
    for ch in brake_channels:
        if str(ch) in df.columns:
            plt.plot(df['Time'], df[str(ch)], label=f'{channel_names[ch]}')
    plt.xlabel('Time (s)')
    plt.ylabel('Brake Pressure (PSI)')
    plt.title('Final Brake Pressure Data')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'{base_path}_BRAKES_FINAL.png')
    plt.close()

    '''
    # FULL PLOT
    plt.figure()
    for ch in all_channels:
        if str(ch) in df.columns:
            plt.plot(df['Time'], df[str(ch)], label=f'{channel_name_units[ch]}')
    plt.xlabel('Time (s)')
    plt.ylabel('Brake Pressure (PSI) and Shock Pot Length (inches)')
    plt.legend()
    plt.savefig(f'{base_path}_FULL_PLOT_FINAL.png')
    plt.close()


    print("Plotting complete.")
    '''

    # STACKED FULL PLOT
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
    fig.suptitle('Stacked Data Plot (Brakes and Shocks)')

    # Plot brakes
    for ch in brake_channels:
        if str(ch) in df.columns:
            ax1.plot(df['Time'], df[str(ch)], label=f'{channel_names[ch]}')

    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Brake Pressure (PSI)')
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax1.grid(True)

    # Plot shock pots
    for ch in shock_channels:
        if str(ch) in df.columns:
            ax2.plot(df['Time'], df[str(ch)], label=f'{channel_names[ch]}')


    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Shock Pot Length (Inches)')
    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax2.grid(True)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(f'{base_path}_STACKED_PLOT.png')
    plt.close(fig)

if __name__ == '__main__':
    latest_csv_path = get_latest_csv_path()
    save_final_plots(latest_csv_path)