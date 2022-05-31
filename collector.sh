while true
do
    printf "D\n";
    date "+%Y-%m-%d %T";
    printf "M\n";
    cat /proc/meminfo
    printf "T\n";
    top -n1 -b -o +%MEM;
    sleep 10m;
done