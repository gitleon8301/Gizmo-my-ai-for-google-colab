# Gizmo MY-AI — Self-Hosted Setup Guide

This guide walks you through setting up Gizmo MY-AI on a Fedora Linux machine for the first time.

---

## 1. Google OAuth Credentials

Gizmo uses Google OAuth for authentication. You need to create OAuth 2.0 credentials in the Google Cloud Console.

### Step-by-step

1. Go to [https://console.cloud.google.com/](https://console.cloud.google.com/) and sign in.
2. Create a new project (or select an existing one).
3. In the sidebar, navigate to **APIs & Services → OAuth consent screen**.
   - Choose **External** user type.
   - Fill in the app name (e.g. "Gizmo MY-AI"), support email, and developer contact email.
   - Add the scope `openid`, `email`, and `profile`.
   - Under **Test users**, add the Gmail addresses that should have access.
4. Navigate to **APIs & Services → Credentials**.
   - Click **Create Credentials → OAuth 2.0 Client ID**.
   - Application type: **Web application**.
   - Add an Authorized redirect URI: `https://gizmohub.ai/auth/callback`
     (replace with your actual domain if different).
   - Click **Create** and copy the **Client ID** and **Client Secret**.
5. Create the environment file:

```bash
mkdir -p user_data
cat > user_data/google_oauth.env << 'EOF'
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://gizmohub.ai/auth/callback
SESSION_SECRET_KEY=change-me-to-a-long-random-string
EOF
```

> **Security:** `user_data/google_oauth.env` is listed in `.gitignore` and will never be committed.

---

## 2. Allowed Emails

Only addresses listed in `user_data/allowed_emails.txt` can log in. The **first** address is treated as the owner.

```bash
cat > user_data/allowed_emails.txt << 'EOF'
owner@gmail.com
friend@gmail.com
EOF
```

> **Security:** `user_data/allowed_emails.txt` is listed in `.gitignore` and will never be committed.

---

## 3. Generating PWA Icons

The PWA manifest references `static/icons/icon-192.png` and `static/icons/icon-512.png`. SVG fallbacks (`icon-192.svg`, `icon-512.svg`) are already included and work in all modern browsers without any extra steps.

To generate the PNG versions (required for maskable-icon support, which the SVG fallbacks do not provide):

```bash
pip install Pillow
python scripts/generate_icons.py
```

This creates `static/icons/icon-192.png` and `static/icons/icon-512.png` with a purple `#6C63FF` background and a white "G".

---

## 4. Storage Directory

### Default: `./storage` (works out of the box)

By default, `config.yaml` uses `./storage` inside the project directory. No extra setup is needed — the launcher creates this directory automatically on first run.

```yaml
storage:
  base_dir: "./storage"
```

### Optional: Dedicated drive at `/mnt/gizmo-storage`

If you have a dedicated drive for model storage (recommended for large models), mount it and update `config.yaml`:

```bash
sudo mkdir -p /mnt/gizmo-storage
sudo chown $USER /mnt/gizmo-storage
```

Then edit `config.yaml`:

```yaml
storage:
  base_dir: "/mnt/gizmo-storage"
  models_dir: "/mnt/gizmo-storage/models"
  cache_dir: "/mnt/gizmo-storage/cache"
  logs_dir: "/mnt/gizmo-storage/logs"
```

---

## 5. First Launch Checklist

Before running `python launcher_fedora.py` for the first time, verify:

- [ ] `user_data/google_oauth.env` exists with valid credentials
- [ ] `user_data/allowed_emails.txt` exists with at least your own Gmail address
- [ ] `config.yaml` `storage.base_dir` is set to your preferred location
- [ ] PNG icons generated (or SVG fallbacks already present in `static/icons/`)
- [ ] Python dependencies installed: `pip install -r requirements/requirements.txt`
- [ ] For GPU inference: CUDA drivers and `llama-cpp-python` with CUDA support installed

Then launch:

```bash
python launcher_fedora.py
```

The launcher will:
1. Create all required storage directories automatically.
2. Present a model download menu.
3. Start the Gradio web server on the port defined in `config.yaml` (default `7860`).

Open your browser at `http://localhost:7860` (or your public URL if behind a reverse proxy).
