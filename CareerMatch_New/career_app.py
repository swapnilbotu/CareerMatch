from flask import Flask, request, render_template, redirect, url_for, session
import google.generativeai as genai
import os
from datetime import datetime
from dotenv import load_dotenv
import utils

# Load environment variables
load_dotenv()

# Configure Google's Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-2.0-flash-lite-001')  # Using stable version

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# ======= Helper Functions =======

def format_response(response_text):
    """Format the chatbot response for better readability."""
    # Remove any markdown formatting
    cleaned_text = response_text.replace('*', '').replace('_', '').replace('`', '')
    
    # Split into paragraphs
    paragraphs = [p.strip() for p in cleaned_text.split('\n') if p.strip()]
    
    # Join paragraphs with proper spacing
    formatted_text = '\n\n'.join(paragraphs)
    
    return formatted_text

def get_chat_response(message, career, chat_history):
    """Get a response from the Gemini model with proper context and history."""
    try:
        # Create a new chat
        chat = model.start_chat(history=[])
        
        # Add initial context - keep it concise for the flash-lite model
        context = [
            "You are a career advisor for high school students.",
            f"Focus on careers in {career}.",
            "Keep responses under 80 words, casual, and engaging.",
            "End with a relevant question.",
            "Consider current market trends and recent developments in the field.",
            "Include information about emerging technologies and industry changes.",
            "Mention any recent news or developments relevant to the career field."
        ]
        
        # Send context
        response = chat.send_message('\n'.join(context))
        if not response or not response.text:
            print("Empty response from context")
            raise ValueError("Empty response from context")
        
        # For flash-lite model, limit the chat history to the last 3 exchanges
        # to stay within token limits
        recent_history = chat_history[-6:] if len(chat_history) > 6 else chat_history
        
        # Add recent chat history
        for msg in recent_history:
            response = chat.send_message(msg['content'])
            if not response or not response.text:
                print(f"Empty response from message: {msg['content']}")
                raise ValueError(f"Empty response from message: {msg['content']}")
        
        # Get response for the current message
        response = chat.send_message(message)
        
        if not response or not response.text:
            print("Empty response from API")
            raise ValueError("Empty response from API")
        
        return format_response(response.text)
        
    except Exception as e:
        print(f"Error in get_chat_response: {str(e)}")
        # Return a more helpful error message
        return f"I'm having trouble connecting to the AI service right now. The error is: {str(e)}. Please try again in a moment."

# ======= Routes =======

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        interests = request.form.get('interests', '')
        strengths = request.form.get('strengths', '')
        skills = request.form.get('skills', '')
        personality = request.form.get('personality', '')
        
        # Enhance the inputs with tech-specific context
        tech_interests = {
            'web': 'web development, frontend, backend, full stack',
            'mobile': 'mobile app development, iOS, Android',
            'ai': 'artificial intelligence, machine learning, deep learning',
            'data': 'data science, data analytics, big data',
            'game': 'game development, game design, game engines',
            'security': 'cybersecurity, information security, network security',
            'cloud': 'cloud computing, DevOps, infrastructure',
            'embedded': 'embedded systems, IoT, hardware programming'
        }
        
        tech_skills = {
            'frontend': 'HTML, CSS, JavaScript, React, Angular, Vue',
            'backend': 'Python, Java, Node.js, PHP, Ruby',
            'database': 'SQL, NoSQL, MongoDB, PostgreSQL',
            'algorithms': 'algorithms, data structures, problem solving',
            'networking': 'networking, security protocols, system administration',
            'ui': 'UI/UX design, user interface, user experience',
            'mobile': 'iOS development, Android development, mobile apps',
            'ai': 'machine learning, neural networks, AI frameworks'
        }
        
        # Get the enhanced descriptions
        enhanced_interests = tech_interests.get(interests, interests)
        enhanced_skills = tech_skills.get(skills, skills)
        
        # Add tech-specific context to strengths
        enhanced_strengths = f"{strengths} in technology and programming"
        
        # Add tech-specific context to personality
        enhanced_personality = f"{personality} in a technology environment"
        
        # Get career recommendations from the CareerMatch API
        careers = utils.get_career_recommendations(
            enhanced_interests,
            enhanced_strengths,
            enhanced_skills,
            enhanced_personality
        )
        
        # Filter for tech-related careers if possible
        tech_keywords = ['software', 'programming', 'developer', 'engineer', 'data', 'security', 
                        'cloud', 'devops', 'ai', 'machine learning', 'cyber', 'web', 'mobile']
        
        # If the API returns career titles, try to filter for tech careers
        if isinstance(careers, list) and careers and isinstance(careers[0], dict) and 'title' in careers[0]:
            tech_careers = []
            for career in careers:
                title = career['title'].lower()
                if any(keyword in title for keyword in tech_keywords):
                    tech_careers.append(career)
            
            # If we found tech careers, use those
            if tech_careers:
                careers = tech_careers
        
        # Get career data for each recommended career
        career_data = {}
        for career in careers:
            if isinstance(career, dict) and 'title' in career:
                career_title = career['title']
            else:
                career_title = career
            career_data[career_title] = utils.get_career_data(career_title)
        
        return render_template('results.html', careers=careers, career_data=career_data)
    
    return render_template('quiz.html')

