"use client";

import { useEffect } from "react";
import Header from "./components/Header";
import HeroSection from "./components/HeroSection";
import FeaturesGrid from "./components/FeatureGrid";
import HowItWorksSection from "./components/HowItWorks";
import CTASection from "./components/CTA";
import Footer from "./components/Footer";
import AnimationStyles from "./components/AnimationStyles";

export default function HomePage() {
  useEffect(() => {
    const animateElements = document.querySelectorAll("[data-animate]");
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("animate-in");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    
    animateElements.forEach(el => observer.observe(el));
    
    return () => observer.disconnect();
  }, []);

  return (
    <div className="font-sans min-h-screen bg-background text-foreground">
      <Header />
      <HeroSection />
      <div className="container mx-auto max-w-5xl px-4">
        <FeaturesGrid />
      </div>
      <HowItWorksSection />
      <CTASection />
      <Footer />
      <AnimationStyles />
    </div>
  );
}