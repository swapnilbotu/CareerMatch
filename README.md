# CareerPath Navigator

A comprehensive career guidance application designed to help high school students find their ideal career paths and guide them on how to reach their goals.

## Features

- **Career Quiz**: Gather information about interests, strengths, skills, and personality traits to get personalized career recommendations.
- **AI Career Bot**: Interact with an AI chatbot to dive deeper into career choices and get additional insights.
- **Career Details**: View essential information about chosen careers, including salary, education requirements, daily tasks, and employment projections.
- **Career Videos**: Watch short videos that summarize the main points of each career.
- **Training Programs**: Access information about related training programs and certifications.
- **Volunteer Opportunities**: Find relevant volunteer opportunities based on your location and career field.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Git (for cloning the repository)
- A modern web browser

## Setup Instructions

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/KTHacks_CareerMatch.git
   cd KTHacks_CareerMatch
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with the following variables:
   ```
   CAREER_USER_ID=your-career-onestop-user-id
   CAREER_API_TOKEN=your-career-onestop-api-token
   FLASK_SECRET_KEY=your-secret-key-here
   ```
   Note: You'll need to sign up for a CareerOneStop API account to get the user ID and API token.

5. Run the application:
   ```bash
   # On Windows
   python career_app.py

   # On macOS/Linux
   python3 career_app.py
   ```

6. Open your browser and navigate to `http://localhost:5000`

## Development

### Project Structure

```
KTHacks_CareerMatch/
├── career_app.py          # Main application file
├── utils.py              # Utility functions
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables
├── templates/           # HTML templates
│   ├── base.html       # Base template
│   ├── index.html      # Home page
│   ├── quiz.html       # Career quiz
│   └── ...
├── static/             # Static assets
│   ├── css/           # Stylesheets
│   ├── js/            # JavaScript files
```

## Troubleshooting

Common issues and solutions:

1. **ModuleNotFoundError**: Make sure you've activated the virtual environment and installed all dependencies.
   ```bash
   pip install -r requirements.txt
   ```

2. **API Connection Error**: Verify your API credentials in the `.env` file.

3. **Port Already in Use**: If port 5000 is already in use, you can change it in `career_app.py`:
   ```python
   if __name__ == '__main__':
       app.run(port=5001)  # Change to a different port
   ```

## Contact

For support or questions:
- Email: swapnilbotu@gmail.com
- Phone: 916-577-0628

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
