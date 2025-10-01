# Risk Assessment API

A FastAPI-based application for processing Control Self-Assessment (CSA) questionnaires and generating risk registers using AI.

## Features

- **Questionnaire Submission**: Submit CSA questionnaires for processing
- **Async Processing**: Background processing with status tracking
- **AI-Powered Analysis**: Uses Omni LLM server for risk assessment
- **MongoDB Storage**: Persistent storage for questionnaires and reports
- **REST API**: RESTful endpoints with automatic OpenAPI documentation
- **Export Capabilities**: Export risk registers in JSON/CSV formats

## Project Structure

```
app/
├── api/
│   └── routes/
│       ├── questionnaire.py    # Questionnaire submission endpoints
│       └── reports.py          # Report generation endpoints
├── core/
│   └── config.py              # Configuration settings
├── database/
│   └── mongodb.py             # Database connection
├── models/
│   └── schemas.py             # Pydantic models
└── services/
    ├── llm_service.py         # LLM integration
    └── risk_service.py        # Risk processing logic
```

## API Endpoints

### Questionnaire Management
- `POST /api/v1/questionnaire/submit` - Submit questionnaire for processing
- `GET /api/v1/questionnaire/{id}/status` - Check processing status

### Reports
- `GET /api/v1/reports/{id}` - Get processed risk register
- `GET /api/v1/reports/{id}/export` - Export risk register (JSON/CSV)

### Documentation
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

## Setup

1. **Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start MongoDB**
   ```bash
   # Using Docker
   docker run -d -p 27017:27017 mongo:latest
   
   # Or install MongoDB locally
   ```

4. **Start Omni LLM Server**
   ```bash
   # Make sure your Omni server is running on localhost:10240
   ```

5. **Run the Application**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `DATABASE_NAME` | Database name | `risk_assessment` |
| `OMNI_BASE_URL` | Omni server URL | `http://localhost:10240/v1` |
| `OMNI_API_KEY` | Omni API key | `mlx-omni-server` |
| `OMNI_MODEL` | LLM model name | `Qwen3-4B-8bit` |

## Usage Example

1. **Submit Questionnaire**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/questionnaire/submit" \
     -H "Content-Type: application/json" \
     -d '{
       "questionnaire_data": "Your CSA questionnaire text here...",
       "department": "Finance",
       "submitted_by": "John Doe"
     }'
   ```

2. **Check Status**
   ```bash
   curl "http://localhost:8000/api/v1/questionnaire/{questionnaire_id}/status"
   ```

3. **Get Report**
   ```bash
   curl "http://localhost:8000/api/v1/reports/{questionnaire_id}"
   ```

## Development

- **FastAPI**: Modern async web framework
- **Motor**: Async MongoDB driver
- **Pydantic**: Data validation and serialization
- **OpenAI**: LLM integration (compatible with Omni server)

## License

This project is for Proof of Concept (PoC) purposes.
