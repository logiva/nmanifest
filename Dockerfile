FROM fluxcd/flux:1.20.0

RUN /sbin/apk add python3 py3-pip && pip3 install nmanifest==0.0.2
