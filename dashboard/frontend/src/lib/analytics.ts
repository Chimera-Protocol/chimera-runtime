/**
 * Umami analytics helper — tracks custom events.
 *
 * Usage:
 *   import { trackEvent } from "@/lib/analytics";
 *   trackEvent("cta-click", { button: "start-free-trial" });
 *
 * Events are no-ops when Umami is not loaded (dev, ad-blockers, etc.).
 */

declare global {
  interface Window {
    umami?: {
      track: (name: string, data?: Record<string, string | number>) => void;
    };
  }
}

export function trackEvent(
  name: string,
  data?: Record<string, string | number>
) {
  if (typeof window !== "undefined" && window.umami) {
    window.umami.track(name, data);
  }
}

// Pre-defined event helpers
export const analytics = {
  // Landing page
  ctaClick: (button: string) => trackEvent("cta-click", { button }),
  pricingView: () => trackEvent("pricing-view"),
  pricingClick: (tier: string) => trackEvent("pricing-click", { tier }),

  // Auth
  registerStart: () => trackEvent("register-start"),
  registerComplete: () => trackEvent("register-complete"),
  loginComplete: () => trackEvent("login-complete"),

  // Dashboard
  policyCreate: () => trackEvent("policy-create"),
  policyVerify: () => trackEvent("policy-verify"),
  auditExport: () => trackEvent("audit-export"),
  licenseGenerate: () => trackEvent("license-generate"),

  // Contact / Lead
  contactSubmit: () => trackEvent("contact-submit"),
  demoRequest: () => trackEvent("demo-request"),

  // Docs
  docsView: (slug: string) => trackEvent("docs-view", { slug }),
};
