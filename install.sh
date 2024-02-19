sudo cp jetson_stats_prometheus_collector.py /usr/local/bin/

# Install service for the current user
mkdir -p ~/.config/systemd/user

cp jetson_stats_prometheus_collector.service /etc/systemd/system/
systemctl daemon-reload
systemctl start jetson_stats_prometheus_collector
systemctl status jetson_stats_prometheus_collector
