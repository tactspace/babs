// Header.tsx
"use client";

import { useState } from "react";

export default function Header() {
  // Add state for mobile menu
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Toggle mobile menu
  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  return (
    <header className="fixed top-0 left-0 w-full bg-background/80 backdrop-blur-sm z-50 border-b border-border">
      <div className="container mx-auto px-4 py-3 flex justify-between items-center relative">
        <div className="flex items-center">
          <img src="/optily_logo.png" alt="Optily Logo" className="h-10" />
        </div>
        
        {/* Desktop Navigation */}
        <nav className="hidden md:flex gap-6">
          <a href="https://calendar.app.google/wFGuAq55LVxxvrEe8" className="text-sm font-medium hover:text-primary transition-colors">Book a Call</a>
          <a href="https://www.linkedin.com/company/optily-eu" className="text-sm font-medium hover:text-primary transition-colors">Contact Us</a>
        </nav>
        
        {/* Mobile Hamburger Button */}
        <button 
          className="md:hidden flex flex-col justify-center items-center w-8 h-8 space-y-1.5 focus:outline-none"
          onClick={toggleMobileMenu}
          aria-label="Toggle menu"
        >
          <span className={`block w-5 h-0.5 bg-foreground transition-transform duration-300 ease-in-out ${mobileMenuOpen ? 'rotate-45 translate-y-2' : ''}`}></span>
          <span className={`block w-5 h-0.5 bg-foreground transition-opacity duration-300 ease-in-out ${mobileMenuOpen ? 'opacity-0' : ''}`}></span>
          <span className={`block w-5 h-0.5 bg-foreground transition-transform duration-300 ease-in-out ${mobileMenuOpen ? '-rotate-45 -translate-y-2' : ''}`}></span>
        </button>
        
        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="absolute top-full left-0 right-0 bg-background/95 backdrop-blur-md border-b border-border shadow-lg md:hidden">
            <div className="flex flex-col p-4 space-y-4">
              <a 
                href="https://calendar.app.google/wFGuAq55LVxxvrEe8" 
                className="text-sm font-medium hover:text-primary transition-colors py-2"
                onClick={() => setMobileMenuOpen(false)}
              >
                Schedule a Demo
              </a>
              <a 
                href="https://www.linkedin.com/company/optily-eu" 
                className="text-sm font-medium hover:text-primary transition-colors py-2"
                onClick={() => setMobileMenuOpen(false)}
              >
                Contact Us
              </a>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}