#!/bin/bash

server="sekilx830"
geo="160x40+30+30"

cluster1_nodes=(ki20enb1510 kienb1526 kienb1529)
cluster1_uctools=(ki20uctoolv20001 ki20uctoolv20003 kiuctoolbs018)
cluster1_ltesims=(ki20ltesim0006)

cluster2_nodes=(ki20enb1511 kienb1525 kienb1527 kiwrbs1528)
cluster2_uctools=(kiuctoolbs018 ki20uctoolv20004 ki20uctoolv20002)
cluster2_ltesims=(ki20ltesim0005)

all_nodes=(ki20enb1510 ki20enb1511 kienb1525 kienb1526 kienb1527 kiwrbs1528 kienb1529)


nodes=(${cluster1_nodes[@]})
uctools=(${cluster1_uctools[@]})
ltesims=(${cluster1_ltesims[@]})
if [ $# -eq 1 ]
then
    sel=$1
    echo "Starting cluster$1"
else
    echo "$0 <1|2>"
    exit 1
fi


if [ $sel -eq 2 ]
then
    nodes=(${cluster2_nodes[@]})
    uctools=(${cluster2_uctools[@]})
    ltesims=(${cluster2_ltesims[@]})
fi


for node in ${nodes[*]}
do
    gnome-terminal --geometry=$geo -t $node -e "moshell $node" &
done

sleep 1
for uctool in ${uctools[*]}
do
    gnome-terminal --geometry=$geo -t $uctool -e "expect -f ssh.exp $uctool ltelab ltesimltesim" &
done

sleep 1
for ltesim in ${ltesims[*]}
do
    gnome-terminal --geometry=$geo -t $ltesim -e "expect -f ssh.exp $ltesim ltelab ltesimltesim" &
done
