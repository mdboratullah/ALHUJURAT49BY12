ALHUJURAT49BY12 — Local Privacy & Access Control Dashboard
​Developed by: Md Borat Ullah
Stack: Python 3, Flask, JSON Storage, Termux / Linux Compatible
​1. What is ALHUJURAT49BY12?
​ALHUJURAT49BY12 is a lightweight, self-hosted Python Flask web dashboard designed for local domain privacy inspection, custom tracker flagging, user access management (ON/OFF permission toggles), live activity logging, and Tor control (NEWNYM) signaling.
​Rather than relying on opaque third-party cloud tools, this application keeps all logic, user accounts, and logs directly on your own local machine or Android device (via Termux).
​2. Key Features & Capabilities
​Authentication & Role-Based Access Control:
​Password-protected Admin and User login portal.
​Create new user accounts, update the Admin password, delete users, and toggle individual user access permissions (ON / OFF) in real time.
​Live Access & Activity Audit Logs:
​Tracks login attempts, unauthorized access blocks, permission changes, and dashboard activity in a structured log table (access_logs.json).
​Single & Bulk Domain Privacy Check:
​Inspect individual URLs or domains (with DNS and HTTP Header checks) as well as bulk domain lists to identify known trackers or flagged risks.
​Custom Flagged Domains Manager:
​Maintain a personalized watchlist of domains with custom risk levels and notes.
​History Search, Filtering & Export:
​Search and filter past domain check history and export reports cleanly as .TXT or .JSON files.
​Tor Control (9051) Circuit Rotation:
​Connects to a local Tor control port (127.0.0.1:9051) to send NEWNYM circuit rotation signals (with clear status reporting when Tor is active or in fallback mode).
​3. Who Benefits & Why Use It?
​Privacy-Conscious Individuals & Researchers: Quickly inspect suspicious links or domains for trackers and headers, maintain a custom watchlist, and export findings without sending queries to external analytics platforms.
​Small Teams & Administrators: Manage who can access the local dashboard using per-user ON/OFF toggles and audit every login or action through built-in activity logs.
​Developers & Termux Learners: A practical, self-contained foundation for running a secure Flask control panel with JSON persistence, Tor socket signaling, and clean backup workflows.
​Important Scope & Limitations
​This is a local control panel and inspection tool running on 127.0.0.1:8080.
​It is not a system-wide firewall, antivirus, or full-device VPN/proxy that automatically blocks or hides traffic from other apps on your phone.
​4. Installation & How to Run (Termux / Linux)
​Prerequisites
​Python 3 (python3)
​Flask (pip install flask)
​(Optional) Tor daemon configured with ControlPort 9051 if you want live NEWNYM circuit rotation.
​Quick Setup Steps
