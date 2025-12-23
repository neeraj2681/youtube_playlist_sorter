import streamlit as st
import os
import pandas as pd
import isodate
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# --- Configuration ---
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

# Allow OAuth over HTTP for local testing
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

st.set_page_config(
    page_title="Watch Later Sorter",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Styling ---
st.markdown("""
<style>
    .stApp {
        background-color: #0f1115;
        color: #ffffff;
    }
    .main-header {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        font-size: 3rem;
        background: linear-gradient(90deg, #FF4D4D, #ffffff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    .video-card {
        background-color: #181b21;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 0;
        overflow: hidden;
        transition: transform 0.2s;
        margin-bottom: 1rem;
    }
    .video-card:hover {
        transform: translateY(-5px);
        border-color: rgba(255, 77, 77, 0.5);
    }
    .video-content {
        padding: 1rem;
    }
    .video-title {
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
        color: #fff;
        text-decoration: none;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .video-meta {
        font-size: 0.85rem;
        color: #a1a1aa;
    }
    .duration-badge {
        background-color: #FF4D4D;
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- Functions ---

def get_auth_flow():
    """Constructs the OAuth flow from st.secrets."""
    if "client_oauth" not in st.secrets:
        st.error("Missing `client_oauth` in `st.secrets`. Please configure your secrets.toml.")
        st.stop()
    
    # Construct config dictionary from secrets
    client_config = {
        "web": {
            "client_id": st.secrets["client_oauth"]["client_id"],
            "client_secret": st.secrets["client_oauth"]["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [st.secrets["client_oauth"]["redirect_uri"]],
        }
    }
    
    return Flow.from_client_config(
        client_config=client_config,
        scopes=SCOPES,
        redirect_uri=st.secrets["client_oauth"]["redirect_uri"]
    )

def get_authenticated_service():
    """
    Authenticates the user using OAuth2 Web Flow.
    1. Checks for 'code' in URL (return from Google).
    2. If code, exchanges for credentials.
    3. If no code/creds, returns None (UI should show Login button).
    """
    
    # 1. Check for existing credentials in session
    if 'credentials' in st.session_state:
        return build('youtube', 'v3', credentials=st.session_state['credentials'])

    # 2. Check for Auth Code in URL (Redirect back from Google)
    query_params = st.query_params
    if "code" in query_params:
        code = query_params["code"]
        try:
            flow = get_auth_flow()
            flow.fetch_token(code=code)
            credentials = flow.credentials
            st.session_state['credentials'] = credentials
            
            # Clear the code from URL to prevent re-submission on refresh
            # Note: st.query_params are mutable in newer Streamlit versions, 
            # but currently st.query_params.clear() or rerunning works.
            # We'll just continue; the app will re-render with 'credentials' found.
            return build('youtube', 'v3', credentials=credentials)
        except Exception as e:
            st.error(f"Authentication failed: {e}")
            return None

    return None

def parse_iso_duration(duration_str):
    try:
        dur = isodate.parse_duration(duration_str)
        return dur.total_seconds()
    except:
        return 0

def format_duration(seconds):
    if seconds == 0: return "Live"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{int(h)}:{int(m):02d}:{int(s):02d}"
    else:
        return f"{int(m)}:{int(s):02d}"

def fetch_playlists(youtube):
    """Fetches the user's playlists."""
    playlists = [{'id': 'WL', 'title': 'Watch Later (Default)'}]
    
    try:
        request = youtube.playlists().list(
            part="snippet",
            mine=True,
            maxResults=50
        )
        while request:
            response = request.execute()
            for item in response['items']:
                playlists.append({
                    'id': item['id'],
                    'title': item['snippet']['title']
                })
            request = youtube.playlists().list_next(request, response)
            if len(playlists) > 50: break
    except Exception as e:
        st.error(f"Error fetching playlists: {e}")
        
    return playlists

def fetch_videos(youtube, playlist_id):
    """Fetches videos from a specific playlist."""
    videos = []
    
    # 1. Get Playlist Items
    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=playlist_id,
        maxResults=50
    )
    
    status_text = st.empty()
    status_text.text('Fetching videos...')
    
    while request:
        try:
            response = request.execute()
        except Exception as e:
            st.error(f"Error fetching playlist items: {e}")
            return []

        # We need to fetch video details to get duration (contentDetails)
        video_ids = [item['contentDetails']['videoId'] for item in response['items']]
        
        if video_ids:
            try:
                vid_request = youtube.videos().list(
                    part="snippet,contentDetails,statistics",
                    id=",".join(video_ids)
                )
                vid_response = vid_request.execute()
                
                for item in vid_response['items']:
                    dur_sec = parse_iso_duration(item['contentDetails'].get('duration', 'PT0S'))
                    videos.append({
                        'id': item['id'],
                        'title': item['snippet']['title'],
                        'thumbnail': item['snippet']['thumbnails'].get('medium', {}).get('url', ''),
                        'channel': item['snippet']['channelTitle'],
                        'duration_sec': dur_sec,
                        'duration_fmt': format_duration(dur_sec),
                        'view_count': int(item['statistics'].get('viewCount', 0))
                    })
            except Exception as e:
                st.warning(f"Could not fetch details for batch: {e}")

        request = youtube.playlistItems().list_next(request, response)
        status_text.text(f"Fetched {len(videos)} videos so far...")
        if len(videos) > 200: # Safety break
            break
    
    status_text.empty()
    return videos

# --- Main App Interface ---

st.markdown('<div class="main-header">Watch Later Sorter 🎬</div>', unsafe_allow_html=True)

if 'credentials' not in st.session_state:
    # Try to complete auth if query params are present
    service = get_authenticated_service()
    if service:
        # If successful (e.g. from code), rerun to clear URL
        st.query_params.clear()
        st.rerun()

    # If still not authenticated, show Login Button
    st.info("Please sign in to access your YouTube account.")
    
    # We can't put a button that opens a new tab/window directly in pure python logic easily without a link.
    # So we generate the URL and show a styled link.
    try:
        flow = get_auth_flow()
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        st.markdown(f"""
            <a href="{auth_url}" target="_self" style="
                display: inline-block;
                padding: 0.5em 1em;
                color: #FFFFFF;
                background-color: #FF4D4D;
                border-radius: 4px;
                text-decoration: none;
                font-weight: bold;
            ">Sign in with Google</a>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Could not generate login link: {e}")
else:
    # User is logged in
    col1, col2 = st.columns([3, 1])
    with col2:
         if st.button("Sign Out / Reset"):
            st.session_state.pop('credentials', None)
            st.session_state.pop('videos_df', None)
            st.rerun()

    service = build('youtube', 'v3', credentials=st.session_state['credentials'])
    
    # Tabs for different input methods
    tab1, tab2 = st.tabs(["📺 API Fetch (Playlists)", "📋 Paste Video IDs"])
    
    with tab1:
        # Playlist Selector
        playlists = fetch_playlists(service)
        playlist_options = {p['title']: p['id'] for p in playlists}
        
        col_a, col_b = st.columns([2, 1])
        with col_a:
            selected_playlist_name = st.selectbox("Select a Playlist", options=list(playlist_options.keys()))
            selected_playlist_id = playlist_options[selected_playlist_name]
        with col_b:
            sort_order_1 = st.radio("Sort Order", ["Shortest -> Longest", "Longest -> Shortest"], key="sort1")

        if st.button("Fetch & Sort Playlist"):
            data = fetch_videos(service, selected_playlist_id)
            if data:
                df = pd.DataFrame(data)
                st.session_state['videos_df'] = df
                st.session_state['current_sort'] = sort_order_1
                st.session_state['current_page'] = 0  # Reset page on new fetch
            else:
                st.warning(f"No videos found in '{selected_playlist_name}'. If this is 'Watch Later', the API is likely blocked. Please try the 'Paste Video IDs' tab instead.")

    with tab2:
        st.markdown("""
        **Workaround for Watch Later Privacy:**
        1. Go to your [Watch Later](https://www.youtube.com/playlist?list=WL) page.
        2. Scroll down to load all videos.
        3. Open Developer Console (`F12` or `Cmd+Opt+J`).
        4. Paste this script to copy all IDs:
        ```javascript
        copy(Array.from(document.querySelectorAll('ytd-playlist-video-renderer a#video-title')).map(a => a.href).join('\\n'))
        ```
        5. Paste the result below.
        """)
        pasted_text = st.text_area("Paste Links or IDs here", height=150)
        sort_order_2 = st.radio("Sort Order", ["Shortest -> Longest", "Longest -> Shortest"], key="sort2")
        
        if st.button("Process Pasted Videos"):
            # Extract IDs using simple regex
            import re
            # Matches youtube.com/watch?v=ID or youtu.be/ID or just ID (11 chars)
            # We'll look for 11 char strings that look like IDs if flexible, 
            # but picking out URL patterns is safer.
            video_ids = []
            
            # Simple splitter
            tokens = pasted_text.split()
            for token in tokens:
                # Try to find ?v=...
                match = re.search(r'v=([a-zA-Z0-9_-]{11})', token)
                if match:
                    video_ids.append(match.group(1))
                    continue
                # Try short url
                match = re.search(r'youtu\.be/([a-zA-Z0-9_-]{11})', token)
                if match:
                    video_ids.append(match.group(1))
                    continue
            
            if not video_ids:
                st.error("No valid YouTube video IDs found in the text.")
            else:
                # Remove duplicates
                video_ids = list(set(video_ids))
                st.info(f"Found {len(video_ids)} unique video IDs. Fetching details...")
                
                # Fetch details manually
                videos = []
                batch_size = 50
                for i in range(0, len(video_ids), batch_size):
                    batch = video_ids[i:i+batch_size]
                    try:
                        vid_request = service.videos().list(
                            part="snippet,contentDetails,statistics",
                            id=",".join(batch)
                        )
                        vid_response = vid_request.execute()
                        for item in vid_response['items']:
                            dur_sec = parse_iso_duration(item['contentDetails'].get('duration', 'PT0S'))
                            videos.append({
                                'id': item['id'],
                                'title': item['snippet']['title'],
                                'thumbnail': item['snippet']['thumbnails'].get('medium', {}).get('url', ''),
                                'channel': item['snippet']['channelTitle'],
                                'duration_sec': dur_sec,
                                'duration_fmt': format_duration(dur_sec),
                                'view_count': int(item['statistics'].get('viewCount', 0))
                            })
                    except Exception as e:
                        st.error(f"Error fetching batch: {e}")
                
                if videos:
                    df = pd.DataFrame(videos)
                    st.session_state['videos_df'] = df
                    st.session_state['current_sort'] = sort_order_2
                    st.session_state['current_page'] = 0  # Reset page on new fetch
                else:
                    st.error("Could not fetch video details.")


    if 'videos_df' in st.session_state:
        df = st.session_state['videos_df']
        
        # Determine sort order
        # Fallback to whatever was last set or default
        sort_order = st.session_state.get('current_sort', "Shortest -> Longest")
        
        
        # --- Search & Sort Controls ---
        col_search, col_sort = st.columns([3, 1])
        with col_search:
            search_query = st.text_input("Search Videos", placeholder="Filter by title...", key="search_query")
        
        # Apply Search Filter
        if search_query:
            # Case-insensitive containment check
            df = df[df['title'].str.contains(search_query, case=False, na=False)]
            
            # Reset pagination if search changes (handled by session state or simple logic)
            # We need to detect if search changed. A simple way is to check if the filtered length
            # is different or just reset to 0 if we change the query.
            # However, since streamlit reruns on input change, we can just check a stored previous query.
            if st.session_state.get('last_search_query') != search_query:
                st.session_state['current_page'] = 0
                st.session_state['last_search_query'] = search_query
        
        # Apply Sort (on filtered or full df)
        ascending = (sort_order == "Shortest -> Longest")
        df = df.sort_values(by='duration_sec', ascending=ascending).reset_index(drop=True)

        
        # --- Pagination Logic ---
        if 'current_page' not in st.session_state:
            st.session_state['current_page'] = 0
            
        col_p1, col_p2 = st.columns([1, 3])
        with col_p1:
            items_per_page = st.selectbox("Videos per page", [10, 20, 50, 100], index=0)
        
        total_videos = len(df)
        total_pages = (total_videos - 1) // items_per_page + 1
        
        # Ensure current_page is valid
        if st.session_state['current_page'] >= total_pages:
            st.session_state['current_page'] = max(0, total_pages - 1)
            
        current_page = st.session_state['current_page']
        start_idx = current_page * items_per_page
        end_idx = min(start_idx + items_per_page, total_videos)
        
        # Slice the dataframe
        current_df = df.iloc[start_idx:end_idx]
        
        st.success(f"Found {total_videos} videos. Showing {start_idx + 1}-{end_idx} ({sort_order}).")
        
        # Navigation Controls (Top)
        col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
        with col_nav1:
            if st.button("Previous", disabled=(current_page == 0)):
                st.session_state['current_page'] -= 1
                st.rerun()
        with col_nav2:
             st.markdown(f"<div style='text-align: center; padding-top: 10px;'>Page {current_page + 1} of {total_pages}</div>", unsafe_allow_html=True)
        with col_nav3:
            if st.button("Next", disabled=(current_page >= total_pages - 1)):
                st.session_state['current_page'] += 1
                st.rerun()

        # Debug / List View
        with st.expander("View as List (Debug)"):
            st.dataframe(current_df[['title', 'duration_fmt', 'duration_sec', 'channel']])

        # Grid Layout
        # We use native columns now to support embedded players
        
        # CSS to style the native columns like cards
        st.markdown("""
        <style>
            /* Removed previous card styling hack since we are building full custom cards now */

        </style>
        """, unsafe_allow_html=True)
        
        cols = st.columns(3)
        
        cols = st.columns(3)
        for idx, row in current_df.iterrows():
            with cols[idx % 3]:
                # st.video replacement with custom iframe for better tracking support
                # enablejsapi=1 and origin are key for tracking
                video_url = f"https://www.youtube.com/embed/{row['id']}?enablejsapi=1&origin=http://localhost:8501"
                
                st.markdown(f"""
                <div class="video-card">
                    <iframe 
                        width="100%" 
                        height="200" 
                        src="{video_url}" 
                        title="YouTube video player" 
                        frameborder="0" 
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                        allowfullscreen
                        style="border-radius: 10px 10px 0 0;">
                    </iframe>
                    <div class="video-content">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                            <span class="duration-badge">{row['duration_fmt']}</span>
                            <span class="video-meta" title="{row['duration_sec']} sec">#{start_idx + idx + 1}</span>
                        </div>
                        <a href="https://www.youtube.com/watch?v={row['id']}" target="_blank" class="video-title" title="{row['title']}">
                            {row['title']}
                        </a>
                        <div class="video-meta">by {row['channel']}</div>
                        <div style="margin-top: 10px; text-align: right;">
                             <a href="https://www.youtube.com/watch?v={row['id']}" target="_blank" style="font-size: 0.8rem; color: #FF4D4D; text-decoration: none;">
                                Open in YouTube ↗
                             </a>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        
        # Navigation Controls (Bottom - for convenience)
        st.write("---")
        col_b_nav1, col_b_nav2, col_b_nav3 = st.columns([1, 2, 1])
        with col_b_nav1:
            if st.button("Previous ", key="prev_bottom", disabled=(current_page == 0)):
                st.session_state['current_page'] -= 1
                st.rerun()
        with col_b_nav2:
             st.markdown(f"<div style='text-align: center; padding-top: 10px;'>Page {current_page + 1} of {total_pages}</div>", unsafe_allow_html=True)
        with col_b_nav3:
            if st.button("Next ", key="next_bottom", disabled=(current_page >= total_pages - 1)):
                st.session_state['current_page'] += 1
                st.rerun()

