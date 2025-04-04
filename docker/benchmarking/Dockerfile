FROM opnfv/functest-kubernetes-smoke

ARG NETPERF_TAG=1104ce23f6c1758796e88f3c23b050099074cf81
ARG PLOTPERF_TAG=2455313f4b9581795a8f642243acaad472d91804

USER root
COPY plotperf.py.patch /tmp/plotperf.py.patch
RUN apk --no-cache add --update py3-matplotlib && \
    apk --no-cache add --virtual .build-deps --update patch go && \
    git clone https://github.com/kubernetes/perf-tests && \
    (cd perf-tests && git checkout $NETPERF_TAG) && \
    (cd perf-tests/network/benchmarks/netperf && go build -o /usr/local/bin/launch launch.go) && \
    curl https://raw.githubusercontent.com/girishkalele/pyplot-docker/$PLOTPERF_TAG/plotperf.py \
        --output /usr/local/bin/plotperf.py && \
    (cd /usr/local/bin && patch -p0 < /tmp/plotperf.py.patch && \
        mv plotperf.py plotperf && chmod a+x plotperf) && \
    rm -rf perf-tests /tmp/plotperf.py.patch && \
    apk del .build-deps
USER xtesting
COPY testcases.yaml /etc/xtesting/testcases.yaml
CMD ["run_tests", "-t", "all"]
