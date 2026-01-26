# SEO Implementation Templates
## Ready-to-Use Code for All Pages

---

## PART 1: HEAD SECTION UPDATES

### Add These to ALL 12 Pages (Universal)

**Location:** Between `<meta name="author" content="Allan Niñal">` and the opening `<link>` tags

```html
<!-- Canonical Tag - CHANGE URL FOR EACH PAGE -->
<link rel="canonical" href="https://www.allanninal.dev/">

<!-- Robots Meta Tag -->
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">

<!-- Language already present, no changes needed -->
<!-- Favicon already present, no changes needed -->
```

**For each project page, update the href:**
- fies-analysis: `href="https://www.allanninal.dev/projects/fies-analysis"`
- health-analysis: `href="https://www.allanninal.dev/projects/health-analysis"`
- etc.

---

### Update Open Graph Tags

**Current state:** og:image is missing on 11/12 pages

**Find this section and add og:image:**

```html
<!-- Open Graph / Social Media -->
<meta property="og:type" content="website">
<meta property="og:url" content="https://www.allanninal.dev/projects/health-analysis">
<meta property="og:title" content="Philippine Health Indicators Analysis | Allan Niñal">
<meta property="og:description" content="Comprehensive analysis of 66 years of Philippine health data examining life expectancy, mortality rates, and healthcare indicators.">

<!-- ADD THESE LINES -->
<meta property="og:image" content="https://www.allanninal.dev/images/og/health-analysis.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:type" content="image/png">
<!-- END ADD -->
```

---

### Update Twitter Card Tags

**Find this section and add image:**

```html
<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Philippine Health Indicators Analysis | Allan Niñal">
<meta name="twitter:description" content="66 years of Philippine health data: life expectancy trends, mortality rates, and disease patterns.">

<!-- ADD THIS LINE -->
<meta name="twitter:image" content="https://www.allanninal.dev/images/og/health-analysis.png">
<meta name="twitter:image:alt" content="Philippine Health Indicators Analysis data visualization">
<!-- END ADD -->
```

**Repeat for all 12 pages** (change the image path and alt text accordingly)

---

## PART 2: JSON-LD SCHEMA MARKUP

### For index.html ONLY

**Add inside `<head>` section, after favicon link:**

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Allan Niñal",
  "jobTitle": "Data & AI Engineer",
  "description": "Data analyst and AI engineer specializing in Philippine socioeconomic data analysis, machine learning applications, and AI-powered solutions.",
  "url": "https://www.allanninal.dev",
  "image": "https://www.allanninal.dev/images/profile.jpg",
  "sameAs": [
    "https://www.linkedin.com/in/allanninal",
    "https://github.com/allanninal",
    "https://dev.to/allanninal"
  ],
  "email": "landix.ninal@gmail.com",
  "knowsAbout": [
    "Data Analytics",
    "Python",
    "Machine Learning",
    "Data Visualization",
    "Philippine Economics",
    "Public Health Analysis",
    "Labor Economics",
    "Education Systems"
  ]
}
</script>
```

---

## PART 3: PROJECT PAGE SCHEMA MARKUP

### Template for health-analysis.html

**Add inside `<head>` section, after favicon:**

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Philippine Health Indicators Analysis (1953-2019)",
  "description": "Comprehensive analysis of 66 years of Philippine health data examining life expectancy trends, mortality rates, disease patterns, and healthcare indicators.",
  "image": "https://www.allanninal.dev/images/og/health-analysis.png",
  "datePublished": "2025-03-15",
  "dateModified": "2026-01-26",
  "author": {
    "@type": "Person",
    "name": "Allan Niñal",
    "url": "https://www.allanninal.dev"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Allan Niñal - Data & AI Engineer",
    "url": "https://www.allanninal.dev"
  },
  "mainEntity": {
    "@type": "Dataset",
    "name": "Philippine Health Indicators (1953-2019)",
    "description": "Comprehensive WHO Global Health Observatory data for the Philippines covering mortality, infectious diseases, child health, non-communicable diseases, substance use, and health systems indicators.",
    "url": "https://data.humdata.org/dataset/who-data-for-philippines",
    "temporalCoverage": "1953/2019",
    "spatialCoverage": {
      "@type": "Place",
      "name": "Philippines"
    },
    "creator": {
      "@type": "Organization",
      "name": "World Health Organization (WHO)"
    },
    "distribution": {
      "@type": "DataDownload",
      "encodingFormat": "CSV",
      "contentUrl": "https://data.humdata.org/dataset/who-data-for-philippines"
    }
  }
}
</script>
```

