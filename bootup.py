#!/usr/bin/python3

import RPi.GPIO as GPIO
import time
import threading
import subprocess

# To verify the script runs @ pi bootup, execute the following commands on the terminal:
# 1. 'sudo reboot'
# 2. 'cat script_log.txt'

# NOTE: Press button on RaspPi to start collecting data.

print("Program starting...")

# GPIO setup
GPIO.setmode(GPIO.BCM)
BUTTON_PIN = 16
LED_PIN = 21

GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LED_PIN, GPIO.OUT)

# Global flag to indicate if logging is active
actively_logging = threading.Event()

# ---------------------------
# LED blinking thread function
# ---------------------------
# - LED blinks when actively logging data
# - LED is OFF when not logging data
#
# ... aka led go BLINK BLINK BLINK while data is being LOGGED LOGGED LOGGED
def led_blinky():
    while True:
        if actively_logging.is_set():
            GPIO.output(LED_PIN, GPIO.HIGH)
            time.sleep(0.8)
            GPIO.output(LED_PIN, GPIO.LOW)
            time.sleep(0.5)
        else:
            GPIO.output(LED_PIN, GPIO.LOW)
            time.sleep(0.1)

# ---------------------------
# Data logging thread function
# ---------------------------
# - Starts/stops the data logging script based on actively_logging flag
# - Defines a single "process" to ensure only one instance of the data logging script runs at a time
def log_data():

    process = None

    while True:

        if actively_logging.is_set():

            # The data logging flag is set aka TRUE aka DATA LOGGING SHOULD BE HAPPENING.
            # Therefore, if the logging process is not already running, start it.

            if process is None or process.poll() is not None:

                print("Starting data logging process...")

                process = subprocess.Popen(
                    ['python3', '/home/pi/Nitzan/logger.py']
                )

        else:

            # The data logging flag is not set aka FALSE aka DATA LOGGING SHOULD NOT BE HAPPENING.
            # Therefore, if the logging process is running, terminate it.

            if process is not None and process.poll() is None:

                print("Stopping data logging process...")

                process.terminate() # send SIGTERM to process

                try:
                    process.wait(timeout=2)
                    print("Data logging process terminated gracefully.")

                    # Run the plotting script after logging thread has terminated
                    print("Starting final plot generation ...")
                    subprocess.run(
                        ['python3', '/home/pi/Nitzan/plotter.py'],
                        check=True #any exit code other than zero will raise error (indicating subprocess failure)
                    )
                    print("Final plots generated.")

                except subprocess.TimeoutExpired:
                    print("Data logging process did not terminate in time (2 seconds). Killing it...")
                    process.kill()
                    process.wait()

                process = None

        time.sleep(0.1)

# ---------------------------
# Main function
# ---------------------------
def main():

    # Initial button state
    previous_button_state = GPIO.input(BUTTON_PIN) # HIGH = not pressed, LOW = pressed
    print(f"Initial button state: {'unpressed' if previous_button_state else 'pressed'}")

    # Start threads (LED blinker & data logger)
    # NOTE: daemon=True means the daemon-thread will automatically be killed exit when the main program exits
    threading.Thread(target=led_blinky, daemon=True).start()
    threading.Thread(target=log_data, daemon=True).start()

    # --- Toggle variable for logging ---
    toggle_logging = False

    print("Bootup complete. Waiting for button press...")

    # Main loop: monitor button state
    try:
        while True:

            current_button_state = GPIO.input(BUTTON_PIN)

            if previous_button_state == GPIO.HIGH and current_button_state == GPIO.LOW:
                # Button has just been pressed (HIGH -> LOW)
                toggle_logging = not toggle_logging  # flip logging state
                if toggle_logging:
                    print("Button pressed: Starting data logging...")
                    actively_logging.set()
                else:
                    print("Button pressed: Stopping data logging...")
                    actively_logging.clear()

            previous_button_state = current_button_state

            time.sleep(0.02) # 20ms debounce ==> press + release of button must be held at least 0.02 seconds.

    except KeyboardInterrupt:
        print("Exiting program...")

    finally:
        GPIO.cleanup()

# Runs the main function
if __name__ == '__main__':
    main()
