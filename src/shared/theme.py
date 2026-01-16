"""
Shared theme and styling for the portfolio.
Provides consistent v0.dev-style CSS across all pages.
Merged with v0-generated component patterns.
"""

import streamlit as st


def apply_theme():
    """Apply the shared v0.dev-style theme to the page."""
    st.markdown(get_theme_css(), unsafe_allow_html=True)


def get_theme_css() -> str:
    """Return the shared CSS theme with v0 color system."""
    return """
<style>
    /* ========================================
       CSS Variables - v0 Design System
       OKLCH colors converted to hex for compatibility
       ======================================== */
    :root {
        /* Primary - Deep Blue */
        --primary: #1e40af;
        --primary-light: #3b82f6;
        --primary-foreground: #ffffff;
        --primary-10: rgba(30, 64, 175, 0.1);
        --primary-20: rgba(30, 64, 175, 0.2);

        /* Secondary - Green */
        --secondary: #22c55e;
        --secondary-light: #4ade80;
        --secondary-foreground: #ffffff;
        --secondary-10: rgba(34, 197, 94, 0.1);
        --secondary-20: rgba(34, 197, 94, 0.2);

        /* Accent - Amber/Orange */
        --accent: #f59e0b;
        --accent-light: #fbbf24;
        --accent-foreground: #0f172a;
        --accent-10: rgba(245, 158, 11, 0.1);
        --accent-20: rgba(245, 158, 11, 0.2);

        /* Backgrounds */
        --background: #fafafa;
        --background-secondary: #f1f5f9;
        --card: #ffffff;
        --card-hover: #f8fafc;
        --muted: #f1f5f9;

        /* Text */
        --foreground: #0f172a;
        --foreground-secondary: #334155;
        --foreground-muted: #64748b;
        --foreground-70: rgba(15, 23, 42, 0.7);
        --foreground-60: rgba(15, 23, 42, 0.6);

        /* Borders */
        --border: #e2e8f0;
        --border-hover: #cbd5e1;
        --border-50: rgba(226, 232, 240, 0.5);

        /* Semantic Colors */
        --success: #10b981;
        --success-light: #ecfdf5;
        --warning: #f59e0b;
        --warning-light: #fffbeb;
        --danger: #ef4444;
        --danger-light: #fef2f2;
        --info: #0ea5e9;
        --info-light: #f0f9ff;

        /* Chart Colors */
        --chart-1: #3b82f6;
        --chart-2: #22c55e;
        --chart-3: #f59e0b;
        --chart-4: #06b6d4;
        --chart-5: #ef4444;
        --chart-6: #8b5cf6;

        /* Gradients */
        --gradient-primary: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        --gradient-secondary: linear-gradient(135deg, #059669 0%, #22c55e 100%);
        --gradient-accent: linear-gradient(135deg, #d97706 0%, #f59e0b 100%);
        --gradient-purple: linear-gradient(135deg, #7c3aed 0%, #8b5cf6 100%);
        --gradient-hero: linear-gradient(to bottom, var(--background) 0%, var(--background) 50%, var(--muted) 100%);

        /* Radius */
        --radius-sm: 6px;
        --radius-md: 10px;
        --radius-lg: 12px;
        --radius-xl: 16px;
        --radius-full: 9999px;

        /* Shadows */
        --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.04);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        --shadow-card-hover: 0 10px 40px -10px rgba(0, 0, 0, 0.15);

        /* Transitions */
        --transition-fast: 150ms ease;
        --transition-base: 200ms ease;
        --transition-slow: 300ms ease;
    }

    /* ========================================
       Global Styles
       ======================================== */
    .stApp {
        background: var(--background);
    }

    .main {
        background: var(--background);
    }

    .main .block-container {
        padding-top: 0;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* Hide Streamlit UI elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    .stDeployButton {display: none !important;}
    button[kind="header"] {display: none !important;}

    /* ========================================
       Hero Section (v0 Pattern - Enhanced)
       ======================================== */
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-6px); }
    }

    @keyframes shimmer {
        0% { background-position: -200% center; }
        100% { background-position: 200% center; }
    }

    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 20px rgba(30, 64, 175, 0.15); }
        50% { box-shadow: 0 0 40px rgba(30, 64, 175, 0.25); }
    }

    @keyframes fade-in-up {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes gradient-shift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }

    .hero-section {
        min-height: 80vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--gradient-hero);
        padding: 4rem 2rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }

    /* Subtle animated background decoration */
    .hero-section::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle at 30% 30%, rgba(30, 64, 175, 0.03) 0%, transparent 50%),
                    radial-gradient(circle at 70% 70%, rgba(34, 197, 94, 0.03) 0%, transparent 50%);
        animation: gradient-shift 15s ease infinite;
        background-size: 200% 200%;
        pointer-events: none;
    }

    .hero-content {
        max-width: 800px;
        margin: 0 auto;
        position: relative;
        z-index: 1;
    }

    .hero-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        justify-content: center;
        margin-bottom: 1.5rem;
        animation: fade-in-up 0.6s ease-out;
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background: var(--primary-10);
        border: 1px solid var(--primary-20);
        border-radius: var(--radius-full);
        color: var(--primary);
        font-size: 0.875rem;
        font-weight: 500;
        animation: float 4s ease-in-out infinite;
    }

    .hero-badge-status {
        background: var(--secondary-10);
        border-color: var(--secondary-20);
        color: var(--secondary);
        animation-delay: 0.5s;
    }

    .hero-badge-status::before {
        content: '';
        width: 8px;
        height: 8px;
        background: var(--secondary);
        border-radius: 50%;
        animation: pulse-glow 2s ease-in-out infinite;
    }

    .hero-greeting {
        font-size: 1.125rem;
        color: var(--foreground-muted);
        font-weight: 500;
        margin-bottom: 0.5rem;
        animation: fade-in-up 0.6s ease-out 0.1s both;
    }

    .hero-title {
        font-size: clamp(2.75rem, 7vw, 5rem);
        font-weight: 800;
        color: var(--foreground);
        line-height: 1.05;
        letter-spacing: -0.03em;
        margin-bottom: 1.5rem;
        animation: fade-in-up 0.6s ease-out 0.2s both;
    }

    .hero-title-gradient {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #1e40af 100%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: shimmer 4s linear infinite;
    }

    .hero-subtitle {
        font-size: 1.25rem;
        color: var(--foreground-70);
        line-height: 1.8;
        max-width: 620px;
        margin: 0 auto 2.5rem auto;
        animation: fade-in-up 0.6s ease-out 0.3s both;
    }

    .hero-highlight {
        color: var(--primary);
        font-weight: 600;
    }

    .hero-buttons {
        display: flex;
        gap: 1rem;
        justify-content: center;
        flex-wrap: wrap;
        animation: fade-in-up 0.6s ease-out 0.4s both;
    }

    .hero-btn-primary,
    a.hero-btn-primary,
    a.hero-btn-primary:hover {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 1rem 2rem;
        background: var(--primary);
        color: #ffffff !important;
        border: none;
        border-radius: var(--radius-lg);
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all var(--transition-base);
        position: relative;
        overflow: hidden;
    }

    .hero-btn-primary svg,
    a.hero-btn-primary svg {
        fill: #ffffff !important;
    }

    .hero-btn-primary::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s ease;
    }

    .hero-btn-primary:hover,
    a.hero-btn-primary:hover {
        background: var(--primary-light);
        transform: translateY(-3px);
        box-shadow: 0 10px 30px -10px rgba(30, 64, 175, 0.5);
        color: #ffffff !important;
    }

    .hero-btn-primary:hover::before {
        left: 100%;
    }

    .hero-btn-secondary {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 1rem 2rem;
        background: var(--card);
        color: var(--foreground);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all var(--transition-base);
        position: relative;
    }

    .hero-btn-secondary:hover {
        background: var(--muted);
        border-color: var(--primary);
        color: var(--primary);
        transform: translateY(-3px);
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.15);
    }

    /* Quick stats in hero */
    .hero-stats {
        display: flex;
        justify-content: center;
        gap: 3rem;
        margin-top: 3rem;
        padding-top: 2rem;
        border-top: 1px solid var(--border-50);
        animation: fade-in-up 0.6s ease-out 0.5s both;
    }

    .hero-stat {
        text-align: center;
    }

    .hero-stat-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--primary);
        line-height: 1;
    }

    .hero-stat-label {
        font-size: 0.8rem;
        color: var(--foreground-muted);
        margin-top: 0.375rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    @media (max-width: 640px) {
        .hero-stats {
            gap: 1.5rem;
        }
        .hero-stat-value {
            font-size: 1.5rem;
        }
    }

    /* ========================================
       Stats Section (v0 Pattern)
       ======================================== */
    .stats-section {
        padding: 4rem 2rem;
        background: var(--muted);
    }

    .stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1.5rem;
        max-width: 1200px;
        margin: 0 auto;
    }

    @media (max-width: 1024px) {
        .stats-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }

    @media (max-width: 640px) {
        .stats-grid {
            grid-template-columns: 1fr;
        }
    }

    .stat-card {
        background: var(--card);
        border: 1px solid var(--border-50);
        border-radius: var(--radius-xl);
        padding: 1.5rem;
        transition: all var(--transition-base);
    }

    .stat-card:hover {
        border-color: var(--border);
        box-shadow: var(--shadow-md);
    }

    .stat-label {
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--foreground-muted);
        margin-bottom: 0.5rem;
    }

    .stat-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--primary);
        margin-bottom: 0.5rem;
    }

    .stat-value-secondary {
        color: var(--secondary);
    }

    .stat-value-accent {
        color: var(--accent);
    }

    .stat-description {
        font-size: 0.875rem;
        color: var(--foreground-60);
    }

    /* Gradient stat cards (original style) */
    .stat-card-gradient {
        background: var(--gradient-primary);
        border-radius: var(--radius-xl);
        padding: 1.5rem;
        text-align: center;
        color: white;
    }

    .stat-card-gradient.green {
        background: var(--gradient-secondary);
    }

    .stat-card-gradient.purple {
        background: var(--gradient-purple);
    }

    .stat-card-gradient.orange {
        background: var(--gradient-accent);
    }

    .stat-card-gradient .stat-value {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
    }

    .stat-card-gradient .stat-label {
        color: rgba(255, 255, 255, 0.9);
        font-size: 0.875rem;
    }

    /* ========================================
       Project Cards (v0 Pattern)
       ======================================== */
    .projects-section {
        padding: 4rem 2rem;
        background: var(--muted);
    }

    .projects-header {
        margin-bottom: 3rem;
    }

    .projects-header h2 {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--foreground);
        margin-bottom: 0.5rem;
    }

    .projects-header p {
        font-size: 1.125rem;
        color: var(--foreground-70);
    }

    .projects-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1.5rem;
        max-width: 1200px;
        margin: 0 auto;
    }

    @media (max-width: 768px) {
        .projects-grid {
            grid-template-columns: 1fr;
        }
    }

    .project-card {
        background: var(--card);
        border: 1px solid var(--border-50);
        border-radius: var(--radius-xl);
        padding: 1.5rem;
        transition: all var(--transition-base);
        position: relative;
        overflow: hidden;
    }

    .project-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: var(--gradient-primary);
        transform: scaleX(0);
        transform-origin: left;
        transition: transform var(--transition-base);
    }

    .project-card:hover {
        box-shadow: var(--shadow-lg);
        border-color: var(--border);
    }

    .project-card:hover::before {
        transform: scaleX(1);
    }

    .project-card-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        margin-bottom: 1rem;
    }

    .project-category {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        background: var(--accent-10);
        border: 1px solid var(--accent-20);
        border-radius: var(--radius-full);
        color: var(--accent);
        font-size: 0.75rem;
        font-weight: 500;
    }

    .project-arrow {
        color: var(--foreground-muted);
        transition: color var(--transition-base);
    }

    .project-card:hover .project-arrow {
        color: var(--accent);
    }

    .project-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--foreground);
        margin-bottom: 0.75rem;
    }

    .project-description {
        color: var(--foreground-70);
        font-size: 0.95rem;
        line-height: 1.6;
        margin-bottom: 1rem;
    }

    .project-impact {
        padding-top: 1rem;
        border-top: 1px solid var(--border-50);
    }

    .project-impact p {
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--secondary);
    }

    /* Style for st.page_link after project cards */
    .project-card + div [data-testid="stPageLink-nav"] > a {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1.5rem !important;
        background: var(--primary) !important;
        color: #ffffff !important;
        border-radius: var(--radius-md) !important;
        font-size: 0.875rem !important;
        font-weight: 600 !important;
        text-decoration: none !important;
        transition: all var(--transition-base) !important;
        border: none !important;
        margin-top: 0.75rem;
    }

    .project-card + div [data-testid="stPageLink-nav"] > a:hover {
        background: var(--primary-light) !important;
        transform: translateX(4px);
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(30, 64, 175, 0.3) !important;
    }

    /* Alternative selector for page links */
    .stPageLink a {
        display: inline-flex !important;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1.5rem !important;
        background: var(--primary) !important;
        color: #ffffff !important;
        border-radius: var(--radius-md) !important;
        font-size: 0.875rem !important;
        font-weight: 600 !important;
        text-decoration: none !important;
        transition: all var(--transition-base) !important;
        border: none !important;
    }

    .stPageLink a:hover {
        background: var(--primary-light) !important;
        transform: translateX(4px);
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(30, 64, 175, 0.3) !important;
        text-decoration: none !important;
    }

    .stPageLink a span {
        color: #ffffff !important;
    }

    /* Project insights box */
    .project-insights {
        background: var(--muted);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 1rem;
        margin-bottom: 1rem;
    }

    .project-insights-title {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--foreground-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    .project-insight-item {
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
        color: var(--foreground-secondary);
        font-size: 0.875rem;
        margin-bottom: 0.375rem;
    }

    .project-insight-item::before {
        content: '→';
        color: var(--primary);
        font-weight: bold;
    }

    .project-insight-value {
        color: var(--primary);
        font-weight: 600;
    }

    /* ========================================
       Research Section (v0 Pattern)
       ======================================== */
    .research-section {
        padding: 4rem 2rem;
        background: var(--background);
    }

    .research-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.5rem;
        max-width: 1200px;
        margin: 0 auto;
    }

    @media (max-width: 1024px) {
        .research-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }

    @media (max-width: 640px) {
        .research-grid {
            grid-template-columns: 1fr;
        }
    }

    .research-card {
        background: var(--card);
        border: 1px solid var(--border-50);
        border-radius: var(--radius-xl);
        padding: 1.5rem;
        transition: all var(--transition-base);
    }

    .research-card:hover {
        box-shadow: var(--shadow-lg);
    }

    .research-card h4 {
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--foreground);
        margin-bottom: 0.75rem;
    }

    .research-card p {
        color: var(--foreground-70);
        font-size: 0.95rem;
        line-height: 1.6;
        margin-bottom: 1rem;
    }

    .research-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    .research-tag {
        padding: 0.25rem 0.75rem;
        background: var(--secondary-10);
        border: 1px solid var(--secondary-20);
        border-radius: var(--radius-full);
        color: var(--secondary);
        font-size: 0.75rem;
        font-weight: 500;
    }

    /* ========================================
       Footer Section (v0 Pattern)
       ======================================== */
    .footer-section {
        padding: 4rem 2rem;
        background: var(--foreground);
        color: var(--background);
    }

    .footer-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 3rem;
        max-width: 1200px;
        margin: 0 auto 3rem auto;
    }

    @media (max-width: 768px) {
        .footer-grid {
            grid-template-columns: 1fr;
            gap: 2rem;
        }
    }

    .footer-brand h3 {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }

    .footer-brand p {
        color: rgba(255, 255, 255, 0.7);
        line-height: 1.7;
    }

    .footer-links h4 {
        font-weight: 600;
        margin-bottom: 1.5rem;
    }

    .footer-links ul {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .footer-links li {
        margin-bottom: 0.75rem;
    }

    .footer-links a {
        color: rgba(255, 255, 255, 0.7);
        text-decoration: none;
        transition: color var(--transition-base);
    }

    .footer-links a:hover {
        color: white;
    }

    .footer-cta h4 {
        font-weight: 600;
        margin-bottom: 1rem;
    }

    .footer-cta p {
        color: rgba(255, 255, 255, 0.7);
        margin-bottom: 1rem;
    }

    .footer-cta-btn {
        padding: 0.5rem 1.5rem;
        background: var(--background);
        color: var(--foreground);
        border: none;
        border-radius: var(--radius-lg);
        font-weight: 600;
        cursor: pointer;
        transition: all var(--transition-base);
    }

    .footer-cta-btn:hover {
        opacity: 0.9;
    }

    .footer-bottom {
        border-top: 1px solid rgba(255, 255, 255, 0.2);
        padding-top: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        max-width: 1200px;
        margin: 0 auto;
    }

    @media (max-width: 640px) {
        .footer-bottom {
            flex-direction: column;
            gap: 1.5rem;
            text-align: center;
        }
    }

    .footer-copyright {
        color: rgba(255, 255, 255, 0.6);
        font-size: 0.875rem;
    }

    .footer-social {
        display: flex;
        gap: 1rem;
    }

    .footer-social a {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: var(--radius-md);
        color: white;
        text-decoration: none;
        transition: background var(--transition-base);
    }

    .footer-social a:hover {
        background: rgba(255, 255, 255, 0.2);
    }

    /* ========================================
       Section Headers
       ======================================== */
    .section-header {
        margin-bottom: 3rem;
    }

    .section-header h2 {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--foreground);
        margin-bottom: 0.5rem;
    }

    .section-header p {
        font-size: 1.125rem;
        color: var(--foreground-70);
    }

    .section-header-line {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin: 2rem 0 1.5rem 0;
    }

    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--foreground);
        margin: 0;
    }

    .section-line {
        flex: 1;
        height: 1px;
        background: var(--border);
    }

    /* ========================================
       Page Title Styling (Dashboards)
       ======================================== */
    .page-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: var(--gradient-primary);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }

    .page-subtitle {
        color: var(--foreground-secondary);
        font-size: 1.1rem;
        font-style: italic;
        margin-bottom: 1.5rem;
    }

    /* Data Badge */
    .data-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: var(--primary-10);
        color: var(--primary);
        padding: 0.5rem 1rem;
        border-radius: var(--radius-full);
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 1rem;
        border: 1px solid var(--primary-20);
    }

    /* ========================================
       Info Boxes
       ======================================== */
    .info-box {
        background: var(--info-light);
        border: 1px solid var(--info);
        border-left: 4px solid var(--info);
        border-radius: var(--radius-md);
        padding: 1rem 1.25rem;
        color: var(--foreground);
        margin: 1rem 0;
    }

    .warning-box {
        background: var(--warning-light);
        border: 1px solid var(--warning);
        border-left: 4px solid var(--warning);
        border-radius: var(--radius-md);
        padding: 1rem 1.25rem;
        color: var(--foreground);
        margin: 1rem 0;
    }

    .success-box {
        background: var(--success-light);
        border: 1px solid var(--success);
        border-left: 4px solid var(--success);
        border-radius: var(--radius-md);
        padding: 1rem 1.25rem;
        color: var(--foreground);
        margin: 1rem 0;
    }

    .danger-box {
        background: var(--danger-light);
        border: 1px solid var(--danger);
        border-left: 4px solid var(--danger);
        border-radius: var(--radius-md);
        padding: 1rem 1.25rem;
        color: var(--foreground);
        margin: 1rem 0;
    }

    /* ========================================
       Tech Tags
       ======================================== */
    .tech-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    .tech-tag {
        background: var(--muted);
        border: 1px solid var(--border);
        color: var(--foreground-secondary);
        padding: 0.375rem 0.75rem;
        border-radius: var(--radius-sm);
        font-size: 0.8rem;
        font-weight: 500;
        transition: all var(--transition-base);
    }

    .tech-tag:hover {
        border-color: var(--primary);
        color: var(--foreground);
    }

    .tech-tag-sidebar {
        display: inline-block;
        background: var(--primary-10);
        color: var(--primary);
        padding: 0.25rem 0.75rem;
        border-radius: var(--radius-sm);
        font-size: 0.8rem;
        font-weight: 500;
        margin: 0.25rem 0.25rem 0.25rem 0;
    }

    /* ========================================
       Sidebar Styling
       ======================================== */
    [data-testid="stSidebar"] {
        background: var(--background);
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] > div:first-child {
        background: var(--background);
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: var(--foreground-secondary);
    }

    [data-testid="stSidebar"] h3 {
        color: var(--foreground);
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.75rem;
    }

    [data-testid="stSidebar"] a {
        color: var(--foreground-secondary);
        text-decoration: none;
        transition: color var(--transition-base);
    }

    [data-testid="stSidebar"] a:hover {
        color: var(--primary);
    }

    /* ========================================
       Buttons
       ======================================== */
    .stButton > button {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        color: var(--foreground) !important;
        border-radius: var(--radius-md) !important;
        padding: 0.625rem 1.25rem !important;
        font-weight: 500 !important;
        transition: all var(--transition-base) !important;
        box-shadow: var(--shadow-sm) !important;
    }

    .stButton > button:hover {
        border-color: var(--primary) !important;
        background: var(--primary-10) !important;
        color: var(--primary) !important;
        box-shadow: var(--shadow-md) !important;
    }

    /* ========================================
       Tabs Styling
       ======================================== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.25rem;
        background: var(--muted);
        padding: 0.375rem;
        border-radius: var(--radius-md);
        border: 1px solid var(--border);
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: var(--radius-sm);
        color: var(--foreground-muted);
        font-weight: 500;
        padding: 0.5rem 1rem;
        font-size: 0.875rem;
    }

    .stTabs [aria-selected="true"] {
        background: var(--card) !important;
        color: var(--foreground) !important;
        box-shadow: var(--shadow-sm);
    }

    /* ========================================
       Expander Styling
       ======================================== */
    .streamlit-expanderHeader {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        font-weight: 500 !important;
        color: var(--foreground) !important;
        box-shadow: var(--shadow-sm) !important;
    }

    .streamlit-expanderHeader:hover {
        border-color: var(--border-hover) !important;
        background: var(--muted) !important;
    }

    /* ========================================
       Data Table Styling
       ======================================== */
    .stDataFrame {
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-sm);
    }

    .stDataFrame [data-testid="stDataFrameResizable"] {
        border-radius: var(--radius-md);
        overflow: hidden;
    }

    /* ========================================
       Links
       ======================================== */
    a {
        color: var(--primary);
        text-decoration: none;
    }

    a:hover {
        text-decoration: underline;
    }

    /* ========================================
       Metric Styling
       ======================================== */
    [data-testid="stMetricValue"] {
        color: var(--primary);
    }

    /* ========================================
       Plotly chart container
       ======================================== */
    .js-plotly-plot {
        border-radius: var(--radius-md);
    }

    /* ========================================
       Insight Card (original style)
       ======================================== */
    .insight-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: var(--radius-xl);
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: all var(--transition-base);
        box-shadow: var(--shadow-sm);
    }

    .insight-card:hover {
        border-color: var(--border-hover);
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }

    .insight-card h4 {
        color: var(--foreground);
        margin-bottom: 0.5rem;
    }

    .insight-card p {
        color: var(--foreground-secondary);
        font-size: 0.95rem;
        line-height: 1.6;
    }

    /* ========================================
       Callout Box
       ======================================== */
    .callout {
        background: var(--gradient-primary);
        border-radius: var(--radius-xl);
        padding: 1.5rem 2rem;
        color: white;
        margin: 1.5rem 0;
    }

    .callout h2 {
        color: white;
        margin-bottom: 0.5rem;
    }

    .callout p {
        opacity: 0.9;
    }

    /* ========================================
       Page Footer
       ======================================== */
    .page-footer {
        text-align: center;
        padding: 2rem 0;
        margin-top: 2rem;
        border-top: 1px solid var(--border);
        color: var(--foreground-muted);
        font-size: 0.875rem;
    }

    .page-footer a {
        color: var(--foreground-secondary);
        margin: 0 1rem;
    }

    .page-footer a:hover {
        color: var(--primary);
    }
</style>
"""


