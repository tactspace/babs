 

export default function Home() {
  return (
    <div className="font-sans min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="bg-primary rounded-md p-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary-foreground">
                <path d="M5 18h14.5M5 14h14.5M5 10h14.5M5 6h14.5M19.5 18v-6.75a2.25 2.25 0 0 0-2.25-2.25h-3a2.25 2.25 0 0 0-2.25 2.25V18"></path>
                <rect width="3" height="6" x="3.5" y="12" rx="1.5"></rect>
              </svg>
            </div>
            <span className="text-2xl font-bold">Babs</span>
          </div>
          <nav className="hidden md:flex gap-6">
            <a href="#features" className="text-sm font-medium hover:text-primary transition-colors">Features</a>
            <a href="#how-it-works" className="text-sm font-medium hover:text-primary transition-colors">How It Works</a>
            <a href="#demo" className="text-sm font-medium hover:text-primary transition-colors">Demo</a>
          </nav>
          <a href="/simulate" className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-9 px-4 py-2">
            Get Started
          </a>
        </div>
      </header>

      {/* Hero */}
      <section className="py-20 px-4">
        <div className="container mx-auto max-w-5xl">
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
              Smart Route Planning for E-Truck Fleets
            </h1>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Babs is an AI dispatcher that optimizes routes, charging stops, and schedules for electric truck fleets, reducing costs while ensuring on-time deliveries.
            </p>
          </div>
          
          <div className="grid gap-8 p-8 rounded-lg border bg-card text-card-foreground shadow-sm">
            <div className="grid md:grid-cols-3 gap-6">
              <div className="flex flex-col gap-2">
                <div className="bg-primary/10 p-3 rounded-full w-12 h-12 flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                    <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                    <path d="M2 17l10 5 10-5"></path>
                    <path d="M2 12l10 5 10-5"></path>
                  </svg>
                </div>
                <h3 className="font-semibold text-lg">Route Optimization</h3>
                <p className="text-muted-foreground text-sm">Intelligent algorithms find the most efficient routes considering traffic, weather, and delivery windows.</p>
              </div>
              
              <div className="flex flex-col gap-2">
                <div className="bg-primary/10 p-3 rounded-full w-12 h-12 flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                  </svg>
                </div>
                <h3 className="font-semibold text-lg">Charging Strategy</h3>
                <p className="text-muted-foreground text-sm">Optimize when and where to charge based on electricity prices, charging speeds, and availability.</p>
              </div>
              
              <div className="flex flex-col gap-2">
                <div className="bg-primary/10 p-3 rounded-full w-12 h-12 flex items-center justify-center">
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
                <p className="text-muted-foreground text-sm">Dynamically adjust plans when conditions change due to traffic, charger availability, or delivery schedule changes.</p>
              </div>
            </div>
          </div>
        </div>
      </section>
      
      {/* How it works */}
      <section id="how-it-works" className="py-16 bg-muted/50">
        <div className="container mx-auto max-w-5xl px-4">
          <h2 className="text-3xl font-bold mb-12 text-center">How Babs Works</h2>
          
          <div className="grid md:grid-cols-2 gap-12">
            <div className="space-y-6">
              <div className="flex gap-4 items-start">
                <div className="bg-primary text-primary-foreground rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0">1</div>
                <div>
                  <h3 className="font-semibold text-lg mb-2">Input Variables</h3>
                  <p className="text-muted-foreground">Babs takes delivery stops, truck specifications, charging locations, electricity prices, and driver schedules as input.</p>
                </div>
              </div>
              
              <div className="flex gap-4 items-start">
                <div className="bg-primary text-primary-foreground rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0">2</div>
                <div>
                  <h3 className="font-semibold text-lg mb-2">AI Processing</h3>
                  <p className="text-muted-foreground">Our algorithms analyze thousands of possible combinations to find the optimal route and charging strategy.</p>
                </div>
              </div>
              
              <div className="flex gap-4 items-start">
                <div className="bg-primary text-primary-foreground rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0">3</div>
                <div>
                  <h3 className="font-semibold text-lg mb-2">Optimized Plan</h3>
                  <p className="text-muted-foreground">Receive a detailed drive and charge plan that balances cost, time, and reliability.</p>
                </div>
              </div>
            </div>
            
            <div className="bg-card rounded-lg border shadow-sm p-6">
              <div className="text-sm font-mono space-y-2 text-muted-foreground">
                <p>Route #3: Świebodzin (PL) → Grünheide → Bamberg → Świebodzin (PL)</p>
                <p className="border-l-2 border-primary pl-4">
                  Optimized charging stops:<br/>
                  • Depot charging: 80% (€0.22/kWh)<br/>
                  • Public charging at Bamberg: 40% (€0.35/kWh)<br/>
                  • Total cost: €42.80<br/>
                  • Estimated arrival: On time
                </p>
                <p className="mt-4">Alternative scenario (weather delay +30min):</p>
                <p className="border-l-2 border-primary pl-4">
                  • Skip Bamberg charging<br/>
                  • Reroute to Berlin-Mitte fast charger<br/>
                  • New ETA: +15min (still within window)
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
      
      {/* CTA */}
      <section className="py-20">
        <div className="container mx-auto max-w-5xl px-4">
          <div className="bg-primary text-primary-foreground rounded-lg p-8 md:p-12 text-center">
            <h2 className="text-3xl font-bold mb-4">Ready to optimize your e-truck fleet?</h2>
            <p className="text-lg mb-8 max-w-2xl mx-auto opacity-90">Join the sustainable logistics revolution with Babs AI dispatcher.</p>
            <div className="flex gap-4 justify-center flex-wrap">
              <a href="/simulate" className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary-foreground text-primary hover:bg-primary-foreground/90 h-10 px-6 py-2">
                Try Simulation
              </a>
              <button className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-primary-foreground/20 bg-transparent hover:bg-primary-foreground/10 h-10 px-6 py-2">
                Learn More
              </button>
            </div>
          </div>
        </div>
      </section>
      
      {/* Footer */}
      <footer className="border-t border-border py-8">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="bg-primary rounded-md p-1">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary-foreground">
                  <path d="M5 18h14.5M5 14h14.5M5 10h14.5M5 6h14.5M19.5 18v-6.75a2.25 2.25 0 0 0-2.25-2.25h-3a2.25 2.25 0 0 0-2.25 2.25V18"></path>
                  <rect width="3" height="6" x="3.5" y="12" rx="1.5"></rect>
                </svg>
              </div>
              <span className="font-semibold">Babs</span>
            </div>
            
            <div className="flex gap-6 text-sm text-muted-foreground">
              <a href="#" className="hover:text-foreground transition-colors">Privacy</a>
              <a href="#" className="hover:text-foreground transition-colors">Terms</a>
              <a href="#" className="hover:text-foreground transition-colors">Contact</a>
            </div>
            
            <div className="text-sm text-muted-foreground">
              © 2025 Babs. All rights reserved.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
