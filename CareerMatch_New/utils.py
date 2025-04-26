"""
Utility functions for the CareerPath Navigator application.
"""

import os
import requests
import re
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CareerMatch:
    def __init__(self):
        self.base_url = 'https://api.careeronestop.org/v1/occupation/'
        self.user_id = os.getenv('CAREER_USER_ID')
        self.token = os.getenv('CAREER_API_TOKEN')

    def is_valid_zip(self, zipcode):
        """Check if the given zip code is valid."""
        return bool(re.match(r'^\d{5}(-\d{4})?$', zipcode))

    def validate_zip_with_api(self, zipcode):
        """Check if the zip code corresponds to a real location using an external API."""
        url = f"http://api.zippopotam.us/us/{zipcode}"
        response = requests.get(url)
        return response.status_code == 200

    def find_career(self, keyword):
        """Search for careers based on a keyword."""
        jobs_url = f'{self.base_url}{self.user_id}/{keyword}/N/0/10'
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.token
        }

        response = requests.get(jobs_url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            occupations = data.get("OccupationList", [])
            return [{"OnetTitle": item["OnetTitle"], "OnetCode": item["OnetCode"], "OccupationDescription": item["OccupationDescription"]} for item in occupations]
        else:
            print(f"Error fetching occupation details: {response.status_code}")
            return None

    def get_career_videos(self, onetCode):
        """Get videos specifically for a career."""
        videos_url = f'https://api.careeronestop.org/v1/video/{self.user_id}/{onetCode}'
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.token
        }

        try:
            response = requests.get(videos_url, headers=headers)
            print(f"Video API response status: {response.status_code}")  # Debug print
            
            if response.status_code == 200:
                data = response.json()
                print(f"Video API response data: {data}")  # Debug print
                videos = data.get("Videos", [])
                if videos and len(videos) > 0:
                    # Get the full video URL
                    video = videos[0]
                    if video.get("URL"):
                        return video.get("URL")  # Return the full video URL
            return None
        except Exception as e:
            print(f"Error fetching videos: {str(e)}")
            return None

    def get_career_data(self, onetID, location):
        """Get detailed information about a specific career."""
        # First try to get videos from dedicated endpoint
        video_url = self.get_career_videos(onetID)
        print(f"Got video URL from dedicated endpoint: {video_url}")  # Debug print

        occupation_url = f'{self.base_url}{self.user_id}/{onetID}/{location}'
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.token
        }

        params = {
            "training": True,
            "interest": False,
            "videos": True,
            "tasks": False,
            "dwas": True,
            "wages": True,
            "alternateOnetTitles": False,
            "projectedEmployment": True,
            "ooh": True,
            "stateLMILinks": False,
            "relatedOnetTitles": True,
            "skills": False,
            "knowledge": False,
            "ability": False,
            "trainingPrograms": True,
            "industryEmpPattern": False,
            "toolsAndTechnology": False,
            "workValues": False,
            "enableMetaData": True
        }

        response = requests.get(occupation_url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            if data.get("RecordCount", 0) > 0:
                occupation_detail = data['OccupationDetail'][0]

                # Process wages
                entries_to_remove = ("NationalWagesList", "BLSAreaWagesList", "WageYear", "SocData", "SocWageInfo", "SocTitle", "SocDescription")
                for k in entries_to_remove:
                    occupation_detail["Wages"].pop(k, None)

                if len(occupation_detail.get("Wages", {}).get("StateWagesList", [])) > 1:
                    annualWage = occupation_detail.get("Wages", {}).get("StateWagesList")[0].get("Median", "Data Not Available")
                    hourlyWage = occupation_detail.get("Wages", {}).get("StateWagesList")[1].get("Median", "Data Not Available")
                elif len(occupation_detail.get("Wages", {}).get("StateWagesList", [])) == 1:
                    annualWage = occupation_detail.get("Wages", {}).get("StateWagesList")[0].get("Median", "Data Not Available")
                    hourlyWage = "(Hourly Salary Data Not Available for this Occupation)"
                else:
                    annualWage, hourlyWage = "(Annual Salary Data Not Available for this Occupation)", "(Hourly Salary Data Not Available for this Occupation)"

                # Process projections
                if len(occupation_detail.get("Projections", {}).get("Projections", [])) > 1:
                    stateGrowthProjection = int(occupation_detail.get("Projections").get("Projections")[0]["PerCentChange"])
                    stateName = occupation_detail.get("Projections").get("Projections")[0].get("StateName", "")
                    nationGrowthProjection = int(occupation_detail.get("Projections").get("Projections")[1]["PerCentChange"])
                    nationName = occupation_detail.get("Projections").get("Projections")[1].get("StateName", "")

                    stateGrowth = "increase" if stateGrowthProjection > 0 else "not change" if stateGrowthProjection == 0 else "decrease"
                    nationGrowth = "increase" if nationGrowthProjection > 0 else "not change" if nationGrowthProjection == 0 else "decrease"

                    statement = f"\nWe predict the employment for this job to {stateGrowth} by {stateGrowthProjection}% in {stateName}.\nWe predict the employment for this job to {nationGrowth} by {nationGrowthProjection}% in {nationName}."
                
                elif len(occupation_detail.get("Projections", {}).get("Projections", [])) == 1:
                    stateGrowthProjection = int(occupation_detail.get("Projections").get("Projections")[0]["PerCentChange"])
                    stateName = occupation_detail.get("Projections").get("Projections")[0].get("StateName", "")

                    stateGrowth = "increase" if stateGrowthProjection > 0 else "not change" if stateGrowthProjection == 0 else "decrease"
                    statement = f"\nWe predict the employment for this job to {stateGrowth} by {stateGrowthProjection}% in {stateName}."
                
                else:
                    statement = "Projection Data Not Available for this Occupation"

                # Get tasks
                tasks = []
                for dwa in occupation_detail.get("Dwas", {})[:10]:
                    tasks.append(dwa.get("DwaTitle"))

                # Get related careers
                relatedCareers = dict(list(occupation_detail.get("RelatedOnetTitles", {}).items())[:8])

                # Format links
                volunteer_link = f"https://www.volunteermatch.org/search/?l={location}&k={occupation_detail.get('OnetTitle')}&v=true"
                
                # Try alternate video source if primary not available
                if not video_url:
                    video_url = occupation_detail.get("COSVideoURL")
                    print(f"Using alternate video URL: {video_url}")  # Debug print

                # If still no video, try getting from multimedia
                if not video_url and occupation_detail.get("Multimedia"):
                    multimedia = occupation_detail.get("Multimedia", [])
                    if multimedia and len(multimedia) > 0:
                        video_url = multimedia[0].get("URL")
                        print(f"Using multimedia URL: {video_url}")  # Debug print

                return {
                    "title": occupation_detail.get("OnetTitle"),
                    "description": occupation_detail.get("OnetDescription"),
                    "salary_range": f"Annual: ${annualWage}, Hourly: ${hourlyWage}",
                    "education_required": occupation_detail.get("EducationTraining", {}).get("EducationTitle", "N/A"),
                    "daily_tasks": tasks,
                    "growth_potential": str(occupation_detail.get("BrightOutlook")) + ". This job is/has " + str(occupation_detail.get("BrightOutlookCategory")) + " in employment.",
                    "growth_projections": statement,
                    "related_careers": relatedCareers,
                    "training_programs": occupation_detail.get("TrainingPrograms", [])[:10],
                    "volunteer_link": volunteer_link,
                    "video_url": video_url
                }

        return None

    def get_certifications(self, occupation_title):
        """Get certifications for a specific occupation."""
        certifications_url = f'https://api.careeronestop.org/v1/certificationfinder/{self.user_id}/{occupation_title}/0/0/0/0/0/0/0/0/0/5'
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.token
        }

        response = requests.get(certifications_url, headers=headers)

        if response.status_code == 200:
            certifications = response.json()
            return certifications.get("CertList", [])
        else:
            print(f"Error fetching certification details: {response.status_code}")
            return []

