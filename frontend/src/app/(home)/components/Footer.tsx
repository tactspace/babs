// Footer.tsx
export default function Footer() {
    return (
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
    );
  }