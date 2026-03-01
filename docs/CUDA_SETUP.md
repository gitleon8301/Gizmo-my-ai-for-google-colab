# Fedora CUDA Setup Guide for Gizmo MY-AI

This guide covers installing NVIDIA drivers and CUDA on Fedora Linux to enable
GPU-accelerated inference with the RTX 4080.

---

## 1. Check your GPU

```bash
lspci | grep -i nvidia
```

---

## 2. Install RPM Fusion (required for NVIDIA drivers)

```bash
sudo dnf install \
  https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm \
  https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm
```

---

## 3. Install the NVIDIA driver

```bash
sudo dnf install akmod-nvidia xorg-x11-drv-nvidia-cuda
```

> **Reboot after installation:**
> ```bash
> sudo reboot
> ```

After reboot, verify:

```bash
nvidia-smi
```

You should see your RTX 4080 listed with VRAM info.

---

## 4. Install CUDA Toolkit (optional — for compilation)

```bash
sudo dnf install cuda
```

Or download the runfile from [developer.nvidia.com/cuda-downloads](https://developer.nvidia.com/cuda-downloads).

---

## 5. Install PyTorch with CUDA support

```bash
# Inside your Gizmo virtual environment:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

Verify:

```bash
python3 -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

Expected output: `True  NVIDIA GeForce RTX 4080`

---

## 6. Install llama-cpp-python with CUDA support

```bash
CMAKE_ARGS="-DLLAMA_CUDA=on" pip install llama-cpp-python --upgrade --force-reinstall --no-cache-dir
```

---

## 7. Verify Gizmo detects your GPU

```bash
python3 -c "from modules.cuda_setup import setup_cuda; setup_cuda()"
```

Expected output:
```
   🟢 GPU: NVIDIA GeForce RTX 4080  (16.0 GB VRAM)
```

---

## 8. Troubleshooting

| Problem | Solution |
|---|---|
| `nvidia-smi: command not found` | Run step 3 again and reboot |
| `torch.cuda.is_available()` returns False | Reinstall PyTorch with CUDA (step 5) |
| llama.cpp uses CPU only | Reinstall llama-cpp-python with `LLAMA_CUDA=on` (step 6) |
| Driver conflict with Nouveau | `sudo grubby --update-kernel=ALL --args="modprobe.blacklist=nouveau"` |

---

## 9. Useful commands

```bash
# Monitor GPU usage in real time
watch -n 1 nvidia-smi

# Check CUDA version
nvcc --version

# Check PyTorch CUDA version
python3 -c "import torch; print(torch.version.cuda)"
```
