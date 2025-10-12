import streamlit as st
from twelvelabs import TwelveLabs
from twelvelabs import SearchItem, SearchItemClipsItem, SearchResults
import requests
import os
from dotenv import load_dotenv
import threading
from apscheduler.schedulers.background import BackgroundScheduler
import time


load_dotenv()

def keep_alive():
    print("Keep-alive ping executed at:", time.strftime("%Y-%m-%d %H:%M:%S"))
    try:
        app_url = os.getenv("STREAMLIT_APP_URL", "http://twelvelabs-olympics-app.streamlit.app/")
        requests.get(app_url, timeout=10)
        print("Successfully pinged the app")
    except Exception as e:
        print(f"Keep-alive ping failed: {str(e)}")


scheduler = BackgroundScheduler()
scheduler.add_job(keep_alive, 'interval', minutes=10)
scheduler.start()

API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.twelvelabs.io/v1.2"

INDEX_ID = os.getenv("INDEX_ID")

client = TwelveLabs(api_key=API_KEY)

page_element = """
<style>
[data-testid="stAppViewContainer"] {
    background-image: url("https://s3-alpha-sig.figma.com/img/c5c5/bd88/207d602d6f1a4924e04616fe11668326?Expires=1742169600&Key-Pair-Id=APKAQ4GOSFWCW27IBOMQ&Signature=jRL24wXnNnnMNMIKVSjdmtMwTfV-gmeTZ4OqgCuvi7El-VElqYoY3I2nQMJZTVmSD8M6Hf-mAPJ-sb9-GBSQ~kuTeaWGR~DoTcuBlmZUYaUQJ82aOwjS3WbZd9shioxELBesNeFSqrokAwwoyJIBJ-cZafIyom6GPyZlGZym2~E1jiTOYl-avB0YcxKxFfDVtC4Faxpa4phIq6wWpOmVz0S0HVfOmeNUR1GEk5y8UcQMhdwXsj2S~mnE586NhNACbG~1LXVuYW7KXkcK0zr~TeNiWF5Q9cd34kkplxTbqjtl2HTqgdI3FGjhFw6jJyhurArEuPAjrkykzZSiSUUBFg__");
    background-size: cover;
    background-color: rgba(255, 255, 255, 0.7);
    background-blend-mode: overlay;
    backdrop-filter: blur(3px);
    -webkit-backdrop-filter: blur(3px);
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
 
def get_custom_classes():
    if 'custom_classes' not in st.session_state:
        st.session_state.custom_classes = []
    return st.session_state.custom_classes

def add_custom_class(name, prompts):
    custom_classes = get_custom_classes()
    custom_classes.append({"name": name, "prompts": prompts})
    st.session_state.custom_classes = custom_classes
    st.session_state.new_class_added = True

def search_videos(selected_prompts, selected_class_names):
    results_by_prompt = {}
    
    for i, prompt in enumerate(selected_prompts):
        try:
            class_name = next((class_name for class_name in selected_class_names 
                              for cls in get_initial_classes() + get_custom_classes() 
                              if cls["name"] == class_name and prompt in cls["prompts"]), "Unknown")
            
            result = client.search.create(
                index_id=INDEX_ID,
                search_options=["visual", "audio"],
                query_text=prompt,
                group_by="video",
                threshold="medium",
                operator="or",
                page_limit=5,
                sort_option="score"
            )
            
            print(f"Search response for prompt '{prompt}':")
            print(f"  Total results: {result.page_info.total_results}")
            print(f"  Index ID: {result.search_pool.index_id}")
            print(f"  Total count in pool: {result.search_pool.total_count}")
            
            if result.data and len(result.data) > 0:
                print(f"  First result type: {type(result.data[0])}")
                if isinstance(result.data[0], SearchItem) and result.data[0].clips:
                    clip = result.data[0].clips[0]
                    print(f"  Sample clip data: score={clip.score}, start={clip.start}, end={clip.end}")
                    print(f"  Confidence type: {type(clip.confidence)}")
                    print(f"  Confidence value: {clip.confidence}")
            
            results_by_prompt[prompt] = {
                "class_name": class_name,
                "result": result
            }
        except Exception as e:
            st.error(f"API Error for prompt '{prompt}': {str(e)}")
            print(f"Exception details: {type(e).__name__}: {str(e)}")
    
    return results_by_prompt

def get_video_urls(video_ids):
    base_url = f"https://api.twelvelabs.io/v1.3/indexes/{INDEX_ID}/videos/{{}}"
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

def render_video(video_url, key):
    hls_player = f"""
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <div style="width: 100%; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin-bottom: 10px; position: relative; padding-top: 56.25%;">
        <video id="video-{key}" controls style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: contain;"></video>
    </div>
    <script>
      var video = document.getElementById('video-{key}');
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
    st.components.v1.html(hls_player, height=400)


