# Cloud Hosting & Deployment Guide - AutoForm AI Platform

This guide provides step-by-step instructions to host your full-stack web automation platform online 24/7 so it runs independently without keeping your local computer on.

---

## 🌐 Option 1: Render.com (Recommended - Free Tier)

Render supports Docker deployment out-of-the-box using the `Dockerfile` in your project folder.

### Steps:
1. **Create a GitHub Repository**:
   - Push your project folder `/Users/radityac/.gemini/antigravity/scratch/auto_form_platform` to a new repository on [GitHub](https://github.com/).

2. **Sign Up on Render**:
   - Go to **[https://render.com/](https://render.com/)** and create a free account.

3. **Deploy Web Service**:
   - Click **New +** ➔ **Web Service**.
   - Connect your GitHub repository.
   - Set **Environment**: `Docker`.
   - Set **Region**: Choose closest to your target audience (e.g. Singapore or Frankfurt).
   - Click **Deploy Web Service**!

Render will automatically build the Docker container, install Playwright Chromium, compile the React frontend, and give you an online URL (e.g., `https://autoform-platform.onrender.com`).

---

## 🚀 Option 2: Railway.app (Fastest 1-Click Deployment)

Railway provides $5 free monthly credit and handles Playwright headless browser execution smoothly.

### Steps:
1. Go to **[https://railway.app/](https://railway.app/)**.
2. Click **New Project** ➔ **Deploy from GitHub repo**.
3. Select your `auto_form_platform` repository.
4. Railway automatically detects the `Dockerfile` and deploys your full-stack app online.
5. Under **Settings ➔ Networking**, click **Generate Domain** to get your public HTTPS URL.

---

## 🖥 Option 3: VPS Server (DigitalOcean / Hetzner / AWS EC2)

For maximum speed with no rate limits ($4-$6/month).

### Commands on VPS:
```bash
# 1. Clone repository
git clone https://github.com/your-username/auto_form_platform.git
cd auto_form_platform

# 2. Build and run Docker container
docker build -t autoform-platform .
docker run -d -p 8000:8000 --name autoform autoform-platform
```

Your platform will be accessible online 24/7 at `http://your-server-ip:8000`!