# Create a global instance of CareerMatch
career_match = CareerMatch()

def get_career_recommendations(interests, strengths, skills, personality):
    """Get career recommendations based on user inputs."""
    try:
        # Combine all inputs into a search query
        search_query = f"{interests} {strengths} {skills} {personality}"
        careers = career_match.find_career(search_query)
        
        if careers:
            return [career["OnetTitle"] for career in careers]
        return []
    except Exception as e:
        print(f"Error getting career recommendations: {str(e)}")
        return []

def get_career_data(career_name):
    """Get detailed information about a specific career."""
    try:
        # First find the career to get its OnetCode
        careers = career_match.find_career(career_name)
        if not careers:
            return None
            
        # Get the first matching career's OnetCode
        onetCode = careers[0]["OnetCode"]
        
        # Get detailed data using the OnetCode
        return career_match.get_career_data(onetCode, "10001")  # Default to NYC area if no location specified
    except Exception as e:
        print(f"Error getting career data: {str(e)}")
        return None

def get_volunteer_opportunities(career, zip_code, radius):
    """Get volunteer opportunities based on career interest and location."""
    try:
        if not career_match.is_valid_zip(zip_code):
            return []
            
        if not career_match.validate_zip_with_api(zip_code):
            return []
            
        # Get career data to use the title for volunteer search
        career_data = get_career_data(career)
        if not career_data:
            return []
            
        # Use the volunteer link from career data
        volunteer_link = career_data.get("volunteer_link", "")
        
        # For now, return a placeholder opportunity
        return [{
            "title": f"Volunteer {career} Assistant",
            "organization": "Local Community Center",
            "description": f"Help with {career} related activities",
            "location": f"Near {zip_code}",
            "age_requirement": "16+",
            "time_commitment": "4 hours/week",
            "link": volunteer_link
        }]
    except Exception as e:
        print(f"Error getting volunteer opportunities: {str(e)}")
        return []

