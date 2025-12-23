# YouTube Watch Later Sorter 🎬

A Streamlit web application that helps you manage your YouTube "Watch Later" playlist (or any other playlist). It allows you to sort videos by duration, view them in a clean interface, and even filter by name.

## Features

-   **Sort by Duration**: Easily find short videos to fill a quick break or long ones for a deep dive.
-   **Clean UI**: A "premium" dark-mode interface for browsing your videos.
-   **Playlist Support**: Fetch videos from your YouTube playlists.
-   **Watch Later Workaround**: Includes a manual workaround for YouTube's API restrictions on the "Watch Later" playlist privacy.

## Prerequisites

-   Python 3.8 or higher.
-   A Google account.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/youtube-sorter.git
    cd youtube-sorter
    ```

2.  **Create a virtual environment (optional but recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 🔑 Configuration (Important!)

To use this app, you need to set up a project in the Google Cloud Console to get your own `client_secret.json`. This file is **private** and should not be shared or committed to GitHub.

### Step-by-Step Guide to Get `client_secret.json`:

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  **Create a New Project**: Click the project dropdown at the top and select "New Project". Give it a name (e.g., "YouTube Sorter").
3.  **Enable YouTube Data API v3**:
    *   In the sidebar, go to **APIs & Services** > **Library**.
    *   Search for "YouTube Data API v3".
    *   Click on it and click **Enable**.
4.  **Configure OAuth Consent Screen**:
    *   Go to **APIs & Services** > **OAuth consent screen**.
    *   Select **External** user type and click **Create**.
    *   Fill in the "App Information" (App name, email). You can skip the rest for personal use.
    *   **Scopes**: Add `.../auth/youtube.readonly` if prompted, or just save and continue.
    *   **Test Users**: **Crucial!** Add your own Google email address here. Since the app is in "Testing" mode, only added users can log in.
5.  **Create Credentials**:
    *   Go to **APIs & Services** > **Credentials**.
    *   Click **Create Credentials** > **OAuth client ID**.
    *   Application type: **Desktop app**.
    *   Name: "YouTube Sorter Desktop".
    *   Click **Create**.
6.  **Download JSON**:
    *   You will see a dialog saying "OAuth client created".
    *   Click the **Download JSON** button (icon looks like a download arrow).
    *   Save this file as `client_secret.json` in the root directory of this project (same folder as `main.py`).

## Usage

1.  Run the Streamlit app:
    ```bash
    streamlit run main.py
    ```

2.  The app will open in your browser.
3.  Click **Sign in with Google**.
    *   *Note*: You might see a "Google hasn't verified this app" warning. This is normal for personal projects. Click "Advanced" -> "Go to (App Name) (unsafe)" to proceed.
4.  **Load Videos**:
    *   **For regular playlists**: Use the "API Fetch" tab, select a playlist, and click "Fetch".
    *   **For Watch Later**: Due to API privacy changes, you may need to use the "Paste Video IDs" tab. Follow the on-screen instructions to run a small script in your browser console on the YouTube Watch Later page to grab your video IDs.

## Troubleshooting

-   **Quota Exceeded**: The free tier of YouTube Data API has a daily limit. If you load too many videos, you might hit it.
-   **Authentication Error**: Delete the `client_secret.json` (if invalid) or ensure you added your email to "Test Users" in the Google Cloud Console.
