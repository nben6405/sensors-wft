#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#original owen script with changes i made

"""
Wrapper call demonstrated:    ai_device.a_in_load_queue()

Purpose:                      Set up the queue with available ranges
                              and input modes

Demonstration:                Initialize and load the queue

Steps:
1.  Call get_daq_device_inventory() to get the list of available DAQ devices
2.  Create a DaqDevice object
3.  Call daq_device.get_ai_device() to get the ai_device object for the AI
    subsystem
4.  Verify the ai_device object is valid
5.  Call ai_device.get_info() to get the ai_info object for the AI subsystem
6.  Verify the analog input subsystem has a hardware pacer
7.  Call daq_device.connect() to establish a UL connection to the DAQ device
8.  Call ai_info.get_queue_types() to get the supported queue types for the AI
    subsystem
9.  Create the queue array
10. Call ai_device.a_in_load_queue() to load the queue
11. Call ai_device.a_in_scan() to start the scan of A/D input channels
12. Call ai_device.get_scan_status() to check the status of the background
    operation
13. Display the data for each channel
14. Call ai_device.scan_stop() to stop the background operation
15. Call daq_device.disconnect() and daq_device.release() before exiting the
    process.
"""
from __future__ import print_function
from os import system
from sys import stdout
from time import time, strftime
import csv
import yaml
#from plotter import LivePlotter
import os

#import shutil

from uldaq import (get_daq_device_inventory, DaqDevice, AInScanFlag,
                   AiInputMode, AiQueueElement, create_float_buffer,
                   ScanOption, ScanStatus, InterfaceType, Range)
#-----------------------------------------------
# SAVE CONFIG FILE WITH SAME NAME AS SCRIPT
#-----------------------------------------------
def save_config_copy(config_file_path, csv_name):
    '''
    Saves a copy of the config file that this script is using with the same name as the csv.

    @param config_file_path: original config file path, probably "ShockPotConfig.yaml"

    @param csv_name: the filename of the csv, datetime dependent
    '''

    og_config = 'ShockPotConfig.yaml'
    copy_config = f"{csv_name}.yaml"
    with open(og_config, 'r') as og_file:
        config = og_file.read()
    with open(copy_config, 'w') as copy_file:
        copy_file.write(config)

#--------------------------------
# LOAD CAL DATA FROM CONFIG FILE
#--------------------------------
def load_shock_config(filename='ShockPotConfig.yaml'):
    '''
    Loads shock pot config data from the config file. Hardcoded to always call the config file "SchockPotConfig.yaml".
    '''
    with open(filename, 'r') as f:
        config = yaml.safe_load(f)
    return config['shock_pot_calibration']

def load_brake_config(filename='ShockPotConfig.yaml'):
    '''
    Loads brake pressure sensor config data from the config file. Hardcoded to always call the config file "ShockPotConfig.yaml"
    '''
    with open(filename, 'r') as f:
        config = yaml.safe_load(f)
    return config['brake_pressure_calibration']

shock_cal = load_shock_config()
short_cal = shock_cal['short_shock_pots']
long_cal = shock_cal['long_shock_pots']

brake_cal = load_brake_config()
front_cal = brake_cal['front_brake_sensor']
rear_cal = brake_cal['rear_brake_sensor']



#--------------------
# MAPPING FUNCTIONS
#--------------------

def map(current_voltage, min_voltage, max_voltage, min_target, max_target):
    '''
    accept voltage value from shock pots / brake pressure sensors and map it to a length in inches / pressure in psi.

    @param current_voltage: voltage from sensor

    @param min_voltage: minimum voltage of voltage mapping range

    @param max_voltage: maximum voltage of voltage mapping range

    @param min_target: minimum value of target unit (either inches or psi)

    @param max_target: maximum value of target unit (either inches or psi)
    '''

    # make sure all inputs are floats
    current_voltage = float(current_voltage)
    min_voltage = float(min_voltage)
    max_voltage = float(max_voltage)
    min_length = float(min_target)
    max_length = float(max_target)

    # linear mapping formula to determine length form current voltage
    mapped = ((current_voltage - min_voltage)/(max_voltage - min_voltage))*(max_length - min_length)+ min_length
    return mapped


def get_short_shock_length(current_voltage):
    '''
    maps voltage to length in inches for the short shock pots (rear) and returns the value.
    '''
    short_pot_length = map(current_voltage, short_cal['short_min_voltage'], short_cal['short_max_voltage'], short_cal['short_min_length'], short_cal['short_max_length'])
    return short_pot_length

