import re

path = "backend/app/ai/local_provider.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

# Expand known names
code = code.replace(
    'known_names = ["Ravi", "Kumar", "Arun", "Priya", "Anand", "Suresh", "Divya", "Rahul"]',
    'known_names = ["Poovarasan", "Kisho Varma", "Kisho", "Ravi", "Kumar", "Arun", "Priya", "Anand"]'
)

# Expand projects
if 'if "burnex" in lower' not in code:
    code = code.replace(
        'if "sih" in lower or "smart india hackathon" in lower:',
        '''if "burnex" in lower:
            projects.append(ExtractedEntity(type="project", name="BurnEx AI", confidence=0.98))
        if "fixmycollege" in lower:
            projects.append(ExtractedEntity(type="project", name="FixMyCollege", confidence=0.97))
        if "portrait" in lower or "art" in lower:
            projects.append(ExtractedEntity(type="project", name="Portrait Art", confidence=0.96))
        if "sih" in lower or "smart india hackathon" in lower:'''
    )

# Expand activities & food
if 'parotta' not in code:
    code = code.replace(
        'if "biryani" in lower:',
        'if "biryani" in lower or "parotta" in lower:'
    )

# Disambiguation question for friends if needed
code = code.replace(
    '"options": ["Ravi Kumar (College)", "Ravi S (Client)", "Create new person"]',
    '"options": ["Poovarasan (College Friend)", "Kisho Varma (Tech Teammate)", "Confirm"]'
)

with open(path, "w", encoding="utf-8") as f:
    f.write(code)

print("AI provider updated with Joe's profile entities!")