def render_sidebar_nav():
    """Render consistent sidebar navigation."""
    st.markdown("### Navigation")
    st.page_link("Home.py", label="Home", icon="🏠")
    st.page_link("pages/2_Media_Perception.py", label="Media Perception", icon="📰")
    st.page_link("pages/3_Mobile_Data_Pricing.py", label="Mobile Data Pricing", icon="📱")
    st.page_link("pages/4_World_Happiness.py", label="World Happiness", icon="😊")
    st.page_link("pages/5_Economic_History.py", label="Economic History", icon="💰")
    st.page_link("pages/6_Life_Expectancy.py", label="Life Expectancy", icon="🏥")
    st.page_link("pages/7_Plastic_Waste.py", label="Plastic Waste", icon="🌊")
    st.page_link("pages/8_Natural_Disasters.py", label="Natural Disasters", icon="🌋")


def render_tech_tags(tags: list):
    """Render tech tags in sidebar."""
    st.markdown("### Built With")
    tags_html = "".join([f'<span class="tech-tag-sidebar">{tag}</span>' for tag in tags])
    st.markdown(tags_html, unsafe_allow_html=True)


def render_page_footer(dataset_url: str = None):
    """Render consistent page footer."""
    footer_html = '<div class="page-footer">'
    if dataset_url:
        footer_html += f'<a href="{dataset_url}" target="_blank">Dataset Source</a> | '
    footer_html += '<a href="/">Back to Portfolio</a>'
    footer_html += '</div>'
    st.markdown(footer_html, unsafe_allow_html=True)
