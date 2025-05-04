# AI News Analyzer

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)

An intelligent news analysis tool that leverages AI to collect, analyze, and summarize news articles from various sources. The system tracks trends, sentiment, and key entities across news stories, providing comprehensive insights into current events.

## 🚀 Features

- **Automated News Collection**: Scrapes news from multiple reputable sources
- **AI-Powered Analysis**: Performs sentiment analysis, entity recognition, and topic modeling
- **Smart Summarization**: Generates concise summaries of lengthy articles
- **Trend Identification**: Tracks trending topics and evolving narratives
- **Interactive Visualization**: Presents data in user-friendly dashboards
- **Bias Detection**: Identifies potential bias in news reporting
- **Historical Tracking**: Archives and compares news coverage over time

## 📋 Prerequisites

- Python 3.8+
- pip
- API keys for news services (instructions below)

## 🔧 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/dhruv-shgal/AI-news-analyser.git
   cd AI-news-analyser
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up API keys:
   - Create a `.env` file in the project root
   - Add your API keys as shown in `.env.example`

## 🔍 Usage

### Basic Operation

Run the main application:
```bash
python src/main.py
```

### Configuration

Modify `config.yaml` to adjust:
- News sources to monitor
- Analysis parameters
- Update frequency
- Output formats

## 🔄 Pipeline

1. **Collection**: News articles are collected from various sources
2. **Preprocessing**: Text is cleaned and normalized
3. **Analysis**: Multiple analysis techniques are applied
4. **Summarization**: Key points are extracted
5. **Visualization**: Results are displayed in an interactive dashboard

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