@app.route('/career/<career_name>')
def career_details(career_name):
    # Convert URL-friendly format back to original career name
    original_career_name = career_name.replace('-', ' ')
    
    # Get career data from the CareerMatch API
    career_data = utils.get_career_data(original_career_name)
    
    if not career_data:
        return redirect(url_for('index'))
    
    return render_template('career_details.html', career=original_career_name, career_data=career_data)

@app.route('/volunteer', methods=['GET'])
def volunteer_opportunities():
    career = request.args.get('career', '')
    zip_code = request.args.get('zip_code', '')
    radius = int(request.args.get('radius', 25))
    
    if not career:
        return redirect(url_for('index'))
    
    if not zip_code:
        # If no zip code provided, redirect back to career details
        return redirect(url_for('career_details', career_name=career))
    
    # Get volunteer opportunities from the CareerMatch API
    opportunities = utils.get_volunteer_opportunities(career, zip_code, radius)
    
    return render_template('volunteer.html', 
                         career=career, 
                         zip_code=zip_code, 
                         radius=radius, 
                         opportunities=opportunities)

@app.route('/chatbot/<career>', methods=['GET', 'POST'])
def chatbot(career):
    # Initialize session variables if they don't exist
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    # Handle initial message only on GET requests
    if request.method == 'GET':
        initial_message = request.args.get('initial_message')
        # Only process if message exists AND chat history is currently empty
        if initial_message and not session['chat_history']:
            # Add user message to chat history
            session['chat_history'].append({
                'role': 'user',
                'content': initial_message,
                'time': datetime.now().strftime('%I:%M %p')
            })
            
            try:
                # Get response from Gemini - pass empty history for initial query
                response_text = get_chat_response(initial_message, career, [])
                
                # Add bot response to chat history
                session['chat_history'].append({
                    'role': 'assistant',
                    'content': response_text,
                    'time': datetime.now().strftime('%I:%M %p')
                })
                
                # Save the updated chat history
                session.modified = True
                
            except Exception as e:
                print(f"Error generating initial chat response: {str(e)}")
                error_message = f"I'm having trouble connecting to the AI service right now. The error is: {str(e)}. Please try again in a moment."
                session['chat_history'].append({
                    'role': 'assistant',
                    'content': error_message,
                    'time': datetime.now().strftime('%I:%M %p')
                })
                session.modified = True
    
    # Handle POST requests (user sending a message from the input field)
    if request.method == 'POST':
        message = request.form.get('message', '')
        if message:
            # Add user message to chat history
            session['chat_history'].append({
                'role': 'user',
                'content': message,
                'time': datetime.now().strftime('%I:%M %p')
            })
            
            try:
                # Get response from Gemini, passing the history *before* the current message
                response_text = get_chat_response(message, career, session['chat_history'][:-1])
                
                # Add bot response to chat history
                session['chat_history'].append({
                    'role': 'assistant',
                    'content': response_text,
                    'time': datetime.now().strftime('%I:%M %p')
                })
                
                # Save the updated chat history
                session.modified = True
                
            except Exception as e:
                print(f"Error generating subsequent chat response: {str(e)}")
                error_message = f"I'm having trouble connecting to the AI service right now. The error is: {str(e)}. Please try again in a moment."
                session['chat_history'].append({
                    'role': 'assistant',
                    'content': error_message,
                    'time': datetime.now().strftime('%I:%M %p')
                })
                session.modified = True
    
    return render_template('chatbot.html',
                         career=career,
                         chat_history=session.get('chat_history', []),
                         now=datetime.now())

