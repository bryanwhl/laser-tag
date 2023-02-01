#!/bin/bash

echo "Tunneling..."

read -p "Insert Student ID (EXXXXXX): " id

ssh -L 8888:pynq:8080 -J ${id}@stu.comp.nus.edu.sg xilinx@192.168.95.247
