Follow the steps below to connect your Ubuntu machine to NUS Wireless Network:

    Select System>Preferences>Network Connections
    Click on the Wireless tab. Then click Add
    Click on the Wireless tab. Then type SSID:
    NUS for staff and visitors, and NUS_STU for students
    Click on the Wireless Security tab. Fill in the following fields and click Apply.
        Security : WPA & WPA2 Enterprise​​​
        Authentication: Protected EAP (PEAP)
        Anonymous Identity: Leave blank
        Domain: auth01.nw.nus.edu.sg
        CA certificate: None
        PEAP version: Automatic
        Inner authentication : MSCHAPv2
        Username : Enter your “Domain\Username” where the domain is NUSSTF (staff) or NUSSTU (students) or NUSEXT (visitors)
        E.g. nusstf\cceabd or nusstu\e0123456 or nusext\ccev1234
        Password : (Enter your Password)
    A pop-up “Connection Established with NUS SSID” will be shown on the top right-hand side of the screen.

Getting permission on arduino https://docs.arduino.cc/software/ide-v1/tutorials/Linux
It might happen that when you upload a sketch after you have selected your board and the serial port, 
you get an error Error opening serial port ... If you get this error, you need to set serial port permission.

Open Terminal and type:

    ls -l /dev/ttyACM*

you will get something like:

    crw-rw---- 1 root dialout 188, 0 5 apr 23.01 ttyACM0

The "0" at the end of ACM might be a different number, or multiple entries might be returned. 
The data we need is "dialout" (is the group owner of the file).
Now we just need to add our user to the group:

    sudo usermod -a -G dialout <username>

where
<username>
is your Linux user name. You will need to log out and log in again for this change to take effect.

setup ble on bluno https://wiki.dfrobot.com/Bluno_SKU_DFR0267#target_6

1. Open the Arduino IDE.
2. Select the correct serial port in Menu->Tool->Serial port
3. Open the Serial monitor (on the upper right of the IDE windows)
4. Select the "No line ending"(①) and 115200 baud（②） in the two pull-down menu
5. Type "+++"（③） like this and press send button（④）
6. If the AT Command Mode is successfully Entered , you will receive "Enter AT Mode"（⑤） from it.
7. Select the "Both NL & CR"(①) and 115200 baud（②） in the two pull-down menu
8. Type or copy the AT command in the dialog（③） like this and press send button（④）
9. "AT+MAC=?<CR+LF>" Request MAC address for use in python code.
10. "AT+ROLE=ROLE_PERIPHERAL<CR+LF>" Set device to peripheral mode
11. "AT+CMODE=ANYONE<CR+LF>" Set device connection mode to anyone
12. ''' USE “AT+EXIT” to exit AT Mode '''


setup bluetooth on linux

rfkill unblock bluetooth
sudo service bluetooth restart
bluetoothctl
scan on
discoverable on
pairable on
trust address(replaced with address of your beetle)
trust B0:B1:13:2D:CD:A2
connect address

^^ manually restart bluetooth if does not work ^^