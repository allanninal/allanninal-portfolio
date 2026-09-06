// Data analyses and AI/ML demos — ported from the original portfolio.
// Data-analysis pages live at /projects/*.html (preserved at the site root).
// AI/ML demos link to open-source repos on GitHub.

export interface WorkItem {
  name: string;
  href: string;
}

// Open-data deep dives: mostly Philippine, plus a growing set of global ones.
// Links resolve at the deployed site root.
export const dataProjects: WorkItem[] = [
  { name: 'Climate Model Spread: Seven Models, Ten Cities', href: '/projects/global-climate-spread-analysis.html' },
  { name: 'Diamond Open Access: Auditing A Label Against DOAJ', href: '/projects/global-openaccess-analysis.html' },
  { name: 'The Same Trade, Counted Twice: Mirror Statistics', href: '/projects/global-trade-mirror-analysis.html' },
  { name: 'Where Networks Actually Meet: 1,323 Internet Exchanges', href: '/projects/global-interconnect-analysis.html' },
  { name: 'Safe Water: The Number A Quarter Of The World Lacks', href: '/projects/global-water-analysis.html' },
  { name: 'The European Grid, Hour By Hour', href: '/projects/global-grid-analysis.html' },
  { name: 'What The World Reads: Wikipedia by Country', href: '/projects/global-reading-analysis.html' },
  { name: 'Philippine Household Income: FIES 2015', href: '/projects/fies-analysis.html' },
  { name: 'Philippine Food Prices: 62 Foods, 26 Years', href: '/projects/food-prices-analysis.html' },
  { name: 'Philippine Public Education: 11 Years of DepEd Counts', href: '/projects/education-analysis.html' },
  { name: 'Filipino Forenames: The Top 1,000', href: '/projects/philippine-names-analysis.html' },
  { name: 'Philippine Climate: ERA5, 1940–2024', href: '/projects/weather-analysis.html' },
  { name: 'Philippine Housing: Asking Prices per m²', href: '/projects/housing-analysis.html' },
  { name: 'Metro Manila Traffic: What 17,312 Tweets Measure', href: '/projects/traffic-analysis.html' },
  { name: 'Cebu Logistics Analysis (2022–2024)', href: '/projects/cebu-logistics-analysis.html' },
  { name: 'Philippine Tourism Arrivals (2010–Q1 2026)', href: '/projects/tourism-analysis.html' },
  { name: 'Philippine Dengue Surveillance (2016–Q1 2026)', href: '/projects/dengue-analysis.html' },
  { name: 'Philippine Foreign Trade (2015–Q1 2026)', href: '/projects/trade-analysis.html' },
  { name: 'Philippine Typhoon Tracks (1980–2024)', href: '/projects/typhoon-analysis.html' },
  { name: 'Poverty and the Jobs That Do Not Fix It', href: '/projects/poverty-analysis.html' },
  { name: 'Philippine Health 1960-2024', href: '/projects/health-analysis.html' },
  { name: 'What Migration Sends Home', href: '/projects/ofw-analysis.html' },
  { name: 'Philippine COVID-19 2020-2026', href: '/projects/covid-analysis.html' },
  { name: 'Philippine Earthquakes 2000-2026', href: '/projects/earthquake-analysis.html' },
  { name: 'Philippine Agriculture 1961-2024', href: '/projects/agriculture-analysis.html' },
  { name: 'Philippine Public Finances', href: '/projects/budget-analysis.html' },
  { name: 'The 2022 Philippine Election', href: '/projects/election-analysis.html' },
  { name: 'Philippine Internet 2000-2025', href: '/projects/internet-analysis.html' },
  { name: 'Philippine Stock Market (PSE) Analysis', href: '/projects/stock-market-analysis.html' },
  { name: 'Philippine Logistics Performance', href: '/projects/competitiveness-analysis.html' },
  { name: 'What Metro Manila Transit Mapping Misses', href: '/projects/transit-analysis.html' },
  { name: 'Inside a Filipino Hate-Speech Corpus', href: '/projects/social-media-analysis.html' },
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
