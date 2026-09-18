# Build-time networking installs the tools once. Production jobs use this image
# by sha256 digest with --network none; they never run apt or pip.
FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      blender python3 python3-pil python3-numpy \
      imagemagick libmagickcore-6.q16-7-extra ffmpeg krita xvfb xauth fonts-dejavu-core \
      libgl1-mesa-dri mesa-vulkan-drivers libvulkan1 ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 10001 --create-home --home-dir /home/creative creative

COPY runtime/imagemagick-policy.xml /etc/ImageMagick-6/policy.xml
COPY runtime/capabilities.py runtime/smoke.py /opt/creative-runtime/
COPY runtime/material-maker.lock.json runtime/install_material_maker.py runtime/material-maker-LICENSE.md /opt/creative-runtime/
COPY runtime/material-maker-renderer.gd /opt/creative-runtime/
RUN python3 /opt/creative-runtime/install_material_maker.py
RUN python3 /opt/creative-runtime/capabilities.py --require-base \
      --output /opt/creative-runtime/capabilities.json

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LIBGL_ALWAYS_SOFTWARE=1 \
    VK_ICD_FILENAMES=/opt/creative-runtime/lavapipe.json \
    OMP_NUM_THREADS=2 \
    OPENBLAS_NUM_THREADS=2 \
    QT_QPA_PLATFORM=xcb \
    HOME=/tmp/creative-home \
    XDG_CACHE_HOME=/tmp/creative-cache \
    XDG_CONFIG_HOME=/tmp/creative-config \
    XDG_RUNTIME_DIR=/tmp/creative-runtime \
    TMPDIR=/tmp

USER creative
WORKDIR /work
CMD ["python3", "/opt/creative-runtime/capabilities.py", "--require-base"]
