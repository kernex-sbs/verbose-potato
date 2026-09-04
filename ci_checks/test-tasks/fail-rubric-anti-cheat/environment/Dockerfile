FROM ubuntu:24.04
WORKDIR /app
RUN echo -n "benchmark" | sha256sum | awk '{print $1}' > /app/.secret-answer.txt
