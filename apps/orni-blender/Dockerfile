FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    blender python3 ffmpeg espeak libass9 xvfb fluxbox x11vnc novnc websockify ca-certificates \
    mesa-utils libgl1-mesa-dri libegl1 libxkbcommon0 fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
COPY start.sh /usr/local/bin/orni-blender-start
COPY automation.py /workspace/automation.py
COPY cozo_rig.py /workspace/cozo_rig.py
COPY cozo_boutique.py /workspace/cozo_boutique.py
COPY render_cozo_episode.py /workspace/render_cozo_episode.py
COPY cozo_postprocess.py /workspace/cozo_postprocess.py
RUN python3 -m py_compile /workspace/automation.py /workspace/cozo_rig.py /workspace/cozo_boutique.py /workspace/render_cozo_episode.py /workspace/cozo_postprocess.py
COPY viewer.html /workspace/viewer.html
RUN chmod +x /usr/local/bin/orni-blender-start
ENV DISPLAY=:1 LIBGL_ALWAYS_SOFTWARE=1
EXPOSE 6080
CMD ["/usr/local/bin/orni-blender-start"]
