# Capacity Planning

The 1,000-candidate figure is a planning assumption, not a concurrency guarantee.

At an assumed 64 kbps audio bitrate, a 40-minute recording is about 19.2 MB before container overhead. One thousand recordings are therefore about 19.2 GB of audio alone. Actual size must be measured from the selected browser recording format.

Measure separately:
- API concurrency and latency
- upload throughput
- PostgreSQL connection utilization
- worker queue delay
- transcription throughput
- summarization throughput
- RAM and CPU/GPU utilization
- storage growth

Do not increase AI worker concurrency until hardware measurements show sufficient capacity.
