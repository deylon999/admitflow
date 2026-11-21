import { Header } from '../../components/Header';
import { Hero } from '../../components/Hero';
import { StatsStrip } from '../../components/StatsStrip';
import { Problems } from '../../components/Problems';
import { Features } from '../../components/Features';
import { Calculator } from '../../components/Calculator';
import { Competition } from '../../components/Competition';
import { Testimonial } from '../../components/Testimonial';
import { FAQ } from '../../components/FAQ';
import { FinalCTA } from '../../components/FinalCTA';

export function LandingPage() {
  return (
    <div className="landing-page">
      <Header />
      <main>
        <Hero />
        <StatsStrip />
        <Problems />
        <Features />
        <Calculator />
        <Competition />
        <Testimonial />
        <FAQ />
        <FinalCTA />
      </main>

    </div>
  );
}
