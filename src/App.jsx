import React from 'react';
import HeroSection from './components/HeroSection';
import PortalSection from './components/PortalSection';
import MissionStrip from './components/MissionStrip';
import FeaturesGrid from './components/FeaturesGrid';
import Footer from './components/Footer';

/**
 * App — root component composing all landing-page sections.
 *
 * @returns {React.JSX.Element}
 */
export default function App() {
  return (
    <>
      <main>
        <HeroSection />
        <PortalSection />
        <MissionStrip />
        <FeaturesGrid />
      </main>
      <Footer />
    </>
  );
}