---

### Template for ofw-analysis.html

**Replace the above with this (tailored for OFW data):**

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Overseas Filipino Workers (OFW) Analysis 2024",
  "description": "Data-driven analysis of 2.19 million OFWs examining remittance patterns, regional deployment, gender distribution, and economic impact on the Philippines.",
  "image": "https://www.allanninal.dev/images/og/ofw-analysis.png",
  "datePublished": "2025-12-01",
  "dateModified": "2026-01-26",
  "author": {
    "@type": "Person",
    "name": "Allan Niñal",
    "url": "https://www.allanninal.dev"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Allan Niñal - Data & AI Engineer",
    "url": "https://www.allanninal.dev"
  },
  "mainEntity": {
    "@type": "Dataset",
    "name": "Survey on Overseas Filipinos 2024",
    "description": "Philippine Statistics Authority survey covering 2.19 million Overseas Filipino Workers (OFWs), their remittances totaling PHP 262 billion, destination countries, occupations, and economic demographics.",
    "url": "https://psa.gov.ph/statistics/survey/labor-and-employment/survey-overseas-filipinos",
    "temporalCoverage": "2024",
    "spatialCoverage": {
      "@type": "Place",
      "name": "Philippines"
    },
    "creator": {
      "@type": "Organization",
      "name": "Philippine Statistics Authority (PSA)"
    }
  }
}
</script>
```

---

### Template for education-analysis.html

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Philippine Public Education Analysis",
  "description": "Analysis of Philippine education systems including enrollment trends, educational outcomes, and quality indicators.",
  "image": "https://www.allanninal.dev/images/og/education-analysis.png",
  "datePublished": "2025-06-01",
  "dateModified": "2026-01-26",
  "author": {
    "@type": "Person",
    "name": "Allan Niñal",
    "url": "https://www.allanninal.dev"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Allan Niñal - Data & AI Engineer",
    "url": "https://www.allanninal.dev"
  },
  "mainEntity": {
    "@type": "Dataset",
    "name": "Philippine Education Statistics",
    "description": "Comprehensive education data covering enrollment, graduation rates, educational quality, and institutional metrics.",
    "spatialCoverage": {
      "@type": "Place",
      "name": "Philippines"
    }
  }
}
</script>
```

**Follow this pattern for remaining pages:**
- food-prices-analysis.html
- housing-analysis.html
- weather-analysis.html
- traffic-analysis.html
- typhoon-analysis.html
- poverty-analysis.html
- philippine-names-analysis.html

Change: headline, description, datePublished, image URL, dataset name/description

---

## PART 4: FAQ SECTIONS (Add to Each Project Page)

### Example for health-analysis.html

**Add this before the CTA section (before `<!-- CTA Section -->`):**

