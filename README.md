# Raspberry Pi Embedded Data Acquisition System

## Overview
This project implements a fully automated embedded data acquisition system designed for experimental measurements and sensor monitoring applications. It integrates Raspberry Pi GPIO control, MCC DAQ analog acquisition hardware, real-time calibration mapping, and automated post-processing visualization into a single workflow. 

The system enables reliable hands-off data logging where acquisition can be started or stopped via a hardware button while maintaining full data traceability and automated analysis output. I developed this to log data from various sensors while conducting wheel force transducer testing. 

---

## System Architecture

### Boot Controller (`bootup.py`)
- Runs automatically on Raspberry Pi startup  
- Monitors a physical pushbutton to toggle logging  
- Provides LED status indication during active logging  
- Manages logging subprocess lifecycle  
- Automatically launches plotting after logging ends  

### Data Acquisition Logger (`logger.py`)
- Interfaces with MCC DAQ hardware via ULDAQ  
- Performs continuous multichannel analog sampling  
- Converts raw voltages into physical units using calibration data  
- Logs both raw and calibrated data to timestamped CSV files  
- Saves a snapshot of calibration configuration for reproducibility  

### Plotting and Analysis (`plotter.py`)
- Automatically processes completed CSV data  
- Generates shock displacement and brake pressure plots  
- Produces combined and stacked visualization outputs  
- Designed for headless operation using a non-interactive plotting backend  

---

## Key Features

### Embedded Hardware Control
- Boot-time automatic execution  
- Pushbutton-triggered logging control  
- LED status feedback  
- Headless operation capability  

### Multichannel Analog Acquisition
- Continuous buffered DAQ sampling  
- Configurable voltage ranges  
- Multiple sensor channels recorded simultaneously  

### Sensor Calibration Mapping
Automatic conversion from voltage to physical units:

- Shock potentiometer displacement (inches)  
- Brake pressure sensors (PSI)  

Calibration values are stored in YAML configuration files.
