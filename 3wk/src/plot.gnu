#!/usr/bin/gnuplot

reset
set term png size 1920, 1080
set ylabel "CWIN size (bytes)"
set xlabel "time (s)"
set title "Congestion window monitoring"
set grid

set out 'cwnd.png'
plot "cwnd.log" using 1:2 with linespoints title "cwnd_"



