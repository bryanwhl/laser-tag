rfkill unblock bluetooth
sudo service bluetooth restart
bluetoothctl
scan on
discoverable on
pairable on
trust B0:B1:13:2D:CD:A2
trust B0:B1:13:2D:D4:89
trust B0:B1:13:2D:D4:AB
trust B0:B1:13:2D:B3:08
connect B0:B1:13:2D:CD:A2
connect B0:B1:13:2D:D4:89
connect B0:B1:13:2D:D4:AB
connect B0:B1:13:2D:B3:08