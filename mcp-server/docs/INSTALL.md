# OpenTryOn MCP Server - Installation Guide

Complete installation guide for the OpenTryOn MCP Server.

## Prerequisites

- **Python 3.10+** installed
- **pip** package manager
- **Git** (for cloning the repository)

## Step-by-Step Installation

### Step 1: Install OpenTryOn Core Library

The MCP server depends on the OpenTryOn core library. Install it first:

```bash
# Navigate to OpenTryOn root directory
cd /path/to/opentryon

# Install OpenTryOn in editable mode
pip install -e .
```

This will install all OpenTryOn dependencies including:
- PyTorch
- diffusers
- transformers
- PIL/Pillow
- And more...

### Step 2: Install MCP Server Dependencies

```bash
# Navigate to MCP server directory
cd mcp-server

# Install MCP server specific dependencies
pip install -r requirements.txt
```

This installs:
- `mcp>=1.0.0` - Model Context Protocol library
- `pydantic>=2.0.0` - Data validation
- `python-dotenv>=1.0.0` - Environment variable management

### Step 3: Configure Environment Variables

Create or update the `.env` file in the OpenTryOn root directory:

```bash
# Navigate to OpenTryOn root
cd /path/to/opentryon

# Create .env file if it doesn't exist
touch .env

# Edit .env file with your favorite editor
nano .env  # or vim, code, etc.
```

Add your API keys:

```env
# AWS Credentials (for Amazon Nova Canvas)
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AMAZON_NOVA_REGION=us-east-1

# Kling AI
KLING_AI_API_KEY=your_kling_api_key_here
KLING_AI_SECRET_KEY=your_kling_secret_key_here
KLING_AI_BASE_URL=https://api-singapore.klingai.com

# Segmind
SEGMIND_API_KEY=your_segmind_api_key_here

# Google Gemini (Nano Banana)
GEMINI_API_KEY=your_gemini_api_key_here

# BFL API (FLUX.2)
BFL_API_KEY=your_bfl_api_key_here

# Luma AI
LUMA_AI_API_KEY=your_luma_ai_api_key_here

# U2Net Checkpoint (for preprocessing)
U2NET_CLOTH_SEG_CHECKPOINT_PATH=cloth_segm.pth
```

**Note**: You don't need all API keys. Configure only the services you plan to use.

### Step 4: Download Required Model Checkpoints (Optional)

If you plan to use preprocessing tools, download the U2Net checkpoint:

```bash
# Download from huggingface-cloth-segmentation repository
# Follow instructions at: https://github.com/wildoctopus/huggingface-cloth-segmentation
```

### Step 5: Verify Installation

Run the test suite to verify everything is set up correctly:

```bash
cd /path/to/opentryon/mcp-server
python test_server.py
```

Expected output:
```
============================================================
OpenTryOn MCP Server - Test Suite
============================================================

✓ PASSED: Directory Structure
✓ PASSED: Configuration
✓ PASSED: Module Imports
✓ PASSED: OpenTryOn Library
✓ PASSED: Tool Definitions

Total: 5/5 tests passed

✓ All tests passed! Server is ready to use.
```

## Integration Options

### Option 1: Claude Desktop Integration

1. **Locate Claude Desktop config file:**
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

2. **Edit the config file:**

```json
{
  "mcpServers": {
    "opentryon": {
      "command": "python",
      "args": [
        "/absolute/path/to/opentryon/mcp-server/server.py"
      ],
      "env": {
        "PYTHONPATH": "/absolute/path/to/opentryon"
      }
    }
  }
}
```

**Important**: Replace `/absolute/path/to/opentryon` with the actual absolute path to your OpenTryOn installation.

3. **Restart Claude Desktop**

4. **Verify integration:**
   - Open Claude Desktop
   - Look for the tools icon (🔧) in the interface
   - You should see OpenTryOn tools available

### Option 2: Standalone Server

Run the server directly:

```bash
cd /path/to/opentryon/mcp-server
python server.py
```

The server will:
1. Load configuration
2. Print status of configured services
3. Start listening for MCP protocol messages via stdio

### Option 3: Programmatic Usage

Use the tools directly in your Python code:

