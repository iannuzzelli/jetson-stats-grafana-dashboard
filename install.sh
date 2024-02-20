sudo cp jetson_stats_prometheus_collector.py /usr/local/bin/
cp jetson_stats_prometheus_collector.service /etc/systemd/system/

systemctl daemon-reload
systemctl start jetson_stats_prometheus_collector
systemctl status jetson_stats_prometheus_collector
