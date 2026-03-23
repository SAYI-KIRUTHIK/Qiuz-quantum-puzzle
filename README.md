# 🧩 Qiuz: A Quantum Puzzle Game

Welcome to **Qiuz**, an interactive web game built to make learning Quantum Computing fun, visual, and story-driven! 

Instead of just looking at dry textbook math, Qiuz lets you physically wire up quantum circuits to solve puzzles, earn currency, and defeat hackers.

### 🎮 Features
* **🕵️‍♀️ Story Mode:** Play as Alice and Bob in an interactive spy-thriller. Learn real-world quantum cryptography (like BB84 and Teleportation) to stop Eve from stealing your data!
* **🧰 The Sandbox:** A free-play quantum circuit builder. Wire up qubits and watch the exact mathematical states and 3D Bloch spheres update in real-time.
* **🏆 Challenge Mode:** Solve randomly generated quantum puzzles against the clock to earn Catty-Coins.
* **🏪 The Lore Shop:** Spend your hard-earned coins to unlock textbook definitions and learn the physics behind the game.
* **💾 Cloud Saves:** Create a profile and pick up your game right where you left off.

### 🛠️ Tech Stack
This project runs entirely on Python, bridging the gap between game design and actual quantum physics engines.
* **Frontend UI:** Streamlit
* **Quantum Engine:** IBM Qiskit & Qiskit Aer
* **Database:** Supabase (PostgreSQL)
* **Visuals:** Matplotlib & LaTeX

### 🚀 How to Play Locally
Want to run the game on your own machine?

1. Clone this repository: or download the zip file 
   ```bash (in terminal)
   git clone [https://github.com/SAYI-KIRUTHIK/Qiuz-quantum-puzzle.git](https://github.com/SAYI-KIRUTHIK/Qiuz-quantum-puzzle.git)
2. Install the required dependencies: ( type the below code in the terminal where your file is in)

   pip install -r requirements.txt
3. Run the game

   streamlit run qiuz.py
