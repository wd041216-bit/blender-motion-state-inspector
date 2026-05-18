FROM ubuntu:24.04
RUN apt-get update && apt-get install -y wget blender python3-pip && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /root/.config/blender/4.2/scripts/addons/motion_state_inspector
WORKDIR /workspace
