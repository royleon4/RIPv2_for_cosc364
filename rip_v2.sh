#!/bin/sh

python3 rip_v2.py config_1.txt&
gnome-terminal -e "python3 rip_v2.py config_2.txt"
gnome-terminal -e "python3 rip_v2.py config_3.txt"
gnome-terminal -e "python3 rip_v2.py config_4.txt"
gnome-terminal -e "python3 rip_v2.py config_5.txt"
gnome-terminal -e "python3 rip_v2.py config_6.txt"
gnome-terminal -e "python3 rip_v2.py config_7.txt"
