# YouTube Watch Later Sorter 🎬

A Streamlit web application that helps you manage your YouTube "Watch Later" playlist (or any other playlist). It allows you to sort videos by duration, view them in a clean interface, and even filter by name.

## Features

-   **Sort by Duration**: Easily find short videos to fill a quick break or long ones for a deep dive.
-   **Clean UI**: A "premium" dark-mode interface for browsing your videos.
-   **Playlist Support**: Fetch videos from your YouTube playlists (requires sign-in).
-   **Watch Later Workaround**: Includes a manual workaround for YouTube's API restrictions on the "Watch Later" playlist privacy.

## Prerequisites

-   Python 3.8 or higher.
-   A Google account.

## Installation & Local Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/youtube-sorter.git
    cd youtube-sorter
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Local Configuration (.streamlit/secrets.toml)**:
    *   Create a folder named `.streamlit` in the root directory.
    *   Create a file inside it named `secrets.toml`.
    *   Add your Google OAuth credentials (see below section on how to get them):
        ```toml
        [client_oauth]
        client_id = "YOUR_CLIENT_ID"
        client_secret = "YOUR_CLIENT_SECRET"
        redirect_uri = "http://localhost:8501" 
        ```

5.  **Run the app:**
    ```bash
    streamlit run streamlit_app.py
    ```

## ☁️ Deploying to Streamlit Cloud

1.  Push your code to GitHub.
2.  Go to [Streamlit Cloud](https://share.streamlit.io/).
3.  Click **New app** and select your repository.
4.  **Before clicking Deploy**, click on **Advanced Settings** -> **Secrets**.
5.  Paste your TOML configuration into the text area:
    ```toml
    [client_oauth]
    client_id = "YOUR_CLIENT_ID"
    client_secret = "YOUR_CLIENT_SECRET"
    redirect_uri = "https://<your-app-name>.streamlit.app"
    ```
    *Note*: You must update `redirect_uri` to match your actual deployed app URL.

## 🔑 Getting Google OAuth Credentials

To use this app, you need a Google Cloud Project with the YouTube Data API enabled.

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  **Create a New Project**.
3.  **Enable YouTube Data API v3**:
    *   Library -> Search "YouTube Data API v3" -> Enable.
4.  **Configure OAuth Consent Screen**:
    *   **User Type**: External.
    *   **Test Users**: Add your email address. This is required for the app to work in testing mode.
5.  **Create Credentials**:
    *   Credentials -> Create Credentials -> **OAuth client ID**.
    *   **Application type**: **Web application** (NOT Desktop).
    *   **Authorized redirect URIs**:
        *   For Local: `http://localhost:8501`
        *   For Cloud: `https://<your-app-name>.streamlit.app` (Add both if needed).
    *   Click **Create**.
6.  Copy the **Client ID** and **Client Secret** and paste them into your `secrets.toml` or Streamlit Cloud Secrets.

## Troubleshooting

-   **Login Loop**: If clicking "Sign in" just reloads the page without logging you in, ensure your `redirect_uri` is correct and traffic is not being blocked.

## 🌍 Making it Available to Everyone

By default, your Google Cloud Project is in **Testing** mode, meaning only users you manually add to the "Test Users" list can log in.

To let **anyone** log in:
1.  Go to **APIs & Services** > **OAuth consent screen**.
2.  Click the button to **Publish App** (push to Production).
3.  **Note**: Since your app uses the `youtube.readonly` scope, Google may require a verification process if you want to remove the "Unverified App" warning screen.
    *   **Without Verification**: Users will see a warning ("Google hasn't verified this app"). They can click **Advanced** -> **Go to 'App Name' (unsafe)** to use it. This is usually fine for personal tools shared with friends.
    *   **With Verification**: You submit a video demo to Google to prove you aren't doing anything malicious. This takes time.

### Privacy Note
This app works by authenticating the user in *their* browser session.
-   User A logs in -> They see **User A's** playlists.
-   User B logs in -> They see **User B's** playlists.
-   You (the host) **cannot** see their data, and they cannot see yours. Streamlit isolates each user's session.
