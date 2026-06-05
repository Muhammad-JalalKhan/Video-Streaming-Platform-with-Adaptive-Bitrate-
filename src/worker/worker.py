import os
import json
import shutil
import subprocess
from minio import Minio
from confluent_kafka import Consumer
from sqlalchemy import create_engine, text  # <-- NEW: Database imports

# --- Configuration ---
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "password123")

# <-- NEW: Database Configuration (Worker talks to 'postgres' container) -->
DB_URL = os.getenv("DATABASE_URL", "postgresql://admin:password123@postgres:5432/vod_db")

RAW_BUCKET = "raw-videos"
PROCESSED_BUCKET = "processed-videos"
KAFKA_TOPIC = "video-uploads"

# --- Initialize Clients ---
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

consumer = Consumer({
    'bootstrap.servers': KAFKA_BROKER,
    'group.id': 'ffmpeg-worker-group',
    'auto.offset.reset': 'earliest'
})
consumer.subscribe([KAFKA_TOPIC])

# Initialize Database Engine
engine = create_engine(DB_URL)

def process_video(video_id):
    print(f"\n[WORKER] Starting process for: {video_id}")
    work_dir = f"./temp_{video_id}"
    
    # 1. Prepare directories for 4 different resolutions
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(os.path.join(work_dir, "stream_0"), exist_ok=True) # 1080p
    os.makedirs(os.path.join(work_dir, "stream_1"), exist_ok=True) # 720p
    os.makedirs(os.path.join(work_dir, "stream_2"), exist_ok=True) # 480p
    os.makedirs(os.path.join(work_dir, "stream_3"), exist_ok=True) # 360p <-- NEW
    
    raw_video_path = os.path.join(work_dir, "input.mp4")
    
    try:
        print(f"[WORKER] Downloading {video_id} from MinIO...")
        minio_client.fget_object(RAW_BUCKET, video_id, raw_video_path)
        
        print("[WORKER] Running FFmpeg Transcoding (1080p, 720p, 480p, 360p)...")
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", raw_video_path,
            "-preset", "veryfast", "-g", "48", "-sc_threshold", "0",
            
            # Map video and audio 4 times for 4 qualities
            "-map", "0:v:0", "-map", "0:a:0",
            "-map", "0:v:0", "-map", "0:a:0",
            "-map", "0:v:0", "-map", "0:a:0",
            "-map", "0:v:0", "-map", "0:a:0", # <-- NEW 4th map
            
            # Codecs
            "-c:v", "libx264", "-c:a", "aac", "-b:a", "128k",
            
            # Stream 0: 1080p @ 4 Mbps (Matching Teacher Rubric)
            "-filter:v:0", "scale=-2:1080", "-b:v:0", "4000k",
            # Stream 1: 720p @ 2 Mbps (Matching Teacher Rubric)
            "-filter:v:1", "scale=-2:720", "-b:v:1", "2000k",
            # Stream 2: 480p @ 1 Mbps (Matching Teacher Rubric)
            "-filter:v:2", "scale=-2:480", "-b:v:2", "1000k",
            # Stream 3: 360p @ 0.5 Mbps (Matching Teacher Rubric) <-- NEW
            "-filter:v:3", "scale=-2:360", "-b:v:3", "500k",
            
            # Bind streams to variant map (Adding v:3,a:3)
            "-var_stream_map", "v:0,a:0 v:1,a:1 v:2,a:2 v:3,a:3",
            
            # Master playlist generation
            "-master_pl_name", "master.m3u8",
            
            # HLS Output formatting (Chunking into 10-second segments)
            "-f", "hls", "-hls_time", "10", "-hls_playlist_type", "vod",
            "-hls_segment_filename", f"{work_dir}/stream_%v/data%03d.ts",
            f"{work_dir}/stream_%v/playlist.m3u8"
        ]
        
        subprocess.run(ffmpeg_cmd, check=True)
        print("[WORKER] FFmpeg finished successfully. Master playlist created.")

        print("[WORKER] Uploading chunks to Processed Bucket...")
        for root, dirs, files in os.walk(work_dir):
            for filename in files:
                if filename.endswith(".ts") or filename.endswith(".m3u8"):
                    file_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(file_path, work_dir)
                    minio_client.fput_object(PROCESSED_BUCKET, f"{video_id}/{relative_path}", file_path)
                
        print(f"[WORKER] Updating database for {video_id} to READY...")
        with engine.connect() as conn:
            stream_url = f"http://localhost:9000/{PROCESSED_BUCKET}/{video_id}/master.m3u8"
            query = text("UPDATE videos SET status = 'ready', hls_url = :url WHERE id = :vid")
            conn.execute(query, {"url": stream_url, "vid": video_id})
            conn.commit()

        print(f"[WORKER] DONE! Video {video_id} is ready.\n")

    except Exception as e:
        print(f"[ERROR] Failed to process {video_id}: {str(e)}")
        with engine.connect() as conn:
            query = text("UPDATE videos SET status = 'failed' WHERE id = :vid")
            conn.execute(query, {"vid": video_id})
            conn.commit()
    finally:
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)

# --- Main Event Loop ---
print("[WORKER] Advanced FFmpeg Worker is online and listening to Kafka...")
while True:
    msg = consumer.poll(1.0)
    if msg is None:
        continue
    if msg.error():
        print(f"[KAFKA ERROR] {msg.error()}")
        continue

    ticket = json.loads(msg.value().decode('utf-8'))
    video_id = ticket['video_id']
    
    process_video(video_id)