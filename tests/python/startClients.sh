for i in $(seq 1 30)
do
        python3 client.py 192.168.10.0/24 $((i + 5))000 192.168.0.34 $((9000 + i)) &
done
