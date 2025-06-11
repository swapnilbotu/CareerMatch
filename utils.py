"""
Utility functions for the CareerPath Navigator application.
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CareerMatch:
    def __init__(self):
        self.base_url = 'https://api.careeronestop.org/v1/occupation/'
        self.user_id = os.getenv('CAREER_USER_ID')
        self.token = os.getenv('CAREER_API_TOKEN')

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
            if response.status_code == 200:
                data = response.json()
                videos = data.get("Videos", [])
                if videos and len(videos) > 0:
                    video = videos[0]
                    if video.get("URL"):
                        return video.get("URL")
            return None
        except Exception as e:
            print(f"Error fetching videos: {str(e)}")
            return None

    def get_career_data(self, onetID, location):
        """Get detailed information about a specific career."""
        video_url = self.get_career_videos(onetID)

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

                # If still no video, try getting from multimedia
                if not video_url and occupation_detail.get("Multimedia"):
                    multimedia = occupation_detail.get("Multimedia", [])
                    if multimedia and len(multimedia) > 0:
                        video_url = multimedia[0].get("URL")

                return {
                    "title": occupation_detail.get("OnetTitle"),
                    "description": occupation_detail.get("OnetDescription"),
                    "salary_range": f"Annual: ${annualWage}, Hourly: ${hourlyWage}",
                    "education_required": occupation_detail.get("EducationTraining", {}).get("EducationTitle", "N/A"),
                    "daily_tasks": tasks,
                    "growth_potential": str(occupation_detail.get("BrightOutlook")) + ". This job is/has " + str(occupation_detail.get("BrightOutlookCategory")) + " in employment.",
                    "growth_projections": statement,
                    "related_careers": relatedCareers,
                    "training_programs": [
                        "Data Science Bootcamp (e.g., DataCamp, Springboard)",
                        "Machine Learning Specialization (Coursera)",
                        "Data Engineering Certification (AWS, Google Cloud)",
                        "Python for Data Science (DataCamp)",
                        "SQL and Database Management",
                        "Big Data Technologies (Hadoop, Spark)",
                        "Data Visualization (Tableau, Power BI)",
                        "Statistical Analysis and Mathematics",
                        "Deep Learning Specialization",
                        "Cloud Data Platforms (AWS, Azure, GCP)"
                    ] if "data" in occupation_detail.get("OnetTitle", "").lower() or "machine learning" in occupation_detail.get("OnetTitle", "").lower() else occupation_detail.get("TrainingPrograms", [])[:10],
                    "volunteer_link": volunteer_link,
                    "video_url": video_url
                }

        return None

# Create a global instance of CareerMatch
career_match = CareerMatch()

# Add this after the career_match initialization
TECH_CAREERS = [
    "Software Developer",
    "Data Scientist",
    "Machine Learning Engineer",
    "DevOps Engineer",
    "Cloud Architect",
    "Cybersecurity Analyst",
    "Full Stack Developer",
    "Mobile App Developer",
    "UI/UX Designer",
    "Game Developer",
    "Blockchain Developer",
    "AI Research Scientist",
    "Systems Administrator",
    "Network Engineer",
    "Database Administrator",
    "Quality Assurance Engineer",
    "Technical Product Manager",
    "IT Project Manager",
    "Robotics Engineer",
    "Computer Vision Engineer",
    "Natural Language Processing Engineer",
    "Embedded Systems Engineer",
    "IoT Solutions Architect",
    "AR/VR Developer",
    "Quantum Computing Engineer"
]

def get_career_recommendations(interests, strengths, skills, personality):
    """Get career recommendations based on user inputs."""
    try:
        # First, get API-based recommendations
        search_query = f"{interests} {strengths} {skills} {personality}"
        api_careers = career_match.find_career(search_query)
        
        # Initialize results with tech careers
        recommended_careers = TECH_CAREERS.copy()
        
        # Add API-based careers if they exist
        if api_careers:
            api_career_titles = [career["OnetTitle"] for career in api_careers]
            # Add unique API careers to our list
            for career in api_career_titles:
                if career not in recommended_careers:
                    recommended_careers.append(career)
        
        # Filter for tech-related careers
        tech_keywords = [
            'software', 'programming', 'developer', 'engineer', 'data', 'security',
            'cloud', 'devops', 'ai', 'machine learning', 'cyber', 'web', 'mobile',
            'computer', 'information', 'technology', 'system', 'network', 'database',
            'application', 'code', 'digital', 'technical', 'robotics', 'automation',
            'blockchain', 'quantum', 'virtual', 'augmented', 'reality', 'iot'
        ]
        
        filtered_careers = []
        for career in recommended_careers:
            career_lower = career.lower()
            if any(keyword in career_lower for keyword in tech_keywords):
                filtered_careers.append(career)
        
        # If we have filtered careers, return them; otherwise return the original list
        return filtered_careers[:7] if filtered_careers else recommended_careers[:7]
        
    except Exception as e:
        print(f"Error getting career recommendations: {str(e)}")
        return TECH_CAREERS[:7]  # Return top 7 tech careers as fallback

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
        return career_match.get_career_data(onetCode, "95747")  # Default to my area code if no location specified
    except Exception as e:
        print(f"Error getting career data: {str(e)}")
        return None

def get_volunteer_opportunities(career, zip_code, radius):
    """Get volunteer opportunities based on career interest and location."""
    try:
        # Get career data to use the title for volunteer search
        career_data = get_career_data(career)
        if not career_data:
            return []
            
        # Use the volunteer link from career data
        volunteer_link = career_data.get("volunteer_link", "")
        
        # Return a list of sample opportunities
        # In a production environment, this would be replaced with actual API calls to volunteer platforms
        return [
            {
            "title": f"Volunteer {career} Assistant",
                "organization": "Local Tech Community Center",
                "description": f"Help with {career} related activities and projects. Great opportunity to gain hands-on experience and build your portfolio.",
                "location": f"Within {radius} miles of {zip_code}",
            "age_requirement": "16+",
                "commitment": "4-8 hours/week",
                "link": volunteer_link
            },
            {
                "title": f"{career} Mentorship Program",
                "organization": "Tech Education Initiative",
                "description": f"Share your knowledge and mentor aspiring {career}s. Help others learn and grow in the field.",
                "location": f"Within {radius} miles of {zip_code}",
                "age_requirement": "18+",
                "commitment": "2-4 hours/week",
                "link": volunteer_link
            },
            {
                "title": f"Open Source {career} Contributor",
                "organization": "Open Source Community",
                "description": f"Contribute to open source projects related to {career}. Work with a team of developers and make an impact.",
                "location": "Remote",
                "age_requirement": "18+",
                "commitment": "Flexible",
            "link": volunteer_link
            }
        ]
    except Exception as e:
        print(f"Error getting volunteer opportunities: {str(e)}")
        return [] 