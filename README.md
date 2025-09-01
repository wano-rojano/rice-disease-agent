# 🌾 Rice Disease Agent - A2A Protocol Implementation

A sophisticated rice disease diagnosis and management agent built with LangGraph and the **A2A (Agent-to-Agent) Protocol**. This intelligent system provides expert guidance on rice pathology, disease identification, and integrated pest management (IPM) strategies through both a web API and an intuitive Chainlit chat interface.

## 🚀 Quick Start

```bash
# Clone and setup
git clone <your-repo-url>
cd rice-disease-agent

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Start the A2A agent server
uv run python -m app

# In another terminal, start the Chainlit UI
uv run chainlit run app/chainlit_app.py

# Test the agent API
uv run python app/test_client.py
```

## ✨ Key Features

- **🌾 Rice Disease Expertise**: Specialized knowledge base for rice pathology and IPM
- **🤖 LangGraph Agent**: Advanced agent architecture with state management
- **🔗 A2A Protocol**: Full compliance with Agent-to-Agent communication standards
- **💬 Chainlit UI**: User-friendly chat interface for rice disease consultation
- **🔍 Multi-Tool Integration**: Web search (Tavily), scientific papers (PubMed and arXiv), and RAG
- **📚 RAG System**: Retrieval from rice diseases documents
- **🌊 Streaming Support**: Real-time response streaming
- **☁️ Cloud Deploy Ready**: Configured for Render deployment

## 🏗️ Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Chainlit UI    │───▶│  A2A Server       │───▶│  LangGraph      │
│  (Frontend)     │     │  (Backend API)   │     │  Agent          │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐   ┌─────────────────┐
                       │  JSON-RPC 2.0    │   │  Tool Execution │
                       │  Communication   │   │  • Web Search   │
                       └──────────────────┘   │  • PubMed, arXiv│
                                              │  • RAG System   │
                                              └─────────────────┘
```

## 🛠️ Rice Disease Tools

| Tool | Description | Rice Disease Use Case |
|------|-------------|-----------------------|
| **🌐 Web Search**  | Real-time search via Tavily API | Current disease outbreaks, new treatments |
| **📚 Academic Papers** | PubMed and arXiv research paper search | Latest research on rice pathology |
| **📄 Document RAG** | Rice disease knowledge retrieval | Disease identification from symptoms |

## 📋 Prerequisites

- **Python 3.12+**
- **uv package manager**
- **API Keys**:
  - OpenAI API Key (required)
  - Tavily API Key (optional, for web search)

## ⚙️ Configuration

### Environment Setup

Create a `.env` file in the project root:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional (for enhanced functionality)
TAVILY_API_KEY=your_tavily_api_key_here
A2A_BASE_URL=http://localhost:10000
RAG_DATA_DIR=data
ENVIRONMENT=development
```

### Rice Diseases Documents Setup

```bash
# The data directory contains rice disease PDFs
ls data/
# Rice diseases: Biology and selected management practices.pdf
# (add your own rice disease documents)
```

## 🚀 Running the Project

### 1. Development (Local)

```bash
# Terminal 1: Start A2A server
uv run python -m app
# Server runs on http://localhost:10000

# Terminal 2: Start Chainlit UI
uv run chainlit run app/chainlit_app.py
# UI available at http://localhost:8000

# Terminal 3: Test the API
uv run python app/test_client.py
```

### 2. Production Deployment (Render)

```bash
# Deploy A2A server (uses render.yaml)
git push origin main
# Render auto-deploys from render.yaml

# Deploy Chainlit UI as separate service
# Set start command: uv run chainlit run app/chainlit_app.py --host 0.0.0.0 --port $PORT
# Set A2A_BASE_URL to your deployed A2A server URL
```

## 🔧 Project Structure

```
📦 rice-disease-agent/
├── 📁 app/                          # Main application package
│   ├── 📄 __init__.py              # Package initialization
│   ├── 📄 __main__.py              # A2A server entry point
│   ├── 📄 agent.py                 # Core rice disease agent
│   ├── 📄 agent_executor.py        # A2A protocol executor
│   ├── 📄 agent_graph_with_helpfulness.py  # LangGraph implementation
│   ├── 📄 chainlit_app.py          # Chainlit chat interface
│   ├── 📄 rag.py                   # RAG for rice disease docs
│   ├── 📄 tools.py                 # Tool belt (web search, PubMed, arXiv, RAG)
│   └── 📄 test_client.py           # API test client
├── 📁 data/                        # Rice disease documents
│   ├── 📄 rice-diseases-guide.pdf
│   └── 📄 *.pdf                    # Your rice disease PDFs
├── 📄 render.yaml                  # Render deployment config
├── 📄 pyproject.toml               # Project dependencies
├── 📄 check_env.py                 # Environment validation
└── 📄 README.md                    # This file
```