def get_long_shock_length(current_voltage):
    '''
    maps voltage to length in inches for the long shock pots (front) and returns the value.
    '''
    long_pot_length = map(current_voltage, long_cal['long_min_voltage'], long_cal['long_max_voltage'], long_cal['long_min_length'], long_cal['long_max_length'])
    return long_pot_length

def get_front_brake_pressure(front_brake_v):
    '''
    maps voltage to pressure in psi for the front brake pressure sensor and returns the value.
    '''
    front_brake_psi = map(front_brake_v, front_cal['front_min_voltage'], front_cal['front_max_voltage'], front_cal['front_min_brake_pressure'], front_cal['front_max_brake_pressure'])
    return front_brake_psi


def get_rear_brake_pressure(rear_brake_v):
    '''
    maps voltage to pressure in psi for the rear brake pressure sensor and returns the value.
    '''
    rear_brake_psi = map(rear_brake_v, rear_cal['rear_min_voltage'], rear_cal['rear_max_voltage'], rear_cal['rear_min_brake_pressure'], rear_cal['rear_max_brake_pressure'])
    return rear_brake_psi


#------------------------------
# CHANNEL MAP CONFIGURATION
#------------------------------

channel_map = {5: get_long_shock_length, #front right shock pot
               13: get_short_shock_length, #rear right shock pot
               6: get_short_shock_length, #rear left shock pot
               14: get_long_shock_length, #front left shock pot
               12: get_rear_brake_pressure, #rear brake pressure sensor
               4: get_front_brake_pressure #front brake pressure sensor
               }

#------------------------------
# CHANNEL NAME CONFIGURATION
#------------------------------

channel_name = {
        5: 'Front right shock pot',
        13: 'Rear right shock pot',
        6: 'Rear left shock pot',
        14: 'Front left shock pot',
        12: 'Rear brake pressure sensor',
        4: 'Front brake pressure sensor'
        }


channel_name_mapped = {
        5: 'Front right shock pot (inches)',
        13: 'Rear right shock pot (inches)',
        6: 'Rear left shock pot (inches)',
        14: 'Front left shock pot (inches)',
        12: 'Rear brake pressure (PSI)',
        4: 'Front brake pressure (PSI)'
        }

channel_name_raw = {
        5: 'Front right shock pot (V)',
        13: 'Rear right shock pot (V)',
        6: 'Rear left shock pot (V)',
        14: 'Front left shock pot (V)',
        12: 'Rear brake sensor (V)',
        4: 'Front brake sensor (V)'
        }

