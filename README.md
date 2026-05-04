# E-Commerce Analyzer

A Flask-based web application for analyzing e-commerce data, including product listings, shopping cart, user orders, and dashboard insights.

## Features
- User authentication (login/register)
- Product catalog browsing
- Shopping cart management
- Order history
- Dashboard for analytics
- Responsive design with custom CSS and JS

## Tech Stack
- **Backend**: Flask (Python)
- **Database**: SQLite (via Flask-SQLAlchemy)
- **Frontend**: HTML templates, Bootstrap (assumed), custom CSS/JS
- **Dependencies**: Listed in `requirements.txt`

## Quick Start
1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Set up the database (run the app once or use Flask shell):
   ```
   flask shell
   # Then db.create_all() if using SQLAlchemy
   ```
3. Run the application:
   ```
   python app.py
   ```
4. Open `http://127.0.0.1:5000/` in your browser.

## Project Structure
```
e-commerce analyzer/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── instance/           # SQLite database
│   └── ecommerce.db
├── static/             # CSS, JS, images
│   ├── css/style.css
│   └── js/main.js
├── templates/          # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── products.html
│   ├── cart.html
│   ├── orders.html
│   └── dashboard.html
└── README.md           # This file
```

## Usage Pages
- `/` - Home page
- `/login` - User login
- `/register` - User registration
- `/products` - Product listings
- `/cart` - Shopping cart
- `/orders` - Order history
- `/dashboard` - Analytics dashboard

## Deployment
Ready for deployment on platforms like Heroku, Railway, or Render. Update database config for production.

## Contributing
Feel free to fork and submit pull requests!

## License
MIT License

