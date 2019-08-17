FROM continuumio/miniconda3

RUN apt-get update -qq && apt-get install -y locales -qq && echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && locale-gen && apt-get install -y libgl1-mesa-glx
# apt-get install -y software-properties-common
# RUN /usr/sbin/update-locale LANG=en_US.UTF-8

ENV LANG=en_US.UTF-8 LANGUAGE=en_US.UTF-8 LC_ALL=en_US.UTF-8

ADD https://github.com/alexei-gl/language-learning/raw/master/environment.yml /tmp/environment.yml

WORKDIR /tmp

RUN conda update -y -q conda && conda env create -f environment.yml -q && useradd -ms /bin/bash opencog-ull && chown -R opencog-ull:opencog-ull /opt/conda

USER opencog-ull

CMD /bin/bash

WORKDIR /home/opencog-ull

ONBUILD USER root