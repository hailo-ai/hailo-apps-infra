# Hailo Applications Infrastructure - Release Notes v25.10.0

**Release Date:** November 2025

---

## What's New

We're excited to announce version 25.10.0 of the Hailo Applications Infrastructure! This release brings Hailo10 hardware support, Three powerful new applications, and significant improvements across the entire platform.

#### Important: Trixie support for RPi! Bookworm is no longer supported (Use previous release if need to stay on Bookworm).

---

## 🎯 Headline Features

### Hailo10 (H10) Hardware Support
We've added full support for the new Hailo10 hardware accelerator. The installation process has been updated to handle both H8 and H10 devices seamlessly, with proper version detection and model zoo support (v5.0.0 for H10, v2.17.0 for H8).

### Three New Applications

**1. Tiling Application (Beta)**  
Detect small objects in high-resolution images by intelligently splitting frames into tiles. Perfect for aerial footage and scenarios where objects are tiny relative to frame size.

- Process high-resolution frames efficiently
- Single and multi-scale tiling modes
- Includes VisDrone MobileNetSSD model for aerial detection
- Compatible with YOLO models and COCO dataset
- Run with: `hailo-tiling`

**2. Multisource Application**  
Process multiple video streams in parallel from different sources—USB cameras, files, RTSP streams, and more.

- Handle multiple streams simultaneously
- Optimized for Raspberry Pi (up to 3 sources)
- Individual callback functions per stream
- Run with: `hailo-multisource`

**3. REID Multisource Application (Beta)**  
Track people across multiple cameras using face recognition and person re-identification.

- Cross-camera tracking with face embeddings
- Persistent database storage using LanceDB
- Optimized at 15 FPS for multi-stream performance
- Run with: `hailo-reid`

---

## 🔧 Improvements

### Better Installation Experience
We've completely overhauled the installation process with improved error handling, clearer feedback, and better compatibility across Ubuntu versions. New cleanup and uninstall scripts make managing your installation easier.

### Enhanced C++ Post-Processing
Added three new post-processing functions:
- `mobilenet_ssd` and variants for object detection
- `repvgg_reid` for person re-identification
- `all_detections_cropper` for detection utilities

### Face Recognition Overhaul
Cleaned up the face recognition application by removing UI-specific components and moving to a streamlined, backend-focused design. Fixed matplotlib visualization issues and improved overall reliability.

### Core Infrastructure
- New comprehensive logging system for better debugging
- Enhanced database handling with improved LanceDB integration
- Better GStreamer pipeline management with fixed video looping issues
- Optimized buffer and memory management

---

## 🐛 Notable Bug Fixes

- **Critical:** Fixed Hailo8L compatibility bug
- **Critical:** Resolved video looping issue in pipelines
- Fixed H8/H10 version detection problems
- Corrected resource download functionality
- Improved installation permissions handling
- Fixed matplotlib backend issues in face recognition

---

## 📦 Version Requirements

- **HailoRT:** 4.23.0 or 5.1.0
- **Tappas:** 5.1.0
- **Python:** 3.10 or higher
- **Model Zoo:** v5.0.0 (H10) / v2.17.0 (H8)

---

## 🚀 Getting Started

**Updated Installation:**
```bash
sudo ./install.sh
```

**Updating from Previous Version:**
```bash
sudo ./scripts/cleanup_installation.sh
sudo ./install.sh
```

---

## 📝 Migration Guide

### For Users
- Re-run the installation script to get H10 support
- Review the updated `config/config.yaml` for new configuration options
- Check out the new applications in the documentation

### For Developers
- Face recognition UI components have been removed—update any custom integrations
- New C++ post-processors are available; some deprecated ones have been removed
- Pre-commit hooks now enforce code formatting with Ruff

---

## ⚠️ Known Limitations

- **Tiling and REID applications** are in beta—expect some rough edges
- **Multisource** performs best with up to 3 sources on Raspberry Pi
- **REID** frame rate is currently locked at 15 FPS for stability

---

## 📚 Learn More

Full documentation for each application is available in:
- `hailo_apps/hailo_app_python/apps/tiling/README.md`
- `hailo_apps/hailo_app_python/apps/multisource/README.md`
- `hailo_apps/hailo_app_python/apps/reid_multisource/README.md`

---

## 🙏 Thanks

Special thanks to our contributors: OmriAx, hailocs, giladnah, and mikehailodev for making this release possible.

---

## 💬 Support

Need help? Visit [hailo.ai](https://hailo.ai/) or join our [Community Forum](https://community.hailo.ai/)