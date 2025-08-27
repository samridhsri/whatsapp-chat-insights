# 📱 WhatsApp Chat Analyzer

A production-grade tool for analyzing WhatsApp chat exports with support for both Android and iOS platforms. Features a modern Streamlit web interface and a robust command-line interface.

## ✨ Features

- **Multi-Platform Support**: Automatically detects and parses both Android and iOS WhatsApp export formats
- **Comprehensive Analysis**: Message statistics, participant behavior, activity patterns, response times, and more
- **Modern Web UI**: Beautiful Streamlit interface with interactive charts and real-time insights
- **Robust CLI**: Full-featured command-line interface for automation and scripting
- **Privacy-First**: All analysis performed locally - no data leaves your system
- **Export Options**: Multiple export formats including CSV, Excel, and JSON
- **Production Ready**: Proper error handling, logging, testing, and Docker support

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/whatsapp-chat-analyzer.git
   cd whatsapp-chat-analyzer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   # Auto-detect interface (prefers Streamlit if available)
   python main.py
   
   # Force Streamlit UI
   python main.py --ui
   
   # Force CLI
   python main.py --cli --help
   ```

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build and run manually
docker build -t whatsapp-analyzer .
docker run -p 8501:8501 whatsapp-analyzer
```

## 📖 Usage

### Web Interface (Streamlit)

1. Run the application: `python main.py --ui`
2. Open your browser to `http://localhost:8501`
3. Upload a WhatsApp chat export (.txt file)
4. Explore insights and download reports

### Command Line Interface

```bash
# Basic analysis
python main.py --cli --file chat.txt

# Force specific platform
python main.py --cli --file chat.txt --platform ios

# Export results
python main.py --cli --file chat.txt --export report.xlsx

# Read from stdin
cat chat.txt | python main.py --cli --stdin

# Verbose output with debug info
python main.py --cli --file chat.txt --verbose --debug

# Use demo data for testing
python main.py --cli --demo
```

### CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--file, -f` | Path to WhatsApp chat export file | - |
| `--stdin` | Read chat data from standard input | False |
| `--demo` | Use built-in demo data | False |
| `--platform, -p` | Platform format (auto/android/ios) | auto |
| `--include-media` | Include media placeholder messages | False |
| `--threshold-hours` | Conversation gap threshold (hours) | 1 |
| `--export, -o` | Export results to file | - |
| `--format` | Export format (excel/csv/json) | excel |
| `--verbose, -v` | Enable verbose output | False |
| `--debug` | Enable debug output | False |
| `--quiet, -q` | Suppress all output except errors | False |

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `WHATSAPP_LOG_LEVEL` | Logging level | INFO |
| `WHATSAPP_LOG_FILE` | Log file path | None |
| `WHATSAPP_MAX_FILE_SIZE` | Maximum file size in MB | 100 |
| `WHATSAPP_DEFAULT_PLATFORM` | Default platform | auto |
| `WHATSAPP_CONVERSATION_THRESHOLD` | Conversation threshold (hours) | 1 |
| `WHATSAPP_DEBUG` | Enable debug mode | false |
| `WHATSAPP_ANONYMIZE` | Default anonymization | false |
| `WHATSAPP_INCLUDE_MEDIA` | Default media inclusion | false |

### Example Configuration

```bash
export WHATSAPP_LOG_LEVEL=DEBUG
export WHATSAPP_MAX_FILE_SIZE=500
export WHATSAPP_DEFAULT_PLATFORM=ios
```

## 📊 Analysis Features

### Basic Statistics
- Total messages and participants
- Date range and activity period
- Word and character counts
- Media message tracking

### Participant Analysis
- Message counts per participant
- Average message lengths
- Activity periods
- Engagement metrics

### Activity Patterns
- Hourly activity distribution
- Daily activity patterns
- Date-based timeline analysis
- Peak activity identification

### Engagement Metrics
- Response time analysis
- Conversation starter identification
- Interaction patterns
- Communication flow analysis

### Content Analysis
- Emoji usage statistics
- Word frequency analysis
- Message type categorization
- Language patterns

## 🧪 Development

### Project Structure

```
whatsapp-chat-analyzer/
├── whatsapp_analyzer/          # Main package
│   ├── core/                   # Core functionality
│   │   ├── parser.py          # Chat parsing logic
│   │   └── analyzer.py        # Analysis engine
│   ├── ui/                     # User interfaces
│   │   └── streamlit_app.py   # Streamlit web app
│   ├── utils/                  # Utility functions
│   │   └── emoji_extractor.py # Emoji detection
│   ├── cli.py                 # Command-line interface
│   └── config.py              # Configuration management
├── tests/                      # Test suite
├── main.py                     # Main entry point
├── requirements.txt            # Dependencies
├── setup.py                   # Package setup
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose
└── README.md                  # This file
```

### Running Tests

```bash
# Install development dependencies
pip install -r requirements.txt[dev]

# Run all tests
pytest

# Run with coverage
pytest --cov=whatsapp_analyzer

# Run specific test file
pytest tests/test_parser.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code with Black
black whatsapp_analyzer/ tests/

# Lint with flake8
flake8 whatsapp_analyzer/ tests/

# Type checking with mypy
mypy whatsapp_analyzer/
```

### Adding New Features

1. **Core Logic**: Add functionality to `core/` modules
2. **UI Updates**: Modify `ui/streamlit_app.py` for web interface
3. **CLI Commands**: Extend `cli.py` for command-line features
4. **Tests**: Add comprehensive tests in `tests/` directory
5. **Documentation**: Update README and docstrings

## 🐳 Docker Development

### Development Container

```bash
# Build development image
docker build -f Dockerfile.dev -t whatsapp-analyzer:dev .

# Run with volume mounting for development
docker run -it --rm \
  -v $(pwd):/app \
  -p 8501:8501 \
  whatsapp-analyzer:dev
```

### Production Deployment

```bash
# Deploy with Docker Compose
docker-compose -f docker-compose.yml --profile production up -d

# Scale the service
docker-compose up -d --scale whatsapp-analyzer=3
```

## 📈 Performance

### Optimization Tips

- **Large Files**: For chats with >100MB, consider preprocessing or chunking
- **Memory Usage**: The analyzer loads the entire chat into memory
- **Export Formats**: Excel exports are slower than CSV/JSON for large datasets
- **Caching**: Streamlit automatically caches expensive operations

### Benchmarks

| File Size | Parse Time | Memory Usage | Export Time (Excel) |
|-----------|------------|--------------|---------------------|
| 1MB | ~0.5s | ~50MB | ~1s |
| 10MB | ~2s | ~200MB | ~5s |
| 100MB | ~15s | ~1GB | ~30s |

## 🔒 Security & Privacy

- **Local Processing**: All analysis performed on your local machine
- **No Data Transmission**: Chat data never leaves your system
- **Secure Exports**: Downloaded reports contain only processed statistics
- **User Control**: Full control over data retention and deletion

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Ensure all tests pass: `pytest`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **WhatsApp**: For providing the export functionality
- **Streamlit**: For the excellent web framework
- **Pandas & Plotly**: For data analysis and visualization
- **Open Source Community**: For the amazing tools and libraries

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/whatsapp-chat-analyzer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/whatsapp-chat-analyzer/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/whatsapp-chat-analyzer/wiki)

## 🔄 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

---

**Made with ❤️ by the WhatsApp Chat Analyzer Team** 