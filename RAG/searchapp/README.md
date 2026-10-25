# TechTrapture Search App

A modern, AI-powered search application built with Google Cloud's Gen App Builder widget.

## Features

- 🎨 **Premium Design** - Modern dark theme with vibrant gradients and smooth animations
- ⚡ **Lightning Fast** - Instant search results powered by Google Cloud AI
- 🎯 **Smart Context** - AI understands user intent for better accuracy
- ⌨️ **Keyboard Shortcuts** - Press `Cmd+K` (Mac) or `Ctrl+K` (Windows/Linux) to focus search
- 📱 **Responsive** - Works beautifully on all devices
- ♿ **Accessible** - Built with accessibility best practices

## Getting Started

### Prerequisites

- A modern web browser (Chrome, Firefox, Safari, Edge)
- A local web server (optional, for development)

### Running Locally

1. **Simple Method** - Just open `index.html` in your browser

2. **Using Python's HTTP Server**:
   ```bash
   python3 -m http.server 8000
   ```
   Then visit `http://localhost:8000`

3. **Using Node.js HTTP Server**:
   ```bash
   npx http-server -p 8000
   ```
   Then visit `http://localhost:8000`

## Project Structure

```
searchapp/
├── index.html      # Main HTML file with search widget
├── index.css       # Comprehensive styling and design system
├── app.js          # JavaScript for interactions and animations
└── README.md       # This file
```

## Technologies Used

- **HTML5** - Semantic markup
- **CSS3** - Modern styling with custom properties, gradients, and animations
- **Vanilla JavaScript** - No dependencies, pure JS
- **Google Cloud Gen App Builder** - AI-powered search widget
- **Google Fonts** - Inter font family

## Keyboard Shortcuts

- `Cmd+K` / `Ctrl+K` - Focus search input
- `Esc` - Blur search input

## Customization

### Colors

Edit the CSS custom properties in `index.css`:

```css
:root {
    --color-primary: hsl(250, 70%, 65%);
    --color-secondary: hsl(320, 85%, 65%);
    --color-accent: hsl(190, 100%, 60%);
    /* ... more colors */
}
```

### Search Widget Configuration

The search widget is configured with:
- **Config ID**: `c1934cbc-8bf8-4583-9d69-fa614dde29c7`
- **Trigger ID**: `searchWidgetTrigger`

To use your own configuration, update the `configId` attribute in `index.html`.

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Opera (latest)

## License

MIT License - Feel free to use this project for personal or commercial purposes.

## Credits

- Powered by [Google Cloud Gen App Builder](https://cloud.google.com/generative-ai-app-builder)
- Design inspired by modern web aesthetics
- Icons: Custom SVG graphics
