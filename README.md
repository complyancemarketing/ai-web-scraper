# AI Web Scraper

A comprehensive web scraping tool with intelligent sitemap monitoring, change detection, and automated report generation.

## Features

- **Intelligent Sitemap Monitoring**: Automatically fetches and monitors website sitemaps for changes
- **Change Detection**: Compares sitemaps over time to identify new, modified, or removed URLs
- **Automated Scraping**: Scrapes only new/changed content to minimize bandwidth and processing
- **PDF Report Generation**: Creates professional PDF reports from scraped content
- **Web Interface**: Modern Flask-based web interface for task management
- **Scheduling**: Built-in scheduling for automated monitoring
- **Government Site Support**: Specialized crawling for sites without standard sitemaps

## Project Structure

```
ai-web-scraper/
├── app.py                      # Flask web application
├── requirements.txt            # Python dependencies
├── scraping_scheduler.db      # SQLite database
├── scrapy/                    # Core scraping package
│   ├── __init__.py
│   ├── main.py               # Main scraping tool
│   ├── core/                 # Core modules
│   │   ├── __init__.py
│   │   ├── config.py         # Configuration settings
│   │   ├── sitemap_fetcher.py    # Sitemap fetching logic
│   │   ├── sitemap_comparator.py # Sitemap comparison logic
│   │   ├── web_scraper.py        # Web scraping logic
│   │   └── pdf_generator.py      # PDF report generation
│   ├── utils/                # Utility modules
│   │   ├── __init__.py
│   │   └── government_sitemap_generator.py  # Government site crawler
│   ├── sitemaps/            # Stored sitemaps
│   ├── scraped_data/        # Scraped content
│   └── pdfs/               # Generated reports
├── static/                 # Web assets
│   ├── css/
│   └── js/
└── templates/              # HTML templates
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ai-web-scraper
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**:
   ```bash
   python3 app.py
   ```

## Usage

### Web Interface

1. **Start the Flask application**:
   ```bash
   python3 app.py
   ```

2. **Open your browser** and navigate to `http://localhost:8080`

3. **Add scraping tasks** through the web interface

### Command Line Interface

The scraping tool can also be used directly from the command line:

```bash
# Navigate to the scrapy directory
cd scrapy

# Automated workflow (recommended)
python3 main.py --auto https://example.com

# Individual operations
python3 main.py --url https://example.com          # Fetch sitemap only
python3 main.py --compare example.com              # Compare sitemaps
python3 main.py --scrape-new example.com           # Scrape new URLs
python3 main.py --pdf batch_name                   # Generate PDF report

# Scheduled monitoring
python3 main.py --schedule https://example.com --interval 24
```

### Interactive Mode

```bash
cd scrapy
python3 main.py
```

## API Endpoints

- `GET /` - Main dashboard
- `POST /add_task` - Add new scraping task
- `GET /tasks` - View all tasks
- `GET /api/tasks` - Get tasks as JSON
- `POST /edit_task/<id>` - Edit existing task
- `POST /delete_task/<id>` - Delete task
- `GET /latest_updates` - View latest sitemap updates
- `GET /test_sitemap/<url>` - Test if URL has sitemap

## Configuration

The application uses SQLite for data storage and includes:

- **scraping_tasks** table: Stores scheduled scraping tasks
- **sitemap_updates** table: Tracks discovered URL changes

## Dependencies

- **Flask**: Web framework
- **requests**: HTTP client
- **beautifulsoup4**: HTML parsing
- **lxml**: XML processing
- **reportlab**: PDF generation
- **schedule**: Task scheduling
- **readability-lxml**: Content extraction

## Development

### Running Tests

```bash
python3 -c "from scrapy.main import ScrapingTool; print('Import test successful')"
```

### Adding New Features

1. Core scraping logic goes in `scrapy/core/`
2. Utility functions go in `scrapy/utils/`
3. Web interface changes go in `templates/` and `static/`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please create an issue in the repository.