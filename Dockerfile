# See here https://hub.docker.com/r/gorialis/discord.py/
FROM gorialis/discord.py

# Authors
LABEL authors="31870999+KenwoodFox@users.noreply.github.com"

# Set the name of our app
ARG APP_NAME=bacubot
ENV APP_NAME=${APP_NAME}

# Get the current git version
ARG GIT_COMMIT
ENV GIT_COMMIT=$GIT_COMMIT

# App home
ARG HOME="/app"
ENV HOME=${HOME}

# Upgrade pip
RUN pip install --upgrade pip

# Set workdir
WORKDIR ${HOME}

# Copy in all requirements
ADD bacubot/requirements.txt .

# Install normal reqs
RUN pip install -r requirements.txt

# Copy in everything else
ADD . ${HOME}
# Add /bin to path
ENV PATH $PATH:${HOME}/bin

# Install bconsole
RUN apt update && \
    apt install -y bacula-console
ADD resources/bconsole.conf /etc/bacula/bconsole.conf

# Install our app in edit mode using pip
RUN pip install -e ${HOME}

# Drop root and change ownership of /app to app:app
RUN chown -R ${USER_ID}:${GROUP_ID} ${HOME}
USER ${USER_ID}

# Run the entrypoint bin
ENTRYPOINT ["entrypoint"]
