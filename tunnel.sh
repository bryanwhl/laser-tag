#!/bin/bash

echo "Tunneling..."

read -p "Insert Student ID (EXXXXXX): " id

ssh -t -t  ${id}@stu.comp.nus.edu.sg exec ssh xilinx@192.168.95.247
