# OpenTryOn MCP Server - Architecture

This document describes the architecture and design of the OpenTryOn MCP Server.

## Overview

The OpenTryOn MCP Server is a Model Context Protocol (MCP) server that exposes OpenTryOn's AI-powered fashion tech capabilities to AI agents and applications. It follows a modular architecture with clear separation of concerns.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         MCP Clients                              │
│  (Claude Desktop, Custom Agents, Other MCP-compatible clients)   │
└───────────────────────────────┬─────────────────────────────────┘
                                │ MCP Protocol (stdio)
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                      OpenTryOn MCP Server                        │
│                         (server.py)                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              MCP Protocol Handler                         │  │
│  │  - Tool Registration                                      │  │
│  │  - Request/Response Processing                            │  │
│  │  - Error Handling                                         │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                      │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │                  Tool Router                              │  │
│  │  Routes requests to appropriate tool implementations      │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐   ┌────────▼────────┐   ┌────▼──────────┐
│   Tools      │   │     Utils       │   │   Config      │
│              │   │                 │   │               │
│ Virtual      │   │ Image Utils     │   │ Environment   │
│ Try-On       │   │ - Validation    │   │ Variables     │
│ - Nova       │   │ - Loading       │   │               │
│ - Kling      │   │ - Encoding      │   │ API Keys      │
│ - Segmind    │   │                 │   │               │
│              │   │ Validation      │   │ Settings      │
│ Image Gen    │   │ - Aspect Ratios │   │               │
│ - Nano       │   │ - Resolutions   │   │               │
│   Banana     │   │ - Parameters    │   │               │
│ - FLUX.2     │   │                 │   │               │
│ - Luma AI    │   └─────────────────┘   └───────────────┘
│              │                                  │
│ Video Gen    │                                  │
│ - Luma Ray   │                                  │
│              │                                  │
│ Preprocessing│                                  │
│ - Segment    │                                  │
│ - Extract    │                                  │
│              │                                  │
│ Datasets     │                                  │
│ - Fashion-   │                                  │
│   MNIST      │                                  │
│ - VITON-HD   │                                  │
└──────┬───────┘                                  │
       │                                          │
       │ Uses                                     │
       │                                          │
┌──────▼──────────────────────────────────────────▼──────┐
│              OpenTryOn Core Library                     │
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   API       │  │ Preprocessing │  │  Datasets    │ │
│  │  Adapters   │  │   Pipeline    │  │   Loaders    │ │
│  └─────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────┬───────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐  ┌─────────▼────────┐  ┌────────▼────────┐
│  External APIs │  │  ML Models       │  │  File System    │
│                │  │                  │  │                 │
│ - AWS Bedrock  │  │ - U2Net          │  │ - Input Images  │
│ - Kling AI     │  │ - SAM2           │  │ - Output Images │
│ - Segmind      │  │ - OpenPose       │  │ - Datasets      │
│ - Google       │  │                  │  │ - Temp Files    │
│   Gemini       │  │                  │  │                 │
│ - BFL (FLUX.2) │  │                  │  │                 │
│ - Luma AI      │  │                  │  │                 │
└────────────────┘  └──────────────────┘  └─────────────────┘
```

## Component Details

### 1. MCP Server Core (`server.py`)

**Responsibilities:**
- Implement MCP protocol
- Register and expose tools
- Handle incoming requests
- Route to appropriate tool implementations
- Format responses
- Error handling and logging

**Key Functions:**
- `list_tools()`: Returns list of available tools
- `call_tool()`: Executes requested tool
- `main()`: Server entry point

### 2. Tools Module (`tools/`)

**Structure:**
```
tools/
├── __init__.py           # Tool exports
├── virtual_tryon.py      # Virtual try-on implementations
├── image_gen.py          # Image generation implementations
├── video_gen.py          # Video generation implementations
├── preprocessing.py      # Preprocessing implementations
└── datasets.py           # Dataset loading implementations
```

**Responsibilities:**
- Implement tool logic
- Validate inputs
- Call OpenTryOn library functions
- Handle API interactions
- Process results
- Save outputs

**Design Pattern:**
Each tool function follows a consistent pattern:
1. Validate inputs
2. Initialize appropriate adapter/module
3. Execute operation
4. Process results
5. Save outputs (if requested)
6. Return structured response

### 3. Utils Module (`utils/`)

**Structure:**
```
utils/
├── __init__.py           # Utility exports
├── image_utils.py        # Image handling utilities
└── validation.py         # Input validation utilities
```

**Responsibilities:**
- Image loading/saving
- Base64 encoding/decoding
- URL validation
- Parameter validation
- File system operations

### 4. Configuration (`config.py`)

**Responsibilities:**
- Load environment variables
- Manage API keys
- Configure server settings
- Validate configuration
- Provide status information

**Key Features:**
- Automatic `.env` loading
- Configuration validation
- Status reporting
- Default values

## Data Flow

### Example: Virtual Try-On Request

```
1. Client Request
   ↓
