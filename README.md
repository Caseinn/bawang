## Bawang — Anime Streaming TUI For Samehadaku

**Bawang** Is A **Python-Based CLI/TUI Application** That Lets Users **Search Anime On Samehadaku And Stream Episodes Directly** From The Terminal.
It Uses A **Rich-Powered Terminal UI** And Launches Playback In An **External Media Player** Such As **mpv** Or **ffplay**.

> 🎯 **Stream-Only By Design** — Bawang Does **Not Download** Or Permanently Store Any Video Files.

---

## Core Flow

1. **Search**
   The User Enters An Anime Title → Bawang Sends A Request To Samehadaku’s Search Endpoint.

2. **Results**
   A List Of Matching Anime Titles Is Displayed → The User Selects One.

3. **Episodes**
   Bawang Fetches And Lists Available Episodes → The User Selects An Episode.

4. **Player Options**
   Streaming Links Are Resolved From The Episode Page → Available Qualities / Hosts Are Shown.

5. **Playback**
   The Selected Stream URL Is Opened In **mpv** Or **ffplay**.

---

## How It Works (Technical Overview)

### Scraper

* Fetches HTML Pages Using **httpx**.
* Falls Back To **cloudscraper** Or **requests** To Bypass:

  * HTTP 403
  * Basic Anti-Bot Protection
* Parses Pages Using **BeautifulSoup**:

  * Search Result Pages
  * Anime Detail Pages
  * Episode Pages

---

### Resolver

* Extracts **Direct Video URLs** (`.mp4` / `.m3u8`) From Episode Pages.
* Supports Dynamically Loaded Players By Calling:

  * `admin-ajax.php` To Retrieve Embedded Player HTML.
* Handles Multiple Embed Types:

  * **Blogger / Blogspot** (`VIDEO_CONFIG`)
  * Iframe-Based Players
* Applies Heuristics To Locate Real Media URLs.
* Ranks Resolved Links By **Preferred Hosts** (E.g. `googlevideo`, `blogspot` First).

---

### Player

* Automatically Detects **mpv** Or **ffplay** In The System `PATH`.
* Launches The Selected Player With:

  * Buffering And Cache Arguments
  * Stream-Optimized Settings
* No File Is Written To Disk.

---

### UI (TUI)

* Built With **Rich** For Tables, Panels, And Layout.

* Screen-Based Flow:

  * Search
  * Results
  * Episodes
  * Quality / Host Selection

* Input Handling:

  * Numeric Selection
  * Optional Arrow-Key Navigation Via `prompt_toolkit`
  * Windows-Compatible Fallback For Input Handling

---

## Project Structure

```
src/bawang/
├── cli.py / __main__.py      # Application Entrypoints
├── config.py                # Base URL, Timeouts, mpv Args, Preferred Hosts
├── models.py                # Dataclasses (SearchResult, Episode, QualityOption, VideoLink)

├── tui/
│   ├── app.py               # Main TUI Orchestrator
│   ├── screens.py           # Search / Results / Episodes / Quality Screens
│   ├── widgets.py           # Rich Tables, Panels, Layouts
│   └── events.py            # Input Handling (Numeric + Arrow Keys)

├── scraper/
│   ├── search.py            # Search Result Parsing
│   ├── episodes.py          # Episode List Parsing (Normalized To “Episode X”)
│   └── common.py            # Fetch Helpers And URL Normalization

├── resolver/
│   ├── resolve.py           # Core Link Resolution Logic
│   ├── heuristics.py        # Media URL Detection From HTML
│   └── hosts/               # Host-Specific Embed Parsers

├── player/
│   ├── detect.py            # Detect mpv / ffplay Availability
│   ├── mpv.py               # mpv Launcher
│   └── ffplay.py            # ffplay Launcher

└── utils/
    ├── net.py               # HTTP Client With Fallback Strategy
    └── text.py              # Text Helpers (Truncate, Normalize)
```

---

## How To Use

### From Source (Python)

1. Clone The Repo

```powershell
git clone https://github.com/caseinn/bawang.git
cd bawang
```

2. Install Dependencies (Editable)

```powershell
python -m pip install -e .
```

3. Install A Media Player

* mpv (Recommended) Or ffplay Must Be In PATH.
* Windows Quick Install:

```powershell
winget install mpv
```

4. Run

```powershell
bawang
# or
python -m bawang
```

---

### From Prebuilt Exe (Windows)

1. Download `bawang.exe` From The GitHub Releases Page.
2. Run It Directly:

```powershell
.\bawang.exe
```

3. Optional: Add To PATH So You Can Run `bawang` From Anywhere.

```powershell
setx PATH "$env:PATH;C:\path\to\folder"
```

---

## Why Bawang Exists

Bawang Is Built For Users Who Want A **Fast, Minimal, Keyboard-Driven** Way To Watch Anime Without:

* Opening A Browser
* Dealing With Ads
* Switching Between Mouse And Keyboard

> Think Of It As **mpv + Samehadaku + A Clean Terminal UI** — Nothing More, Nothing Less.

---

## 📄 License

MIT License — Free To Use, Adapt, Or Share For Personal, Educational, Or Community Projects.

> Created By **[Dito Rifki Irawan](https://instagram.com/ditorifkii)** (@caseinn)

---

## ❤️ Support

If This App Makes Watching Anime Easier:
* ⭐ Star The Repo