## 🧪 Rice Disease Agent Usage

### Disease Diagnosis
```
User: "My rice plants have brown spots on leaves with yellow halos. What disease is this?"
Agent: 🔬 **Diagnosis:** Likely bacterial leaf blight (Xanthomonas oryzae)
        🔍 **Differentials:** Consider leaf blast if lesions are diamond-shaped
        ⚡ **Immediate Actions:** Remove infected plants, improve drainage
```

### IPM Recommendations
```
User: "What IPM strategy should I use for rice blast in irrigated lowland?"
Agent: 🌾 **Integrated Management:**
        • Use resistant varieties (Pi genes)
        • Balanced nitrogen application
        • Water management (avoid continuous flooding)
        • Fungicide rotation if needed
```

### Quick Actions in Chainlit UI
- **🦠 Common Rice Diseases**: Get regional disease information
- **🔍 Identify Symptoms**: Structured symptom assessment
- **🌾 IPM Strategies**: Integrated management recommendations

## 🔄 A2A Protocol Features

### JSON-RPC 2.0 Communication
The agent uses standard JSON-RPC messages for communication:

```json
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [{"kind": "text", "text": "Symptoms of rice blast?"}],
      "message_id": "unique-id"
    }
  },
  "id": "request-id"
}
```

### Context Management
- Maintains conversation history across interactions
- Preserves disease diagnosis context for follow-up questions
- Supports multi-turn consultations

## 🎯 Customization

### Adding Rice Disease Knowledge

```python
# Add documents to data/ directory
cp new-rice-disease-guide.pdf data/

# RAG system automatically indexes new PDFs
# Restart server to reload document index
```

### Customizing Response Formatting

```python
# In app/chainlit_app.py
def format_response(text: str) -> str:
    replacements = {
        "Diagnosis:": "🔬 **Diagnosis:**",
        "Treatment:": "💊 **Treatment:**",
        # Add more rice-specific formatting
    }
```

## 🌐 Deployment

### Render Cloud Deployment

1. **Deploy A2A Server**:
   ```bash
   # Uses render.yaml configuration
   # Automatically deploys on git push
   ```

2. **Deploy Chainlit UI**:
   - Create new Render web service
   - Build: `uv sync`
   - Start: `uv run chainlit run app/chainlit_app.py --host 0.0.0.0 --port $PORT`
   - Set `A2A_BASE_URL` environment variable

3. **Environment Variables**:
   ```
   OPENAI_API_KEY=your_key
   TAVILY_API_KEY=your_key
   A2A_BASE_URL=deployment URL
   RAG_DATA_DIR=data
   ```

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Chainlit can't connect to A2A** | Check A2A_BASE_URL and ensure A2A server is running |
| **Missing disease knowledge** | Verify PDFs are in `data/` directory |
| **API key errors** | Run `python check_env.py` to verify environment |
| **Render deployment fails** | Check start command syntax and logs |

### Debug Commands

```bash
# Check environment
uv run python check_env.py

# Test A2A server health
curl http://localhost:10000/health

# Test tools
uv run python -c "from app.tools import get_tool_belt; print([tool.name for tool in get_tool_belt()])"
```

## 📊 Performance Tips

- **Document Chunking**: Optimize for rice disease content (scientific papers, guides)
- **Model Selection**: Use `gpt-4o-mini` for cost-effective responses
- **Caching**: RAG vectors are cached for faster retrieval
- **Render Free Tier**: Monitor 750-hour monthly limit

## 🔮 Future Enhancements

- **Image Analysis**: Add support for disease photo analysis
- **Geographic Adaptation**: Regional disease prevalence data
- **Weather Integration**: Climate-based disease risk assessment
- **Mobile App**: Extend Chainlit UI for field use
- **Multi-language**: Support for local languages

## 📚 Rice Disease Resources

- **Primary Source**: [Rice Diseases Online Resource](https://rice-diseases.irri.org/contents)
Mew TW, Hibino H, Savary S, Vera Cruz CM, Opulencia R, Hettel GP, eds. 2018. Rice diseases: Biology and selected management practices. Los Baños (Philippines): International Rice Research Institute. PDF e-book. rice-diseases.irri.org. 
- **IRRI Knowledge Bank**: Rice disease identification guides
- **Academic Research**: Latest pathology research via arXiv integration
- **IPM Guidelines**: Integrated pest management strategies

## 🤝 Contributing

1. Fork the repository
2. Add rice disease expertise or tools
3. Test with real disease scenarios
4. Submit pull request with examples

## 📄 License

Parts of this project are from PSI AI LLM Engineering course. See the course materials for licensing information.

---

**🌾 Built for Rice Farmers and Agronomists**
*Combining AI expertise with agricultural knowledge for better rice disease management*

**Tech Stack**: LangGraph • OpenAI • Chainlit • A2A Protocol • Render Cloud