2. MCP Server receives request via stdio
   ↓
3. Server validates request format
   ↓
4. Router identifies tool: virtual_tryon_nova
   ↓
5. Tool function called with arguments
   ↓
6. Tool validates inputs (image paths, parameters)
   ↓
7. Tool initializes AmazonNovaCanvasVTONAdapter
   ↓
8. Adapter calls AWS Bedrock API
   ↓
9. API returns generated images
   ↓
10. Tool saves images to disk
    ↓
11. Tool returns structured response
    ↓
12. Server formats response as TextContent
    ↓
13. Response sent to client via stdio
```

## Error Handling

The server implements multi-layer error handling:

1. **Input Validation Layer**
   - Validates file paths and URLs
   - Checks parameter ranges
   - Verifies required fields

2. **Tool Execution Layer**
   - Try-catch blocks around tool logic
   - Graceful degradation
   - Detailed error messages

3. **API Interaction Layer**
   - Network error handling
   - API quota management
   - Timeout handling

4. **Response Layer**
   - Consistent error format
   - Error context inclusion
   - Stack trace logging (debug mode)

## Security Considerations

1. **API Key Management**
   - Keys stored in environment variables
   - Never exposed in responses
   - Loaded from secure `.env` file

2. **File System Access**
   - Path validation to prevent traversal
   - Sandboxed temp directory
   - File size limits

3. **Input Sanitization**
   - URL validation
   - File type checking
   - Parameter range validation

4. **Resource Management**
   - Temp file cleanup
   - Memory limits
   - Request timeouts

## Performance Optimizations

1. **Lazy Loading**
   - Models loaded on-demand
   - Adapters initialized per-request

2. **Caching**
   - Configuration cached
   - Validation results cached

3. **Async Operations**
   - MCP protocol uses async/await
   - Non-blocking I/O

4. **Resource Cleanup**
   - Automatic temp file cleanup
   - Connection pooling for APIs

## Extensibility

### Adding New Tools

1. Create tool function in appropriate `tools/*.py` file
2. Add tool definition to `TOOLS` list in `server.py`
3. Add routing logic in `call_tool()` function
4. Update documentation

Example:

```python
# In tools/new_feature.py
def new_tool(param1: str, param2: int) -> dict:
    """New tool implementation."""
    try:
        # Implementation
        return {"success": True, "result": "..."}
    except Exception as e:
        return {"success": False, "error": str(e)}

# In server.py
Tool(
    name="new_tool",
    description="Description of new tool",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "..."},
            "param2": {"type": "integer", "description": "..."}
        },
        "required": ["param1", "param2"]
    }
)
```

### Adding New API Providers

1. Create adapter in OpenTryOn core library
2. Create tool wrapper in `tools/` module
3. Add configuration in `config.py`
4. Register tool in `server.py`
5. Update documentation

## Testing Strategy

1. **Unit Tests**
   - Test individual tool functions
   - Mock API calls
   - Validate error handling

2. **Integration Tests**
   - Test with real APIs (using test keys)
   - Validate end-to-end flows
   - Check file I/O

3. **MCP Protocol Tests**
   - Validate protocol compliance
   - Test request/response formats
   - Check error responses

## Deployment

### Local Development
```bash
python server.py
```

### Claude Desktop Integration
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "opentryon": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {"PYTHONPATH": "/path/to/opentryon"}
    }
  }
}
```

### Docker Deployment (Future)
```dockerfile
FROM python:3.10
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "server.py"]
```

## Monitoring and Logging

1. **Server Logs**
   - Startup configuration status
   - Request/response logging
   - Error tracking

2. **Metrics** (Future)
   - Request count per tool
   - Average response time
   - Error rate
   - API quota usage

## Future Enhancements

1. **Caching Layer**
   - Cache generated images
   - Cache dataset metadata
   - Redis integration

2. **Batch Processing**
   - Process multiple requests
   - Queue management
   - Priority handling

3. **Streaming Support**
   - Stream video generation progress
   - Stream large image results
   - Real-time status updates

4. **Advanced Error Recovery**
   - Automatic retry logic
   - Fallback providers
   - Circuit breaker pattern

5. **Rate Limiting**
   - Per-tool rate limits
   - Per-client quotas
   - Adaptive throttling

---

Made with ❤️ by [TryOn Labs](https://www.tryonlabs.ai)

