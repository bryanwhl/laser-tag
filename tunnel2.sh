#!/bin/bash

echo "Tunneling..."

read -p "Insert Student ID (EXXXXXX): " id

ssh -X -L 7777:pynq:7070 -J ${id}@stu.comp.nus.edu.sg xilinx@192.168.95.247
