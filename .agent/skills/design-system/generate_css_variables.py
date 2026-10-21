# Script to generate standard CSS variables for both Dark and Light modes.
# Place this in `.agent/skills/gabaritei-design-guardian/generate_css_variables.py`

css_vars = """
/* DEFAULT: DARK MODE */
:root {
    --bg-main: #0E1117;
    --bg-card: #1D232A;
    --text-primary: #F0F3F5;
    --text-secondary: #7C838F;
    --border-main: #2F3640;
    
    /* Shared Accents */
    --accent-blue: #3b82f6;
    --accent-purple: #8b5cf6;
    --accent-green: #10b981;

    /* Styling */
    --border-radius-standard: 8px;
    --font-family-sans-serif: 'Inter', sans-serif;
    --font-size-body: 16px;
    --shadow-standard: none; /* Dark mode relies more on borders */
}

/* LIGHT MODE OVERRIDES */
[data-theme="light"], .light-mode {
    --bg-main: #F4F6F8;
    --bg-card: #FFFFFF;
    --text-primary: #1E293B;
    --text-secondary: #64748B;
    --border-main: #E2E8F0;
    
    --shadow-standard: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}
"""

with open('gabaritei_design_vars.css', 'w') as f:
    f.write(css_vars)
print("CSS Variables for Dark/Light mode generated successfully!")