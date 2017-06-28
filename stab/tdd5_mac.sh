#!/bin/bash

declare -A pcids
pcids=([3]="120x30+30+30" [4]="120x30+800+30" [5]="120x30+30+450" [6]="120x30+800+450")

if [ $# -eq 0 ]
then
   keys=${!pcids[@]}
else
   keys=$@
fi

echo "Login to mac: $keys"


for pcid in $keys
do
    title="mac00"$pcid
    addr="lteran@seki20mac00"$pcid
    geo=${pcids[$pcid]}
    cmd1="expect -f ssh_mac.exp $addr cd Documents" 
    cmd2="expect -f ssh_mac.exp $addr cd waftools" 
    gnome-terminal -t $title --geometry=$geo -e "$cmd1"
    gnome-terminal -t $title"_waf" --geometry=$geo -e "$cmd2"
done

sleep 1
processes=$(ps -C "expect" --no-heading -f | grep ssh_mac | awk '{print $2}')
echo $processes > "$0.log"

