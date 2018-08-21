@echo off
mos build --platform esp32
mos flash
mos wifi ssid password
mos gcp-iot-setup --gcp-project ml-demo-212200 --gcp-region us-central1 --gcp-registry iot-registry
mos console
