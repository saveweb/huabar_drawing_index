FROM golang:latest AS builder
COPY . /src

WORKDIR /src

RUN CGO_ENABLED=1 go build -ldflags="-extldflags=-static -s -w" -o huabar_draws_index

FROM alpine:latest

COPY --from=builder /src/huabar_draws_index /app/huabar_draws_index
    
RUN chmod +x /app/huabar_draws_index

WORKDIR /app

CMD ["/app/huabar_draws_index"]
