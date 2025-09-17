// HeroSection.tsx
export default function HeroSection() {
    return (
      <section className="pt-28  px-4">
        <div className="container mx-auto max-w-5xl">
          <div className="text-center mb-12">
            <h1 
              className="text-4xl md:text-6xl font-bold tracking-tight mb-6 opacity-0 animate-fade-in" 
              style={{ animationDelay: "0.2s", animationFillMode: "forwards" }}
            >
              AI Route Planning for E-Truck Fleets
            </h1>
            <p 
              className="text-xl text-muted-foreground max-w-3xl mx-auto opacity-0 animate-fade-in p-4"
              style={{ animationDelay: "0.4s", animationFillMode: "forwards" }}
            >
              optily is an AI dispatcher that optimizes routes, charging stops, and schedules for electric truck fleets, reducing costs while ensuring on-time deliveries.
            </p>
            
            {/* Book a Call button */}
            <div 
              className="mt-8 opacity-0 animate-fade-in"
              style={{ animationDelay: "0.6s", animationFillMode: "forwards" }}
            >
              <a 
                href="https://calendar.app.google/wFGuAq55LVxxvrEe8"
                className="inline-flex items-center justify-center rounded-lg text-base font-medium transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 bg-gradient-to-r from-primary to-primary/80 text-primary-foreground hover:scale-105 hover:shadow-[0_0_15px_rgba(59,130,246,0.5)] h-12 px-10 py-6 relative overflow-hidden animate-pulse-slow shadow-md group"
              >
                <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent shine-effect"></span>
                <span className="relative flex items-center gap-2">
                  Schedule a Demo
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12h14"></path>
                    <path d="m12 5 7 7-7 7"></path>
                  </svg>
                </span>
              </a>
            </div>
          </div>
        </div>
      </section>
    );
  }