```html
<!-- FAQ Section -->
<section class="section">
    <div class="container">
        <div class="section-header fade-up">
            <div class="section-number">13</div>
            <h2>Frequently Asked Questions</h2>
            <p class="section-description">
                Common questions about Philippine health data and analysis
            </p>
        </div>

        <div class="chart-container fade-up" style="max-width: 900px; margin: 0 auto;">
            <div itemscope itemtype="https://schema.org/FAQPage">

                <div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question" style="margin-bottom: 2rem; padding-bottom: 2rem; border-bottom: 1px solid var(--border-color);">
                    <h3 itemprop="name" style="font-size: 1.1rem; margin-bottom: 0.75rem;">What is the data source for this analysis?</h3>
                    <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                        <p itemprop="text" style="color: var(--text-secondary);">
                            This analysis uses data from the <strong>World Health Organization's Global Health Observatory</strong>, compiled via the Humanitarian Data Exchange (HDX). The dataset contains 56 health indicators covering mortality, infectious diseases, child health, non-communicable diseases, and health systems for the Philippines from 1953 to 2019.
                        </p>
                    </div>
                </div>

                <div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question" style="margin-bottom: 2rem; padding-bottom: 2rem; border-bottom: 1px solid var(--border-color);">
                    <h3 itemprop="name" style="font-size: 1.1rem; margin-bottom: 0.75rem;">Why has measles resurged after near-elimination in 2006?</h3>
                    <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                        <p itemprop="text" style="color: var(--text-secondary);">
                            The Philippines achieved near-elimination with only 9 measles cases in 2006. However, measles vaccination coverage declined from 88% (2015) to 67% (2018) due to vaccine hesitancy following the 2016 Dengvaxia controversy. This 21-percentage-point decline directly caused outbreaks: 58,848 cases in 2014 and 20,827 cases in 2018.
                        </p>
                    </div>
                </div>

                <div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question" style="margin-bottom: 2rem; padding-bottom: 2rem; border-bottom: 1px solid var(--border-color);">
                    <h3 itemprop="name" style="font-size: 1.1rem; margin-bottom: 0.75rem;">What is the biggest current health challenge facing the Philippines?</h3>
                    <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                        <p itemprop="text" style="color: var(--text-secondary);">
                            The rapidly escalating HIV epidemic is perhaps the most urgent challenge. New HIV infections increased 24-fold from 660 in 2003 to 16,000 in 2019, making the Philippines one of Asia-Pacific's fastest-growing epidemics. The epidemic is concentrated among men who have sex with men (MSM) and young people aged 15-24, requiring targeted prevention interventions.
                        </p>
                    </div>
                </div>

                <div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question" style="margin-bottom: 2rem; padding-bottom: 2rem; border-bottom: 1px solid var(--border-color);">
                    <h3 itemprop="name" style="font-size: 1.1rem; margin-bottom: 0.75rem;">Has the Philippines made progress in reducing infant mortality?</h3>
                    <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                        <p itemprop="text" style="color: var(--text-secondary);">
                            Yes - significant progress has been made. Infant mortality dropped dramatically from 85 per 1,000 live births in 1953 to 22.5 per 1,000 in 2018, a 73.5% reduction over 65 years. Under-5 mortality fell even more sharply: from 136.5 per 1,000 to 28.4 per 1,000 (79% reduction). This reflects improved vaccination coverage, better nutrition, and improved healthcare access.
                        </p>
                    </div>
                </div>

                <div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question" style="margin-bottom: 2rem; padding-bottom: 0;">
                    <h3 itemprop="name" style="font-size: 1.1rem; margin-bottom: 0.75rem;">What is stunting and why is it a concern?</h3>
                    <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                        <p itemprop="text" style="color: var(--text-secondary);">
                            Stunting is height-for-age deficiency indicating chronic malnutrition. Approximately 30.3% of Philippine children under 5 are stunted, affecting their cognitive development, immune function, and future productivity. Early intervention through nutrition programs and food security improvements is critical for breaking the cycle of poverty and poor health outcomes.
                        </p>
                    </div>
                </div>

            </div>
        </div>
    </div>
</section>
```

---

### Example for ofw-analysis.html

**Add this FAQ section customized for OFW data:**

