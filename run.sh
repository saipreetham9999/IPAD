#!/bin/sh
 
 # Prevent iPad from sleeping
  keepAwake 
   
   # Force switch and sync with main
    lg2 checkout main
     lg2 fetch origin
      lg2 reset --hard origin/main 
       lg2 pull origin main
        
        # Update libraries and run
	 pip install -r requirements.txt
	  python app.py
