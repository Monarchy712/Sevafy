/**
 * @fileoverview Application constants — portal metadata, feature descriptions, and redirect URLs.
 */

/** Student portal redirect URL */
export const STUDENT_PORTAL_URL = 'https://student.antigravity.in';

/** NGO portal redirect URL */
export const NGO_PORTAL_URL = 'https://ngo.antigravity.in';

/** Donor portal redirect URL */
export const DONOR_PORTAL_URL = 'https://donor.antigravity.in';

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
      'Partner with us. Submit your data, get vetted, and receive disbursements tracked on-chain.',
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
    title: 'Blockchain Ledger',
    description:
      'Donor account, NGO account, amount, and date logged immutably on-chain.',
  },
  {
    id: 'ml-scholarship-finder',
    title: 'ML Scholarship Finder',
    description:
      'Authenticated scholarships sourced through a live ML pipeline — no fake listings.',
  },
  {
    id: 'scam-ngo-detection',
    title: 'Scam NGO Detection',
    description:
      'Historical scam data cross-referenced with Maharashtra NGO registry to filter untrustworthy organizations.',
  },
  {
    id: 'fund-flow-normalization',
    title: 'Fund Flow Normalization',
    description:
      'ML recommendation engine redistributes donations to underfunded NGOs — popularity bias eliminated.',
  },
  {
    id: 'transparent-disbursement',
    title: 'Transparent Disbursement UI',
    description:
      'Real-time public dashboard showing every donation, bond, and disbursement.',
  },
  {
    id: 'donor-testimony-chain',
    title: 'Donor Testimony Chain',
    description:
      'Verified donor testimonials recorded on-chain — no fake reviews.',
  },
];

/**
 * Social / footer links.
 * @type {Array<{id: string, label: string, url: string}>}
 */
export const FOOTER_LINKS = [
  { id: 'github', label: 'GitHub', url: 'https://github.com/antigravity' },
  { id: 'docs', label: 'Docs', url: 'https://docs.antigravity.in' },
  { id: 'contact', label: 'Contact', url: 'mailto:hello@antigravity.in' },
];
