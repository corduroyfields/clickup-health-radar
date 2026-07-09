# Dockerfile — the recipe Cloud Build follows to package the radar as a
# container image: our code + Python 3.12 + the exact locked dependencies,
# frozen into one runnable artifact that behaves the same on any machine.

# Start from the official uv image: a slim Debian Linux with Python 3.12
# and uv preinstalled — the same toolchain we use on the laptop.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Copy ONLY the dependency manifests first, then install. Docker caches
# each step: as long as these two files don't change, rebuilds skip the
# (slow) dependency install even when the code below changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
# --frozen = install exactly what uv.lock says, or fail loudly.
# This is why uv.lock is committed: reproducibility IS the lockfile.

# Now the code. Just the radar — no seed script, no notes, no .env
# (see .dockerignore: the token must never be baked into an image).
COPY radar.py radar2.py ./

# What runs when the container starts. --no-sync: the venv was built two
# steps up; don't re-resolve at runtime.
CMD ["uv", "run", "--no-sync", "python", "radar2.py"]
