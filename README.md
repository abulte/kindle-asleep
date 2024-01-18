# kindle-asleep

I use my Kindle (or the Kindle app) every day to put me through sleep.

This means that Kindle data should give me a very precise way of knowing the time when I fell asleep. I have various sleep trackers (Withings sleep, Garmin watch) that are not good at this job, they count my reading as sleeping time.

Amazon does not, to my knowledge, provide any API or similar tool to access those informations easily. _But_ you can [request of very complete export of your Kindle data](https://jakelee.co.uk/analysing-5-years-of-amazon-kindle-reading/), wait a few hours/days for Amazon to ship them to you (via email, not drone) and crunch the numbers.

Hence this script. It takes the export as input and tries to find the latest end of reading session for a given day, or early in the next day.

Data is exported to CSV for further analysis. Datetimes are converted to a local timezone (`Europe/Paris` by default).

```shell
pip install -r requirements.txt
# move your uncompressed Kindle export here
mv ~/Downloads/Kindle data
python cli.py compute --timezone "Europe/Paris"
```

Output should look something like this:

```
[...]
2024-01-14	2024-01-15 00:06:01+00:00
2024-01-15	2024-01-15 23:07:04+00:00
2024-01-16	2024-01-16 21:41:46+00:00
Results written to output/2024-01-18.csv, with timezone Europe/Paris
```
