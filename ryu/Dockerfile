FROM alpine:latest

ENV RYU_PACKAGES "curl python3 py3-setuptools py3-pip py3-greenlet py3-lxml py3-msgpack git"

RUN apk --update add apk-tools \
	&& apk add ${RYU_PACKAGES} \
	&& rm -rf /var/lib/apt/lists/* \
	&& git clone https://github.com/timofei-durakov/ryu \
	&& pip3 install --upgrade pip \
	&& cd ryu \
	&& git checkout novi_actions \
	&& pip3 install -r tools/pip-requires \
	&& pip3 install potsdb \
	&& python3 setup.py install \
	&& mkdir /files

ADD files/* /files/

EXPOSE 6653 8080

CMD ["/files/entrypoint.sh"]
