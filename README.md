# AI Web Scraper

A modern web application for scheduling intelligent AI-powered web scraping tasks. Users can input URLs and set scraping schedules (daily, every 2 days, weekly, monthly) with a beautiful, responsive interface powered by artificial intelligence.

## Features

- 🤖 **AI-Powered Scraping**: Intelligent data extraction with machine learning
- 📅 **Smart Scheduling**: AI-optimized scheduling for maximum efficiency
- 📊 **Task Management**: View and manage all your AI scraping tasks
- 🎨 **Modern UI**: Beautiful, responsive design with smooth animations
- 📱 **Mobile Friendly**: Works perfectly on all devices
- 💾 **Data Storage**: SQLite database for persistent task storage

## Screenshots

### Home Page
- Clean, modern interface with gradient background
- Simple form for adding new AI scraping tasks
- Feature cards highlighting AI capabilities

### Tasks Page
- Table view of all AI scraping tasks
- Status indicators and schedule badges
- Action buttons for editing/deleting tasks

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd web-scraping-scheduler
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Open your browser**
   Navigate to `http://localhost:5000`

## Usage

### Adding a New AI Task
1. Enter the website URL you want to scrape
2. Select the AI scraping frequency (daily, every 2 days, weekly, monthly)
3. Click "Add Task" to schedule the AI scraping

### Viewing Tasks
- Click "View All Tasks" to see all AI scraping tasks
- Each task shows the URL, schedule, creation date, last run time, and status

## Project Structure

```
ai-web-scraper/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── templates/            # HTML templates
│   ├── index.html       # Home page
│   └── tasks.html       # Tasks page
└── static/              # Static files
    ├── css/
    │   ├── style.css    # Main styles
    │   └── tasks.css    # Tasks page styles
    └── js/
        └── script.js    # JavaScript functionality
```

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: Custom CSS with gradients and animations
- **Icons**: Font Awesome

## Database Schema

```sql
CREATE TABLE scraping_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    schedule TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_run TIMESTAMP,
    status TEXT DEFAULT 'active'
);
```

## Future Enhancements

- [ ] **AI Scraping Engine**: Implement intelligent data extraction with ML
- [ ] **Smart Task Scheduler**: Add AI-optimized scheduling with APScheduler
- [ ] **Data Export**: Export scraped data in various formats
- [ ] **User Authentication**: Add user accounts and login system
- [ ] **Email Notifications**: Send notifications when AI scraping completes
- [ ] **Advanced AI Scheduling**: Custom AI-powered scheduling options
- [ ] **Data Visualization**: AI-driven charts and insights for scraped data
- [ ] **API Endpoints**: RESTful API for external integrations

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you have any questions or need help, please open an issue on GitHub. 