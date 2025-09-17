// HowItWorksSection.tsx
"use client";

import { useState, useEffect } from "react";

export default function HowItWorksSection() {
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
    <section id="how-it-works" className="py-32 bg-muted/50">
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
            <StepItem 
              number={1}
              title="Give a route"
              description="optily takes delivery stops, truck specifications, charging locations, electricity prices, and driver schedules as inputs."
              isActive={activeStep === 0}
            />
            
            <StepItem 
              number={2}
              title="AI Processing"
              description="Our algorithms analyze thousands of possible combinations to find the optimal route and charging strategy."
              isActive={activeStep === 1}
            />
            
            <StepItem 
              number={3}
              title="Get Optimized Plan"
              description="Receive a detailed drive and charge plan that balances cost, time, and reliability."
              isActive={activeStep === 2}
            />
          </div>
          
          <div className="bg-gradient-to-br from-card to-background rounded-xl border shadow-md p-6 opacity-0 animate-slide-left"
               style={{ animationDelay: "0.6s", animationFillMode: "forwards" }}>
            <div className="text-sm font-mono space-y-4 text-muted-foreground">
              <div className="text-center text-lg font-bold bg-primary/10 py-2 rounded-md text-primary">
                Berlin → Munich → Berlin
              </div>
              
              <PlanDetail 
                title="Optimized Plan"
                icon={
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                    <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                    <path d="M2 17l10 5 10-5"></path>
                    <path d="M2 12l10 5 10-5"></path>
                  </svg>
                }
              >
                • Start with 90% charge<br/>
                • Charge in Munich: 60%<br/>
                • Total cost: <span className="text-primary font-semibold">€75.20</span><br/>
                • Total time: <span className="text-primary font-semibold">8h 15m</span>
              </PlanDetail>
              
              <PlanDetail 
                title="Traffic Delay Response"
                icon={
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                    <path d="M12 8c-2.8 0-5 2.2-5 5s2.2 5 5 5 5-2.2 5-5-2.2-5-5-5z"></path>
                    <path d="M12 3v1"></path>
                    <path d="M12 20v1"></path>
                    <path d="M3 12h1"></path>
                    <path d="M20 12h1"></path>
                  </svg>
                }
              >
                • Add quick charge at Stuttgart<br/>
                • Reduce charging time in Munich<br/>
                • New arrival: <span className="text-green-500 font-semibold">On schedule</span>
              </PlanDetail>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

interface StepItemProps {
  number: number;
  title: string;
  description: string;
  isActive: boolean;
}

function StepItem({ number, title, description, isActive }: StepItemProps) {
  return (
    <div className={`flex gap-4 items-start transition-all duration-500 ${isActive ? 'animate-blink' : 'opacity-50'} ${isActive ? 'p-4 rounded-lg shadow-lg border border-primary/20 bg-card/50' : ''}`}>
      <div className={`${isActive ? 'bg-primary' : 'bg-muted'} text-primary-foreground rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0 transition-colors duration-500`}>{number}</div>
      <div>
        <h3 className="font-semibold text-lg mb-2">{title}</h3>
        <p className="text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}

interface PlanDetailProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}

function PlanDetail({ title, icon, children }: PlanDetailProps) {
  return (
    <div className="bg-background/50 rounded-lg p-4 backdrop-blur-sm">
      <div className="flex items-center mb-2">
        <div className="bg-primary/20 p-1 rounded-full mr-2">
          {icon}
        </div>
        <span className="font-semibold text-foreground">{title}</span>
      </div>
      <div className="border-l-2 border-primary pl-4 py-1 ml-2">
        {children}
      </div>
    </div>
  );
}