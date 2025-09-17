// AnimationStyles.tsx
export default function AnimationStyles() {
  return (
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

      @keyframes shine {
        from {
          transform: translateX(-100%);
        }
        to {
          transform: translateX(100%);
        }
      }
      
      .shine-effect {
        animation: shine 3s infinite;
      }
    `}</style>
  );
}
