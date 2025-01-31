document.addEventListener('DOMContentLoaded', () => {
    // Particles.js Configuration - Updated with darker blue and slightly more particles
    particlesJS('particles-js', {
      particles: {
        number: {
          value: 100,  // Increased from 80 to 100
          density: {
            enable: true,
            value_area: 800
          }
        },
        color: {
          value: '#0F3042'  // Darkened from primary blue to a deeper blue
        },
        shape: {
          type: 'circle',
          stroke: {
            width: 0,
            color: '#000000'
          }
        },
        opacity: {
          value: 0.4,  // Slightly increased opacity
          random: false,
          anim: {
            enable: true,
            speed: 1,
            opacity_min: 0.1,
            sync: false
          }
        },
        size: {
          value: 3,
          random: true,
          anim: {
            enable: true,
            speed: 40,
            size_min: 0.1,
            sync: false
          }
        },
        line_linked: {
          enable: true,
          distance: 150,
          color: '#1A5F7A',  // Changed to primary blue for connecting lines
          opacity: 0.5,  // Slightly increased opacity
          width: 1
        },
        move: {
          enable: true,
          speed: 4,
          direction: 'none',
          random: false,
          straight: false,
          out_mode: 'out',
          bounce: false,
          attract: {
            enable: false,
            rotateX: 600,
            rotateY: 1200
          }
        }
      },
      interactivity: {
        detect_on: 'canvas',
        events: {
          onhover: {
            enable: true,
            mode: 'repulse'
          },
          onclick: {
            enable: true,
            mode: 'push'
          },
          resize: true
        },
        modes: {
          repulse: {
            distance: 100,
            duration: 0.4
          },
          push: {
            particles_nb: 4
          }
        }
      },
      retina_detect: true
    });
  
    // Modal Functionality
    const loginModal = document.getElementById('loginModal');
    const signupModal = document.getElementById('signupModal');
    const openLoginModalBtn = document.getElementById('openLoginModal');
    const openSignupModalBtn = document.getElementById('openSignupModal');
    const closeButtons = document.querySelectorAll('.close-btn');
  
    // Open Login Modal
    openLoginModalBtn.addEventListener('click', (e) => {
      e.preventDefault();
      loginModal.style.display = 'block';
    });
  
    // Open Signup Modal
    openSignupModalBtn.addEventListener('click', (e) => {
      e.preventDefault();
      signupModal.style.display = 'block';
    });
  
    // Close Modals
    closeButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        loginModal.style.display = 'none';
        signupModal.style.display = 'none';
      });
    });
  
    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
      if (e.target === loginModal) loginModal.style.display = 'none';
      if (e.target === signupModal) signupModal.style.display = 'none';
    });
  
    // Form Submission Handlers (currently just preventing default)
    document.getElementById('loginForm').addEventListener('submit', (e) => {
      e.preventDefault();
      // Add login logic here
      console.log('Login submitted');
      loginModal.style.display = 'none';
    });
  
    document.getElementById('signupForm').addEventListener('submit', (e) => {
      e.preventDefault();
      // Add signup logic here
      console.log('Signup submitted');
      signupModal.style.display = 'none';
    });
  
    // Existing app.js code
    const searchInput = document.querySelector('.search-input');
    const voiceBtn = document.querySelector('.voice-btn');
    const fileUpload = document.getElementById('fileUpload');
    const fileUploadBtn = document.getElementById('fileUploadBtn');
  
    // Voice Input Handler
    voiceBtn.addEventListener('click', () => {
      if ('webkitSpeechRecognition' in window) {
        const recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
  
        recognition.onresult = (event) => {
          const transcript = event.results[0][0].transcript;
          searchInput.value = transcript;
        };
  
        recognition.start();
      } else {
        alert('Speech recognition is not supported in this browser.');
      }
    });
  
    // File Upload Handler
    fileUploadBtn.addEventListener('click', () => {
      fileUpload.click();
    });
  
    fileUpload.addEventListener('change', (event) => {
      const file = event.target.files[0];
      console.log('Uploaded file:', file);
      // Add file processing logic here
    });
  });