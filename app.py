#Import Necessary Dependencies
import streamlit as st
from twelvelabs import TwelveLabs
import requests
import os
from dotenv import load_dotenv


load_dotenv()


# Get the API Key from the Dashboard - https://playground.twelvelabs.io/dashboard/api-key
API_KEY = os.getenv("API_KEY")

# Create the INDEX ID as specified in the README.md and get the INDEX_ID
INDEX_ID = os.getenv("INDEX_ID")

client = TwelveLabs(api_key=API_KEY)

# Background Setting of the Application
page_element = """
<style>
[data-testid="stAppViewContainer"] {
    background-image: url("https://wallpapercave.com/wp/wp3589963.jpg");
    background-size: cover;
}
[data-testid="stHeader"] {
    background-color: rgba(0,0,0,0);
}
[data-testid="stToolbar"] {
    right: 2rem;
    background-image: url("");
    background-size: cover;
}
</style>
"""
st.markdown(page_element, unsafe_allow_html=True)


# Classes to classify the video into, there are categories name and 
# the prompts which specifc finds that factor to label that category

@st.cache_data
def get_initial_classes():
    return [
        {"name": "AquaticSports", "prompts": ["swimming competition", "diving event", "water polo match", "synchronized swimming", "open water swimming"]},
        {"name": "AthleticEvents", "prompts": ["track and field", "marathon running", "long jump competition", "javelin throw", "high jump event"]},
        {"name": "GymnasticsEvents", "prompts": ["artistic gymnastics", "rhythmic gymnastics", "trampoline gymnastics", "balance beam routine", "floor exercise performance"]},
        {"name": "CombatSports", "prompts": ["boxing match", "judo competition", "wrestling bout", "taekwondo fight", "fencing duel"]},
        {"name": "TeamSports", "prompts": ["basketball game", "volleyball match", "football (soccer) match", "handball game", "field hockey competition"]},
        {"name": "CyclingSports", "prompts": ["road cycling race", "track cycling event", "mountain bike competition", "BMX racing", "cycling time trial"]},
        {"name": "RacquetSports", "prompts": ["tennis match", "badminton game", "table tennis competition", "squash game", "tennis doubles match"]},
        {"name": "RowingAndSailing", "prompts": ["rowing competition", "sailing race", "canoe sprint", "kayak event", "windsurfing competition"]}
    ]

# Session State for the custom classes 
def get_custom_classes():
    if 'custom_classes' not in st.session_state:
        st.session_state.custom_classes = []
    return st.session_state.custom_classes

# Utitlity Function to add the custom classes in app
def add_custom_class(name, prompts):
    custom_classes = get_custom_classes()
    custom_classes.append({"name": name, "prompts": prompts})
    st.session_state.custom_classes = custom_classes
    st.session_state.new_class_added = True

# Utitlity Function to classify all the videos in the specified Index
def classify_videos(selected_classes):
    return client.classify.index(
        index_id=INDEX_ID,
        options=["visual"],
        classes=selected_classes,
        include_clips=True
    )

# To get the video urls from the resultant video id
def get_video_urls(video_ids):
    base_url = f"https://api.twelvelabs.io/v1.2/indexes/{INDEX_ID}/videos/{{}}"
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    video_urls = {}

    for video_id in video_ids:
        try:
            response = requests.get(base_url.format(video_id), headers=headers)
            response.raise_for_status()
            data = response.json()
            if 'hls' in data and 'video_url' in data['hls']:
                video_urls[video_id] = data['hls']['video_url']
            else:
                st.warning(f"No video URL found for video ID: {video_id}")
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to get data for video ID: {video_id}. Error: {str(e)}")

    return video_urls

