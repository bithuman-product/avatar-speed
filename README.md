# avatar-speed

Real-time avatar render speed, by device: the numbers bitHuman publishes at
[docs.bithuman.ai/performance](https://docs.bithuman.ai/performance), as a CSV and a JSON
snapshot you can cite, diff and load into anything.

Every configuration we publish renders faster than real time, including 10-minute sustained runs
on iPhone 15 and Samsung Galaxy S25+.

## What the numbers mean

× real time is seconds of avatar video rendered per second, end to end from speech audio in to
frame out, one session, unpaced; each figure is the slowest of three quiet runs on the published
release. At 1.0× or more an avatar holds a live conversation.

The full method is at [docs.bithuman.ai/performance/method](https://docs.bithuman.ai/performance/method).
Rows marked "held 10 min" are the same measure held for a sustained run.

Browser rows. In Chrome on an Apple M4 with WebGPU: Essence 2 1.7× real time, Expression 2 1.9×
real time. This is the engine's render speed in the tab, not the frame rate a visitor sees.

## The table

Generated from `data/performance.csv` (source file generated 2026-09-29, fetched 2026-09-30).

| Runs on | Hardware | Essence 2 | Expression 2 | Release | Measured |
|---|---|---|---|---|---|
| Cloud API · GPU | NVIDIA RTX 4090 | 4.16× | 17.0× | cloud API | 2026-09-23 to 2026-09-27 |
| Cloud API · Apple silicon | Apple M4 Max | 2.84× | 5.55× | cloud API | 2026-09-23 to 2026-09-26 |
| Cloud API · CPU | x86 server CPU | 1.12× | 1.35× | cloud API | 2026-09-24 to 2026-09-25 |
| macOS · CLI | Apple M4 | 4.24× | 8.4× | CLI 2.8.1 | 2026-09-27 |
| macOS · Python | Apple M4 | 6.96× | 8.45× | bithuman 2.11.12 | 2026-09-25 |
| macOS · Swift package | Apple M4 | 4.8× | 8.85× | Swift package 2.15.0 | 2026-09-24 |
| Linux · CLI | Intel Core i7-13700F (x86_64) | 2.0× | 2.2× | CLI 2.8.1 | 2026-09-27 |
| Linux · Python | Intel Core i7-13700F (x86_64) | 1.96× | 2.35× | bithuman 2.11.13 | 2026-09-26 |
| iPhone · Swift package | iPhone 15 | 2.16× | 5.55× | Swift package 2.17.3 / Swift package 2.18.0 | 2026-09-27 |
| Android | Samsung Galaxy S25+ | 2.08× | 2.4× | essence2-android 0.7.0 / expression2-android 0.4.10 | 2026-09-23 to 2026-09-25 |
| Web browser (WebGPU) | Chrome on Apple M4 | 1.72× | 1.95× | web viewer | 2026-09-27 |
| iPhone · Swift package · held 10 min | iPhone 15 | 1.32× | 5.15× | Swift package 2.15.0 | 2026-09-25 |
| Android · held 10 min | Samsung Galaxy S25+ | 1.48× | 2.2× | essence2-android 0.8.1 / expression2-android 0.5.2 | 2026-09-27 |
| Web browser (WebGPU) · held 10 min | Chrome on Apple M4 | 2.16× | 2.05× | web viewer | 2026-09-25 to 2026-09-27 |

The web rows are the engine's render speed in the tab, not the frame rate a visitor sees.

## Files

| Path | What it is |
|---|---|
| `data/performance.csv` | One row per published configuration and model. |
| `data/performance.json` | The docs `performance.json` as fetched, wrapped with `source_url`, `fetched` (date), `generated` and the `sha256` of the fetched bytes. |
| `scripts/regen.py` | Re-fetches `performance.json` and rewrites both data files. Python 3 standard library only; it makes no renders. |
| `tests/` | Tests for `regen.py` against a fixture. |

CSV columns:

| Column | Meaning |
|---|---|
| `row_id` | Configuration id in the docs file (`linux-cpu`, `iphone-15`, ...). |
| `runs_on` | Platform and SDK or runtime, as labelled on the docs page. |
| `hardware` | The device or chip measured. |
| `model` | `essence-2` or `expression-2`. |
| `x_realtime` | Seconds of avatar video rendered per second (see above). |
| `realtime` | `true` when `x_realtime` is 1.0 or more. |
| `sustained` | `true` for the 10-minute held runs. |
| `release` | The published release measured. |
| `measured_on` | Measurement date (YYYY-MM-DD). |
| `clip_seconds` | Length of the speech clip rendered. |

The CSV leaves out the frame-rate and memory fields; `data/performance.json` keeps every field of
the source file.

## Regenerate

```sh
python3 scripts/regen.py            # fetch docs.bithuman.ai/performance.json, rewrite data/
python3 scripts/regen.py --check    # exit 1 if data/ is out of date; writes nothing
python3 -m unittest discover -s tests -v
```

An unchanged source file leaves `data/` untouched, so re-runs do not create noise commits.

## How to cite

Cite the row you use with its device, release and date, and link the source page. For example:

> On a Linux PC with no GPU (Intel Core i7-13700F, CLI): Essence 2 2.0× real time, Expression 2
> 2.2× real time. Source: bitHuman Team, avatar-speed, data generated 2026-09-29,
> https://docs.bithuman.ai/performance

Quote a figure with the device it was measured on; one device's number does not carry over to
another. When you quote a browser figure, add: "This is the engine's render speed in the tab, not
the frame rate a visitor sees."

Machine-readable citation metadata is in `CITATION.cff`.

## Licenses

- Code (`scripts/`, `tests/`): Apache License 2.0, see `LICENSE`.
- Data (`data/`): Creative Commons Attribution 4.0 International (CC BY 4.0), see `DATA-LICENSE`.
  Attribute "bitHuman Team" and link https://docs.bithuman.ai/performance.
