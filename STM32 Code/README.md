# STM32 Code Documentation

This code is used in conjunction with some other pieces of code, the software layers are described below:

| Abstraction     | Purpose                                                                                                     |
|-----------------|-------------------------------------------------------------------------------------------------------------|
| Dispatcher      | Application layer code that handles error conditions, retransmission and backoff for RobotController        |
| RobotController | Provides a python interface which constructs and sends the necessary UART commands                          |
| this code       | Provides a serial UART interface to issue a set of pre-defined commands to control motion and exchange data |

## Overview

In general, there are four important user tasks, ordered by decreasing priority:
- procTask which manages UART communication, data de-encapsulation and queueing
- sensorTask which reads sensor data periodically and calculates derived values
- ctrlTask which controls the motors/servo based on incoming queue data
- oledTask which writes debug and status info to the display

And there are also different user code files:
- main.c: contains ioc generated code and starts idle task and sensorTask.
- app_main.cpp: starts procTask and ctrlTask, contains sensorTask code.
- app_parser.cpp: contains procTask, UART DMA handler.
- app_motion.cpp: contains ctrlTask, motor control code and PID controllers.
- app_display.cpp: contains oledTask.


The operation can be summarized as follows:

<---UART---> [DMA buffer] <---> [procTask] ---context_wrapper{command data queue}---> [ctrlTask]<br>
<br>
[sensorTask] -----> sensor readings/signals -------------------------------------------------------------^

## Errata list
*Any k stray bytes for buffer of size N causes indefinite offset of the DMA buffer.*<br>
Workaround: Flush buffer in task if there are not N zeros, at the low chance of flushing data while rx. The ISR does memcpy of DMA buffer if it is triggered.
<br><br>
*I2C ack timeout caused by slave device holding the data line for no reason.*<br>
Workaround: Modification on HAL to drive (and toggle) the line with higher drive strength which seems to free the I2C bus.
<br><br>
*Servo motor is not zeroed relative to the center position.*<br>
Workaround: NONE. this is a mechanical issue.
<br><br>
*Implicit start of task fns from within class instance causes undefined behavior with queues.*<br>
Workaround: Make the task fns static, and pass the pointer to class instance within context wrapper to the task fn.
<br><br>
*Turning movement will occasionally overshoot the target and continue past.*<br>
Workaround: The turn is set to terminate whenever the previous distance to target is less than the current (i.e. negative progress was made).

## Other documentation
The documentation can be found in their respective code files, including the UART command set found in app_parser.h.
