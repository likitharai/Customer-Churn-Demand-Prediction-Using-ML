# RetainIQ — Hugging Face Spaces Deployment Guide (100% Free, All-in-One)

Deploy the entire RetainIQ platform (React Frontend + FastAPI Backend + LightGBM v1.0.0 ML Pipeline + SQLite Database) into a single, free container with **16 GB RAM and 2 vCPUs** on Hugging Face Spaces.

---

## Why Hugging Face Spaces?
* **100% Free**: 2 vCPUs, 16 GB RAM, no credit card required.
* **Single Public URL**: No separate frontend/backend URLs to configure.
* **Zero CORS Issues**: React and FastAPI run inside the same container on port `7860`.
* **Permanent Live Demo**: Won't sleep or expire after inactivity like some cloud free tiers.

---

## 3-Minute Deployment Instructions

### Step 1: Create a Space on Hugging Face
1. Go to [huggingface.co/new-space](https://huggingface.co/new-space).
2. Set **Space name** (e.g., `retainiq-churn-intelligence`).
3. Set **License** to `Apache 2.0` or `MIT`.
4. Under **Select the Space SDK**, select **Docker** (Blank template).
5. Under **Space hardware**, keep the default **Free (2 vCPU · 16 GB RAM)**.
6. Click **Create Space**.

---

### Step 2: Push Your Code to the Space

On your computer terminal, run these 2 commands (replace `<username>` and `<space-name>` with yours):

```bash
git remote add space https://huggingface.co/spaces/<your-username>/<your-space-name>
git push space main
```

*(When prompted for a password, generate an Access Token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) with `write` permission).*

---

### Step 3: That's It!
Hugging Face will automatically:
1. Run **Stage 1**: Compile the React Vite frontend into `dist/`.
2. Run **Stage 2**: Install Python dependencies, load `model_pipeline.pkl`, and initialize the database.
3. Launch on port `7860`.

Within 2 minutes, your Space status will turn **Running** with a live public link:
`https://huggingface.co/spaces/<your-username>/<your-space-name>`

You can now share this URL with anyone in the world to explore the full interactive dashboard, test real-time predictions, inspect risk queues, and review customer retention playbooks.
