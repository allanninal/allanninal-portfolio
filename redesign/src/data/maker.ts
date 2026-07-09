// Single source of truth for Allan Niñal's portfolio.
// Edit this file to update the hero, products grid, stats, and contact info.

export const maker = {
  name: 'Allan Niñal',
  handle: 'allanninal',
  email: 'landix.ninal@gmail.com',
  title: 'AI Solutions Engineer',
  tagline: 'I build AI-powered tools and data products that solve real problems.',
  bio: [
    "I'm an AI Solutions Engineer based in Talisay, Cebu, Philippines. I build intelligent products that combine data analytics with modern AI — from data pipelines and visualizations to full applications powered by state-of-the-art machine learning models.",
    "My work spans the whole stack: data engineering and analysis, AI/ML application development, and the fullstack and AWS infrastructure to ship and run them — DNS, SSL, and servers included. I care about making AI practical and accessible through well-designed software.",
    "I ship in public and a lot: a growing portfolio of live products across AI tools, Cebu-focused services, trading, and SaaS — plus a year-long project releasing one free, MIT-licensed website template every day. If you're building something, I'd love to hear about it.",
  ],
  location: 'Talisay, Cebu, Philippines · UTC+8',
  availableFor: 'AI solutions, data engineering, and fullstack consulting.',
  socials: {
    github: 'https://github.com/allanninal',
    linkedin: 'https://www.linkedin.com/in/allanninal/',
    facebook: 'https://www.facebook.com/allan.ninal/',
    devto: 'https://dev.to/allanninal',
    kofi: 'https://ko-fi.com/allanninal',
    email: 'mailto:landix.ninal@gmail.com',
  },
};

export interface Product {
  id: string;
  name: string;
  description: string;
  category: string;
  url: string;
  stack?: string[];
}