def main():

    st.markdown("""
    <style>
    .big-font {
        font-size: 40px !important;
        font-weight: bold;
        color: #000000;
        text-align: center;
        margin-bottom: 30px;
        text-shadow: 0px 0px 5px rgba(255, 255, 255, 0.8);
    }
    .subheader {
        font-size: 24px;
        font-weight: bold;
        color: #424242;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .category-header {
        font-size: 22px;
        font-weight: bold;
        color: #0066cc;
        background-color: rgba(230, 240, 255, 0.85);
        padding: 10px;
        border-radius: 5px;
        margin-top: 30px;
        margin-bottom: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .prompt-header {
        font-size: 18px;
        font-weight: bold;
        color: #006600;
        background-color: rgba(240, 255, 240, 0.85);
        padding: 8px;
        border-radius: 5px;
        margin-top: 20px;
        margin-bottom: 10px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .stButton>button {
        width: 100%;
    }
    .video-info {
        background-color: rgba(240, 240, 240, 0.85);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
    }
    .video-card {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .video-meta {
        font-size: 14px;
        color: #666666;
    }
    .confidence-high {
        color: #008800;
        font-weight: bold;
    }
    .confidence-medium {
        color: #cc8800;
        font-weight: bold;
    }
    .confidence-low {
        color: #cc0000;
        font-weight: bold;
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
        background-color: transparent !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: rgba(240, 242, 246, 0.7);
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: rgba(232, 234, 237, 0.8);
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="big-font">Olympics Classification w/t Twelve Labs</p>', unsafe_allow_html=True)

    CLASSES = get_initial_classes() + get_custom_classes()
    

    tab1, tab2 = st.tabs(["Search Videos", "Add Custom Class"])
    
    with tab1:
        st.markdown('<p class="subheader">Search Videos</p>', unsafe_allow_html=True)
        with st.container():
            class_names = [cls["name"] for cls in CLASSES]
            selected_classes = st.multiselect("Choose one or more Olympic sports categories:", class_names)
            
            if st.button("Search Videos", key="search_button"):
                if selected_classes:
                    with st.spinner("Searching videos..."):
                        selected_prompts = []
                        for cls in CLASSES:
                            if cls["name"] in selected_classes:
                                selected_prompts.extend(cls["prompts"])
                        
                        results_by_prompt = search_videos(selected_prompts, selected_classes)
                        
                        video_ids = set()
                        for prompt_data in results_by_prompt.values():
                            result = prompt_data["result"]
                            for item in result.data:
                                if isinstance(item, SearchItem):
                                    video_ids.add(item.id)
                                else:
                                    video_ids.add(item.video_id)
                        
                        video_urls = get_video_urls(list(video_ids))
                        
                        if not video_ids:
                            st.warning("No videos found matching your search criteria.")
                        else:
                            st.success(f"Found {len(video_ids)} unique videos across {len(selected_prompts)} search prompts")
                            
                            results_by_class = {}
                            for prompt, prompt_data in results_by_prompt.items():
                                class_name = prompt_data["class_name"]
                                if class_name not in results_by_class:
                                    results_by_class[class_name] = []
                                results_by_class[class_name].append({
                                    "prompt": prompt,
                                    "result": prompt_data["result"]
                                })
                            
                            for class_name, class_results in results_by_class.items():
                                st.markdown(f'<div class="category-header">{class_name}</div>', unsafe_allow_html=True)
                                
                                for prompt_result in class_results:
                                    prompt = prompt_result["prompt"]
                                    result = prompt_result["result"]
                                    
                                    st.markdown(f'<div class="prompt-header">Results for: "{prompt}"</div>', unsafe_allow_html=True)
                                    
                                    video_count = 0
                                    for item in result.data:
                                        if isinstance(item, SearchItem):
                                            video_id = item.id
                                            if not item.clips:
                                                continue
                                                
                                            with st.expander(f"Video {video_count+1}: {video_id}", expanded=(video_count == 0)):
                                                st.markdown('<div class="video-card">', unsafe_allow_html=True)
                                                
                                                for i, clip in enumerate(item.clips[:3]):  # Limit to top 3 clips
                                                    confidence_class = "confidence-high" if clip.confidence == "high" else "confidence-medium" if clip.confidence == "medium" else "confidence-low"
                                                    
                                                    st.markdown(f"""
                                                    <div class="video-meta">
                                                        <strong>Clip {i+1}:</strong> {float(clip.start):.1f}s - {float(clip.end):.1f}s | 
                                                        Score: {float(clip.score):.1f} | 
                                                        Confidence: <span class="{confidence_class}">{clip.confidence}</span>
                                                    </div>
                                                    """, unsafe_allow_html=True)
                                                
                                                if video_id in video_urls:
                                                    render_video(video_urls[video_id], f"{class_name}-{prompt}-{video_count}")
                                                else:
                                                    st.warning("Video URL not available. Unable to render video.")
                                                
                                                st.markdown('</div>', unsafe_allow_html=True)
                                            
                                            video_count += 1
                                            if video_count >= 3:
                                                break
                                        
                                    if video_count == 0:
                                        st.info(f"No videos found for prompt: {prompt}")
                else:
                    st.warning("Please select at least one class.")
            st.markdown('</div>', unsafe_allow_html=True)

        with tab2:
            st.markdown('<p class="subheader">Add Custom Class</p>', unsafe_allow_html=True)
            with st.container():
                custom_class_name = st.text_input("Enter custom class name")
                custom_class_prompts = st.text_input("Enter custom class prompts (comma-separated)")
                if st.button("Add Custom Class"):
                    if custom_class_name and custom_class_prompts:
                        prompts_list = [p.strip() for p in custom_class_prompts.split(',')]
                        add_custom_class(custom_class_name, prompts_list)
                        st.success(f"Custom class '{custom_class_name}' added successfully!")
                        st.rerun()
                    else:
                        st.warning("Please enter both class name and prompts.")
                st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.get('new_class_added', False):
        st.session_state.new_class_added = False
        st.rerun()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    
    import atexit
    atexit.register(lambda: scheduler.shutdown())
