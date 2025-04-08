# Stage 1: Install cross and build the app using it
FROM rust:1.83 as builder

# Use the official Rust image as the base
WORKDIR /usr/src/myapp

# Copy your source files
COPY . .

# Build the project in release mode
RUN cargo build --release

# Set the startup command to run the compiled binary
ENTRYPOINT  [ "./target/release/redis2ws", "--broker", "--host", "0.0.0.0"]

