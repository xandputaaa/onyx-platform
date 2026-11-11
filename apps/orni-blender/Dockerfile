FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    blender xvfb fluxbox x11vnc novnc websockify ca-certificates \
    mesa-utils libgl1-mesa-dri libegl1 libxkbcommon0 fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
COPY start.sh /usr/local/bin/orni-blender-start
RUN chmod +x /usr/local/bin/orni-blender-start
ENV DISPLAY=:1 LIBGL_ALWAYS_SOFTWARE=1
EXPOSE 6080
CMD ["/usr/local/bin/orni-blender-start"]