# Utitlity Function to Render the Video by the resultant video url
def render_video(video_url):
    hls_player = f"""
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <div style="width: 100%; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
        <video id="video" controls style="width: 100%; height: auto;"></video>
    </div>
    <script>
      var video = document.getElementById('video');
      var videoSrc = "{video_url}";
      if (Hls.isSupported()) {{
        var hls = new Hls();
        hls.loadSource(videoSrc);
        hls.attachMedia(video);
        hls.on(Hls.Events.MANIFEST_PARSED, function() {{
          video.pause();
        }});
      }}
      else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
        video.src = videoSrc;
        video.addEventListener('loadedmetadata', function() {{
          video.pause();
        }});
      }}
    </script>
    """
    st.components.v1.html(hls_player, height=300)


# Main Function
def main():

    # Basic Markdown Setup for the Application
    st.markdown("""
    <style>
    .big-font {
        font-size: 40px !important;
        font-weight: bold;
        color: #000000;
        text-align: center;
        margin-bottom: 30px;
    }
    .subheader {
        font-size: 24px;
        font-weight: bold;
        color: #424242;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .stButton>button {
        width: 100%;
    }
    .video-info {
        background-color: #f0f0f0;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
    }
    .custom-box {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #e8eaed;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="big-font">Olympics Classification w/t Twelve Labs</p>', unsafe_allow_html=True)
    
    # Updation of the classes
    CLASSES = get_initial_classes() + get_custom_classes()
    
    # Nav Tabs Creation
    tab1, tab2 = st.tabs(["Select Classes", "Add Custom Class"])
    
    with tab1:
        st.markdown('<p class="subheader">Select Classes</p>', unsafe_allow_html=True)
        with st.container():

            class_names = [cls["name"] for cls in CLASSES]
            # Multiselect option from the CLASSES
            selected_classes = st.multiselect("Choose one or more Olympic sports categories:", class_names)
            if st.button("Classify Videos", key="classify_button"):
                if selected_classes:
                    with st.spinner("Classifying videos..."):
                        selected_classes_with_prompts = [cls for cls in CLASSES if cls["name"] in selected_classes]
                        res = classify_videos(selected_classes_with_prompts)
                        
                        video_ids = [data.video_id for data in res.data]
                        # Retrieving the video urls from the resultant video which matches to the selected CLASSES
                        video_urls = get_video_urls(video_ids)
                        
                        st.markdown('<p class="subheader">Classified Videos</p>', unsafe_allow_html=True)
                        
                        # Iterating over to showcase the information for every resulatant video
                        for i, video_data in enumerate(res.data, 1):
                            video_id = video_data.video_id
                            video_url = video_urls.get(video_id, "URL not found")
                            
                            st.markdown(f"### Video {i}")
                            st.markdown('<div class="video-info">', unsafe_allow_html=True)
                            st.markdown(f"**Video ID:** {video_id}")
                            
                            for class_data in video_data.classes:
                                st.markdown(f"""
                                **Class:** {class_data.name}
                                - Score: {class_data.score:.2f}
                                - Duration Ratio: {class_data.duration_ratio:.2f}
                                """)
                            
                            if video_url != "URL not found":
                                render_video(video_url)
                            else:
                                st.warning("Video URL not available. Unable to render video.")
                            
                            st.markdown("---")
                        
                        st.success(f"Total videos classified: {len(res.data)}")
                else:
                    st.warning("Please select at least one class.")
            st.markdown('</div>', unsafe_allow_html=True)

        # Nav Tab for the addition of the Custom Classes to select from
        with tab2:
            st.markdown('<p class="subheader">Add Custom Class</p>', unsafe_allow_html=True)
            with st.container():
                custom_class_name = st.text_input("Enter custom class name")
                custom_class_prompts = st.text_input("Enter custom class prompts (comma-separated)")
                if st.button("Add Custom Class"):
                    if custom_class_name and custom_class_prompts:
                        add_custom_class(custom_class_name, custom_class_prompts.split(','))
                        st.success(f"Custom class '{custom_class_name}' added successfully!")
                        st.experimental_rerun()
                    else:
                        st.warning("Please enter both class name and prompts.")
                st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.get('new_class_added', False):
        st.session_state.new_class_added = False
        st.experimental_rerun()

if __name__ == "__main__":
    main()