FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o brainsait-cli ./main.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates git python3 nodejs npm docker
WORKDIR /root/

COPY --from=builder /app/brainsait-cli .

CMD ["./brainsait-cli"]