```html
<!-- FAQ Section -->
<section class="section">
    <div class="container">
        <div class="section-header fade-up">
            <div class="section-number">13</div>
            <h2>Frequently Asked Questions About OFWs</h2>
            <p class="section-description">
                Common questions about Overseas Filipino Workers and remittances
            </p>
        </div>

        <div class="chart-container fade-up" style="max-width: 900px; margin: 0 auto;">
            <div itemscope itemtype="https://schema.org/FAQPage">

                <div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question" style="margin-bottom: 2rem; padding-bottom: 2rem; border-bottom: 1px solid var(--border-color);">
                    <h3 itemprop="name" style="font-size: 1.1rem; margin-bottom: 0.75rem;">How many Overseas Filipino Workers are there?</h3>
                    <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                        <p itemprop="text" style="color: var(--text-secondary);">
                            According to the 2024 Philippine Statistics Authority Survey on Overseas Filipinos, there are approximately <strong>2.19 million OFWs</strong>, of which 97.9% (2.14 million) are overseas contract workers (OCWs). This represents a 1.5% increase from 2.16 million in 2023.
                        </p>
                    </div>
                </div>

                <div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question" style="margin-bottom: 2rem; padding-bottom: 2rem; border-bottom: 1px solid var(--border-color);">
                    <h3 itemprop="name" style="font-size: 1.1rem; margin-bottom: 0.75rem;">Do more women or men work overseas as OFWs?</h3>
                    <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                        <p itemprop="text" style="color: var(--text-secondary);">
                            <strong>Women dominate the OFW population</strong> at 57.2% (1.25 million), compared to men at 42.8% (937,000). Female OFWs grew by 4.4% from 2023, while male OFWs declined by 2.2%. Women primarily work in elementary occupations (68.4%) such as domestic work, while men concentrate in plant/machine operations (32.8%).
                        </p>
                    </div>
                </div>

                <div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question" style="margin-bottom: 2rem; padding-bottom: 2rem; border-bottom: 1px solid var(--border-color);">
                    <h3 itemprop="name" style="font-size: 1.1rem; margin-bottom: 0.75rem;">Where do most OFWs go to work?</h3>
                    <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                        <p itemprop="text" style="color: var(--text-secondary);">
                            <strong>Asia is the dominant destination</strong>, hosting 74.5% of all OFWs. Within Asia, the Middle East leads with ~49% of OFWs. The top 5 destinations are: Saudi Arabia (21.9%), UAE (12.4%), Hong Kong (6.3%), Kuwait (6.3%), and Qatar (5.3%). Different destinations have distinct gender patterns - Hong Kong and Kuwait employ almost exclusively women (domestic workers).
                        </p>
                    </div>
                </div>

                <div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question" style="margin-bottom: 2rem; padding-bottom: 2rem; border-bottom: 1px solid var(--border-color);">
                    <h3 itemprop="name" style="font-size: 1.1rem; margin-bottom: 0.75rem;">How much money do OFWs send home?</h3>
                    <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                        <p itemprop="text" style="color: var(--text-secondary);">
                            Total OFW remittances reached <strong>PHP 262.2 billion in 2024</strong>, a 9.9% increase from PHP 238.6 billion in 2023. Of this, PHP 214.3 billion (81.7%) was sent as cash, growing 14.5% year-over-year. The average remittance per OFW is PHP 129,054. OFWs in the Americas send the highest per capita (PHP 202,761), while those in Asia send PHP 91,252 on average.
                        </p>
                    </div>
                </div>

                <div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question" style="margin-bottom: 2rem; padding-bottom: 0;">
                    <h3 itemprop="name" style="font-size: 1.1rem; margin-bottom: 0.75rem;">What region of the Philippines produces the most OFWs?</h3>
                    <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                        <p itemprop="text" style="color: var(--text-secondary);">
                            <strong>CALABARZON (Cavite, Laguna, Batangas, Rizal, Quezon)</strong> is the top OFW-producing region with 20.5% of all OFWs. Central Luzon follows with 11.3%, and Western Visayas with 9.5%. Overall, Luzon produces 62.9% of all OFWs due to greater industrialization and proximity to international ports and airports.
                        </p>
                    </div>
                </div>

            </div>
        </div>
    </div>
</section>
```

---

## PART 5: AUTHOR BIO SECTION

### Add to All Project Pages

**Add this before the CTA Section (before `<!-- CTA Section -->`):**

```html
<!-- Author Bio Section -->
<section class="section">
    <div class="container">
        <div class="chart-container fade-up">
            <div style="display: grid; grid-template-columns: 1fr 3fr; gap: 2rem; align-items: start;">
                <!-- Author Image -->
                <div style="text-align: center;">
                    <img src="https://www.allanninal.dev/images/profile.jpg" alt="Allan Niñal" style="width: 180px; height: 180px; border-radius: 12px; border: 1px solid var(--border-color); object-fit: cover;">
                </div>

                <!-- Author Info -->
                <div>
                    <h2 style="margin-bottom: 1rem; font-size: 1.5rem;">About the Analyst</h2>

                    <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                        <strong>Allan Niñal</strong> is a Data & AI Engineer specializing in Philippine socioeconomic data analysis. With expertise in Python, data visualization, statistical analysis, and machine learning, he transforms complex datasets into actionable insights that inform policy decisions and research.
                    </p>

                    <div style="margin-bottom: 1.5rem;">
                        <h4 style="margin-bottom: 0.75rem; font-size: 0.95rem; color: var(--text-primary); text-transform: uppercase; letter-spacing: 0.05em;">Focus Areas</h4>
                        <ul style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; color: var(--text-secondary); list-style: none; padding: 0;">
                            <li>Data Analytics & Visualization</li>
                            <li>Health Economics</li>
                            <li>Labor Migration Analysis</li>
                            <li>Education Systems</li>
                            <li>Poverty & Income Analysis</li>
                            <li>Public Policy Research</li>
                        </ul>
                    </div>

                    <div style="margin-bottom: 1.5rem;">
                        <h4 style="margin-bottom: 0.75rem; font-size: 0.95rem; color: var(--text-primary); text-transform: uppercase; letter-spacing: 0.05em;">Technical Skills</h4>
                        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                            <span style="padding: 0.375rem 0.75rem; background: var(--bg-card-hover); border-radius: 6px; font-size: 0.85rem; color: var(--text-secondary);">Python</span>
                            <span style="padding: 0.375rem 0.75rem; background: var(--bg-card-hover); border-radius: 6px; font-size: 0.85rem; color: var(--text-secondary);">Pandas</span>
                            <span style="padding: 0.375rem 0.75rem; background: var(--bg-card-hover); border-radius: 6px; font-size: 0.85rem; color: var(--text-secondary);">Data Visualization</span>
                            <span style="padding: 0.375rem 0.75rem; background: var(--bg-card-hover); border-radius: 6px; font-size: 0.85rem; color: var(--text-secondary);">Statistical Analysis</span>
                            <span style="padding: 0.375rem 0.75rem; background: var(--bg-card-hover); border-radius: 6px; font-size: 0.85rem; color: var(--text-secondary);">HTML/CSS</span>
                            <span style="padding: 0.375rem 0.75rem; background: var(--bg-card-hover); border-radius: 6px; font-size: 0.85rem; color: var(--text-secondary);">Chart.js</span>
                        </div>
                    </div>

                    <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                        <a href="https://www.linkedin.com/in/allanninal" target="_blank" style="color: var(--accent-primary); text-decoration: none; font-weight: 500;">LinkedIn Profile</a>
                        <a href="https://github.com/allanninal" target="_blank" style="color: var(--accent-primary); text-decoration: none; font-weight: 500;">GitHub</a>
                        <a href="https://dev.to/allanninal" target="_blank" style="color: var(--accent-primary); text-decoration: none; font-weight: 500;">Dev.to Articles</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>
```

