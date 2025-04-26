# CareerPath Navigator

A comprehensive career guidance application designed to help high school students find their ideal career paths and guide them on how to reach their goals.

## Features

- **Career Quiz**: Gather information about interests, strengths, skills, and personality traits to get personalized career recommendations.
- **AI Career Bot**: Interact with an AI chatbot to dive deeper into career choices and get additional insights.
- **Career Details**: View essential information about chosen careers, including salary, education requirements, daily tasks, and employment projections.
- **Career Videos**: Watch short videos that summarize the main points of each career.
- **Training Programs**: Access information about related training programs and certifications.
- **Volunteer Opportunities**: Find relevant volunteer opportunities based on your location and career field.

## Setup Instructions

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with the following variables:
   ```
   OPENAI_API_KEY=your-api-key-here
   FLASK_SECRET_KEY=your-secret-key-here
   ```
4. Run the application:
   ```
   python career_app.py
   ```
5. Open your browser and navigate to `http://localhost:5000`

## Project Structure

- `career_app.py`: Main application file
- `templates/`: HTML templates
- `static/`: Static assets (CSS, JavaScript, images)
- `data/`: Data files for careers, volunteer opportunities, etc.

## Technologies Used

- Flask: Web framework
- OpenAI API: For the AI chatbot
- HTML/CSS/JavaScript: Frontend
- Python: Backend logic 