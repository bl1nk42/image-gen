# Image Generation Microservice

A high-performance microservice for generating images from text prompts using Google Cloud Vertex AI Imagen 2, built with FastAPI and featuring intelligent caching for cost optimization.

## Features

- **Text-to-Image Generation**: Generate high-quality images from text prompts using Vertex AI Imagen 2
- **Intelligent Caching**: Automatic caching system to reduce API calls and costs
- **Cloud Storage Integration**: Automatic upload to Google Cloud Storage with public URLs
- **Flexible Caching Backend**: Supports both Redis and in-memory caching
- **RESTful API**: Clean, well-documented API endpoints
- **Container Ready**: Docker and Docker Compose support for easy deployment
- **Health Monitoring**: Built-in health check endpoints

## API Endpoints

### Generate Image
```
POST /v1/images/generate
```

**Request Body:**
```json
{
  "prompt": "A beautiful sunset over mountains",
  "style": "photorealistic",
  "aspect_ratio": "16:9"
}
```

**Response:**
```json
{
  "status": "success",
  "from_cache": false,
  "image_url": "https://storage.googleapis.com/your-bucket/image.png",
  "created_at": "2025-07-25T12:00:00Z"
}
```

### Health Check
```
GET /health
```

**Response:**
```json
{
  "status": "ok"
}
```

## Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud Project with Vertex AI API enabled
- Google Cloud Storage bucket
- Service Account with appropriate permissions
- Redis (optional, for distributed caching)

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd image-generation-service
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Set up Google Cloud credentials:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

5. **Run the service:**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Docker Deployment

### Using Docker

1. **Build the image:**
```bash
docker build -t image-generation-service .
```

2. **Run the container:**
```bash
docker run -p 8000:8000 \
  -e GOOGLE_CLOUD_PROJECT=your-project-id \
  -e GOOGLE_CLOUD_BUCKET=your-bucket \
  -v /path/to/credentials:/app/credentials:ro \
  image-generation-service
```

### Using Docker Compose

1. **Set up credentials:**
```bash
mkdir credentials
cp /path/to/service-account-key.json credentials/
```

2. **Configure environment:**
```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_BUCKET=your-bucket
```

3. **Start services:**
```bash
docker-compose up -d
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GOOGLE_CLOUD_PROJECT` | Google Cloud Project ID | - | Yes |
| `GOOGLE_CLOUD_BUCKET` | Cloud Storage bucket name | - | Yes |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account key | - | Yes |
| `REDIS_URL` | Redis connection URL | - | No |
| `CACHE_EXPIRATION_HOURS` | Cache expiration time | 24 | No |
| `API_HOST` | API host address | 0.0.0.0 | No |
| `API_PORT` | API port number | 8000 | No |
| `VERTEX_AI_LOCATION` | Vertex AI region | us-central1 | No |

### Google Cloud Setup

1. **Enable APIs:**
   - Vertex AI API
   - Cloud Storage API

2. **Create Service Account:**
   - Vertex AI User role
   - Storage Admin role (or Storage Object Admin)

3. **Create Storage Bucket:**
   - Public read access for generated images
   - Appropriate lifecycle policies

## Caching System

The service features an intelligent caching system that:

- **Reduces Costs**: Avoids duplicate API calls for identical prompts
- **Improves Performance**: Instant responses for cached images
- **Flexible Backend**: Supports Redis for distributed caching or in-memory for single instance
- **Automatic Expiration**: Configurable cache expiration (default: 24 hours)
- **Cache Key Strategy**: Uses SHA256 hash of prompt + parameters

### Cache Key Format
```
img_cache:{sha256_hash_of_parameters}
```

## API Documentation

Once the service is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Monitoring and Health Checks

### Health Check Endpoint
```bash
curl http://localhost:8000/health
```

### Docker Health Check
The Docker container includes built-in health checks that monitor the service status.

## Error Handling

The service provides comprehensive error handling with appropriate HTTP status codes:

- **400 Bad Request**: Invalid input parameters
- **500 Internal Server Error**: Service or external API errors

Error responses follow this format:
```json
{
  "status": "error",
  "message": "Error description"
}
```

## Performance Considerations

- **Caching**: Significantly reduces response time for repeated requests
- **Async Operations**: Non-blocking I/O for better concurrency
- **Connection Pooling**: Efficient resource utilization
- **Image Optimization**: Automatic format selection and compression

## Security

- **CORS Configuration**: Configurable cross-origin resource sharing
- **Input Validation**: Comprehensive request validation
- **Service Account**: Secure Google Cloud authentication
- **Container Security**: Non-root user execution

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify service account credentials
   - Check API permissions

2. **Storage Errors**
   - Verify bucket exists and is accessible
   - Check storage permissions

3. **Cache Issues**
   - Verify Redis connection (if using Redis)
   - Check cache configuration

### Logs

Enable detailed logging by setting:
```bash
export PYTHONPATH=/app
export LOG_LEVEL=DEBUG
```

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please refer to the project documentation or create an issue in the repository.



## Modal + ComfyUI GPU backend

The original FastAPI/Vertex AI service remains available. For self-hosted image generation through Hermes, this repository now includes `modal_backend.py`, which runs ComfyUI on a Modal GPU and keeps model/output data in Modal Volumes.

```bash
python -m pip install 'modal>=0.73.82,<1'
modal setup
modal volume create agent-mcp-models --version=2
modal volume create agent-mcp-image-data --version=2
modal deploy modal_backend.py
```

Copy an API-format ComfyUI workflow exported from **Queue Prompt > Save (API Format)** to `/data/workflows/qwen-image-api.json`. The backend replaces `{prompt}`, `{negative_prompt}`, `{width}`, `{height}`, and `{seed}` placeholders before queueing. Qwen-Image model placement and workflow requirements are documented in [`workflows/README.md`](workflows/README.md).

Install the Hermes provider from [`plugins/image_gen/modal-memory`](plugins/image_gen/modal-memory), set `MODAL_BACKEND_URL` to the generated Modal endpoint, and select `image_gen.provider: modal`. The plugin provides the documented provider, model catalog, deterministic prompt normalization, local JSONL memory, CSV training manifest, and the requested memory/image tools.

See [`MODAL_COMFYUI_GUIDE.md`](MODAL_COMFYUI_GUIDE.md) for the complete setup, secrets, workflow, and operational guidance. Use [`verify_modal_project.py`](verify_modal_project.py) for local static/smoke validation.

## Production visual skill pack

The project now ships a real workflow layer rather than a flat list of prompt snippets. [`claude-plugin/SKILLS_INDEX.md`](claude-plugin/SKILLS_INDEX.md) documents the routing system and the nine specialist skills: visual-production-router, image-generation, photo-restoration, Nothing design, memory recall, prompt engineering, character-story video, meme generation, and general video production. Each skill has a concrete workflow, decision gates, quality checks, and references; exact binary/API operations remain in tools.

Install the whole integration set with `python install.py --claude`. The installer copies the Hermes provider and the Claude skill pack, including commands, the style-curator agent, and metadata-only lifecycle hooks. Validate the pack with:

```bash
python3 claude-plugin/scripts/validate_skill_pack.py
python3 verify_modal_project.py
```

The skills deliberately distinguish deterministic work from generative work: Memegen.link is used for classic captioned memes, Mermaid/plotting is preferred for exact diagrams and charts, restoration uses preservation gates, and video/story workflows require reference images and continuity manifests before execution.
