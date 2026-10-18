# Focus Sprint 🎯

An interactive Python script for Windows that generates binaural or monaural beats with background noise to enhance focus during work sessions.

## ✨ Features

- **10 Evidence-Based Activity Presets**: Choose from activities like Programming, Studying, Writing, and Meditation, each with a recommended binaural frequency (Gamma, Beta, Alpha, Theta).
- **Local Audio Generation**: Creates a 30-minute WAV file locally using `binaural-generator`. No external services required.
- **Seamless Looping**: Plays the generated audio on loop using `pygame.mixer`, without opening an external media player.
- **Pomodoro-Style Timers**: Integrates with `FocusCLI` (and optionally `Samaya`) to manage work sessions.
- **Native Windows Notifications**: Sends a toast notification and a popup when a session is complete.
- **Persistent Configuration**: Remembers your last activity and reuses generated WAV files if the settings match.
- **Headphone Check**: Automatically recommends monaural beats if you don't have headphones, as binaural beats require them.

## 🚀 Quick Start

### Prerequisites

- **Windows 10 or 11**
- **Python 3.10+** (Make sure to check "Add python.exe to PATH" during installation)

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/YOUR-USERNAME/focus-sprint.git
    cd focus-sprint
    ```

2.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Usage

Run the script from your terminal:

```bash
python sprint_focus.py
```

Follow the on-screen prompts to:

1.  Select an activity (e.g., 1 for Programming).
2.  Confirm or adjust the recommended frequency, beat type, and background noise.
3.  Choose your session duration.
4.  Start the sprint.

The script will handle audio generation, playback, and timers automatically.

## 🧠 Scientific Background

This tool is inspired by research on brainwave entrainment. Different frequency ranges are associated with different cognitive states:

| State                  | Frequency | Brainwave | Use Case                            |
| :--------------------- | :-------- | :-------- | :---------------------------------- |
| **Hyperfocus**         | 40 Hz     | Gamma     | Complex programming, deep debugging |
| **Sustained Focus**    | 15–25 Hz  | Beta      | Regular work, writing code          |
| **Relaxed Flow**       | 10–12 Hz  | Alpha     | Design, architecture, creativity    |
| **Meditation / Reset** | 4–8 Hz    | Theta     | Breaks between sprints              |

> **Note:** The scientific evidence on binaural beats is mixed. This project is intended as a personal productivity and wellness experiment, not as a medical device. For a deeper dive, see:
>
> - Basu et al. (2023) meta-analysis on binaural beats and memory/attention.
> - Engelbregt et al. (2021) comparing binaural and monaural beats.

## 📝 Notes & Limitations

- The script is designed for **Windows** and uses native Windows notification APIs.
- The generated WAV file is saved in your user home directory (`~`) and is reused across sessions if the configuration is identical.
- The `.yaml` configuration file is temporary and is deleted after each session.
- Volume levels for the binaural beat and background noise are fixed at 40% and 15%, respectively. You can adjust these constants at the top of `sprint_focus.py`.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
