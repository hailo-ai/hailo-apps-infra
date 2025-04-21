
## 🧪 Context: Example Target
Let’s assume you want to run:

```python
hailo_apps_infra/pipelines/hailo_pipelines/detection_pipeline.py
```

---

# 🧰 ALL OPTIONS TO RUN THE PIPELINE FROM ROOT

---

## ✅ 1. Using `python -m` (Best for installed packages)
### Command:
```bash
python -m hailo_apps_infra.pipelines.hailo_pipelines.detection_pipeline
```

### ✅ Why it works:
- You installed the package with `pip install -e ./hailo_apps_infra/pipelines`
- Python treats this as a proper package hierarchy (`import hailo_apps_infra.pipelines...`)
- Imports and relative modules will resolve correctly

### 🔥 Best for: Production, development, test runners

---

## ✅ 2. Using `PYTHONPATH` to run the file directly
### Command:
```bash
PYTHONPATH=./hailo_apps_infra python hailo_apps_infra/pipelines/hailo_pipelines/detection_pipeline.py
```

### ✅ Why it works:
- You’re telling Python explicitly: “treat `hailo_apps_infra` as the top of your module tree”
- Works even if the package isn’t installed

### 🔥 Best for: quick local debugging and script runs

---

## ✅ 3. Using `pip install -e` + entry point in `pyproject.toml`
### Command (after setup):
```bash
hailo-detect
```

### You would define it like this in `pyproject.toml` (in `pipelines`):
```toml
[project.scripts]
hailo-detect = "hailo_pipelines.detection_pipeline:main"
```

### ✅ Why it works:
- Exposes your pipeline as a CLI command
- `main()` function becomes the entrypoint

### 🔥 Best for: end users and CLI interface

---

## ✅ 4. Run a dedicated script that imports and runs the pipeline
### Create a file like `run_detection.py`:
```python
from hailo_apps_infra.pipelines.hailo_pipelines import detection_pipeline

detection_pipeline.main()
```

Then run:
```bash
python run_detection.py
```

### ✅ Why it works:
- Keeps top-level runner file for each pipeline
- Simplifies launching for users or testing

### 🔥 Best for: training notebooks, simplified scripts, testing

---

## ❌ What *Doesn’t* Work

### ❌ This:
```bash
python -m hailo_pipelines.detection_pipeline
```

### ❌ And this:
```bash
python hailo_apps_infra/pipelines/hailo_pipelines/detection_pipeline.py
```

Both will break with:
- `ModuleNotFoundError`
- Broken relative imports

---

## 🧠 TL;DR: What Should You Use?

| Use Case | Recommended Option |
|----------|--------------------|
| Production CLI | `python -m hailo_apps_infra.pipelines.hailo_pipelines.detection_pipeline` |
| Local debugging | `PYTHONPATH=./hailo_apps_infra python hailo_apps_infra/pipelines/hailo_pipelines/detection_pipeline.py` |
| User-friendly CLI | `hailo-detect` via `pyproject.toml` |
| Notebook/testing | Small `run_*.py` wrappers |

---

Want me to wire up the `pyproject.toml` so you can use CLI like `hailo-detect` right now?