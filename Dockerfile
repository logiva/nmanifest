FROM fluxcd/flux:1.15.0

RUN /sbin/apk add python3 && pip3 install nmanifest==0.0.2
