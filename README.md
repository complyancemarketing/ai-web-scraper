# AI Web Scraper - Modern SaaS Dashboard

A modern, professional web application for AI-powered web scraping with a clean SaaS-style interface built using React, Tailwind CSS, and shadcn UI.

## Features

- **Modern SaaS Design**: Clean, professional interface with sidebar navigation
- **Task Management**: Add, view, and manage AI scraping tasks
- **Real-time Updates**: Monitor scraping status and results
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Government Dashboard**: Specialized monitoring for government websites
- **Integrated Apps**: Connect with external services like Google Drive and N8N

## Tech Stack

- **Frontend**: React 18 with Vite
- **Styling**: Tailwind CSS
- **UI Components**: shadcn UI
- **Icons**: Lucide React
- **Backend**: Python Flask (existing)

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn
- Python 3.8+ (for backend)

### Installation

1. **Install Frontend Dependencies**
   ```bash
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm run dev
   ```

3. **Build for Production**
   ```bash
   npm run build
   ```

### Backend Setup

The backend remains the same as your existing Flask application. Make sure to:

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the Flask server:
   ```bash
   python app.py
   ```

## Project Structure

```
ai-web-scraper/
├── src/
│   ├── components/
│   │   ├── ui/           # shadcn UI components
│   │   ├── Sidebar.jsx   # Navigation sidebar
│   │   ├── TaskForm.jsx  # Task creation form
│   │   └── TaskTable.jsx # Task listing table
│   ├── lib/
│   │   └── utils.js      # Utility functions
│   ├── App.jsx           # Main application component
│   ├── main.jsx          # Application entry point
│   └── index.css         # Global styles
├── scrapy/               # Existing backend code
├── templates/            # Existing Flask templates
├── static/               # Existing static files
├── package.json          # Frontend dependencies
├── tailwind.config.js    # Tailwind configuration
├── vite.config.js        # Vite configuration
└── README.md
```

## Design Features

### Modern SaaS Layout
- **Sidebar Navigation**: Clean vertical navigation with icons and labels
- **Card-based Design**: Tasks and forms presented in clean, rounded cards
- **Consistent Spacing**: Proper whitespace and padding throughout
- **Professional Typography**: Inter font family for modern readability

### Color Scheme
- **Primary**: Blue (#2563eb) for primary actions and branding
- **Background**: Light gray (#f9fafb) for subtle contrast
- **Text**: Dark gray for readability
- **Borders**: Subtle gray borders for separation

### Components
- **Task Form**: Centered card with URL input and schedule dropdown
- **Task Table**: Clean table with status badges and action buttons
- **Navigation**: Sidebar with active state indicators
- **Responsive**: Mobile-friendly design with proper breakpoints

## API Integration

The frontend is configured to communicate with your existing Flask backend:

- **Development**: Proxy requests to `http://localhost:5000`
- **Production**: Update API endpoints as needed

## Customization

### Adding New Pages
1. Create a new component in `src/components/`
2. Add navigation item to `Sidebar.jsx`
3. Update routing as needed

### Styling Changes
- Modify `tailwind.config.js` for theme customization
- Update `src/index.css` for global styles
- Use shadcn UI components for consistency

### Backend Integration
- Update API endpoints in components
- Add error handling and loading states
- Implement real-time updates if needed

## Deployment

### Frontend
```bash
npm run build
# Deploy the dist/ folder to your hosting service
```

### Backend
Deploy your existing Flask application as usual.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.