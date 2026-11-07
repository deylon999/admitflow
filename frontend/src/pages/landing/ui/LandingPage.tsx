import { Calculator } from '@/features/calculate-admission';
import {
  HeroSection,
  ProblemSection,
  ExplanationSection,
  InterviewsSection,
  CapabilitiesSection,
  QuestionsSection,
} from './sections';
export function LandingPage() {
  return (
    <main id="top">
      <HeroSection />
      <ProblemSection />
      <ExplanationSection />
      <Calculator />
      <InterviewsSection />
      <CapabilitiesSection />
      <QuestionsSection />
    </main>
  );
}
