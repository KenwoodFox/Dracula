# See here https://hub.docker.com/r/gorialis/discord.py/
#FROM gorialis/discord.py
FROM python:3.10-slim

# Authors
LABEL authors="31870999+KenwoodFox@users.noreply.github.com"

# Set the name of our app
ARG APP_NAME=dracula
ENV APP_NAME=${APP_NAME}

# Get the current git version
ARG GIT_COMMIT
ENV GIT_COMMIT=$GIT_COMMIT

# App home
ARG HOME="/app"
ENV HOME=${HOME}

# Set workdir
WORKDIR ${HOME}

# Upgrade pip
RUN pip install --upgrade pip --no-cache-dir

# Install and configure bconsole
RUN apt update && apt install bacula-console -y

# Copy in all requirements
ADD requirements requirements/

# Install normal reqs
RUN pip install -r requirements/requirements.txt --no-cache-dir

# Copy in everything else
ADD . ${HOME}
# Add /bin to path
ENV PATH $PATH:${HOME}/bin

# Install our app in edit mode using pip
RUN pip install -e ${HOME} --no-cache-dir

# Drop root and change ownership of /app to app:app
RUN chown -R ${USER_ID}:${GROUP_ID} ${HOME}
USER ${USER_ID}

# Run the entrypoint bin
ENTRYPOINT ["entrypoint"]
