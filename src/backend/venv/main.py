from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from minio import Minio
from minio.error import S3Error
from confluent_kafka import Producer
from models import Video, SessionLocal
import io
import uuid
import json

app = FastAPI(title="VOD Upload API")

# --- Enable CORS (Allows the Frontend to talk to this Backend) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. Initialize MinIO Client (The Freezer) ---
minio_client = Minio(
    "localhost:9000", 
    access_key="admin",
    secret_key="password123",
    secure=False 
)
BUCKET_NAME = "raw-videos"

# --- 2. Initialize Kafka Producer (The Ticket Rail) ---
producer_config = {
    'bootstrap.servers': 'localhost:9092' 
}
kafka_producer = Producer(producer_config)
KAFKA_TOPIC = "video-uploads"


# --- ROUTE 1: Upload a Video ---
@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    # 1. Validate file type
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a video.")

    # Open a fresh database connection
    db = SessionLocal()

    try:
        # 2. Read the file into memory
        file_data = await file.read()
        file_size = len(file_data)
        
        # 3. Generate a unique ID for the video
        unique_filename = f"{uuid.uuid4()}_{file.filename}"

        # 4. Upload to MinIO (The Freezer)
        minio_client.put_object(
            BUCKET_NAME,
            unique_filename,
            io.BytesIO(file_data),
            file_size,
            content_type=file.content_type
        )

        # 5. Write the order into the PostgreSQL Ledger
        new_video = Video(
            id=unique_filename,
            title=file.filename,
            status="processing"
        )
        db.add(new_video)
        db.commit()

        # 6. Write the ticket and put it on the Kafka rail
        ticket = {
            "video_id": unique_filename
        }
        kafka_producer.produce(KAFKA_TOPIC, json.dumps(ticket).encode('utf-8'))
        kafka_producer.flush() 

        return {"message": "Upload successful, DB updated, and Ticket Sent!", "video_id": unique_filename}

    except S3Error as e:
        db.rollback() # Cancel the DB save if MinIO crashes
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
    except Exception as e:
        db.rollback() # Cancel the DB save if Kafka or anything else crashes
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        db.close() # Always close the connection


# --- ROUTE 2: Get All Videos (For the Frontend) ---
@app.get("/videos")
def get_all_videos():
    # Open the database connection
    db = SessionLocal()
    try:
        # Fetch all videos from the ledger
        videos = db.query(Video).all()
        return videos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    # 1. Validate file type
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a video.")

    # Open a fresh database connection for this specific customer
    db = SessionLocal()

    try:
        # 2. Read the file into memory
        file_data = await file.read()
        file_size = len(file_data)
        
        # 3. Generate a unique ID for the video
        unique_filename = f"{uuid.uuid4()}_{file.filename}"

        # 4. Upload to MinIO (The Freezer)
        minio_client.put_object(
            BUCKET_NAME,
            unique_filename,
            io.BytesIO(file_data),
            file_size,
            content_type=file.content_type
        )

        # 5. NEW: Write the order into the PostgreSQL Ledger!
        new_video = Video(
            id=unique_filename,
            title=file.filename,
            status="processing"
        )
        db.add(new_video)
        db.commit()

        # 6. Write the ticket and put it on the Kafka rail
        ticket = {
            "video_id": unique_filename
        }
        kafka_producer.produce(KAFKA_TOPIC, json.dumps(ticket).encode('utf-8'))
        kafka_producer.flush() 

        return {"message": "Upload successful, DB updated, and Ticket Sent!", "video_id": unique_filename}

    except S3Error as e:
        db.rollback() # CRITICAL: Cancel the DB save if MinIO crashes
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
    except Exception as e:
        db.rollback() # CRITICAL: Cancel the DB save if Kafka or anything else crashes
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        # ALWAYS close the database door when the transaction is finished
        db.close()

@app.get("/videos")
def get_all_videos():
    # Open the database connection
    db = SessionLocal()
    try:
        # Fetch all videos from the ledger
        videos = db.query(Video).all()
        return videos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        # Close the connection
        db.close()