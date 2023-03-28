FROM gradescope/auto-builds:latest

# Set container metadata.
LABEL MAINTAINER="FirstName LastName <name@example.com>"
LABEL VERSION="1.0"

# install chrome, chromedriver
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get -y update \
    && apt-get install -y google-chrome-stable \
    && apt-get install -yqq unzip \
    && wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ \

# set display port to avoid crash
ENV DISPLAY=:99

### PYTHON 3.7 dependencies #####
RUN apt-get update && apt-get install -y checkinstall libreadline-gplv2-dev \
    libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev \
    libbz2-dev zlib1g-dev openssl libffi-dev python3-dev python3-setuptools liblzma-dev wget \
    && wget https://www.python.org/ftp/python/3.7.0/Python-3.7.0.tar.xz \
    && tar xf Python-3.7.0.tar.xz && cd Python-3.7.0 \
    && ./configure && make altinstall \
    && pip3.7 install --upgrade pip

COPY requirements.txt /autograder/source/
RUN  pip3.7 install -r /autograder/source/requirements.txt

# Copy project to the container
COPY run_autograder /autograder/run_autograder
COPY . /autograder/source/



# Run the autograder script.
CMD ["/autograder/run_autograder"]
