import csv

from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import pendulum

from minicli import cli, run

DEFAULT_PATH = "data/Kindle.Devices.ReadingSession/Kindle.Devices.ReadingSession.csv"
MIN_START_HOUR = 18
MAX_END_HOUR = 6


@cli
def compute(path: Path = Path(DEFAULT_PATH), timezone="Europe/Paris"):
    results = defaultdict(lambda: {"start": None, "end": None})
    orphans = {}

    # BOM in input CSV...
    with path.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader]

    def to_local_dt(dt):
        return pendulum.instance(dt).in_timezone(timezone)

    def get_start(value, existing):
        local_dt = to_local_dt(value)
        if local_dt.hour < MIN_START_HOUR:
            return existing
        if not existing:
            return value
        return value if value < existing else existing

    def get_end(value, existing):
        if not existing:
            return value
        return value if value > existing else existing

    # build a normalized dataset for every day where a start date exists
    # it is computed on the same day UTC and only keeps start hours that seem coherent
    # when no start available, we keep the max end in orphans for end date
    # XXX: this misses chunked reading sessions for next day, e.g. restart a reading
    # session at 00:01 and finish at 00:18

    for row in rows:
        try:
            start = datetime.fromisoformat(row["start_timestamp"])
        except ValueError:
            start = None

        end = datetime.fromisoformat(row["end_timestamp"])

        if start:
            results[start.date()] = {
                "start": get_start(start, results[start.date()]["start"]),
                "end": get_end(end, results[start.date()]["end"]),
            }
        else:
            orphans[end.date()] = (
                end
                if not orphans.get(end.date()) or orphans[end.date()] < end
                else orphans[end.date()]
            )

    results = dict(sorted(results.items()))

    # use orphans to get better quality end datetime if it makes senses
    for today in results:
        tomorrow = today + timedelta(days=1)
        # look for a suitable orphan, same day
        if today in orphans and orphans[today] > results[today]["end"]:
            results[today]["end"] = orphans[today]
        # and/or an early enough orphan for the next day
        local_dt_tomorrow = (
            to_local_dt(orphans[tomorrow]) if tomorrow in orphans else None
        )
        if (
            tomorrow in orphans
            and orphans[tomorrow] > results[today]["end"]
            and local_dt_tomorrow.hour < MAX_END_HOUR
            # avoid jumping to after tomorrow with tz conversion
            and local_dt_tomorrow.day == orphans[tomorrow].day
        ):
            print(f"Gotcha, tomorrow orphan {orphans[tomorrow]} as of {today}")
            results[today]["end"] = orphans[tomorrow]

    for d, data in results.items():
        print(d)
        print(data["start"], data["end"])

    output_path = Path("output")
    output_path.mkdir(exist_ok=True)
    output_file = output_path / f"{datetime.today().date().isoformat()}.csv"
    with Path(output_file).open("w") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "day",
                "start_local",
                "start_utc",
                "end_local",
                "end_utc",
                "reading_time_seconds",
            ],
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "day": k,
                    "start_local": to_local_dt(v["start"]) if v["start"] else None,
                    "start_utc": v["start"],
                    "end_local": to_local_dt(v["end"]),
                    "end_utc": v["end"],
                    "reading_time_seconds": (v["end"] - v["start"]).total_seconds()
                    if v["start"]
                    else None,
                }
                for k, v in results.items()
            ]
        )
    print(f"Results written to {output_file}, with timezone {timezone}")


if __name__ == "__main__":
    run()
