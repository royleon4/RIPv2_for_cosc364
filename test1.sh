#!/bin/sh

python3 rip_v2.py test1_1.txt&
gnome-terminal -e "python3 rip_v2.py test1_2.txt"
gnome-terminal -e "python3 rip_v2.py test1_3.txt"
gnome-terminal -e "python3 rip_v2.py test1_4.txt"
