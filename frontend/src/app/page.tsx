"use client";

import { useEffect, useState } from "react";

export default function Home() {
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

  // Add state for tracking which step is active
  const [activeStep, setActiveStep] = useState(0);
  
  // Setup the step cycling effect
  useEffect(() => {
    // Cycle through steps every 3 seconds
    const interval = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % 3);
    }, 3000);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="font-sans min-h-screen bg-background text-foreground">
      <header className="fixed top-0 left-0 w-full bg-background/80 backdrop-blur-sm z-50 border-b border-border">
        <div className="container mx-auto px-4 py-3 flex justify-between items-center relative">
          <div className="flex items-center">
            <img src="/optily_logo.png" alt="Optily Logo" className="h-10" />
          </div>
          
          <nav className="hidden md:flex gap-6">
            <a href="https://calendar.app.google/wFGuAq55LVxxvrEe8" className="text-sm font-medium hover:text-primary transition-colors">Book a Call</a>
            <a href="https://www.linkedin.com/company/optily-eu" className="text-sm font-medium hover:text-primary transition-colors">Contact Us</a>
          </nav>
        </div>
      </header>
      
      <section className="pt-28 pb-20 px-4">
        <div className="container mx-auto max-w-5xl">
          <div className="text-center mb-12">
            <h1 
              className="text-4xl md:text-6xl font-bold tracking-tight mb-6 opacity-0 animate-fade-in" 
              style={{ animationDelay: "0.2s", animationFillMode: "forwards" }}
            >
              Smart Route Planning for E-Truck Fleets
            </h1>
            <p 
              className="text-xl text-muted-foreground max-w-3xl mx-auto opacity-0 animate-fade-in"
              style={{ animationDelay: "0.4s", animationFillMode: "forwards" }}
            >
              optily is an AI dispatcher that optimizes routes, charging stops, and schedules for electric truck fleets, reducing costs while ensuring on-time deliveries.
            </p>
          </div>
          
          <div 
            className="grid gap-8 p-8 rounded-lg border bg-card text-card-foreground shadow-sm opacity-0 animate-slide-up"
            style={{ animationDelay: "0.6s", animationFillMode: "forwards" }}
          >
            <div className="grid md:grid-cols-3 gap-6">
              <div className="flex flex-col gap-2 hover:translate-y-[-5px] transition-transform duration-300 items-center">
                <div className="bg-primary/10 p-3 rounded-full w-12 h-12 flex items-center justify-center animate-pulse-slow">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                    <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                    <path d="M2 17l10 5 10-5"></path>
                    <path d="M2 12l10 5 10-5"></path>
                  </svg>
                </div>
                <h3 className="font-semibold text-lg">Route Optimization</h3>
                <p className="text-muted-foreground text-sm text-center">Our intelligent algorithms find the most efficient routes considering traffic, weather, and delivery windows.</p>
              </div>
              
              <div className="flex flex-col gap-2 hover:translate-y-[-5px] transition-transform duration-300 items-center" style={{ transitionDelay: "0.1s" }}>
                <div className="bg-primary/10 p-3 rounded-full w-12 h-12 flex items-center justify-center animate-pulse-slow" style={{ animationDelay: "0.5s" }}>
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                  </svg>
                </div>
                <h3 className="font-semibold text-lg">Charging Strategy</h3>
                <p className="text-muted-foreground text-sm text-center">Optimize when and where to charge based on electricity prices, charging speeds, EU regulations, and availability.</p>
              </div>
              
              <div className="flex flex-col gap-2 hover:translate-y-[-5px] transition-transform duration-300 items-center" style={{ transitionDelay: "0.2s" }}>
                <div className="bg-primary/10 p-3 rounded-full w-12 h-12 flex items-center justify-center animate-pulse-slow" style={{ animationDelay: "1s" }}>
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                    <path d="M12 8c-2.8 0-5 2.2-5 5s2.2 5 5 5 5-2.2 5-5-2.2-5-5-5z"></path>
                    <path d="M12 3v1"></path>
                    <path d="M12 20v1"></path>
                    <path d="M3 12h1"></path>
                    <path d="M20 12h1"></path>
                    <path d="m18.364 5.636-.707.707"></path>
                    <path d="m6.343 17.657-.707.707"></path>
                    <path d="m5.636 5.636.707.707"></path>
                    <path d="m17.657 17.657.707.707"></path>
                  </svg>
                </div>
                <h3 className="font-semibold text-lg">Real-time Adaptation</h3>
                <p className="text-muted-foreground text-sm text-center">Dynamically adjust plans when conditions change due to traffic, charger availability, or delivery schedule changes.</p>
              </div>
            </div>
          </div>
        </div>
      </section>
      
      {/* How it works */}
      <section id="how-it-works" className="py-16 bg-muted/50">
        <div className="container mx-auto max-w-5xl px-4">
          <h2 
            className="text-3xl font-bold mb-12 text-center opacity-0 animate-fade-in"
            style={{ animationDelay: "0.2s", animationFillMode: "forwards" }}
          >
            How Optily Works
          </h2>
          
          <div className="grid md:grid-cols-2 gap-12">
            <div className="space-y-6 opacity-0 animate-slide-right"
                 style={{ animationDelay: "0.4s", animationFillMode: "forwards" }}>
              <div className={`flex gap-4 items-start transition-all duration-500 ${activeStep === 0 ? 'animate-blink' : 'opacity-50'} ${activeStep === 0 ? 'p-4 rounded-lg shadow-lg border border-primary/20 bg-card/50' : ''}`}>
                <div className={`${activeStep === 0 ? 'bg-primary' : 'bg-muted'} text-primary-foreground rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0 transition-colors duration-500`}>1</div>
                <div>
                  <h3 className="font-semibold text-lg mb-2">Give a route</h3>
                  <p className="text-muted-foreground">optily takes delivery stops, truck specifications, charging locations, electricity prices, and driver schedules as inputs.</p>
                </div>
              </div>
              
              <div className={`flex gap-4 items-start transition-all duration-500 ${activeStep === 1 ? 'animate-blink' : 'opacity-50'} ${activeStep === 1 ? 'p-4 rounded-lg shadow-lg border border-primary/20 bg-card/50' : ''}`}>
                <div className={`${activeStep === 1 ? 'bg-primary' : 'bg-muted'} text-primary-foreground rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0 transition-colors duration-500`}>2</div>
                <div>
                  <h3 className="font-semibold text-lg mb-2">AI Processing</h3>
                  <p className="text-muted-foreground">Our algorithms analyze thousands of possible combinations to find the optimal route and charging strategy.</p>
                </div>
              </div>
              
              <div className={`flex gap-4 items-start transition-all duration-500 ${activeStep === 2 ? 'animate-blink' : 'opacity-50'} ${activeStep === 2 ? 'p-4 rounded-lg shadow-lg border border-primary/20 bg-card/50' : ''}`}>
                <div className={`${activeStep === 2 ? 'bg-primary' : 'bg-muted'} text-primary-foreground rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0 transition-colors duration-500`}>3</div>
                <div>
                  <h3 className="font-semibold text-lg mb-2">Get Optimized Plan</h3>
                  <p className="text-muted-foreground">Receive a detailed drive and charge plan that balances cost, time, and reliability.</p>
                </div>
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-card to-background rounded-xl border shadow-md p-6 opacity-0 animate-slide-left"
                 style={{ animationDelay: "0.6s", animationFillMode: "forwards" }}>
              <div className="text-sm font-mono space-y-4 text-muted-foreground">
                <div className="text-center text-lg font-bold bg-primary/10 py-2 rounded-md text-primary">
                  Berlin → Munich → Berlin
                </div>
                
                <div className="bg-background/50 rounded-lg p-4 backdrop-blur-sm">
                  <div className="flex items-center mb-2">
                    <div className="bg-primary/20 p-1 rounded-full mr-2">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                        <path d="M2 17l10 5 10-5"></path>
                        <path d="M2 12l10 5 10-5"></path>
                      </svg>
                    </div>
                    <span className="font-semibold text-foreground">Optimized Plan</span>
                  </div>
                  <div className="border-l-2 border-primary pl-4 py-1 ml-2">
                    • Start with 90% charge<br/>
                    • Charge in Munich: 60%<br/>
                    • Total cost: <span className="text-primary font-semibold">€75.20</span><br/>
                    • Total time: <span className="text-primary font-semibold">8h 15m</span>
                  </div>
                </div>
                
                <div className="bg-background/50 rounded-lg p-4 backdrop-blur-sm">
                  <div className="flex items-center mb-2">
                    <div className="bg-primary/20 p-1 rounded-full mr-2">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                        <path d="M12 8c-2.8 0-5 2.2-5 5s2.2 5 5 5 5-2.2 5-5-2.2-5-5-5z"></path>
                        <path d="M12 3v1"></path>
                        <path d="M12 20v1"></path>
                        <path d="M3 12h1"></path>
                        <path d="M20 12h1"></path>
                      </svg>
                    </div>
                    <span className="font-semibold text-foreground">Traffic Delay Response</span>
                  </div>
                  <div className="border-l-2 border-primary pl-4 py-1 ml-2">
                    • Add quick charge at Stuttgart<br/>
                    • Reduce charging time in Munich<br/>
                    • New arrival: <span className="text-green-500 font-semibold">On schedule</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
      
      {/* CTA */}
      <section className="py-20">
        <div className="container mx-auto max-w-5xl px-4">
          <div className="bg-gradient-to-r from-primary to-primary/80 text-primary-foreground rounded-lg p-8 md:p-12 text-center">
            <h2 className="text-3xl font-bold mb-4">Ready to optimize your e-truck fleet?</h2>
            <p className="text-lg mb-8 max-w-2xl mx-auto opacity-90">Join the sustainable logistics revolution with optily.eu AI dispatcher</p>
            <div className="flex gap-4 justify-center flex-wrap">
              <a 
                href="https://calendar.app.google/wFGuAq55LVxxvrEe8"
                className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-primary-foreground/20 bg-transparent hover:bg-primary-foreground/10 h-10 px-6 py-2"
              >
                Book a Call
              </a>
            </div>
          </div>
        </div>
      </section>
      
      {/* Footer */}
      <footer className="border-t border-border py-4">
        <div className="container mx-auto px-4">
          <div className="flex flex-row justify-between items-center">
            <div className="flex items-center gap-2">
              <img src="/optily_logo.png" alt="Optily Logo" className="w-20" />
            </div>
            
            <div className="flex gap-4 text-xs text-muted-foreground">
              <a href="https://calendar.app.google/wFGuAq55LVxxvrEe8" className="hover:text-foreground transition-colors">Contact Us</a>
              <a href="https://www.linkedin.com/company/optily-eu" className="hover:text-foreground transition-colors">LinkedIn</a>
              <span className="text-muted-foreground/50">|</span>
              <span>© 2025 optily.eu</span>
            </div>
          </div>
        </div>
      </footer>

      <style jsx global>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes slideRight {
          from { opacity: 0; transform: translateX(-20px); }
          to { opacity: 1; transform: translateX(0); }
        }
        
        @keyframes slideLeft {
          from { opacity: 0; transform: translateX(20px); }
          to { opacity: 1; transform: translateX(0); }
        }
        
        @keyframes pulseSlow {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); }
        }
        
        @keyframes typing {
          from { width: 0 }
          to { width: 100% }
        }
        
        @keyframes zoom {
          from { opacity: 0; transform: scale(0.95); }
          to { opacity: 1; transform: scale(1); }
        }
        
        .animate-fade-in {
          animation: fadeIn 0.8s ease-out;
        }
        
        .animate-slide-up {
          animation: slideUp 0.8s ease-out;
        }
        
        .animate-slide-right {
          animation: slideRight 0.8s ease-out;
        }
        
        .animate-slide-left {
          animation: slideLeft 0.8s ease-out;
        }
        
        .animate-pulse-slow {
          animation: pulseSlow 3s infinite;
        }
        
        .animate-typing {
          animation: typing 2s steps(40, end);
        }
        
        [data-animate="fade"].animate-in {
          animation: fadeIn 0.8s ease-out forwards;
        }
        
        [data-animate="zoom"].animate-in {
          animation: zoom 0.8s ease-out forwards;
        }

        @keyframes blink {
          0%, 100% { opacity: 1; transform: scale(1); box-shadow: 0 0 0 rgba(59, 130, 246, 0.1); }
          50% { opacity: 0.95; transform: scale(1.01); box-shadow: 0 0 15px rgba(59, 130, 246, 0.2); }
        }
        
        .animate-blink {
          animation: blink 2s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
