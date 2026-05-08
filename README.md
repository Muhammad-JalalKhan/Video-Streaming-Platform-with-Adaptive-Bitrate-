Markdown
# 🎬 Blockflix: Decentralized Video-on-Demand Platform

> **A highly scalable, Web3-integrated Video Streaming Platform featuring Adaptive Bitrate (ABR) delivery and an event-driven microservices architecture. Built as a Cloud Computing Project.**

---

## 📖 Overview

Blockflix bridges the gap between Web2 streaming performance and Web3 decentralized finance. It solves the two major failures of legacy streaming platforms:
1. **The Computational Bottleneck:** By decoupling video transcoding from the main web server using an event-driven Kafka message queue and distributed FFmpeg Docker workers.
2. **Centralized Payment Friction:** By replacing traditional payment gateways (which charge high fees) with Ethereum Smart Contracts, allowing direct peer-to-peer micro-transactions via MetaMask.

## ✨ Key Features

* **Adaptive Bitrate Streaming (HLS):** Automatically scales video quality (1080p, 720p, 480p, 360p) based on the user's real-time network bandwidth to prevent buffering.
* **Event-Driven Transcoding Pipeline:** Uploaded raw `.mp4` files are queued via Apache Kafka and processed asynchronously by dedicated FFmpeg worker containers.
* **Web3 Content Gating:** Video access is secured by an Ethereum Smart Contract. Users must verify their subscription status via MetaMask to unlock the streaming URL.
* **Decentralized Object Storage:** Video chunks and manifests are stored securely using MinIO (S3-compatible storage).
* **Horizontal Scalability:** Processing throughput scales linearly simply by spinning up additional FFmpeg worker containers.

---

## 🛠️ Technology Stack

**Infrastructure & Data Layer**
* **Docker & Docker Compose:** Containerization and network orchestration
* **Apache Kafka & ZooKeeper:** Message broker and distributed coordination
* **MinIO:** S3-compatible object storage (Raw and Processed video buckets)
* **PostgreSQL:** Relational database for video metadata and application state
* **Redis:** In-memory caching and API rate-limiting

**Backend & Processing**
* **FastAPI (Python):** High-performance web API ("The Cashier")
* **FFmpeg:** Industry-standard multimedia framework for video transcoding

**Frontend & Playback**
* **HLS.js & Plyr:** Adaptive HTTP Live Streaming client and custom media player
* **HTML/JS & Tailwind CSS:** Clean, responsive user interface

**Blockchain Layer**
* **Ethereum / Solidity:** Smart contract logic for subscriptions
* **Hardhat:** Local blockchain development environment
* **MetaMask:** Web3 wallet integration

---

## 🚀 Getting Started

Follow these steps to run the complete Blockflix microservices architecture on your local machine.

### Prerequisites
* Docker Desktop installed and running
* Python 3.10+ installed
* Node.js & npm installed
* MetaMask browser extension installed

### 1. Start the Cloud Infrastructure (Docker)
This boots up MinIO, Kafka, ZooKeeper, PostgreSQL, Redis, and your custom FFmpeg worker.
```bash
# From the project root directory
docker compose up -d

# Verify all containers are running successfully
docker ps
2. Start the Local Blockchain (Hardhat)
Open a new terminal to run your local Ethereum network with test accounts.

Bash
cd src/smart-contracts
npx hardhat node
(Leave this terminal running in the background)

3. Deploy Smart Contracts & Start Backend
Open a third terminal. Deploy your contract, then start the FastAPI server.

Bash
cd src/smart-contracts
# Deploy the contract to your local node
npx hardhat run scripts/deploy.js --network localhost
# NOTE: Copy the Contract Address output and update it in your frontend code if necessary!

# Start the Python Backend
cd ../backend
python -m venv venv
.\venv\Scripts\activate   # (On Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
uvicorn main:app --reload
Backend API Docs available at: http://localhost:8000/docs

4. Serve the Frontend UI
Open a fourth terminal. You must serve the frontend via a local server so MetaMask can securely inject its Web3 provider.

Bash
cd src/frontend
python -m http.server 5500
Access the platform at: http://localhost:5500

📊 System Monitoring & Useful Endpoints
MinIO Object Browser: http://localhost:9001 (Default: admin / password123)

FastAPI Swagger UI: http://localhost:8000/docs

Watch FFmpeg Worker Logs: docker logs -f cc_ffmpeg_worker

Access Database Terminal: docker exec -it cc_postgres psql -U admin -d vod_db

👨‍💻 Authors
Muhammad Jalal Khan

Ali Murad

Developed as a Cloud Computing Academic Project.
