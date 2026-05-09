#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

# Pin setup
IN1 = 17
IN2 = 27
ENA = 18

GPIO.setmode(GPIO.BCM)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(ENA, GPIO.OUT)

pwm = GPIO.PWM(ENA, 1000)
pwm.start(0)

def motor_forward(speed):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    pwm.ChangeDutyCycle(speed)

def motor_backward(speed):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    pwm.ChangeDutyCycle(speed)

def motor_stop():
    pwm.ChangeDutyCycle(0)

try:
    print("Forward 50%...")
    motor_forward(50)
    time.sleep(2)

    print("Stop...")
    motor_stop()
    time.sleep(1)

    print("Backward 50%...")
    motor_backward(50)
    time.sleep(2)

    print("Stop.")
    motor_stop()

except KeyboardInterrupt:
    pass
finally:
    pwm.stop()
    GPIO.cleanup()
    print("Done!")
