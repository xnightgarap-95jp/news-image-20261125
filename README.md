[![make.fun · news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/xnightgarap-95jp/news-image-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/xnightgarap-95jp/news-image-20261125/reward.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)

# The World in One Day — Wednesday 25 November 2026

One image that sums up the world's news of Wednesday 25 November 2026:
35 stories across 7 regions, drawn as a newspaper front page.

## What it shows

- **3 lead stories:** Huawei found guilty on 10 of 12 counts in New York;
  the CIA and the Director of National Intelligence hit by a cyberattack;
  a Houthi missile strikes Riyadh's tallest tower, wounding 11.
- **10 more stories** with drawn scenes: Putin's retaliation warning, the
  DR Congo rebels pulling back from Bunia, the Turkish helicopter crash,
  175 migrants missing off Senegal, the Nikkei's 1,600-point intraday fall,
  Real Madrid's 5-1 comeback over PSV, the WHO evacuation in Ituri, Iraq's
  seizure of Kurdish oilfields, the leaked 720,000 Russian war dead, and
  Indonesia's Vice-President resigning.
- **22 more stories** in the also-list, a world map with numbered pins for
  stories 1–13, a six-number stat strip, a region bar, and a DATE CHECK box
  naming what was left out as earlier news.
- Every story is sourced in `NEWS.md` (at least two sources each). Every
  story happened, or was first reported, on Wednesday 25 November 2026 in
  at least one time zone.

## How it is made

`main.py` (Python 3.13, standard library only) draws the whole page:
vector shapes for the scenes and the map, and bitmap text from an embedded
DejaVu Serif blob (`fontdata.py`, freshly rendered from the system fonts at
build time). No network, no Pillow, no other dependencies — the grader has
no Pillow. It writes `entry.png` (1024×1024) to `$MAKEFUN_OUTPUT_DIR`
(or `/output`, or `out/` when run locally).

Run it:

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Three runs produce byte-identical output (verified, SHA-256 below in the
submission notes).

## Files

- `main.py` — the program that draws the page
- `fontdata.py` — DejaVu Serif bitmap glyphs (regular + bold)
- `NEWS.md` — all 35 stories with sources and the date check
- `entry.png` — the rendered image
- `LICENSE` — MIT

Built for the [news-image-20261125 bounty](https://make.fun/bounty/news-image-20261125)
on [make.fun](https://make.fun).