@app.route('/career-explorer')
def career_explorer():
    # Define careers directly in the route for testing
    careers = [
        # Software Development
        {
            'title': 'Software Developer',
            'description': 'Design and develop software applications and systems.',
            'category': 'Software Development',
            'growth_rate': 25,
            'avg_salary': 85000
        },
        {
            'title': 'Full Stack Developer',
            'description': 'Develop both frontend and backend of web applications.',
            'category': 'Software Development',
            'growth_rate': 28,
            'avg_salary': 95000
        },
        {
            'title': 'Mobile App Developer',
            'description': 'Create applications for iOS and Android platforms.',
            'category': 'Software Development',
            'growth_rate': 22,
            'avg_salary': 88000
        },
        {
            'title': 'DevOps Engineer',
            'description': 'Combine development and operations to improve deployment efficiency.',
            'category': 'Software Development',
            'growth_rate': 35,
            'avg_salary': 105000
        },
        
        # Data Science & Analytics
        {
            'title': 'Data Scientist',
            'description': 'Analyze complex data sets to help organizations make better decisions.',
            'category': 'Data Science',
            'growth_rate': 36,
            'avg_salary': 95000
        },
        {
            'title': 'Data Engineer',
            'description': 'Build systems to collect, process, and store data at scale.',
            'category': 'Data Science',
            'growth_rate': 33,
            'avg_salary': 92000
        },
        {
            'title': 'Machine Learning Engineer',
            'description': 'Design and implement machine learning algorithms and models.',
            'category': 'Data Science',
            'growth_rate': 40,
            'avg_salary': 110000
        },
        {
            'title': 'Business Intelligence Analyst',
            'description': 'Transform data into actionable business insights.',
            'category': 'Data Science',
            'growth_rate': 29,
            'avg_salary': 85000
        },
        
        # Cybersecurity
        {
            'title': 'Cybersecurity Analyst',
            'description': 'Protect computer systems and networks from cyber threats.',
            'category': 'Cybersecurity',
            'growth_rate': 32,
            'avg_salary': 90000
        },
        {
            'title': 'Security Engineer',
            'description': 'Design and implement security systems and protocols.',
            'category': 'Cybersecurity',
            'growth_rate': 34,
            'avg_salary': 98000
        },
        {
            'title': 'Penetration Tester',
            'description': 'Test systems for security vulnerabilities.',
            'category': 'Cybersecurity',
            'growth_rate': 30,
            'avg_salary': 92000
        },
        
        # Cloud Computing
        {
            'title': 'Cloud Architect',
            'description': 'Design and implement cloud infrastructure solutions.',
            'category': 'Cloud Computing',
            'growth_rate': 38,
            'avg_salary': 115000
        },
        {
            'title': 'Cloud Engineer',
            'description': 'Build and maintain cloud-based systems and applications.',
            'category': 'Cloud Computing',
            'growth_rate': 35,
            'avg_salary': 105000
        },
        
        # Artificial Intelligence
        {
            'title': 'AI Research Scientist',
            'description': 'Research and develop new AI algorithms and models.',
            'category': 'Artificial Intelligence',
            'growth_rate': 42,
            'avg_salary': 120000
        },
        {
            'title': 'Natural Language Processing Engineer',
            'description': 'Develop systems that understand and process human language.',
            'category': 'Artificial Intelligence',
            'growth_rate': 38,
            'avg_salary': 110000
        },
        {
            'title': 'Computer Vision Engineer',
            'description': 'Develop systems that can interpret visual information.',
            'category': 'Artificial Intelligence',
            'growth_rate': 36,
            'avg_salary': 108000
        },
        
        # Game Development
        {
            'title': 'Game Developer',
            'description': 'Create video games and interactive entertainment.',
            'category': 'Game Development',
            'growth_rate': 24,
            'avg_salary': 82000
        },
        {
            'title': 'Game Designer',
            'description': 'Design game mechanics, levels, and user experience.',
            'category': 'Game Development',
            'growth_rate': 26,
            'avg_salary': 85000
        },
        
        # Web Development
        {
            'title': 'Frontend Developer',
            'description': 'Create user interfaces and interactive web experiences.',
            'category': 'Web Development',
            'growth_rate': 27,
            'avg_salary': 88000
        },
        {
            'title': 'Backend Developer',
            'description': 'Build server-side logic and databases for web applications.',
            'category': 'Web Development',
            'growth_rate': 29,
            'avg_salary': 92000
        },
        
        # Blockchain
        {
            'title': 'Blockchain Developer',
            'description': 'Develop decentralized applications and smart contracts.',
            'category': 'Blockchain',
            'growth_rate': 45,
            'avg_salary': 125000
        },
        {
            'title': 'Smart Contract Developer',
            'description': 'Create and audit smart contracts for blockchain platforms.',
            'category': 'Blockchain',
            'growth_rate': 43,
            'avg_salary': 118000
        },
        
        # Internet of Things
        {
            'title': 'IoT Developer',
            'description': 'Develop applications for connected devices and sensors.',
            'category': 'Internet of Things',
            'growth_rate': 31,
            'avg_salary': 95000
        },
        {
            'title': 'Embedded Systems Engineer',
            'description': 'Design and program embedded systems for various devices.',
            'category': 'Internet of Things',
            'growth_rate': 28,
            'avg_salary': 92000
        }
    ]
    
    # Group careers by category
    career_categories = {}
    for career in careers:
        category = career.get('category', 'Other')
        if category not in career_categories:
            career_categories[category] = []
        career_categories[category].append(career)
    
    return render_template('career_explorer.html', career_categories=career_categories)

@app.route('/reset-chat/<career>')
def reset_chat(career):
    # Clear the chat history from the session
    if 'chat_history' in session:
        session.pop('chat_history')
    
    # Redirect back to the chatbot page with the same career
    return redirect(url_for('chatbot', career=career))

# ======= Run the App =======

if __name__ == '__main__':
    app.run(debug=True)
