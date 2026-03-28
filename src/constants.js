/**
 * @fileoverview Application constants — portal metadata, feature descriptions, and redirect URLs.
 */

/** Student portal redirect URL */
export const STUDENT_PORTAL_URL = '/login';

/** NGO portal redirect URL */
export const NGO_PORTAL_URL = 'https://ngo.sevafy.in';

/** Donor portal redirect URL */
export const DONOR_PORTAL_URL = 'https://donor.sevafy.in';

/**
 * Portal card metadata rendered in the PortalSection component.
 * @type {Array<{id: string, label: string, heading: string, description: string, url: string}>}
 */
export const PORTALS = [
  {
    id: 'student',
    label: 'Student',
    heading: "I'm a Student",
    description:
      'Access ML-verified authentic scholarships. No fake leads, no wasted applications.',
    url: STUDENT_PORTAL_URL,
  },
  {
    id: 'ngo',
    label: 'NGO',
    heading: "I'm an NGO",
    description:
      'Partner with us. Get vetted, receive secure funding, and maintain total transparency.',
    url: NGO_PORTAL_URL,
  },
  {
    id: 'donor',
    label: 'Donor',
    heading: "I'm a Donor",
    description:
      "Donate to causes you believe in. Funds are distributed fairly — you'll know where it went after disbursement.",
    url: DONOR_PORTAL_URL,
  },
];

/**
 * Feature tile metadata rendered in the FeaturesGrid component.
 * @type {Array<{id: string, title: string, description: string}>}
 */
export const FEATURES = [
  {
    id: 'blockchain-ledger',
    title: 'Secure Ledger',
    description:
      'Every donation, recipient, and amount is logged immutably.',
  },
  {
    id: 'ml-scholarship-finder',
    title: 'Smart Scholarship Finder',
    description:
      'Authentic scholarships sourced through live verification — no fake listings.',
  },
  {
    id: 'scam-ngo-detection',
    title: 'Scam NGO Detection',
    description:
      'Historical data cross-referenced with registries to filter untrustworthy organizations.',
  },
  {
    id: 'fund-flow-normalization',
    title: 'Smart Fund Distribution',
    description:
      'Our engine redistributes donations to underfunded NGOs, eliminating popularity bias.',
  },
  {
    id: 'transparent-disbursement',
    title: 'Transparent Dashboard',
    description:
      'Real-time public dashboard showing every verified donation and disbursement.',
  },
  {
    id: 'donor-testimony-chain',
    title: 'Verified Testimonials',
    description:
      'Genuine donor testimonials and stories — no fabricated reviews.',
  },
];

/**
 * Social / footer links.
 * @type {Array<{id: string, label: string, url: string}>}
 */
export const FOOTER_LINKS = [
  { id: 'github', label: 'GitHub', url: 'https://github.com/sevafy' },
  { id: 'docs', label: 'Docs', url: 'https://docs.sevafy.in' },
  { id: 'contact', label: 'Contact', url: 'mailto:hello@sevafy.in' },
];
