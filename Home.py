"""
Allan Niñal - AI Engineer Portfolio

Modern v0.dev-style homepage showcasing data analytics hobby projects.
"""

import streamlit as st
from src.shared.theme import apply_theme

# Page configuration
st.set_page_config(
    page_title="Allan Niñal | Portfolio",
    page_icon="AN",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Apply shared v0 theme
apply_theme()

# Hide sidebar on homepage
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Project data
PROJECTS = [
    {
        "title": "Media Perception vs Reality",
        "category": "Social Analysis",
        "description": "Exploring the disconnect between what kills us and what the media covers. Analyzes 18 years of data from CDC mortality records, NYT & Guardian articles, and Google search trends.",
        "insights": [
            ("Terrorism gets", "3,907x", "more coverage than deaths warrant"),
            ("Heart disease (#1 killer) gets only", "9.6%", "of fair coverage"),
            ("Violence causes 0.8% of deaths but gets", "52.6%", "of media attention"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "2_Media_Perception",
        "impact": "5 research studies • 39 tests",
    },
    {
        "title": "World Happiness Report",
        "category": "Well-being",
        "description": "Analyzing what makes nations happy across 166 countries over 18 years. Examines global happiness patterns, regional differences, and trends over time.",
        "insights": [
            ("Nordic countries", "dominate", "the top 10 happiest nations"),
            ("Gap between happiest and least happy regions:", "2.98", "points"),
            ("Oceania & North America lead with", "7.2+", "average score"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "4_World_Happiness",
        "impact": "166 countries • Regional analysis",
    },
    {
        "title": "Mobile Data Pricing in Africa",
        "category": "Digital Divide",
        "description": "Analyzing the digital divide across 45 African countries. Examines how much 1GB of mobile data costs relative to income.",
        "insights": [
            ("Only", "7 countries", "meet UN affordability target"),
            ("Price gap between extremes:", "75x", "difference"),
            ("DRC: 1GB costs", "122 days", "of average income"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "3_Mobile_Data_Pricing",
        "impact": "45 countries • UN analysis",
    },
    {
        "title": "Economic History (Maddison Project)",
        "category": "Historical",
        "description": "Exploring 2,000 years of global economic development from Roman times to today. Analyzes GDP per capita across 170+ countries using the Maddison Project Database.",
        "insights": [
            ("Global GDP/capita grew", "25x", "since 1820 (Industrial Revolution)"),
            ("The Great Divergence: richest vs poorest gap grew from", "3x to 50x", ""),
            ("China's transformation:", "28x growth", "in just 68 years (1950-2018)"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "5_Economic_History",
        "impact": "2000+ years • 170+ countries",
    },
    {
        "title": "Life Expectancy Analysis (OECD)",
        "category": "Health",
        "description": "Analyzing 55 years of global health progress through OECD life expectancy data. Examines longevity trends, regional disparities, and health improvements across 44 countries.",
        "insights": [
            ("Japan leads with", "83.8 years", "life expectancy in 2015"),
            ("Global average increased by", "+10 years", "since 1960"),
            ("South Korea showed remarkable", "30 year gain", "from 52 to 82 years"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "6_Life_Expectancy",
        "impact": "55 years • 44 countries",
    },
    {
        "title": "Plastic Waste & Ocean Pollution",
        "category": "Environment",
        "description": "Analyzing global coastal plastic waste streams and ocean pollution from Jambeck et al. (2015). Examines mismanaged plastic waste, regional disparities, and projections to 2025 across 186 countries.",
        "insights": [
            ("China leads with", "8.8M tonnes", "of mismanaged plastic (2010)"),
            ("By 2025, global mismanaged plastic projected to reach", "69M tonnes", "(2x increase)"),
            ("Southeast Asia accounts for", "5 of top 10", "polluting countries"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "7_Plastic_Waste",
        "impact": "186 countries • 2025 projections",
    },
    {
        "title": "Natural Disasters (EM-DAT)",
        "category": "Climate",
        "description": "Analyzing 120 years of global natural disaster data from EM-DAT (1900-2020). Examines deaths, affected populations, and economic damage across disaster types including droughts, earthquakes, floods, and storms.",
        "insights": [
            ("Total disaster deaths:", "22.8M", "over 120 years"),
            ("Drought/famine caused", "51%", "of all disaster deaths"),
            ("Deaths have declined", "90%+", "since early 20th century"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "8_Natural_Disasters",
        "impact": "120 years • 216 countries",
    },
    {
        "title": "Technology Adoption (US Households)",
        "category": "Innovation",
        "description": "Exploring 160 years of technology adoption in US households (1860-2019). From flush toilets to smartphones, tracking how quickly Americans embrace new technologies across 45 innovations.",
        "insights": [
            ("Smartphones reached 50% adoption in just", "2 years", "(fastest ever)"),
            ("Technologies adopt", "5x faster", "after 2000 vs pre-1950"),
            ("Dishwasher took", "76 years", "to reach mainstream adoption"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "9_Technology_Adoption",
        "impact": "160 years • 45 technologies",
    },
    {
        "title": "Food Affordability (World Bank/FAO)",
        "category": "Nutrition",
        "description": "Can people afford a healthy diet? Analyzing the cost of nutritious food across 184 countries using World Bank and FAO data, revealing stark disparities by region and income.",
        "insights": [
            ("Over", "3 billion", "people cannot afford a healthy diet"),
            ("Sub-Saharan Africa has the highest unaffordability at", "82%", ""),
            ("A healthy diet costs", "5x more", "than a calorie-sufficient diet"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "10_Food_Affordability",
        "impact": "184 countries • 4 years",
    },
    {
        "title": "Time With People (ATUS)",
        "category": "Social",
        "description": "Who do Americans spend their time with? Exploring 70 years of the human lifespan using American Time Use Survey data, revealing how our social connections evolve from teens to elderly.",
        "insights": [
            ("Time alone increases from 3h to", "8+ hours", "per day by age 85"),
            ("Time with friends drops from 110 min to", "35 min", "after teenage years"),
            ("By age 75, alone time", "exceeds", "all social time combined"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "11_Time_With_People",
        "impact": "Ages 15-85 • 7 companion types",
    },
    {
        "title": "Female Labor Force Participation",
        "category": "Economics",
        "description": "How has women's workforce participation evolved over 126 years? Analyzing OECD and historical data from 1890-2016 across 42 countries, revealing dramatic shifts in gender and work.",
        "insights": [
            ("US participation rose from 18% to", "56%", "since 1890"),
            ("Nordic countries lead with rates above", "60%", "participation"),
            ("Global average more than", "doubled", "over the 20th century"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "12_Female_Labor",
        "impact": "126 years • 42 countries",
    },
    {
        "title": "Gender Wage Gap (OECD)",
        "category": "Economics",
        "description": "How much less do women earn than men? Analyzing 46 years of OECD data across 38 countries, measuring the persistent gap in median earnings between genders.",
        "insights": [
            ("Average OECD gap stands at", "14%", "of men's earnings"),
            ("Belgium leads with just", "3.3%", "wage gap"),
            ("South Korea has the highest gap at", "37%", ""),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "13_Gender_Wage_Gap",
        "impact": "46 years • 38 countries",
    },
    {
        "title": "Working Hours (1870-2000)",
        "category": "Economics",
        "description": "How the work week transformed over 130 years. From 60+ hour weeks in 1870 to under 40 hours by 2000, tracking the evolution of work-life balance across industrialized nations.",
        "insights": [
            ("Average weekly hours dropped from", "65h to 38h", "over 130 years"),
            ("Netherlands leads with just", "33.8h", "work week"),
            ("Germany has the most vacation at", "42.5 days", ""),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "14_Working_Hours",
        "impact": "130 years • 14 countries",
    },
    {
        "title": "Learning-Adjusted Years of Schooling",
        "category": "Education",
        "description": "Not just how long children stay in school, but how much they actually learn. World Bank Human Capital Index data reveals stark disparities in education quality across 157 countries.",
        "insights": [
            ("Singapore leads with", "12.9 years", "of learning-adjusted education"),
            ("Gap between best and worst:", "10.6 years", "of effective schooling"),
            ("High vs low income countries differ by", "6.6 years", ""),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "15_Learning_Adjusted",
        "impact": "157 countries • 7 regions",
    },
    {
        "title": "Global Education Quality (1965-2015)",
        "category": "Education",
        "description": "50 years of harmonized learning outcomes from TIMSS, PISA, PIRLS, and regional assessments. Tracking how student achievement has evolved across 163 countries.",
        "insights": [
            ("Singapore dominates with score of", "619", "out of ~625 max"),
            ("Sub-Saharan Africa averages", "374 pts", "vs 510+ for Europe"),
            ("Only 25-50% achieve minimum", "proficiency", "in low-performing countries"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "16_Education_Quality",
        "impact": "50 years • 163 countries",
    },
    {
        "title": "Global Tree Density (Crowther 2015)",
        "category": "Environment",
        "description": "Mapping Earth's 3 trillion trees using 429,775 ground measurements. From Russia's 642 billion to desert nations with barely any, exploring tree distribution worldwide.",
        "insights": [
            ("Earth has approximately", "3.04 trillion", "trees total"),
            ("Russia leads with", "642 billion", "trees (21% of global)"),
            ("Global average of", "422 trees", "per person"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "17_Tree_Density",
        "impact": "237 countries • 429K measurements",
    },
    {
        "title": "Deaths from Air Pollution (Lelieveld 2019)",
        "category": "Health",
        "description": "Analyzing mortality from outdoor air pollution across 181 countries. Separates fossil fuel deaths from other anthropogenic sources, revealing the true cost of dirty air.",
        "insights": [
            ("Air pollution causes", "8.8 million", "deaths annually"),
            ("Fossil fuels account for", "41%", "of air pollution deaths"),
            ("Bulgaria has the highest rate at", "211/100k", "population"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "18_Air_Pollution",
        "impact": "181 countries • Fossil fuel analysis",
    },
    {
        "title": "CO2 Emissions by Sector (CAIT 2020)",
        "category": "Climate",
        "description": "Tracking 27 years of carbon dioxide emissions from energy, industry, transport, and land use across 193 countries. Breaking down the sources of climate change.",
        "insights": [
            ("Global emissions reached", "32.4 Gt", "CO2 in 2016"),
            ("China leads with", "9.8 Gt", "(30% of global)"),
            ("Qatar has highest per capita at", "31 t/person", ""),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "19_CO2_Emissions",
        "impact": "27 years • 193 countries",
    },
    {
        "title": "Plastic Ocean Pollution (Meijer 2021)",
        "category": "Environment",
        "description": "Tracking riverine plastic emissions to the ocean across 163 countries. More than 1,000 rivers account for 80% of global plastic pollution entering our oceans.",
        "insights": [
            ("Philippines leads with", "36.4%", "of global ocean plastic"),
            ("Total global emissions:", "979 kt", "of plastic to oceans annually"),
            ("Top 10 countries account for", "75%+", "of ocean plastic"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "20_Plastic_Ocean",
        "impact": "163 countries • River emissions",
    },
    {
        "title": "Suicide Rates by Sex and Age (IHME 2019)",
        "category": "Health",
        "description": "Analyzing global suicide mortality patterns across 198 countries over 28 years. Reveals stark gender disparities and age-related vulnerabilities in mental health outcomes.",
        "insights": [
            ("Men die by suicide at", "3-4x", "the rate of women globally"),
            ("Greenland has highest male rate:", "75/100k", "population"),
            ("Ghana shows largest gender gap at", "10.5x", "male:female ratio"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "21_Suicide_Rates",
        "impact": "28 years • 198 countries",
    },
    {
        "title": "Deaths per TWh Energy Production",
        "category": "Energy",
        "description": "Comparing the true human cost of energy sources. Reveals solar and nuclear are over 1,000x safer than coal when accounting for both accidents and air pollution deaths.",
        "insights": [
            ("Brown coal is the deadliest at", "32.7", "deaths per TWh"),
            ("Solar is safest with just", "0.019", "deaths per TWh"),
            ("Coal kills", "1,700x", "more people than solar per TWh"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "22_Energy_Deaths",
        "impact": "9 sources • Safety ranking",
    },
    {
        "title": "Mental Health Services (Wang 2007)",
        "category": "Health",
        "description": "Revealing the global mental health treatment gap across 17 countries. Most people with mental illness never receive care, especially in low-income countries.",
        "insights": [
            ("Only", "39%", "of severe mental illness cases receive treatment"),
            ("US leads with", "17.9%", "receiving any treatment"),
            ("Nigeria has just", "1.6%", "treatment rate - lowest globally"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "23_Mental_Health",
        "impact": "17 countries • WHO Surveys",
    },
    {
        "title": "Healthcare Access and Quality Index (IHME 2017)",
        "category": "Health",
        "description": "Measuring how well healthcare systems prevent deaths from treatable conditions. Tracking 25 years of global progress from 1990 to 2015 across 197 countries.",
        "insights": [
            ("Andorra leads the world with", "94.6", "HAQ Index score"),
            ("66-point gap between", "best and worst", "healthcare systems"),
            ("Maldives improved most:", "+29.6 pts", "in 25 years"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "24_Healthcare_Quality",
        "impact": "197 countries • 25 years",
    },
    {
        "title": "Child Mortality Rates (Gapminder 2017)",
        "category": "Health",
        "description": "One of humanity's greatest achievements: tracking 216 years of progress saving children's lives. From 1-in-2 deaths to 1-in-25 across 210 countries.",
        "insights": [
            ("Global child mortality dropped by", "86%", "since 1950"),
            ("Iceland leads with just", "2.1/1,000", "deaths under age 5"),
            ("South Korea improved", "98.9%", "- most in the world"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "25_Child_Mortality",
        "impact": "210 countries • 216 years",
    },
    {
        "title": "National Poverty Lines (Jolliffe 2022)",
        "category": "Economics",
        "description": "How different countries define poverty - from $0.91 to $37.80 per day. What's considered poor in one country may be middle-class in another.",
        "insights": [
            ("Norway's poverty line is", "42x higher", "than Uzbekistan's"),
            ("High-income countries average", "$25.48/day", "poverty threshold"),
            ("Several countries set lines", "below $2.15", "International Poverty Line"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "26_Poverty_Lines",
        "impact": "157 countries • World Bank",
    },
    {
        "title": "Gini Coefficients (OECD 2016)",
        "category": "Economics",
        "description": "Measuring income inequality across 36 OECD countries. Compares pre-tax and post-tax Gini coefficients to reveal how taxes and transfers reduce inequality.",
        "insights": [
            ("Iceland most equal with post-tax Gini of", "0.244", ""),
            ("Finland's redistribution reduces inequality by", "48.1%", ""),
            ("Chile has highest inequality at", "0.465", "Gini coefficient"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "27_Gini_Coefficients",
        "impact": "36 countries • 28 years",
    },
    {
        "title": "World Bank Poverty & Inequality (PIP)",
        "category": "Economics",
        "description": "Comprehensive global poverty and inequality data from the World Bank. Tracks extreme poverty ($2.15/day), multiple poverty thresholds, and Gini coefficients across 177 countries.",
        "insights": [
            ("Madagascar has highest extreme poverty at", "78.8%", "of population"),
            ("South Africa most unequal with Gini of", "0.63", ""),
            ("~2 billion people live below", "$2.15/day", "extreme poverty line"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "28_Poverty_Inequality",
        "impact": "177 countries • 54 years",
    },
    {
        "title": "Loneliness in Older Adults (OWID)",
        "category": "Social",
        "description": "How common is loneliness among older adults? Analyzing self-reported loneliness rates across 15 countries, revealing a 37 percentage point gap between the loneliest and least lonely nations.",
        "insights": [
            ("Greece has highest rate at", "62%", "of older adults lonely"),
            ("Denmark lowest at just", "25%", "loneliness rate"),
            ("Southern Europe paradox:", "highest rates", "despite family culture"),
        ],
        "tech": ["Python", "DuckDB", "Streamlit", "Plotly", "pandas"],
        "page": "29_Loneliness_Older_Adults",
        "impact": "15 countries • 6 regions",
    },
]

AI_PROJECTS = [
    {"title": "Image Captioning", "icon": "🖼️", "description": "Generate image captions using BLIP model", "tech": ["ReactJS", "Flask", "BLIP"], "github": "https://github.com/allanninal/image-captioning-app"},
    {"title": "Sentiment Analysis", "icon": "💬", "description": "Analyze feedback sentiment with NLP models", "tech": ["ReactJS", "Flask", "NLP"], "github": "https://github.com/allanninal/sentiment-analysis-feedback-app"},
    {"title": "AI Chatbot", "icon": "🤖", "description": "Interactive chatbot powered by DialoGPT", "tech": ["ReactJS", "Flask", "DialoGPT"], "github": "https://github.com/allanninal/personal-ai-chatbot"},
    {"title": "Resume Analyzer", "icon": "📄", "description": "Extract resume info using BERT NER", "tech": ["Python", "BERT-NER", "Flask"], "github": "https://github.com/allanninal/ai-resume-analyzer"},
    {"title": "Recipe Finder", "icon": "🍳", "description": "Find recipes based on ingredients", "tech": ["ReactJS", "Spoonacular API"], "github": "https://github.com/allanninal/recipe-finder"},
    {"title": "Doc Summarizer", "icon": "📝", "description": "Summarize documents with BART model", "tech": ["Python", "BART", "NLP"], "github": "https://github.com/allanninal/document-summarizer"},
    {"title": "Keyword Extractor", "icon": "🔑", "description": "Extract keywords with zero-shot classification", "tech": ["Python", "BART", "NLP"], "github": "https://github.com/allanninal/keyword-extractor"},
    {"title": "Translator", "icon": "🌐", "description": "Translate between languages with Helsinki-NLP", "tech": ["Python", "Helsinki-NLP"], "github": "https://github.com/allanninal/multilingual-translator"},
    {"title": "Toxic Detector", "icon": "🛡️", "description": "Detect harmful content with toxic-bert", "tech": ["Python", "Toxic-BERT"], "github": "https://github.com/allanninal/toxic-comment-detector"},
    {"title": "Agentic AI", "icon": "🧠", "description": "AI agent workflows with OpenRouter API", "tech": ["Python", "OpenRouter", "LLMs"], "github": "https://github.com/allanninal/agentic-ai-workflow"},
]

SKILLS = {
    "AI & ML": {"icon": "🧠", "items": ["Transformers", "NLP", "LLMs", "BERT", "BART", "HuggingFace"]},
    "Data": {"icon": "📊", "items": ["Python", "SQL", "ETL", "DuckDB", "PostgreSQL", "pandas"]},
    "Web": {"icon": "🌐", "items": ["Flask", "ReactJS", "REST APIs", "Streamlit", "Plotly"]},
    "DevOps": {"icon": "⚙️", "items": ["Git", "Docker", "AWS", "Linux", "CI/CD"]},
}


# Hero Section (v0 Pattern - Enhanced)
st.markdown("""
<div class="hero-section">
    <div class="hero-content">
        <div class="hero-badges">
            <span class="hero-badge">Software Engineer</span>
            <span class="hero-badge">AI Enthusiast</span>
            <span class="hero-badge">Data Explorer</span>
        </div>
        <p class="hero-greeting">Hello, I'm</p>
        <h1 class="hero-title">
            <span class="hero-title-gradient">Allan Niñal</span>
        </h1>
        <p class="hero-subtitle">
            Software Engineer who codes with <span class="hero-highlight">AI assistance</span>, builds
            <span class="hero-highlight">AI-powered apps</span>, and creates
            <span class="hero-highlight">data dashboards</span> exploring global datasets.
        </p>
        <div class="hero-buttons">
            <a href="https://github.com/allanninal" target="_blank" class="hero-btn-primary" style="text-decoration: none;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                View GitHub
            </a>
            <a href="https://linkedin.com/in/allanninal" target="_blank" class="hero-btn-secondary" style="text-decoration: none;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>
                Connect
            </a>
        </div>
        <div class="hero-stats">
            <div class="hero-stat">
                <div class="hero-stat-value">28</div>
                <div class="hero-stat-label">Data Dashboards</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-value">10</div>
                <div class="hero-stat-label">AI Mini Projects</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-value">200+</div>
                <div class="hero-stat-label">Countries Analyzed</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# Stats Section (v0 Pattern)
st.markdown("""
<div class="stats-section">
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-label">Projects</div>
            <div class="stat-value">38</div>
            <div class="stat-description">Data analytics & AI projects</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">AI Models</div>
            <div class="stat-value stat-value-secondary">10+</div>
            <div class="stat-description">NLP & ML implementations</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Years of Data</div>
            <div class="stat-value stat-value-accent">2000+</div>
            <div class="stat-description">Historical datasets analyzed</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Countries</div>
            <div class="stat-value">200+</div>
            <div class="stat-description">Global coverage in analyses</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# Featured Projects Section (v0 Pattern)
st.markdown("""
<div class="projects-section">
    <div class="section-header">
        <h2>Featured Projects</h2>
        <p>Data analytics explorations uncovering insights from global datasets</p>
    </div>
""", unsafe_allow_html=True)

# Projects Grid - 2 columns
cols = st.columns(2)
for idx, project in enumerate(PROJECTS):
    insights_html = "".join([
        f'<div class="project-insight-item">{pre} <span class="project-insight-value">{val}</span> {post}</div>'
        for pre, val, post in project["insights"]
    ])
    tech_html = "".join([f'<span class="tech-tag">{t}</span>' for t in project["tech"]])

    with cols[idx % 2]:
        st.markdown(f"""
        <div class="project-card">
            <div class="project-card-header">
                <span class="project-category">{project['category']}</span>
                <span class="project-arrow">→</span>
            </div>
            <h3 class="project-title">{project['title']}</h3>
            <p class="project-description">{project['description']}</p>
            <div class="project-insights">
                <div class="project-insights-title">Key Insights</div>
                {insights_html}
            </div>
            <div class="tech-tags">{tech_html}</div>
            <div class="project-impact">
                <p>{project['impact']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.page_link(f"pages/{project['page']}.py", label="View Project →", icon="📊")

st.markdown("</div>", unsafe_allow_html=True)


# AI Mini Projects Section (Research Cards Pattern)
st.markdown("""
<div class="research-section">
    <div class="section-header">
        <h2>AI Mini Projects</h2>
        <p>Machine learning applications and NLP implementations</p>
    </div>
""", unsafe_allow_html=True)

# AI Projects Grid - 2 columns
cols = st.columns(2)
for idx, project in enumerate(AI_PROJECTS):
    tech_html = "".join([f'<span class="research-tag">{t}</span>' for t in project["tech"]])
    with cols[idx % 2]:
        st.markdown(f"""
        <div class="research-card">
            <div style="font-size: 2rem; margin-bottom: 1rem;">{project['icon']}</div>
            <h4>{project['title']}</h4>
            <p>{project['description']}</p>
            <div class="research-tags">{tech_html}</div>
            <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-50);">
                <a href="{project['github']}" target="_blank" style="color: var(--primary); font-weight: 500; font-size: 0.875rem;">
                    View Code →
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)


# Skills Section
st.markdown("""
<div style="padding: 4rem 2rem; background: var(--muted);">
    <div class="section-header">
        <h2>Technical Skills</h2>
        <p>Tools and technologies I work with</p>
    </div>
""", unsafe_allow_html=True)

skill_cols = st.columns(4)
for idx, (category, data) in enumerate(SKILLS.items()):
    with skill_cols[idx]:
        skills_html = "".join([f'<span class="tech-tag" style="margin: 0.25rem;">{s}</span>' for s in data["items"]])
        st.markdown(f"""
        <div class="stat-card" style="height: 100%;">
            <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
                <div style="font-size: 1.5rem;">{data['icon']}</div>
                <h4 style="margin: 0; font-weight: 600; color: var(--foreground);">{category}</h4>
            </div>
            <div class="tech-tags">{skills_html}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)


# Clean White Footer Section
st.markdown("---")

footer_cols = st.columns([2, 1, 1, 1.5])

with footer_cols[0]:
    st.markdown("### Allan Ninal")
    st.markdown("""
    AI Engineer passionate about data analytics and uncovering insights from global datasets.
    BS Mathematics graduate with focus on Pure Mathematics.
    """)
    st.markdown("[![GitHub](https://img.shields.io/badge/GitHub-100000?style=flat&logo=github&logoColor=white)](https://github.com/allanninal) [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white)](https://linkedin.com/in/allanninal)")

with footer_cols[1]:
    st.markdown("**Data Projects**")
    st.page_link("pages/2_Media_Perception.py", label="Media Perception")
    st.page_link("pages/28_Poverty_Inequality.py", label="Poverty & Inequality")
    st.page_link("pages/29_Loneliness_Older_Adults.py", label="Loneliness in Older Adults")
    st.page_link("pages/4_World_Happiness.py", label="World Happiness")

with footer_cols[2]:
    st.markdown("**More Projects**")
    st.page_link("pages/6_Life_Expectancy.py", label="Life Expectancy")
    st.page_link("pages/21_Suicide_Rates.py", label="Suicide Rates")
    st.page_link("pages/10_Food_Affordability.py", label="Food Affordability")
    st.page_link("pages/19_CO2_Emissions.py", label="CO2 Emissions")

with footer_cols[3]:
    st.markdown("**Get in Touch**")
    st.markdown("Interested in collaborating or have questions about my work?")
    st.link_button("Connect on LinkedIn", "https://linkedin.com/in/allanninal", type="primary")
    st.link_button("View GitHub", "https://github.com/allanninal")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #64748b; font-size: 0.875rem;'>Built with Streamlit &bull; 2025 Allan Ninal</p>", unsafe_allow_html=True)
