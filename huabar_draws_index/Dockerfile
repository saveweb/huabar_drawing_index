ARG APP=huabar_draws_index

FROM golang:latest AS builder
ARG APP
COPY . /src

WORKDIR /src

RUN CGO_ENABLED=1 go build -ldflags="-extldflags=-static -s -w" -o $APP

FROM alpine:latest
ARG APP

COPY --from=builder /src/$APP /app/$APP

RUN chmod +x /app/$APP

WORKDIR /app

CMD ["/app/huabar_draws_index"]