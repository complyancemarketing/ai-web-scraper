# AI Web Scraper

An intelligent automated web scraper powered by Complyance that can extract and track the latest updates from websites.

## Features

### 🚀 Immediate Scraping
- **Scrape Now**: Click the "Start Scraping" button to immediately scrape any website for latest updates
- **Real-time Results**: Get instant feedback on scraping progress and results
- **Latest Updates Detection**: Automatically detects and stores the most recent updates from the last 5 days

### 📊 Latest Updates Dashboard
- **Update Tracking**: View all scraped updates in a clean, organized table
- **Link Management**: Each update shows the page link with clickable URLs
- **Date Tracking**: See when each update was scraped
- **Duplicate Prevention**: Automatically prevents duplicate entries

### 🔄 Scheduled Scraping
- **Flexible Scheduling**: Set up scraping tasks with various frequencies:
  - Scrape Now (immediate)
  - Daily
  - Every 2 Days
  - Weekly
  - Monthly
- **Task Management**: Edit, delete, and monitor scheduled tasks

### 🎨 Modern UI
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Real-time Feedback**: Loading spinners and status indicators
- **Clean Interface**: Intuitive navigation with sidebar menu

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

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Access the application**:
   Open your browser and go to `http://localhost:8080`

## Usage

### Immediate Scraping

1. **Enter a URL**: In the main form, enter the website URL you want to scrape
2. **Click "Start Scraping"**: The system will immediately begin scraping the website
3. **View Results**: After scraping completes, you'll be redirected to the Latest Updates page to see the results

### Scheduled Scraping

1. **Add a Task**: Enter a URL and select a schedule frequency
2. **Manage Tasks**: Use the Dashboard to view, edit, or delete scheduled tasks
3. **Monitor Progress**: Track the status and last run time of each task

### Latest Updates

- **View All Updates**: Navigate to the Latest Updates page to see all scraped content
- **Click Links**: Each update shows a clickable link to the original page
- **Search Updates**: Use the search functionality to find specific updates

## Technical Details

### Database Schema

The application uses SQLite with two main tables:

1. **scraping_tasks**: Stores scheduled scraping tasks
2. **scraped_updates**: Stores the actual scraped content with deduplication

### Scraping Algorithm

The scraping function:
- Extracts all links from the target website
- Filters for same-domain links only
- Detects recent updates using date patterns and keywords
- Prevents duplicate entries using URL hashing
- Stores updates with metadata (title, URL, timestamp)

### Supported Date Formats

The scraper can detect recent updates using various date formats:
- MM/DD/YYYY
- MM-DD-YYYY
- YYYY-MM-DD
- MM.DD.YYYY

### Recent Update Detection

The system identifies recent updates by:
- Looking for date patterns in the last 5 days
- Checking for keywords like "today", "yesterday", "recent", "new", "latest", "updated"
- Analyzing link text and surrounding content

## API Endpoints

- `POST /scrape_now`: Immediate scraping endpoint
- `GET /latest_updates`: View scraped updates
- `GET /tasks`: View scheduled tasks
- `POST /add_task`: Add new scheduled task
- `POST /edit_task/<id>`: Edit existing task
- `POST /delete_task/<id>`: Delete task

## Dependencies

- **Flask**: Web framework
- **requests**: HTTP library for web scraping
- **beautifulsoup4**: HTML parsing
- **lxml**: XML/HTML parser
- **APScheduler**: Task scheduling
- **python-dateutil**: Date utilities

## Testing

Run the test script to verify functionality:

```bash
python test_scraping.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License. 