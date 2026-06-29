// Data analyses and AI/ML demos — ported from the original portfolio.
// Data-analysis pages live at /projects/*.html (preserved at the site root).
// AI/ML demos link to open-source repos on GitHub.

export interface WorkItem {
  name: string;
  href: string;
}

// 25 Philippine open-data deep dives. Links resolve at the deployed site root.
export const dataProjects: WorkItem[] = [
  { name: 'Philippine FIES Analysis', href: '/projects/fies-analysis.html' },
  { name: 'Philippine Food Prices (2000–2023)', href: '/projects/food-prices-analysis.html' },
  { name: 'Philippine Public Education (2010–2021)', href: '/projects/education-analysis.html' },
  { name: 'Most Popular Filipino Names', href: '/projects/philippine-names-analysis.html' },
  { name: 'Philippine Weather Analysis (2023–2024)', href: '/projects/weather-analysis.html' },
  { name: 'Philippine Housing Market 2024', href: '/projects/housing-analysis.html' },
  { name: 'Metro Manila Traffic Incidents (2018–2020)', href: '/projects/traffic-analysis.html' },
  { name: 'Cebu Logistics Analysis (2022–2024)', href: '/projects/cebu-logistics-analysis.html' },
  { name: 'Philippine Tourism Arrivals (2010–Q1 2026)', href: '/projects/tourism-analysis.html' },
  { name: 'Philippine Dengue Surveillance (2016–Q1 2026)', href: '/projects/dengue-analysis.html' },
  { name: 'Philippine Foreign Trade (2015–Q1 2026)', href: '/projects/trade-analysis.html' },
  { name: 'Philippine Typhoon Impact (2014–2020)', href: '/projects/typhoon-analysis.html' },
  { name: 'Philippine Regional Poverty & Income', href: '/projects/poverty-analysis.html' },
  { name: 'Philippine Health Indicators', href: '/projects/health-analysis.html' },
  { name: 'Overseas Filipino Workers 2024', href: '/projects/ofw-analysis.html' },
  { name: 'Philippine COVID-19 Pandemic Analysis', href: '/projects/covid-analysis.html' },
  { name: 'Philippine Earthquake & Volcanic Activity', href: '/projects/earthquake-analysis.html' },
  { name: 'Philippine Agricultural Production', href: '/projects/agriculture-analysis.html' },
  { name: 'Philippine Government Budget & Spending', href: '/projects/budget-analysis.html' },
  { name: 'Philippine Election Results 2022', href: '/projects/election-analysis.html' },
  { name: 'Philippine Internet & Digital Connectivity', href: '/projects/internet-analysis.html' },
  { name: 'Philippine Stock Market (PSE) Analysis', href: '/projects/stock-market-analysis.html' },
  { name: 'Philippine City Competitiveness Index', href: '/projects/competitiveness-analysis.html' },
  { name: 'Metro Manila Public Transit Network', href: '/projects/transit-analysis.html' },
  { name: 'Filipino Social Media Text & Hate Speech', href: '/projects/social-media-analysis.html' },
];

// 10 open-source AI/ML demo apps on GitHub.
export const aiDemos: WorkItem[] = [
  { name: 'Image Captioning App', href: 'https://github.com/allanninal/image-captioning-app' },
  { name: 'Agentic AI Workflow', href: 'https://github.com/allanninal/agentic-ai-workflow' },
  { name: 'AI Resume Analyzer', href: 'https://github.com/allanninal/ai-resume-analyzer' },
  { name: 'Personal AI Chatbot', href: 'https://github.com/allanninal/personal-ai-chatbot' },
  { name: 'Sentiment Analysis App', href: 'https://github.com/allanninal/sentiment-analysis-feedback-app' },
  { name: 'Document Summarizer', href: 'https://github.com/allanninal/document-summarizer' },
  { name: 'Keyword Extractor', href: 'https://github.com/allanninal/keyword-extractor' },
  { name: 'Multilingual Translator', href: 'https://github.com/allanninal/multilingual-translator' },
  { name: 'Toxic Comment Detector', href: 'https://github.com/allanninal/toxic-comment-detector' },
  { name: 'Recipe Finder', href: 'https://github.com/allanninal/recipe-finder' },
];
