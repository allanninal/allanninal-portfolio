// Single source of truth for Allan Niñal's portfolio.
// Edit this file to update the hero, products grid, stats, and contact info.

export const maker = {
  name: 'Allan Niñal',
  handle: 'allanninal',
  title: 'AI and Software Engineer',
  tagline: 'I build AI-powered tools and data products that solve real problems.',
  openTo: 'Open for collaboration',
  bio: [
    "I'm an AI and Software Engineer based in Talisay, Cebu, Philippines. I build intelligent products that combine data analytics with modern AI — from data pipelines and visualizations to full applications powered by state-of-the-art machine learning models.",
    "My work spans the whole stack: data engineering and analysis, AI/ML application development, and the fullstack and AWS infrastructure to ship and run them — DNS, SSL, and servers included. I care about making AI practical and accessible through well-designed software.",
    "I ship in public and a lot: a growing portfolio of live products across AI tools, Cebu-focused services, trading, and SaaS — plus a year-long project releasing one free, MIT-licensed website template every day.",
    "I'm not looking for a job in the usual sense. I'm looking for something to build and people to build it with: a founding engineer or technical co-founder seat at a startup early enough that the product is still being decided, or a collaboration on a hard problem in AI, data or AWS. If you're building something, I'd love to hear about it.",
  ],
  location: 'Talisay, Cebu, Philippines · UTC+8',
  availableFor: 'A founding engineer or technical co-founder seat at an early startup, and collaboration on AI, data and AWS work.',
  socials: {
    github: 'https://github.com/allanninal',
    linkedin: 'https://www.linkedin.com/in/allanninal/',
    facebook: 'https://www.facebook.com/allan.ninal/',
    devto: 'https://dev.to/allanninal',
    kofi: 'https://ko-fi.com/allanninal',
  },
};

// The three shapes of work worth naming individually. "Open for collaboration"
// on its own is true but unsearchable: somebody looking to fill a founding
// engineer seat does not read that and recognise themselves in it.
export const openings = [
  {
    role: 'Technical co-founder',
    detail:
      'A startup early enough that CTO would be a title without a department. ' +
      'Deciding what to build, building the first version of it, and owning the ' +
      'infrastructure it runs on.',
  },
  {
    role: 'Founding engineer',
    detail:
      'First or early engineer on a small team. Shipping product and the AWS it ' +
      'runs on, and setting the conventions the next engineers inherit.',
  },
  {
    role: 'Collaboration',
    detail:
      'Co-building a product, open-source work, or a stubborn problem in AI, ' +
      'data engineering or cloud cost. Paid or not, depending on what it is.',
  },
];

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
    id: 'templates',
    name: 'Templates by Allan Niñal',
    description:
      'A year-long project delivering one free, MIT-licensed website template daily. Mobile-first static sites across 12 themed sprints of business and creative niches.',
    category: 'Open Source',
    url: 'https://www.allanninal.dev/templates/',
    stack: ['Astro', 'MIT Licensed'],
  },
  {
    id: 'spreadsheets',
    name: 'Spreadsheets by Allan Niñal',
    description:
      'Working Excel and Google Sheets workbooks for jobs where the arithmetic is easy to get wrong — WIP schedules, bid pricing, landed cost, underwriting and SPC.',
    category: 'Products',
    url: 'https://www.allanninal.dev/spreadsheets/',
    stack: ['Excel', 'Google Sheets'],
  },
  {
    id: 'build',
    name: 'Build by Allan Niñal',
    description:
      'Design walkthroughs of automated cloud infrastructure on AWS, each centered on a practical AI-powered application — from booking assistants to voice agents.',
    category: 'Engineering',
    url: 'https://www.allanninal.dev/build/',
    stack: ['AWS', 'Architecture'],
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
  url: 'https://www.allanninal.dev/templates/',
  stack: ['Astro', 'Tailwind', 'TypeScript'],
};

