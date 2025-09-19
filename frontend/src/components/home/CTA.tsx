"use client";

export default function CTA() {
    return (
      <section className="py-20">
        <div className="container mx-auto max-w-5xl px-4">
          <div className="bg-gradient-to-r from-primary to-primary/80 text-primary-foreground rounded-lg p-8 md:p-12 text-center relative overflow-hidden shadow-lg animate-pulse-slow">
            {/* Shine effect overlay */}
            <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent shine-effect"></span>
            
            {/* Content with relative positioning to appear above the shine effect */}
            <div className="relative">
              <h2 className="text-3xl font-bold mb-4">Ready to optimize your e-truck fleet?</h2>
              <p className="text-lg mb-8 max-w-2xl mx-auto opacity-90">Join the sustainable logistics revolution with optily.eu AI dispatcher</p>
              <div className="flex gap-4 justify-center flex-wrap">
                <a 
                  href="https://calendar.app.google/wFGuAq55LVxxvrEe8"
                  className="inline-flex items-center justify-center rounded-lg text-base font-medium transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 bg-primary-foreground text-primary hover:scale-105 hover:shadow-[0_0_15px_rgba(255,255,255,0.5)] h-12 px-10 py-6 relative overflow-hidden shadow-md group"
                >
                  <span className="absolute inset-0 bg-gradient-to-r from-transparent via-primary/20 to-transparent shine-effect" style={{ animationDelay: "1.5s" }}></span>
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
        </div>
      </section>
    );
  }