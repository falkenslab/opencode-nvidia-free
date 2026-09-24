# OpenCode en una versión fija, con Python y pytest para la tarea.
FROM node:22-bookworm-slim

ARG OPENCODE_VERSION=1.18.32

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pytest git ca-certificates coreutils \
 && rm -rf /var/lib/apt/lists/* \
 && ln -s /usr/bin/python3 /usr/local/bin/python

RUN npm install -g "opencode-ai@${OPENCODE_VERSION}" && opencode --version

# Configuración global de OpenCode dentro del contenedor (aislado): permisos totales y proveedor nvidia vía proxy.
COPY opencode.json /root/.config/opencode/opencode.json
COPY run_model.sh /usr/local/bin/run_model
RUN chmod +x /usr/local/bin/run_model

RUN git config --global user.email "experiment@falkenslab" && git config --global user.name "experiment"

WORKDIR /work