// Services and field notes lived ONLY in the deployed root index.html — they were
// hand-added there after a build, so every later `npm run build` in redesign/ produced
// a page missing both and root/ could never be regenerated without losing them.
// Moved here 2026-08-27 so the build is once again the single source of truth.
export const services = [
  { name: 'AI Automation', detail: 'AWS Lambda · Step Functions · Bedrock' },
  { name: 'Web Apps & Sites', detail: 'Any site or app, with or without AI' },
  { name: 'SaaS from Scratch', detail: 'Full products, ship-ready' },
  { name: 'AI Integrations', detail: 'LLMs · chatbots · RAG' },
  { name: 'Data & AI/ML', detail: 'Analyses · visualization · ML demos' },
  { name: 'Fixes & Refactors', detail: 'PHP · Laravel · React · Next' },
  { name: 'QA & Testing', detail: 'Unit · API · automation · e2e' },
  { name: 'AWS DevOps', detail: 'CI/CD · IaC · monitoring' },
  { name: 'Cloud Migration', detail: 'Site or app → AWS, lower cost' },
  { name: 'WordPress / Woo', detail: 'Fixes · speed · WooCommerce' },
  { name: 'DNS & Domains', detail: 'Any registrar · SSL · records' },
  { name: 'UI Templates', detail: 'From scratch · Figma · any image' },
];

export const fieldNotes = [
  { href: '/seo/', name: 'Technical SEO', detail: 'Sitemaps of dead URLs, blocked noindex, wrong canonicals and soft 404s' },
  { href: '/cloudflare/', name: 'Cloudflare', detail: 'Shadowed page rules, purges that clear nothing and Flexible SSL loops' },
  { href: '/ci/', name: 'GitHub Actions', detail: 'Empty secrets in fork PRs, silent cache misses and redundant billed runs' },
  { href: '/aws/', name: 'AWS cost', detail: 'Idle NAT gateways, unattached EBS, log retention and tag coverage' },
  { href: '/email/', name: 'Email & SES', detail: 'Amazon SES suppression, bounce rate, DKIM and DMARC alignment fixes' },
  { href: '/woocommerce/', name: 'WooCommerce', detail: 'WooCommerce and Stripe order, subscription, and payment fixes' },
  { href: '/shopify/', name: 'Shopify', detail: 'Shopify order, inventory, and payout reconciliation fixes' },
  { href: '/bigcommerce/', name: 'BigCommerce', detail: 'BigCommerce order, webhook, and catalog fixes' },
  { href: '/medusa/', name: 'Medusa', detail: 'Medusa v2 storefront, inventory, and workflow fixes' },
  { href: '/shopware/', name: 'Shopware', detail: 'Shopware 6 order, stock, and message queue fixes' },
  { href: '/saleor/', name: 'Saleor', detail: 'Saleor checkout, channel, and stock fixes' },
  { href: '/prestashop/', name: 'PrestaShop', detail: 'PrestaShop stock, order state, and Webservice API fixes' },
  { href: '/magento/', name: 'Magento', detail: 'Magento 2 indexing, cron, and MSI inventory fixes' },
  { href: '/dns/', name: 'DNS & Domains', detail: 'DNS records, email auth, DNSSEC, and certificate fixes' },
  { href: '/stripe/', name: 'Stripe', detail: 'Disabled webhooks, undelivered events, stalled subscriptions and blocked payouts' },
  { href: '/twilio/', name: 'Twilio', detail: 'Numbers on demo TwiML, unregistered 10DLC campaigns and webhooks pointing nowhere' },
  { href: '/github/', name: 'GitHub API', detail: 'Secondary rate limits, pagination that stops at 30, and webhooks failing unnoticed' },
  { href: '/slack/', name: 'Slack', detail: 'ok:false behind an HTTP 200, missing scopes, and a bot outside the channel it posts to' },
  { href: '/llm/', name: 'LLM APIs', detail: 'Retired models, runaway spend, and quota exhaustion misread as a rate limit' },
];
