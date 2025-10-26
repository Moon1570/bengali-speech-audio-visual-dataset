#!/bin/bash
# Quick reference for Docker commands - Bengali Speech Pipeline

cat << 'EOF'

╔══════════════════════════════════════════════════════════════════════════════╗
║                 Bengali Speech Pipeline - Docker Quick Reference             ║
╚══════════════════════════════════════════════════════════════════════════════╝

📦 SETUP (One Time)
────────────────────────────────────────────────────────────────────────────────
  ./verify_docker_setup.sh          Check all prerequisites
  ./build_docker.sh                 Build Docker image (5-10 min)
  ./run_docker.sh start             Start the container

🎬 RUNNING THE PIPELINE
────────────────────────────────────────────────────────────────────────────────
  # Basic run
  ./run_docker.sh run VIDEO_ID

  # With options
  ./run_docker.sh run VIDEO_ID --silence-preset sensitive
  ./run_docker.sh run VIDEO_ID --reduce-noise
  ./run_docker.sh run VIDEO_ID --transcription-model google
  
  # Combined
  ./run_docker.sh run VIDEO_ID \
      --silence-preset conservative \
      --reduce-noise \
      --transcription-model google

🎨 SILENCE PRESETS (Choose sensitivity)
────────────────────────────────────────────────────────────────────────────────
  very_sensitive    → Many small chunks (word-level)
  sensitive         → Phrase-level splits
  balanced          → Sentence-level (DEFAULT)
  conservative      → Paragraph-level
  very_conservative → Major topic changes only

🔧 CONTAINER MANAGEMENT
────────────────────────────────────────────────────────────────────────────────
  ./run_docker.sh start             Start container
  ./run_docker.sh stop              Stop container
  ./run_docker.sh status            Check status
  ./run_docker.sh logs              View logs
  ./run_docker.sh shell             Enter container shell
  ./run_docker.sh cleanup           Remove everything
  ./run_docker.sh help              Show full help

📁 DATA LOCATIONS
────────────────────────────────────────────────────────────────────────────────
  downloads/                        Place input videos here
  outputs/VIDEO_ID/                 Intermediate results
  experiments/experiment_data/      Final results
    └── VIDEO_ID/
        ├── audio/                  Audio chunks
        ├── video_normal/           Filtered videos
        └── transcripts_google/     Transcriptions

🚀 COMMON WORKFLOWS
────────────────────────────────────────────────────────────────────────────────
  # Quick test (chunking only)
  ./run_docker.sh run VIDEO_ID --skip-step2 --skip-step3 --skip-step4

  # Full pipeline with high quality
  ./run_docker.sh run VIDEO_ID --silence-preset conservative --reduce-noise

  # Offline transcription
  ./run_docker.sh run VIDEO_ID --transcription-model whisper

  # Batch processing
  for video in downloads/*.mp4; do
      ID=$(basename "$video" .mp4)
      ./run_docker.sh run "$ID"
  done

🐛 TROUBLESHOOTING
────────────────────────────────────────────────────────────────────────────────
  Build fails          → ./verify_docker_setup.sh
  Container crashes    → ./run_docker.sh logs
  Need debugging       → ./run_docker.sh shell
  GPU not working      → docker run --rm --gpus all nvidia/cuda:11.8.0-base nvidia-smi
  Permission issues    → sudo chown -R $USER:$USER outputs/ experiments/

📚 DOCUMENTATION
────────────────────────────────────────────────────────────────────────────────
  DOCKER_README.md                  Quick start guide
  DOCKER_GUIDE.md                   Comprehensive documentation
  DOCKER_CHECKLIST.md               Testing checklist
  docs/DOCKER_ARCHITECTURE.md       Technical architecture

💡 TIPS
────────────────────────────────────────────────────────────────────────────────
  • Build once, run many times
  • Use sensitive preset for more chunks
  • Enable --reduce-noise for noisy audio
  • Use Whisper for offline operation
  • Data persists in mounted directories
  • GPU speeds up processing 10x

✅ QUICK HEALTH CHECK
────────────────────────────────────────────────────────────────────────────────
  docker ps | grep bengali-pipeline    # Container running?
  docker images | grep bengali-speech  # Image exists?
  ls -la downloads/                    # Input videos present?
  ls -la experiments/                  # Results directory exists?

🆘 NEED HELP?
────────────────────────────────────────────────────────────────────────────────
  ./run_docker.sh help                 Built-in help
  cat DOCKER_README.md                 Quick start guide
  cat DOCKER_GUIDE.md | less           Full documentation

╔══════════════════════════════════════════════════════════════════════════════╗
║  Ready to start? Run: ./build_docker.sh                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

EOF
