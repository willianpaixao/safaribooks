# Docker Usage Guide for SafariBooks

This guide explains how to use the SafariBooks downloader with Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose (optional, but recommended)

## Building the Docker Image

Build the Docker image from the project directory:

```bash
docker build -t safaribooks .
```

## Usage

### Method 1: Using Docker Compose (Recommended)

1. **Download a book using SSO cookies** (recommended method):

   ```bash
   # First, copy your cookies.json file to the project directory
   # Then run:
   docker-compose run --rm safaribooks --book-id <BOOK_ID>
   ```

2. **Download a book with credentials**:

   ```bash
   docker-compose run --rm safaribooks --cred "email@example.com:password" --book-id <BOOK_ID>
   ```

3. **Interactive shell access**:

   ```bash
   docker-compose run --rm safaribooks-interactive
   ```

### Method 2: Using Docker directly

1. **Download a book using SSO cookies**:

   ```bash
   docker run --rm \
     -v $(pwd)/downloads:/app/downloads \
     -v $(pwd)/cookies.json:/app/cookies.json:ro \
     safaribooks --book-id <BOOK_ID>
   ```

2. **Download a book with credentials**:

   ```bash
   docker run --rm \
     -v $(pwd)/downloads:/app/downloads \
     safaribooks --cred "email@example.com:password" --book-id <BOOK_ID>
   ```

3. **Interactive mode**:

   ```bash
   docker run -it --rm \
     -v $(pwd)/downloads:/app/downloads \
     -v $(pwd)/cookies.json:/app/cookies.json:ro \
     safaribooks /bin/bash
   ```

## Volume Mounts

- `./downloads:/app/downloads` - Persists downloaded EPUB files to your local `downloads` directory
- `./cookies.json:/app/cookies.json:ro` - Mounts your cookies file for SSO authentication (read-only)

## Environment Variables

You can set the following environment variables:

- `TZ` - Set the timezone (default: UTC)

## Examples

1. **Download multiple books**:

   ```bash
   docker-compose run --rm safaribooks --book-id 9781234567890 9780987654321
   ```

2. **Download with Kindle-friendly formatting**:

   ```bash
   docker-compose run --rm safaribooks --kindle --book-id 9781234567890
   ```

3. **Debug mode**:

   ```bash
   docker-compose run --rm safaribooks --log-level DEBUG --book-id 9781234567890
   ```

## SSO Authentication Setup

For SSO (Single Sign-On) authentication:

1. Log in to Safari Books Online in your browser
2. Extract cookies using browser developer tools or extensions
3. Save cookies to `cookies.json` in the project directory
4. The Docker container will automatically use these cookies

## Notes

- Downloaded books will be saved in the `downloads` directory on your host machine
- The container runs as a non-root user for security
- Logs are displayed in real-time during the download process
- Use `--rm` flag to automatically remove the container after execution

## Troubleshooting

- If you get permission errors, ensure the `downloads` directory is writable
- For SSO issues, verify your `cookies.json` file is properly formatted and up-to-date
- Check the logs with `--log-level DEBUG` for detailed error information
