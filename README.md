# 🧩 Qiuz: A Quantum Puzzle Game

An interactive, gamified educational tool designed to introduce beginners and university students to the fundamentals of quantum gates. A quantum mini game 

**Play it live here:** [https://qiuz-quantum-puzzle-sa-k-hi-aminigame.streamlit.app/]

## 📖 Project Goal
Bridging the gap between abstract linear algebra and practical quantum computing can be difficult. This application gamifies the learning process by translating complex quantum state manipulation into an intuitive puzzle format by the means of visual interactions. 

Instead of presenting a static wall of equations, *Qiuz* utilizes a **"Learn-Play-Unlock"** campaign loop. Users must actively construct circuits using IBM's Qiskit framework to solve puzzles. Solving a puzzle dynamically unlocks the next chapter in the built-in Quantum Textbook, rewarding experimentation with formal knowledge.users must actively construct circuits to manipulate state vectors, leading to independent discovery of foundational concepts like superposition, Gates revesrsiblity, etc.

## ✨ Features
* **Interactive Circuit Builder:** Construct real quantum circuits using X (NOT), H (Hadamard), and CX (CNOT) gates (basic gates). More Challenges will be addes
* **Mathematical Validation:** The app runs accurate quantum simulations using IBM's Qiskit framework to generate and validate the resulting state vectors against target states.
* **Dynamic Visualization:** Circuits are rendered in real-time using Matplotlib, cleanly linking the visual gate layout to the mathematical output.
* **Progressive Difficulty:** Levels scale from simple 1-qubit bit-flips to a 2-qubit "Boss Level" where users must perfectly entangle a Bell State 1\sqrt(|00 > + |11 >, etc).
* **Gamified Economy:** Solving puzzles rewards users with "Catty-Coins" (🐈‍⬛), which can be spent in the Knowledge Shop to unlock accessible explanations of real-world quantum phenomena like Quantum Teleportation and many more coming in future updates.
* * **Campaign Progression:** 6 meticulously designed levels ranging from basic Pauli-X bit-flips to a 3-qubit Toffoli (CCNOT) Boss Level.
* **Dual-Tier Quantum Textbook:** Every concept (Bits, Notation, X, Y, Z, H, CNOT, CCNOT) features a toggle switch. Users can read the "High School Intuition" (e.g., the Y-Gate as a cartwheel) or instantly switch to the "University Math" (Unitary Matrices, Dirac Notation, and Bloch Sphere mapping).
* **The Quantum look-up chart sheet:** A quick-reference lookup table translating quantum symbols into classical digital logic equivalents.

## 🛠️ Technology Stack
* **Frontend/UI:** [Streamlit](https://streamlit.io/)
* **Quantum Logic Engine:** [Qiskit](https://qiskit.org/) (IBM)
* **Visual Rendering:** Matplotlib & NumPy

## 💻 How to Run Locally
If you want to run this project on your own machine:

1. Clone this repository or download requirements and qiuz.py files.
2. Install the required dependencies: ( type the below code in the terminal)

   pip install -r requirements.txt
