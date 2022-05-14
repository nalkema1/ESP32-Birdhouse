@ECHO OFF
IF "%1"=="" GOTO Continue
  ampy --port COM9 --baud 115200 %*
:Continue