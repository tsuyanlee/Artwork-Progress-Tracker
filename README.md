# Artwork Progress Tracker

A GitHub-style contribution calendar for tracking creative work inside a folder.  
It visualizes daily file additions and modifications as a heatmap, helping you see your consistency over time.

Suitable for artists, designers, writers, or developers who want a visual productivity log without using Git.

---

## Features

- GitHub-style calendar heatmap
- Tracks file creation and modification times
- Darker squares indicate more work done on that day
- Hover to see daily statistics
- Click a day to see files modified with exact timestamps
- Track any folder
- Automatic rescanning (no file watchers required)
- Charts:
  - Pie chart (active vs inactive days)
  - Line chart (daily contributions)
  - Bar chart (files by extension)
- Zoom control with percentage display
- Export calendar as PNG
- Persistent tracking using `tracking.json`
- Safe tracking (no double counting, no refresh flicker)

---

## How It Works

- The app scans a selected folder at intervals
- Each file keeps:
  - Last modification time
  - Total modification count
  - Full modification history
- Each modification contributes +1 to the calendar day
- Timestamp comparison prevents:
  - Duplicate counts
  - Restart inflation
  - File system timestamp jitter

The behavior matches how GitHub contribution calendars work — snapshot based, not live event tracking.

---

## Requirements

- Python 3.9 or newer
- Standard library only
- Optional (for PNG export):
  ```bash
  pip install pillow

## License

The MIT License (MIT)
Copyright © 2025 DaveDrafts

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
