# LMCC-Challenge-MURU
LMCC Challenge LoRa People Counter and Bin Fill Meter

Main.py is the most up to date version.

I'm currently experiencing a problem with bad/false readings from the Ultrasonic sensor, and timouts when connecting.

A downlink of two bytes "resets" the device. It recalibrates the distance detected at rest, and disconnects and reconnects the device.
Perhaps I should change it so the connection isnt reset, since if connection is lost it wouldnt receive the downlink anyway.

