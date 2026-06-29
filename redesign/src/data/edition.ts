// Edition flag — turns the free template into its Pro build.
// Free (default): PUBLIC_EDITION unset → isPro false. Pro: PUBLIC_EDITION=pro.
// See docs/PRO_PLATFORM_PLAN.md.
export const EDITION = import.meta.env.PUBLIC_EDITION === 'pro' ? 'pro' : 'free';
export const isPro = EDITION === 'pro';