def get_zip_code_coordinates(zip_code):
    """
    Get latitude and longitude coordinates for a zip code.
    
    Args:
        zip_code (str): The zip code to get coordinates for.
        
    Returns:
        tuple: (latitude, longitude) or None if not found.
    """
    try:
        geolocator = Nominatim(user_agent="career_path_navigator")
        location = geolocator.geocode({"postalcode": zip_code, "country": "US"})
        
        if location:
            return (location.latitude, location.longitude)
        return None
    except Exception as e:
        print(f"Error getting coordinates: {e}")
        return None

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points using their coordinates.
    """
    return geodesic((lat1, lon1), (lat2, lon2)).miles 

def get_all_careers():
    """
    Get a list of all available careers with their details.
    Returns a list of career dictionaries with title, description, category, growth_rate, and avg_salary.
    """
    # This is a sample list of careers - in a real application, this would come from an API or database
    careers = [
        {
            'title': 'Software Developer',
            'description': 'Design and develop software applications and systems. Write clean, efficient code and collaborate with cross-functional teams.',
            'category': 'Technology',
            'growth_rate': 25,
            'avg_salary': 85000
        },
        {
            'title': 'Data Scientist',
            'description': 'Analyze complex data sets to help organizations make better decisions. Use statistical methods and machine learning algorithms.',
            'category': 'Technology',
            'growth_rate': 36,
            'avg_salary': 95000
        },
        {
            'title': 'Registered Nurse',
            'description': 'Provide and coordinate patient care, educate patients about health conditions, and maintain medical records.',
            'category': 'Healthcare',
            'growth_rate': 15,
            'avg_salary': 75000
        },
        {
            'title': 'Physical Therapist',
            'description': 'Help patients recover from injuries and improve their mobility through exercise and hands-on care.',
            'category': 'Healthcare',
            'growth_rate': 18,
            'avg_salary': 82000
        },
        {
            'title': 'High School Teacher',
            'description': 'Educate students in specific subject areas, prepare lesson plans, and assess student progress.',
            'category': 'Education',
            'growth_rate': 8,
            'avg_salary': 62000
        },
        {
            'title': 'School Counselor',
            'description': 'Help students develop academic and social skills, provide career guidance, and address personal issues.',
            'category': 'Education',
            'growth_rate': 10,
            'avg_salary': 58000
        },
        {
            'title': 'Marketing Manager',
            'description': 'Plan and execute marketing campaigns, analyze market trends, and manage marketing budgets.',
            'category': 'Business',
            'growth_rate': 10,
            'avg_salary': 78000
        },
        {
            'title': 'Financial Analyst',
            'description': 'Analyze financial data, prepare reports, and make investment recommendations.',
            'category': 'Business',
            'growth_rate': 9,
            'avg_salary': 85000
        },
        {
            'title': 'Environmental Scientist',
            'description': 'Study environmental problems and develop solutions to protect the environment and human health.',
            'category': 'Science',
            'growth_rate': 8,
            'avg_salary': 72000
        },
        {
            'title': 'Civil Engineer',
            'description': 'Design and oversee construction projects, including roads, bridges, and buildings.',
            'category': 'Engineering',
            'growth_rate': 7,
            'avg_salary': 88000
        }
    ]
    
    return careers 