---

## PART 6: IMPLEMENTATION CHECKLIST

### Week 1 - CRITICAL (Do First)

- [ ] Add canonical tag to index.html
- [ ] Add canonical tags to all 11 project pages (update URLs)
- [ ] Add robots meta tag to all 12 pages
- [ ] Add JSON-LD Person schema to index.html
- [ ] Update og:image and twitter:image on all 12 pages
- [ ] Create og:image graphics (1200x630px) for all 12 pages

### Week 2 - HIGH PRIORITY

- [ ] Add JSON-LD Article + Dataset schema to each project page
- [ ] Add FAQ section to health-analysis.html
- [ ] Add FAQ section to ofw-analysis.html
- [ ] Add FAQ section to education-analysis.html
- [ ] Trim title tags to 50-60 characters
- [ ] Add published/updated dates with schema markup

### Week 3 - ENHANCEMENT

- [ ] Add author bio section to health-analysis.html
- [ ] Add author bio section to all project pages
- [ ] Add internal linking between related projects
- [ ] Enhance methodology sections
- [ ] Create glossary sections for key terms

### Week 4 - VALIDATION & TESTING

- [ ] Test all pages with Google Rich Results Test
- [ ] Validate JSON-LD with Schema.org Validator
- [ ] Check social previews with OpenGraph.xyz
- [ ] Verify Twitter cards with cards-dev.twitter.com
- [ ] Monitor Google Search Console

---

## PART 7: QUICK FILE REFERENCES

All 12 files needing updates:
1. `/Users/allanninal/Projects/allanninal.dev/index.html`
2. `/Users/allanninal/Projects/allanninal.dev/projects/fies-analysis.html`
3. `/Users/allanninal/Projects/allanninal.dev/projects/health-analysis.html`
4. `/Users/allanninal/Projects/allanninal.dev/projects/ofw-analysis.html`
5. `/Users/allanninal/Projects/allanninal.dev/projects/education-analysis.html`
6. `/Users/allanninal/Projects/allanninal.dev/projects/food-prices-analysis.html`
7. `/Users/allanninal/Projects/allanninal.dev/projects/housing-analysis.html`
8. `/Users/allanninal/Projects/allanninal.dev/projects/weather-analysis.html`
9. `/Users/allanninal/Projects/allanninal.dev/projects/traffic-analysis.html`
10. `/Users/allanninal/Projects/allanninal.dev/projects/typhoon-analysis.html`
11. `/Users/allanninal/Projects/allanninal.dev/projects/poverty-analysis.html`
12. `/Users/allanninal/Projects/allanninal.dev/projects/philippine-names-analysis.html`

---

*Template Version: 1.0*
*Created: January 26, 2026*
*Ready to use - copy-paste the code sections above*
