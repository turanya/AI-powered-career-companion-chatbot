"""
Configuration settings for the JobsForHer Foundation AI Chatbot
"""

# Chatbot Identity
CHATBOT_NAME = "Asha"
CHATBOT_TITLE = "JobsForHer AI Assistant"
CHATBOT_ICON = "assets/asha_icon.svg"

# Organization Info
ORGANIZATION = {
    'name': 'JobsForHer Foundation',
    'mission': 'Empowering women to achieve their career aspirations through technology, mentorship, and community.',
    'vision': 'A world where every woman has equal opportunity to pursue and excel in her chosen career path.',
    'phone': '+91-80-4969-4969',
    'email': 'support@jobsforher.com',
    'address': 'Bangalore, Karnataka, India',
    'website': 'https://www.jobsforher.com',
    'social_media': {
        'linkedin': 'https://www.linkedin.com/company/jobsforher',
        'twitter': 'https://twitter.com/jobsforher',
        'facebook': 'https://www.facebook.com/jobsforher',
        'instagram': 'https://www.instagram.com/jobsforher'
    }
}

# Programs and Initiatives
PROGRAMS = {
    'herShakti': {
        'title': 'herShakti Program',
        'description': 'A comprehensive technology upskilling program designed to empower women with in-demand tech skills',
        'technologies': [
            'Data Science & Analytics',
            'Artificial Intelligence & Machine Learning',
            'Cloud Computing',
            'Full Stack Development',
            'DevOps & SRE',
            'Cybersecurity'
        ],
        'duration': '12 weeks',
        'format': 'Hybrid (Online + In-person workshops)',
        'partners': ['Leading Tech Companies', 'Industry Experts', 'Educational Institutions'],
        'benefits': [
            'Hands-on project experience',
            'Industry mentorship',
            'Placement assistance',
            'Networking opportunities',
            'Certification'
        ]
    },
    'divHERsity': {
        'title': 'DivHERsity.club',
        'description': 'An exclusive leadership community for women in technology and business',
        'target_audience': [
            'Women in Technology Leadership',
            'Aspiring Tech Leaders',
            'Women Entrepreneurs',
            'Career Returners',
            'Industry Experts'
        ],
        'features': [
            'Exclusive networking events',
            'Leadership workshops',
            'Mentorship opportunities',
            'Industry insights',
            'Career advancement resources'
        ],
        'events': {
            'frequency': 'Monthly',
            'types': [
                'Leadership Summits',
                'Tech Talks',
                'Networking Mixers',
                'Skill-building Workshops',
                'Panel Discussions'
            ]
        }
    }
}

# UI Theme (matching JobsForHer's brand colors)
CHATBOT_THEME = {
    "primary_color": "#6B46C1",  # Purple for trust and empowerment
    "secondary_color": "#9F7AEA",
    "background_color": "#FFFFFF",
    "text_color": "#2D3748",
    "accent_color": "#F6E05E"
}

# UI Configuration
CHATBOT_UI = {
    "chat_window_height": "500px",
    "chat_window_width": "400px",
    "message_spacing": "12px",
    "font_family": "Arial, sans-serif",
    "font_size": "14px",
    "border_radius": "8px",
    "shadow": "0 4px 6px rgba(0, 0, 0, 0.1)"
}

# Animation Settings
CHATBOT_ANIMATIONS = {
    "message_fade": True,
    "typing_indicator": True,
    "smooth_scroll": True,
    "transition_duration": "0.3s"
}

# Response Timing
RESPONSE_DELAY = 0.5  # seconds 