```python
import sys
sys.path.insert(0, '/path/to/opentryon')

from mcp_server.tools import virtual_tryon_nova

result = virtual_tryon_nova(
    source_image="person.jpg",
    reference_image="garment.jpg",
    output_dir="outputs"
)
print(result)
```

## Troubleshooting

### Issue: "No module named 'mcp'"

**Solution**: Install MCP server dependencies:
```bash
cd mcp-server
pip install -r requirements.txt
```

### Issue: "No module named 'tryon'"

**Solution**: Install OpenTryOn core library:
```bash
cd /path/to/opentryon
pip install -e .
```

### Issue: "No module named 'torch'"

**Solution**: Install PyTorch (OpenTryOn dependency):
```bash
pip install torch torchvision
```

### Issue: "API key not configured"

**Solution**: 
1. Check that `.env` file exists in OpenTryOn root directory
2. Verify API keys are correctly set
3. Ensure no extra spaces or quotes around values
4. Restart the server after updating `.env`

### Issue: "Permission denied" when accessing .env

**Solution**: 
1. Check file permissions: `ls -la .env`
2. Make file readable: `chmod 644 .env`
3. Ensure you own the file: `chown $USER .env`

### Issue: Server starts but tools don't work

**Solution**:
1. Run test suite: `python test_server.py`
2. Check which services are configured
3. Verify API keys are valid
4. Check network connectivity
5. Review server logs for errors

### Issue: "ModuleNotFoundError" for specific modules

**Solution**: Install missing dependencies:
```bash
# For PIL/Pillow
pip install Pillow

# For requests
pip install requests

# For dotenv
pip install python-dotenv

# Or install all OpenTryOn dependencies
cd /path/to/opentryon
pip install -r requirements.txt
```

## Verification Checklist

Before using the MCP server, verify:

- [ ] Python 3.10+ is installed
- [ ] OpenTryOn core library is installed (`pip install -e .`)
- [ ] MCP server dependencies are installed (`pip install -r requirements.txt`)
- [ ] `.env` file is configured with API keys
- [ ] Test suite passes (`python test_server.py`)
- [ ] At least one service is configured (check test output)

## Getting API Keys

### Amazon Nova Canvas (AWS Bedrock)
1. Sign up for AWS account
2. Enable Bedrock in AWS Console
3. Request access to Nova Canvas model
4. Create IAM user with Bedrock permissions
5. Generate access key and secret key

### Kling AI
1. Visit [Kling AI Developer Portal](https://app.klingai.com/)
2. Sign up for account
3. Navigate to API section
4. Generate API key and secret key

### Segmind
1. Visit [Segmind](https://www.segmind.com/)
2. Sign up for account
3. Navigate to API section
4. Generate API key

### Google Gemini
1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Sign in with Google account
3. Navigate to [API Keys](https://aistudio.google.com/app/apikey)
4. Create API key

### BFL (FLUX.2)
1. Visit [BFL AI](https://docs.bfl.ai/)
2. Sign up for account
3. Generate API key from dashboard

### Luma AI
1. Visit [Luma Labs](https://lumalabs.ai/)
2. Sign up for account
3. Navigate to [API section](https://lumalabs.ai/api)
4. Generate API key

## Next Steps

After successful installation:

1. **Read the documentation**
   - [README.md](../README.md) - Complete feature overview
   - [QUICKSTART.md](QUICKSTART.md) - Quick start guide
   - [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture details

2. **Try examples**
   - [examples/example_usage.py](examples/example_usage.py) - Python examples

3. **Integrate with your agent**
   - Use with Claude Desktop
   - Build custom MCP client
   - Use programmatically

4. **Join the community**
   - [Discord](https://discord.gg/T5mPpZHxkY) - Get help and share ideas
   - [GitHub](https://github.com/tryonlabs/opentryon) - Report issues

## Support

Need help? Here are your options:

- **Documentation**: Check [README.md](../README.md) and [QUICKSTART.md](QUICKSTART.md)
- **Test Suite**: Run `python test_server.py` to diagnose issues
- **Discord**: [Join our Discord](https://discord.gg/T5mPpZHxkY) for community support
- **GitHub Issues**: [Report bugs](https://github.com/tryonlabs/opentryon/issues)
- **Email**: Contact TryOn Labs support

---

Made with ❤️ by [TryOn Labs](https://www.tryonlabs.ai)

