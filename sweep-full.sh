#!/bin/bash
set -u
export OUT=/tools/sweep-qemu-full.csv
export NPP=32 NTG=8 REPS=1 THREADS=2
rm -f /tools/sweep-qemu-full.csv
VLENS=128  SCHEDULES="norepack q4_0_8x1 q4_0_8x8"                                bash /tools/sweep-schedules.sh
VLENS=256  SCHEDULES="norepack q4_0_8x1 q4_0_16x1 q4_0_8x8"                      bash /tools/sweep-schedules.sh
VLENS=512  SCHEDULES="norepack q4_0_8x1 q4_0_16x1 q4_0_32x1"                     bash /tools/sweep-schedules.sh
VLENS=1024 SCHEDULES="norepack q4_0_8x1 q4_0_16x1 q4_0_32x1 q4_0_64x1"           bash /tools/sweep-schedules.sh
