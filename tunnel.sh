#!/bin/bash

echo "Tunneling..."

read -p "GAMEMODE: " gamemode

read -p "Insert Student ID (EXXXXXX): " id

ssh -X -L 8888:pynq:8080 -J ${id}@stu.comp.nus.edu.sg xilinx@192.168.95.247