def a_in_main():
    """Analog input scan with queue example."""
    daq_device = None
    ai_device = None
    status = ScanStatus.IDLE

    interface_type = InterfaceType.ANY
    samples_per_channel = 1000
    rate = 1000
    scan_options = ScanOption.DEFAULTIO | ScanOption.CONTINUOUS
    flags = AInScanFlag.DEFAULT

    channels = [5,6,13,14,4,12]
    short_channels = [6,13]
    long_channels = [5,14]
    channel_count = len(channels)
    low_channel=0
    high_channel=3

    #--------------
    # FILE NAMING
    #--------------
    base_dir = '/home/pi/Nitzan'
    timestr = strftime("%m-%d-%Y_%H-%M-%S")
    filename = timestr + "_MCC_DAQ_DATA"
    #filename_mapped = f'{filename}_MAPPED.csv'
    #filename_raw = f'{filename}_RAW.csv'
    #filename_mapped = timestr + "_MCC_DAQ_DATA_MAPPED.csv"
    #filename_raw = timestr + "_MCC_DAQ_DATA_RAW.csv"
    filename_mapped = os.path.join(base_dir, f'{filename}_MAPPPED.csv')
    filename_raw = os.path.join(base_dir, f'{filename}_RAW.csv')


    # Start live plotting
    #plotter = LivePlotter(filename_mapped, update_interval=0.5)
    #plotter.start()

    # Write the path to a control file
    CONTROL_FILE = os.path.join(base_dir, 'latest_csv_path.txt')
    try:
        with open(CONTROL_FILE, 'w') as f:
            f.write(filename_mapped)
        print(f"Control file updated with: {filename_mapped}")
    except Exception as e:
        print(f"ERROR: Could not write control file {CONTROL_FILE}: {e}")

    # Save a copy of config file with the same timestamp as CSVs
    save_config_copy('ShockPotConfig.yaml', filename)
    print(f'Copy of config file saved as: {filename}.yaml')


    try:
        # Get descriptors for all the available DAQ devices.
        devices = get_daq_device_inventory(interface_type)
        number_of_devices = len(devices)
        if number_of_devices == 0:
            raise RuntimeError('Error: No DAQ devices found')

        # Create the DAQ device from the descriptor at the specified index.
        daq_device = DaqDevice(devices[0])

        # Get the AiDevice object and verify that it is valid.
        ai_device = daq_device.get_ai_device()

        # Verify the specified device supports hardware pacing for analog input.
        ai_info = ai_device.get_info()

        # Establish a connection to the DAQ device.
        descriptor = daq_device.get_descriptor()
        print('\nConnecting to', descriptor.dev_string, '- please wait...')
        # For Ethernet devices using a connection_code other than the default
        # value of zero, change the line below to enter the desired code.
        daq_device.connect(connection_code=0)

        # The default input mode is SINGLE_ENDED.
        input_mode = [AiInputMode.SINGLE_ENDED,AiInputMode.SINGLE_ENDED,AiInputMode.SINGLE_ENDED,AiInputMode.SINGLE_ENDED,AiInputMode.SINGLE_ENDED,AiInputMode.SINGLE_ENDED,AiInputMode.SINGLE_ENDED,AiInputMode.SINGLE_ENDED,AiInputMode.SINGLE_ENDED,AiInputMode.SINGLE_ENDED]
        print(input_mode)

        # Get the number of channels and validate the high channel number.
        number_of_channels = ai_info.get_num_chans_by_mode(input_mode[0])

        # Get a list of supported ranges and validate the range index.
        ranges = ai_info.get_ranges(input_mode[0])

        # 0 = BIP10VOLTS, 1 = BIP5VOLTS, 2 = BIP2VOLTS, 3 = BIP1VOLTS
        #channel_ranges = [0, 1, 2, 3]

        # set brake pressure channels to 2V because the voltage range is under 2V (due to incorrect resistor value on Owen's breakout board)
        channel_ranges = [0, 0, 0, 0, 2, 2]

        # Get a list of supported queue types.
        queue_types = ai_info.get_queue_types()

        # Assign each channel in the queue an input mode (SE/DIFF) and a range.
        # If multiple ranges are supported, we will cycle through them and
        # repeat ranges if the number of channels exceeds the number of ranges.
        #
        # This block of code could be used to set other queue elements such as
        # the input mode and channel list.
        queue_list = []
        #print(range(len(channels)))
        for i, n in enumerate(channels):
            queue_element = AiQueueElement()
            queue_element.channel = n
            queue_element.input_mode = input_mode[i]
            print(i, channels[i], n)
            queue_element.range = ranges[channel_ranges[i]]

            queue_list.append(queue_element)

        # Load the queue.
        ai_device.a_in_load_queue(queue_list)

        data = create_float_buffer(channel_count, samples_per_channel)

        print('\n', descriptor.dev_string, ' ready', sep='')
        print('    Function demonstrated: ai_device.a_in_load_queue()')
        print('    Channels: ', channels)
        for i in range(channel_count):
            print('        Channel:', queue_list[i].channel,
                  ', Input mode:', AiInputMode(queue_list[i].input_mode).name,
                  ', Range:', Range(queue_list[i].range).name)
        print('    Samples per channel: ', samples_per_channel)
        print('    Rate: ', rate, 'Hz')
        print('    Scan options:', display_scan_options(scan_options))
        try:
            input('\nHit ENTER to continue\n')
        except (NameError, SyntaxError):
            pass

        # Start the acquisition.
        #
        # When using the queue, the low_channel, high_channel, input_mode, and
        # range parameters are ignored since they are specified in queue_array.
        rate = ai_device.a_in_scan(low_channel, high_channel, input_mode[0],
                                   ranges[0], samples_per_channel,
                                   rate, scan_options, flags, data)

        system('clear')

        starttime = time()

        with open(filename_mapped, mode="w", newline="") as mapped_file, open(filename_raw, mode='w', newline="") as raw_file:
            mapped_writer = csv.writer(mapped_file)
            raw_writer = csv.writer(raw_file)

            # header for mapped CSV
            mapped_header_list = []
            mapped_header_list.append("Time")
            for i in range(channel_count):
                mapped_header_list.append(str(channels[i]))

            mapped_writer.writerow(mapped_header_list)
            mapped_file.flush()

            # header for raw CSV
            raw_header_list = []
            raw_header_list.append("Time")
            for i in range(channel_count):
                raw_header_list.append(str(channels[i]))

            raw_writer.writerow(raw_header_list)
            raw_file.flush()

            #lp = LivePlotter(filename_mapped, base_dir=base_dir)
            #lp.start()

            data_list_mapped = []
            data_list_raw = []
            index_old = 10

            try:
                while True:
                    try:
                        # Get the status of the background operation
                        status, transfer_status = ai_device.get_scan_status()

                        reset_cursor()

                        #print('actual scan rate = ', '{:.6f}'.format(rate), 'Hz\n')

                        index = transfer_status.current_index



                        if(index_old < index):

                            print('currentTotalCount = ',
                                  transfer_status.current_total_count)
                            print('currentScanCount = ',
                                  transfer_status.current_scan_count)
                            print('currentIndex = ', index, '\n')

                            '''
                            data_list_mapped.append(time() - starttime)
                            data_list_raw.append(time() - starttime)

                            # Display the data.
                            print('channel: raw voltage | mapped_value')
                            for i in range(channel_count):
                                chan = channels[i]
                                raw_data = data[index + i]
                                mapped_data = channel_map[chan](raw_data)
                                formatted_raw_data = '{:.6f}'.format(data[index + i])
                                formatted_mapped_data = '{:.6f}'.format(mapped_data)
                                print(f'chan = {chan}: {formatted_raw_data} | {formatted_mapped_data}' )
                                data_list_mapped.append(mapped_data)
                                data_list_raw.append(raw_data)

                            # write to CSV
                            mapped_writer.writerow(data_list_mapped)
                            raw_writer.writerow(data_list_raw)


                            data_list_mapped.append(index)
                            data_list_raw.append(index)

                            index_old = index
                            data_list_mapped.clear()
                            data_list_raw.clear()
                            '''

                            data_list_mapped = [time() - starttime]
                            sata_list_raw = [time() - starttime]

                            for i in range(channel_count):
                                chan = channels[i]
                                raw_data = data[index + i]
                                mapped_data = channel_map[chan](raw_data)
                                formatted_raw_data = '{:.6f}'.format(data[index + i])
                                formatted_mapped_data = '{:.6f}'.format(mapped_data)
                                print(f'chan = {chan}: {formatted_raw_data} | {formatted_mapped_data}' )
                                data_list_mapped.append(mapped_data)
                                data_list_raw.append(raw_data)

                            # write to CSV
                            mapped_writer.writerow(data_list_mapped)
                            raw_writer.writerow(data_list_raw)


                            data_list_mapped.append(index)
                            data_list_raw.append(index)

                            index_old = index
                            data_list_mapped.clear()
                            data_list_raw.clear()


                            data_list_mapped = [time() - starttime]
                            sata_list_raw = [time() - starttime]

                            for i in range(channel_count):
                                chan = channels[i]
                                raw_data = data[index + i]
                                mapped_data = channel_map[chan](raw_data)
                                data_list_mapped.append(mapped_data)
                                data_list_raw.append(raw_data)

                            mapped_writer.writerow(data_list_mapped)
                            raw_writer.writerow(data_list_raw)

                            index_old = index


                            #sleep(0.01)

                        #Check to see if index has rolled back to 0
                        if (index_old == channel_count * (samples_per_channel - 1)):
                            index_old = -1


                    except (ValueError, NameError, SyntaxError):
                        break


            except KeyboardInterrupt:
                pass

    except RuntimeError as error:
        print('\n', error)

    finally:
        if daq_device:
            # Stop the acquisition if it is still running.
            if status == ScanStatus.RUNNING:
                ai_device.scan_stop()
            if daq_device.is_connected():
                daq_device.disconnect()
            daq_device.release()
            #end plotter
           # plotter.stop()
            #plotter.save_final(f"/home/pi/Nitzan/{filename}")
        try:
            lp.stop()
            lp.save_final(os.path.join(base_dir,filename))
        except:
            pass


def display_scan_options(bit_mask):
    """Create a displays string for all scan options."""
    options = []
    if bit_mask == ScanOption.DEFAULTIO:
        options.append(ScanOption.DEFAULTIO.name)
    for option in ScanOption:
        if option & bit_mask:
            options.append(option.name)
    return ', '.join(options)


def reset_cursor():
    """Reset the cursor in the terminal window."""
    stdout.write('\033[1;1H')


def clear_eol():
    """Clear all characters to the end of the line."""
    stdout.write('\x1b[2K')


if __name__ == '__main__':
    a_in_main()
