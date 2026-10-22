================================================================================
  ATTENTION TRACKER v1.0.0 — INSTALLATION & QUICK START GUIDE
================================================================================

Thank you for downloading Attention Tracker!
Attention Tracker uses your webcam and MediaPipe computer vision to watch your
eyes and automatically pause video playback when you look away, resuming when you
look back at your primary display.

--------------------------------------------------------------------------------
1. HOW TO INSTALL & LAUNCH
--------------------------------------------------------------------------------
STEP 1: EXTRACT THE ZIP ARCHIVE
  • Right-click "AttentionTracker-Windows.zip" and select "Extract All..."
  • Choose an extraction destination (for example: C:\Program Files\AttentionTracker,
    or a dedicated folder in your User profile / Documents).
  • IMPORTANT: Do NOT run AttentionTracker.exe directly from inside the ZIP file!
    It must be fully extracted so all dependent libraries in "_internal" can load.

STEP 2: LAUNCH THE APPLICATION
  • Open the extracted "AttentionTracker" folder.
  • Double-click "AttentionTracker.exe".

STEP 3: WINDOWS SMARTSCREEN WARNING (FIRST RUN)
  • Because Attention Tracker is a free, open-source community tool and is not
    signed with an expensive commercial code-signing certificate, Windows Defender
    SmartScreen may display a blue dialog:
      "Windows protected your PC"
  • To proceed:
      1. Click "More info" (underlined link).
      2. Click the "Run anyway" button that appears at the bottom.

STEP 4: CALIBRATE & START TRACKING
  • Choose your webcam from the camera dropdown in the control panel.
  • Click "🎯 Calibrate".
  • Look at your primary video monitor for 3 seconds.
  • Look at your secondary monitor for 3 seconds.
  • Click "▶ Start" — media tracking is now active!

--------------------------------------------------------------------------------
2. SYSTEM REQUIREMENTS
--------------------------------------------------------------------------------
• Operating System: Windows 10 (64-bit, Build 1903+) or Windows 11 (64-bit)
• Hardware: USB webcam or integrated laptop camera
• Supported Media Players:
    - Web Browsers: Google Chrome, Microsoft Edge, Brave, Opera (YouTube, Netflix, etc.)
    - Desktop Players: Spotify, VLC Media Player, Windows Media Player

--------------------------------------------------------------------------------
3. TROUBLESHOOTING
--------------------------------------------------------------------------------
• Camera Not Found: Ensure no other application (Zoom, Teams, OBS) is holding
  an exclusive lock on your camera.
• Media Doesn't Pause: Verify your media player supports Windows System Media
  Transport Controls (SMTC) or hardware media keys.
• High CPU Usage: The application runs MediaPipe at a light ~15-20% single-core
  usage at 30 FPS. You can adjust the FPS to 15 or 20 in settings for lower-spec PCs.

--------------------------------------------------------------------------------
4. LINKS & OPEN-SOURCE SUPPORT
--------------------------------------------------------------------------------
• Official Website & Live Simulator: https://shyammohanvis.github.io/attention-tracker/
• GitHub Repository: https://github.com/ShyamMohanvis/attention-tracker
• Bug Reports & Feedback: https://github.com/ShyamMohanvis/attention-tracker/issues
• License: MIT License
================================================================================
