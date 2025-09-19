"use client";

export default function FeaturesGrid() {
    return (
      <div 
        className="grid gap-8 p-8 rounded-lg border bg-card text-card-foreground shadow-sm opacity-0 animate-slide-up"
        style={{ animationDelay: "0.6s", animationFillMode: "forwards" }}
      >
        <div className="grid md:grid-cols-3 gap-6">
          <FeatureCard 
            title="Route Optimization"
            description="Our intelligent algorithms find the most efficient routes considering traffic, weather, and delivery windows."
            icon={
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                <path d="M2 17l10 5 10-5"></path>
                <path d="M2 12l10 5 10-5"></path>
              </svg>
            }
          />
          
          <FeatureCard 
            title="Charging Strategy"
            description="Optimize when and where to charge based on electricity prices, charging speeds, EU regulations, and availability."
            icon={
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
              </svg>
            }
            transitionDelay="0.1s"
            animationDelay="0.5s"
          />
          
          <FeatureCard 
            title="Real-time Adaptation"
            description="Dynamically adjust plans when conditions change due to traffic, charger availability, or delivery schedule changes."
            icon={
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
            }
            transitionDelay="0.2s"
            animationDelay="1s"
          />
        </div>
      </div>
    );
  }
  
  interface FeatureCardProps {
    title: string;
    description: string;
    icon: React.ReactNode;
    transitionDelay?: string;
    animationDelay?: string;
  }
  
  function FeatureCard({ title, description, icon, transitionDelay, animationDelay }: FeatureCardProps) {
    return (
      <div className="flex flex-col gap-2 hover:translate-y-[-5px] transition-transform duration-300 items-center" style={{ transitionDelay }}>
        <div className="bg-primary/10 p-3 rounded-full w-12 h-12 flex items-center justify-center animate-pulse-slow" style={{ animationDelay }}>
          {icon}
        </div>
        <h3 className="font-semibold text-lg">{title}</h3>
        <p className="text-muted-foreground text-sm text-center">{description}</p>
      </div>
    );
  }