// Live products — verified reachable. Order: flagship & content first.
export const products: Product[] = [
  {
    id: 'wisecashai',
    name: 'WiseCashAI',
    description:
      'Free, privacy-first financial management tool with AI-powered insights. Track income, expenses, budgets, and goals — all data stays in your browser.',
    category: 'AI Tools',
    url: 'https://www.wisecashai.com/',
    stack: ['AI Insights', 'Privacy-First'],
  },
  {
    id: 'daily-ai-collection',
    name: 'Daily AI Collection',
    description:
      'Curated directory of 200+ free AI tools for writing and content creation — grammar checkers, summarizers, email generators. No registration required.',
    category: 'AI Tools',
    url: 'https://www.dailyaicollection.net/',
    stack: ['Directory', '200+ Tools'],
  },
  {
    id: 'daily-ai-prompts',
    name: 'Daily AI Prompts',
    description:
      'One of the largest collections of 129,000+ high-quality prompts for Midjourney and ChatGPT, organized by category for creative and professional use.',
    category: 'AI Tools',
    url: 'https://prompts.dailyaicollection.net/',
    stack: ['129K+ Prompts', 'Midjourney'],
  },
  {
    id: 'n8n-templates',
    name: 'n8n Templates Library',
    description:
      'Curated library of 2,600+ free n8n automation workflow templates — AI workflows, business automation, and API integrations ready to use.',
    category: 'AI Tools',
    url: 'https://n8n.dailyaicollection.net/',
    stack: ['Automation', '2,600+ Templates'],
  },
  {
    id: 'templates',
    name: 'Templates by Allan Niñal',
    description:
      'A year-long project delivering one free, MIT-licensed website template daily. Mobile-first static sites across 12 themed sprints of business and creative niches.',
    category: 'Open Source',
    url: 'https://templates.allanninal.dev/',
    stack: ['Astro', 'Tailwind', 'MIT'],
  },
  {
    id: 'build',
    name: 'Build by Allan Niñal',
    description:
      'Design walkthroughs of automated cloud infrastructure on AWS, each centered on a practical AI-powered application — from booking assistants to voice agents.',
    category: 'Cloud / AWS',
    url: 'https://www.allanninal.dev/build/',
    stack: ['AWS', 'System Design'],
  },
  {
    id: 'pikbooth',
    name: 'Pikbooth',
    description:
      'A free, browser-based photo booth that captures fun photo strips right in your browser. Photos stay on your device — no uploads, accounts, or tracking.',
    category: 'Web Apps',
    url: 'https://pikbooth.com/',
    stack: ['Browser-Based', 'Privacy-First'],
  },
  {
    id: 'maisonlip',
    name: 'Maisonlip',
    description:
      'Free, browser-based virtual lipstick try-on. Preview any shade using your device camera — all processing happens locally, with no photo uploads or accounts.',
    category: 'Web Apps',
    url: 'https://maisonlip.com/',
    stack: ['Virtual Try-On', 'Camera'],
  },
  {
    id: 'dailyscalper',
    name: 'DailyScalper',
    description:
      'XAUUSD gold copy-trading service via RoboForex CopyFX. Verified performance with a 73% win rate across 3,600+ trades — copy professional gold trades from $150.',
    category: 'Trading',
    url: 'https://www.dailyscalper.net/',
    stack: ['Gold (XAUUSD)', 'Copy Trading'],
  },
  {
    id: 'entrypips',
    name: 'EntryPips',
    description:
      'AI-assisted, per-pair-tuned trading signals across forex, crypto, metals, and stocks — with entry, TP, SL, live performance records, and real-time alerts.',
    category: 'Trading',
    url: 'https://entrypips.com/',
    stack: ['Multi-Asset', 'AI-Assisted'],
  },
  {
    id: 'swingharbor',
    name: 'SwingHarbor',
    description:
      'AI-assisted swing-trading setups, explained. A daily multi-asset scanner with explained setups, risk sizing, and a trading coach. Educational, not advice.',
    category: 'Trading',
    url: 'https://swingharbor.com/',
    stack: ['Swing Trading', 'AI Scanner'],
  },
  {
    id: 'kaoncebu',
    name: 'Kaon Cebu',
    description:
      'A chat-based Cebu food guide — "Asa ta mokaon karon?" Conversational recommendations for restaurants, local eats, and hidden gems around Cebu.',
    category: 'Cebu',
    url: 'https://kaoncebu.com/',
    stack: ['Chat-Based', 'Food Guide'],
  },
  {
    id: 'iskolacebu',
    name: 'Iskola Cebu',
    description:
      'A chat-based private school directory for Cebu — find and compare schools through a simple conversational interface.',
    category: 'Cebu',
    url: 'https://iskolacebu.com/',
    stack: ['Chat-Based', 'Directory'],
  },
  {
    id: 'kasalcebu',
    name: 'Kasal Cebu',
    description:
      'Discover Cebu wedding suppliers on chat — venues, photographers, and more, surfaced through a conversational guide.',
    category: 'Cebu',
    url: 'https://kasalcebu.com/',
    stack: ['Chat-Based', 'Weddings'],
  },
  {
    id: 'cebu-jeep',
    name: 'Sakay (Cebu Jeep)',
    description:
      'A chat-based guide to Cebu jeepney routes — ask where to ride and how to get around the city without guesswork.',
    category: 'Cebu',
    url: 'https://cebu-jeep.app/',
    stack: ['Chat-Based', 'Transit'],
  },
  {
    id: 'catholicschedules',
    name: 'Catholic Schedules',
    description:
      'Find Mass and Confession times near you — a simple directory of Catholic church schedules.',
    category: 'Community',
    url: 'https://catholicschedules.com/',
    stack: ['Directory', 'Schedules'],
  },
  {
    id: 'getnotaryo',
    name: 'getnotaryo',
    description:
      'Notarial practice management for Philippine law offices — walk-in intake, document drafting, the notarial register, monthly Form 143 reports, and print-ready output.',
    category: 'SaaS',
    url: 'https://getnotaryo.app/',
    stack: ['LegalTech', 'PH Law Offices'],
  },
  {
    id: 'kitatax',
    name: 'KitaTax',
    description:
      'BIR tax compliance built for Philippine online sellers — stay on top of filings and obligations without the spreadsheet chaos.',
    category: 'SaaS',
    url: 'https://kitatax.com/',
    stack: ['Tax', 'PH Sellers'],
  },
  {
    id: 'nudgecv',
    name: 'NudgeCV',
    description:
      'Honest AI resume and LinkedIn optimization — get a clear, no-fluff read on your CV and how to make it stronger.',
    category: 'AI Tools',
    url: 'https://nudgecv.com/',
    stack: ['AI', 'Resume / CV'],
  },
  {
    id: 'salaryjustify',
    name: 'SalaryJustify',
    description:
      'Generate cited salary justification reports in minutes — research-backed compensation cases without the manual digging.',
    category: 'SaaS',
    url: 'https://salaryjustify.com/',
    stack: ['AI', 'Reports'],
  },
  {
    id: 'sartova',
    name: 'Sartova',
    description:
      'Custom-dress design, made simple: design → measure → sew. A multi-tenant SaaS for bespoke clothing built on AWS serverless.',
    category: 'SaaS',
    url: 'https://sartova.com/',
    stack: ['AWS Serverless', 'Multi-Tenant'],
  },
  {
    id: 'proofroll',
    name: 'ProofRoll',
    description:
      'Manual payment verification, automated — streamline confirming manual and offline payments without the back-and-forth.',
    category: 'SaaS',
    url: 'https://proofroll.app/',
    stack: ['Payments', 'Automation'],
  },
  {
    id: 'nailtryon',
    name: 'Nail Try-On',
    description:
      'Virtual try-on for nail polish, patterns, and nail art — preview designs right in your browser before you commit.',
    category: 'Web Apps',
    url: 'https://nailtryon.app/',
    stack: ['Virtual Try-On', 'Browser-Based'],
  },
  {
    id: 'yardguild',
    name: 'Yard Guild',
    description:
      'Hire-yard software for small operators — manage equipment, hires, and customers from one straightforward tool.',
    category: 'SaaS',
    url: 'https://yardguild.com/',
    stack: ['Operations', 'SaaS'],
  },
];

// Verifiable, non-financial portfolio stats.
export const stats = {
  dataAnalyses: 25,
  dataAnalysesLabel: '25',
  aiDemos: 10,
  aiDemosLabel: '10',
};

// What I'm building now — a genuinely ongoing project.
export const currentProject = {
  name: 'Templates by Allan Niñal',
  description:
    'A year-long build-in-public project: one free, MIT-licensed, mobile-first website template every single day across 12 themed sprints — the design system this very site is built on.',
  status: 'Shipping daily',
  url: 'https://templates.allanninal.dev/',
  stack: ['Astro', 'Tailwind', 'TypeScript'],
};
